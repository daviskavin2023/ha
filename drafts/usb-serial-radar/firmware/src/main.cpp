/**
 * 待审草稿固件：ESP32-S3 + LD2410C → CH343(UART0) 每秒一行 JSON
 * 对齐 3038 esphome/ld2410-radar.yaml：
 *   雷达 UART 256000, ESP TX=GPIO17, RX=GPIO18
 *   USB 串口 JSON: UART0 @ 115200（CH343 Type-C）
 * platform: espressif32@6.9.0 = Arduino-ESP32 2.x
 * ARDUINO_USB_CDC_ON_BOOT=0 → Serial 走 UART0/CH343，不是原生 USB CDC
 */
#include <Arduino.h>
#include <esp_task_wdt.h>
#include <WiFi.h>
#include <esp_bt.h>

static constexpr int PIN_RADAR_TX = 17;  // ESP -> radar RX
static constexpr int PIN_RADAR_RX = 18;  // ESP <- radar TX
static constexpr uint32_t RADAR_BAUD = 256000;
static constexpr uint32_t USB_BAUD = 115200;
static constexpr uint32_t WDT_SECONDS = 8;

HardwareSerial RadarSerial(1);  // UART1

struct RadarState {
  bool occupancy = false;
  bool moving = false;
  bool still = false;
  uint16_t detection_distance = 0;
  uint16_t moving_distance = 0;
  uint16_t still_distance = 0;
  uint8_t moving_energy = 0;
  uint8_t still_energy = 0;
  uint32_t last_frame_ms = 0;
};

static RadarState g_state;
static uint8_t g_buf[128];
static size_t g_len = 0;

// LD2410/LD2410C 目标/工程上报帧：
// F4 F3 F2 F1 | len_le16 | [01|02] AA | state | mov_d_le16 | mov_e |
// still_d_le16 | still_e | det_d_le16 | ... | F8 F7 F6 F5
// state: 0=无, 1=运动, 2=静止, 3=运动+静止
static void parse_target_payload(const uint8_t *p, size_t n) {
  if (n < 11) return;
  const uint8_t dtype = p[0];
  if (!(dtype == 0x01 || dtype == 0x02)) return;
  if (p[1] != 0xAA) return;

  const uint8_t tgt = p[2];
  const uint16_t mov_d = (uint16_t)p[3] | ((uint16_t)p[4] << 8);
  const uint8_t mov_e = p[5];
  const uint16_t st_d = (uint16_t)p[6] | ((uint16_t)p[7] << 8);
  const uint8_t st_e = p[8];
  const uint16_t det_d = (uint16_t)p[9] | ((uint16_t)p[10] << 8);

  g_state.moving = (tgt == 0x01 || tgt == 0x03);
  g_state.still = (tgt == 0x02 || tgt == 0x03);
  g_state.occupancy = (tgt != 0x00);
  g_state.moving_distance = mov_d;
  g_state.moving_energy = mov_e;
  g_state.still_distance = st_d;
  g_state.still_energy = st_e;
  g_state.detection_distance = det_d;
  g_state.last_frame_ms = millis();
}

static void feed_byte(uint8_t b) {
  if (g_len == 0) {
    if (b == 0xF4) g_buf[g_len++] = b;
    return;
  }
  g_buf[g_len++] = b;
  if (g_len == 4) {
    if (!(g_buf[0] == 0xF4 && g_buf[1] == 0xF3 && g_buf[2] == 0xF2 && g_buf[3] == 0xF1)) {
      g_len = 0;
      if (b == 0xF4) g_buf[g_len++] = b;
    }
    return;
  }
  if (g_len < 6) return;
  const uint16_t payload_len = (uint16_t)g_buf[4] | ((uint16_t)g_buf[5] << 8);
  const size_t total = 6UL + payload_len + 4UL;  // head4 + len2 + payload + tail4
  if (payload_len > 100 || total > sizeof(g_buf)) {
    g_len = 0;
    return;
  }
  if (g_len < total) return;
  if (g_buf[total - 4] == 0xF8 && g_buf[total - 3] == 0xF7 && g_buf[total - 2] == 0xF6 &&
      g_buf[total - 1] == 0xF5) {
    parse_target_payload(&g_buf[6], payload_len);
  }
  g_len = 0;
}

static void emit_json() {
  // 字段名与 ha/04-configuration.yaml.snippet 中 from_json 一致
  Serial.printf(
      "{\"occupancy\":%s,\"moving\":%s,\"still\":%s,"
      "\"detection_distance\":%u,\"moving_distance\":%u,\"still_distance\":%u,"
      "\"moving_energy\":%u,\"still_energy\":%u}\n",
      g_state.occupancy ? "true" : "false", g_state.moving ? "true" : "false",
      g_state.still ? "true" : "false", (unsigned)g_state.detection_distance,
      (unsigned)g_state.moving_distance, (unsigned)g_state.still_distance,
      (unsigned)g_state.moving_energy, (unsigned)g_state.still_energy);
}

void setup() {
  // Arduino-ESP32 2.x (espressif32@6.9.0)
  esp_task_wdt_init(WDT_SECONDS, true);
  esp_task_wdt_add(NULL);

  WiFi.mode(WIFI_OFF);
  btStop();

  // Serial = UART0 = CH343（须 ARDUINO_USB_CDC_ON_BOOT=0）
  Serial.begin(USB_BAUD);
  delay(200);
  // UART1: rx=18, tx=17, 256000 8N1
  RadarSerial.begin(RADAR_BAUD, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);
}

void loop() {
  esp_task_wdt_reset();
  while (RadarSerial.available()) {
    feed_byte((uint8_t)RadarSerial.read());
  }
  static uint32_t last_emit = 0;
  const uint32_t now = millis();
  if (now - last_emit >= 1000) {
    last_emit = now;
    if (g_state.last_frame_ms != 0 && (now - g_state.last_frame_ms) > 3000) {
      g_state.occupancy = false;
      g_state.moving = false;
      g_state.still = false;
    }
    emit_json();
  }
}
