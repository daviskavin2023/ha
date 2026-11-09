#include "application.h"
#include "button.h"
#include "codecs/no_audio_codec.h"
#include "config.h"
#include "display/lcd_display.h"
#include "mcp_server.h"
#include "wifi_board.h"

#include <driver/i2c_master.h>
#include <driver/spi_common.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_log.h>
#include <esp_timer.h>
#include <atomic>

static const char* TAG = "MiniCube";

class MinicubeCodec : public NoAudioCodecSimplex {
    esp_timer_handle_t enable_timer_ = nullptr;
    std::mutex transition_mutex_;
    std::mutex gate_mutex_;
    bool requested_ = false;
    int64_t enable_after_us_ = 0;

public:
    MinicubeCodec()
        : NoAudioCodecSimplex(AUDIO_INPUT_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE, DAC_BCK_PIN,
                              DAC_LRCK_PIN, DAC_DATA_PIN, MIC_SCK_PIN, MIC_WS_PIN, MIC_DATA_PIN) {
        esp_timer_create_args_t timer = {};
        timer.callback = [](void* arg) {
            auto* self = static_cast<MinicubeCodec*>(arg);
            std::lock_guard<std::mutex> lock(self->gate_mutex_);
            if (self->requested_ && esp_timer_get_time() >= self->enable_after_us_)
                gpio_set_level(AMP_SD_PIN, 1);
        };
        timer.arg = this;
        timer.name = "amp_settle";
        ESP_ERROR_CHECK(esp_timer_create(&timer, &enable_timer_));
    }

    void EnableOutput(bool enable) override {
        // The timer runs on ESP_TIMER_TASK. It does not block the audio thread.
        std::lock_guard<std::mutex> transition(transition_mutex_);
        if (enable == output_enabled_)
            return;
        esp_timer_stop(enable_timer_);  // An inactive timer is harmless.
        {
            std::lock_guard<std::mutex> lock(gate_mutex_);
            requested_ = false;
            gpio_set_level(AMP_SD_PIN, 0);
        }
        NoAudioCodec::EnableOutput(enable);
        if (enable) {
            std::lock_guard<std::mutex> lock(gate_mutex_);
            requested_ = true;
            enable_after_us_ = esp_timer_get_time() + 10000;
            ESP_ERROR_CHECK(esp_timer_start_once(enable_timer_, 10000));
        }
    }
};

class MinicubeBoard : public WifiBoard {
    Button boot_button_{BOOT_BUTTON_GPIO};
    LcdDisplay* display_ = nullptr;
    i2c_master_bus_handle_t touch_bus_ = nullptr;
    i2c_master_dev_handle_t touch_dev_ = nullptr;
    std::atomic<bool> touch_available_{false};
    std::atomic<bool> touch_pressed_{false};
    std::atomic<int> touch_x_{-1};
    std::atomic<int> touch_y_{-1};

    void InitializeControlPins() {
        ESP_ERROR_CHECK(gpio_set_level(AMP_SD_PIN, 0));
        gpio_config_t amp = {};
        amp.pin_bit_mask = 1ULL << AMP_SD_PIN;
        amp.mode = GPIO_MODE_OUTPUT;
        ESP_ERROR_CHECK(gpio_config(&amp));
        gpio_config_t radar = {};
        radar.pin_bit_mask = 1ULL << RADAR_OUT_PIN;
        radar.mode = GPIO_MODE_INPUT;
        ESP_ERROR_CHECK(gpio_config(&radar));
    }

    void InitializeDisplay() {
        spi_bus_config_t bus = {};
        bus.mosi_io_num = DISPLAY_MOSI_PIN;
        bus.miso_io_num = GPIO_NUM_NC;
        bus.sclk_io_num = DISPLAY_CLK_PIN;
        bus.quadwp_io_num = GPIO_NUM_NC;
        bus.quadhd_io_num = GPIO_NUM_NC;
        bus.max_transfer_sz = DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t);
        ESP_ERROR_CHECK(spi_bus_initialize(SPI3_HOST, &bus, SPI_DMA_CH_AUTO));
        esp_lcd_panel_io_spi_config_t io = {};
        io.cs_gpio_num = DISPLAY_CS_PIN;
        io.dc_gpio_num = DISPLAY_DC_PIN;
        io.spi_mode = 0;
        io.pclk_hz = 20 * 1000 * 1000;
        io.trans_queue_depth = 10;
        io.lcd_cmd_bits = 8;
        io.lcd_param_bits = 8;
        esp_lcd_panel_io_handle_t panel_io = nullptr;
        ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(SPI3_HOST, &io, &panel_io));
        esp_lcd_panel_dev_config_t cfg = {};
        cfg.reset_gpio_num = GPIO_NUM_NC;  // IDF uses ST7789 software reset.
        cfg.rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB;
        cfg.bits_per_pixel = 16;
        esp_lcd_panel_handle_t panel = nullptr;
        ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(panel_io, &cfg, &panel));
        ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
        ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
        ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel, true));
        display_ = new SpiLcdDisplay(panel_io, panel, DISPLAY_WIDTH, DISPLAY_HEIGHT,
                                     DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y, false, false, false);
        ESP_LOGW(TAG, "Panel profile %dx%d, y-offset=%d requires physical validation",
                 DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_OFFSET_Y);
    }

    static void TouchTask(void* arg) {
        auto* self = static_cast<MinicubeBoard*>(arg);
        bool was_pressed = false;
        unsigned errors = 0;
        for (;;) {
            uint8_t reg = 0x02;
            uint8_t state[5] = {};
            esp_err_t err =
                i2c_master_transmit_receive(self->touch_dev_, &reg, 1, state, sizeof(state), 20);
            if (err == ESP_OK) {
                self->touch_available_.store(true);
                errors = 0;
                bool pressed = (state[0] & 0x0f) != 0;
                self->touch_pressed_.store(pressed);
                self->touch_x_.store(((state[1] & 0x0f) << 8) | state[2]);
                self->touch_y_.store(((state[3] & 0x0f) << 8) | state[4]);
                if (was_pressed && !pressed) {
                    auto& app = Application::GetInstance();
                    app.Schedule([&app]() { app.ToggleChatState(); });
                }
                was_pressed = pressed;
            } else {
                // Do not turn a failed read into a tap/release or a reboot.
                self->touch_available_.store(false);
                self->touch_pressed_.store(false);
                was_pressed = false;
                if (++errors == 1 || errors % 250 == 0)
                    ESP_LOGW(TAG, "Touch polling failed: %s", esp_err_to_name(err));
            }
            vTaskDelay(pdMS_TO_TICKS(20));
        }
    }

    void InitializeTouch() {
#if CONFIG_MINICUBE_TOUCH_POLL
        i2c_master_bus_config_t cfg = {};
        cfg.i2c_port = I2C_NUM_0;
        cfg.sda_io_num = TOUCH_SDA_PIN;
        cfg.scl_io_num = TOUCH_SCL_PIN;
        cfg.clk_source = I2C_CLK_SRC_DEFAULT;
        cfg.glitch_ignore_cnt = 7;
        cfg.flags.enable_internal_pullup = true;
        ESP_ERROR_CHECK(i2c_new_master_bus(&cfg, &touch_bus_));
        if (i2c_master_probe(touch_bus_, 0x15, 100) != ESP_OK) {
            ESP_LOGW(TAG, "No initial touch ACK at 0x15; polling will retry in background");
        }
        i2c_device_config_t dev = {};
        dev.dev_addr_length = I2C_ADDR_BIT_LEN_7;
        dev.device_address = 0x15;
        dev.scl_speed_hz = 100000;
        ESP_ERROR_CHECK(i2c_master_bus_add_device(touch_bus_, &dev, &touch_dev_));
        BaseType_t created = xTaskCreate(TouchTask, "minicube_touch", 3072, this, 1, nullptr);
        if (created != pdPASS)
            ESP_LOGE(TAG, "Cannot create touch polling task");
#endif
    }

    void InitializeTools() {
        McpServer::GetInstance().AddTool(
            "self.minicube.status",
            "Read presence OUT and touch status; does not change sensor settings", PropertyList(),
            [this](const PropertyList&) -> ReturnValue {
                return std::string("{\"presence_out\":") +
                       (gpio_get_level(RADAR_OUT_PIN) ? "true" : "false") +
                       ",\"touch_available\":" + (touch_available_.load() ? "true" : "false") +
                       ",\"touch_pressed\":" + (touch_pressed_.load() ? "true" : "false") +
                       ",\"touch_x\":" + std::to_string(touch_x_.load()) +
                       ",\"touch_y\":" + std::to_string(touch_y_.load()) + "}";
            });
    }

public:
    MinicubeBoard() {
        InitializeControlPins();
        InitializeDisplay();
        InitializeTouch();
        InitializeTools();
        boot_button_.OnClick([this]() {
            auto& app = Application::GetInstance();
            app.Schedule([this, &app]() {
                if (app.GetDeviceState() == kDeviceStateStarting)
                    EnterWifiConfigMode();
                else
                    app.ToggleChatState();
            });
        });
    }

    AudioCodec* GetAudioCodec() override {
        static MinicubeCodec codec;
        return &codec;
    }
    Display* GetDisplay() override { return display_; }
    Backlight* GetBacklight() override { return nullptr; }
};

DECLARE_BOARD(MinicubeBoard);
