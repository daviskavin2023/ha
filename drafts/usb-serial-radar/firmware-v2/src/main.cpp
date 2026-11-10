/**
 * 待审草稿固件 v2：ESP32-S3 + LD2410C → CH343(UART0) 每秒一行 JSON + 读取/修改雷达配置
 * 对齐 3038 esphome/ld2410-radar.yaml：
 *   雷达 UART 256000, ESP TX=GPIO17, RX=GPIO18
 *   USB 串口 JSON: UART0 @ 115200（CH343 Type-C）
 * platform: espressif32@6.9.0 = Arduino-ESP32 2.x
 * ARDUINO_USB_CDC_ON_BOOT=0 → Serial 走 UART0/CH343，不是原生 USB CDC
 *
 * v2 相对 v1（已上线 2026-11-10）：
 *  - 每秒一行 JSON 不变：8 个原字段、顺序、格式逐字相同；没有附加信息的行与 v1 逐字节一致
 *  - 开机 3 秒后、之后每 10 分钟、或收到 USB 命令 GET 时：进配置模式(0xFF) → 读固件版本(0xA0)
 *    → 读参数(0x61) → 退出配置模式(0xFE)。开机只读，绝不写参数
 *  - 读到的配置分 3 行附在正常上报行末尾（每行最多一个附加字段，整行 <=250 字符）：
 *      "cfg":{"ok":true,"mg":最大运动门,"sg":最大静止门,"idle":无人持续秒,"fw":"版本","age":距读取秒}
 *      "ms":[门0..8 运动灵敏度]      "ss":[门0..8 静止灵敏度]
 *    读取后立即发一轮，之后每 60 秒重发一轮（HA 重启后 1 分钟内能拿到）
 *  - USB 串口文本命令（以 \n 或 \r 结尾，大小写不敏感）：
 *      GET
 *      SET MAXGATE <运动门 2-8> <静止门 2-8> <无人秒 0-900>
 *      SET SENS <门 0-8|ALL> <运动 0-100> <静止 0-100>
 *    结果以 "ack":"..." 附在下一行上报里，设置成功后自动重读配置
 *    不提供恢复出厂、重启雷达、改波特率、改蓝牙等命令
 */
#include <Arduino.h>
#include <esp_task_wdt.h>
#include <WiFi.h>
#include <esp_bt.h>
#include <ctype.h>
#include <stdlib.h>

#include "ld2410_proto.h"

using namespace ld2410;

static constexpr int PIN_RADAR_TX = 17;  // ESP -> radar RX
static constexpr int PIN_RADAR_RX = 18;  // ESP <- radar TX
static constexpr uint32_t RADAR_BAUD = 256000;
static constexpr uint32_t USB_BAUD = 115200;
static constexpr uint32_t WDT_SECONDS = 8;

static constexpr uint32_t BOOT_READ_DELAY_MS = 3000;
static constexpr uint32_t PERIODIC_READ_MS = 10UL * 60UL * 1000UL;
static constexpr uint32_t ANNOUNCE_MS = 60UL * 1000UL;
static constexpr uint32_t MIN_TXN_GAP_MS = 2000;
static constexpr uint32_t ACK_TIMEOUT_MS = 400;
static constexpr uint32_t STUCK_REPORT_MS = 10000;  // 10 秒无上报帧：补发一次退出配置模式

HardwareSerial RadarSerial(1);  // UART1

static Report g_report;
static uint32_t g_last_frame_ms = 0;
static FrameParser g_parser;

static Config g_cfg;
static uint32_t g_cfg_read_ms = 0;
static char g_cfg_err[16] = "";
static bool g_cfg_attempted = false;

// 最近一次 ACK
static uint8_t g_ack_cmd = 0;
static bool g_ack_ok = false;
static bool g_ack_seen = false;

// 附加字段队列：bit 1=cfg 2=ms 3=ss 4=ack
static uint8_t g_pending = 0;
static char g_ack_text[40] = "";

static uint32_t g_last_emit = 0;
static uint32_t g_last_txn_ms = 0;
static uint32_t g_last_announce = 0;
static uint32_t g_last_periodic = 0;
static bool g_boot_read_done = false;
static uint32_t g_last_unstick = 0;

static inline void set_pending(Extra e) { g_pending |= (uint8_t)(1u << e); }

static Extra take_pending() {
  static const Extra order[] = {EX_ACK, EX_CFG, EX_MS, EX_SS};
  for (Extra e : order) {
    if (g_pending & (1u << e)) {
      g_pending &= (uint8_t) ~(1u << e);
      return e;
    }
  }
  return EX_NONE;
}

static void announce_cfg() {
  if (!g_cfg_attempted) return;
  set_pending(EX_CFG);
  if (g_cfg.valid && g_cfg_err[0] == 0) {
    set_pending(EX_MS);
    set_pending(EX_SS);
  }
}

static void handle_frame(FrameKind k) {
  const uint8_t *p = g_parser.payload();
  const size_t n = g_parser.payload_len();
  if (k == FrameKind::REPORT) {
    if (parse_report(p, n, g_report)) g_last_frame_ms = millis();
  } else if (k == FrameKind::ACK) {
    uint8_t cmd;
    bool ok;
    if (!ack_header(p, n, cmd, ok)) return;
    g_ack_cmd = cmd;
    g_ack_ok = ok;
    g_ack_seen = true;
    if (ok && cmd == CMD_READ_PARAMS) {
      Config c = g_cfg;
      if (parse_params_ack(p, n, c)) g_cfg = c;
      else g_ack_ok = false;
    } else if (ok && cmd == CMD_READ_VERSION) {
      parse_version_ack(p, n, g_cfg);
    }
  }
}

static void pump_radar() {
  while (RadarSerial.available()) {
    FrameKind k = g_parser.feed((uint8_t)RadarSerial.read());
    if (k != FrameKind::NONE) handle_frame(k);
  }
}

// 每秒一行；与 v1 相同的 3 秒无帧清零规则
static void tick_emit() {
  const uint32_t now = millis();
  if (now - g_last_emit < 1000) return;
  g_last_emit = now;
  if (g_last_frame_ms != 0 && (now - g_last_frame_ms) > 3000) {
    g_report.occupancy = false;
    g_report.moving = false;
    g_report.still = false;
  }
  const Extra ex = take_pending();
  const uint32_t age = g_cfg_read_ms ? (now - g_cfg_read_ms) / 1000 : 0;
  char line[256];
  bool used = false;
  build_line(g_report, ex, g_cfg, g_cfg_err, age, g_ack_text, line, sizeof(line), &used);
  Serial.print(line);
  Serial.print('\n');
}

static void send_cmd(uint8_t cmd, const uint8_t *val, uint8_t vlen) {
  uint8_t f[32];
  const size_t n = build_cmd(cmd, val, vlen, f);
  RadarSerial.write(f, n);
  RadarSerial.flush();
}

// 发命令并等对应 ACK；等待时继续解析上报帧、继续每秒发 JSON、继续喂狗
static bool cmd_wait(uint8_t cmd, const uint8_t *val, uint8_t vlen, uint32_t timeout_ms = ACK_TIMEOUT_MS) {
  g_ack_seen = false;
  send_cmd(cmd, val, vlen);
  const uint32_t t0 = millis();
  while (millis() - t0 < timeout_ms) {
    esp_task_wdt_reset();
    pump_radar();
    if (g_ack_seen && g_ack_cmd == cmd) return g_ack_ok;
    tick_emit();
    delay(2);
  }
  return false;
}

static bool enter_config() {
  const uint8_t v[2] = {0x01, 0x00};
  if (cmd_wait(CMD_ENABLE_CONF, v, 2)) return true;
  delay(100);
  return cmd_wait(CMD_ENABLE_CONF, v, 2);  // 重试一次
}

static void leave_config() {
  if (!cmd_wait(CMD_END_CONF, nullptr, 0)) cmd_wait(CMD_END_CONF, nullptr, 0);
}

// 只读：版本 + 参数
static bool txn_read() {
  g_last_txn_ms = millis();
  g_cfg_attempted = true;
  bool ok = false;
  if (!enter_config()) {
    strncpy(g_cfg_err, "noack_ff", sizeof(g_cfg_err));
    leave_config();  // 万一已进入配置模式，确保退出
  } else {
    cmd_wait(CMD_READ_VERSION, nullptr, 0);  // 失败不影响参数读取
    Config before = g_cfg;
    g_cfg.valid = false;
    ok = cmd_wait(CMD_READ_PARAMS, nullptr, 0) && g_cfg.valid;
    if (!ok) {
      g_cfg = before;
      strncpy(g_cfg_err, "noack_61", sizeof(g_cfg_err));
    } else {
      g_cfg_err[0] = 0;
      g_cfg_read_ms = millis();
    }
    leave_config();
  }
  announce_cfg();
  g_last_announce = millis();
  return ok;
}

static void set_ack(const char *s) {
  strncpy(g_ack_text, s, sizeof(g_ack_text) - 1);
  g_ack_text[sizeof(g_ack_text) - 1] = 0;
  set_pending(EX_ACK);
}

// 写参数：只在收到 USB 命令时执行
static void txn_write(uint8_t cmd, const uint8_t v[18], const char *name) {
  g_last_txn_ms = millis();
  char msg[40];
  if (!enter_config()) {
    leave_config();
    snprintf(msg, sizeof(msg), "%s err noack_ff", name);
    set_ack(msg);
    return;
  }
  const bool ok = cmd_wait(cmd, v, 18);
  leave_config();
  snprintf(msg, sizeof(msg), "%s %s", name, ok ? "ok" : "err radar");
  set_ack(msg);
  delay(50);
  txn_read();  // 写完立刻回读，HA 看到的永远是雷达里的真实值
}

// ---- USB 文本命令 ----
static bool parse_int(const char *s, int lo, int hi, int &out) {
  if (!s || !*s) return false;
  char *end = nullptr;
  long v = strtol(s, &end, 10);
  if (*end != 0 || v < lo || v > hi) return false;
  out = (int)v;
  return true;
}

static void handle_command(char *line) {
  for (char *c = line; *c; c++) *c = (char)toupper((unsigned char)*c);
  char *tok[6] = {0};
  int nt = 0;
  for (char *t = strtok(line, " \t"); t && nt < 6; t = strtok(nullptr, " \t")) tok[nt++] = t;
  if (nt == 0) return;

  if (millis() - g_last_txn_ms < MIN_TXN_GAP_MS && g_last_txn_ms != 0) {
    set_ack("err busy");
    return;
  }
  if (nt == 1 && strcmp(tok[0], "GET") == 0) {
    txn_read();
    set_ack(g_cfg_err[0] ? "get err" : "get ok");
    return;
  }
  if (nt == 5 && strcmp(tok[0], "SET") == 0 && strcmp(tok[1], "MAXGATE") == 0) {
    int mg, sg, idle;
    if (!parse_int(tok[2], MAX_GATE_MIN, MAX_GATE_MAX, mg) || !parse_int(tok[3], MAX_GATE_MIN, MAX_GATE_MAX, sg) ||
        !parse_int(tok[4], IDLE_MIN, IDLE_MAX, idle)) {
      set_ack("maxgate err range");
      return;
    }
    uint8_t v[18];
    build_maxdist_value((uint8_t)mg, (uint8_t)sg, (uint16_t)idle, v);
    txn_write(CMD_SET_MAXDIST, v, "maxgate");
    return;
  }
  if (nt == 5 && strcmp(tok[0], "SET") == 0 && strcmp(tok[1], "SENS") == 0) {
    int gate = 0, mv, st;
    uint16_t gw;
    if (strcmp(tok[2], "ALL") == 0) {
      gw = 0xFFFF;
    } else if (parse_int(tok[2], 0, TOTAL_GATES - 1, gate)) {
      gw = (uint16_t)gate;
    } else {
      set_ack("sens err range");
      return;
    }
    if (!parse_int(tok[3], SENS_MIN, SENS_MAX, mv) || !parse_int(tok[4], SENS_MIN, SENS_MAX, st)) {
      set_ack("sens err range");
      return;
    }
    uint8_t v[18];
    build_gate_sens_value(gw, (uint8_t)mv, (uint8_t)st, v);
    txn_write(CMD_SET_GATE_SENS, v, "sens");
    return;
  }
  set_ack("err unknown");
}

static void pump_usb() {
  static char buf[64];
  static size_t n = 0;
  static bool overflow = false;
  while (Serial.available()) {
    const int c = Serial.read();
    if (c < 0) break;
    if (c == '\n' || c == '\r') {
      if (!overflow && n > 0) {
        buf[n] = 0;
        handle_command(buf);
      } else if (overflow) {
        set_ack("err toolong");
      }
      n = 0;
      overflow = false;
    } else if (c >= 0x20 && c < 0x7F) {
      if (n < sizeof(buf) - 1) buf[n++] = (char)c;
      else overflow = true;
    }
    // 其它控制字符/非 ASCII 直接丢弃
  }
}

void setup() {
  esp_task_wdt_init(WDT_SECONDS, true);
  esp_task_wdt_add(NULL);

  WiFi.mode(WIFI_OFF);
  btStop();

  Serial.begin(USB_BAUD);
  delay(200);
  RadarSerial.begin(RADAR_BAUD, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);
}

void loop() {
  esp_task_wdt_reset();
  pump_radar();
  pump_usb();

  const uint32_t now = millis();
  if (!g_boot_read_done && now >= BOOT_READ_DELAY_MS) {
    g_boot_read_done = true;
    txn_read();
    g_last_periodic = millis();
  } else if (g_boot_read_done && now - g_last_periodic >= PERIODIC_READ_MS) {
    g_last_periodic = now;
    if (now - g_last_txn_ms >= MIN_TXN_GAP_MS) txn_read();
  } else if (g_cfg_attempted && now - g_last_announce >= ANNOUNCE_MS) {
    g_last_announce = now;
    announce_cfg();
  }

  // 自愈：超过 10 秒收不到上报帧（可能卡在配置模式），每 10 秒补发一次退出配置模式
  if (g_boot_read_done && (now - g_last_frame_ms) > STUCK_REPORT_MS && now - g_last_unstick > STUCK_REPORT_MS &&
      now - g_last_txn_ms > STUCK_REPORT_MS) {
    g_last_unstick = now;
    send_cmd(CMD_END_CONF, nullptr, 0);
  }

  tick_emit();
}
