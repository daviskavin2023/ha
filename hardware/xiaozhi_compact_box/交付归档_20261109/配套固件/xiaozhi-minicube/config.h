#pragma once

#include <driver/gpio.h>
#include "sdkconfig.h"

// These assignments follow the actual carrier nets, not the stock breadboard.
#define AUDIO_INPUT_SAMPLE_RATE 16000
#define AUDIO_OUTPUT_SAMPLE_RATE 24000
#define MIC_DATA_PIN GPIO_NUM_4
#define MIC_WS_PIN GPIO_NUM_5
#define MIC_SCK_PIN GPIO_NUM_6
#define DAC_BCK_PIN GPIO_NUM_7
#define DAC_LRCK_PIN GPIO_NUM_15
#define DAC_DATA_PIN GPIO_NUM_16
#define AMP_SD_PIN GPIO_NUM_9
#define RADAR_OUT_PIN GPIO_NUM_8
#define TOUCH_SCL_PIN GPIO_NUM_1
#define TOUCH_SDA_PIN GPIO_NUM_2
#define DISPLAY_MOSI_PIN GPIO_NUM_12
#define DISPLAY_DC_PIN GPIO_NUM_10
#define DISPLAY_CLK_PIN GPIO_NUM_11
#define DISPLAY_CS_PIN GPIO_NUM_13
#define BOOT_BUTTON_GPIO GPIO_NUM_0

// Eight-wire panel: do not drive unidentified BL/RST/INT solder pads.
#define DISPLAY_RST_PIN GPIO_NUM_NC
#define DISPLAY_BACKLIGHT_PIN GPIO_NUM_NC
#define DISPLAY_WIDTH 240
#define DISPLAY_HEIGHT CONFIG_MINICUBE_LCD_HEIGHT
#define DISPLAY_OFFSET_X 0
#define DISPLAY_OFFSET_Y CONFIG_MINICUBE_LCD_OFFSET_Y

#if DISPLAY_HEIGHT + DISPLAY_OFFSET_Y > 320
#error "MiniCube display height plus offset exceeds ST7789 RAM height"
#endif

// This profile excludes PSRAM, UART0, USB, strap and optional solder-pad pins.
constexpr int kMinicubeFunctionalPins[] = {4, 5, 6, 7, 15, 16, 9, 8, 1, 2, 12, 10, 11, 13};
constexpr bool MinicubePinsAreDistinct() {
    for (unsigned i = 0; i < sizeof(kMinicubeFunctionalPins) / sizeof(int); ++i) {
        for (unsigned j = i + 1; j < sizeof(kMinicubeFunctionalPins) / sizeof(int); ++j) {
            if (kMinicubeFunctionalPins[i] == kMinicubeFunctionalPins[j])
                return false;
        }
    }
    return true;
}
static_assert(MinicubePinsAreDistinct(), "MiniCube functional GPIO conflict");
