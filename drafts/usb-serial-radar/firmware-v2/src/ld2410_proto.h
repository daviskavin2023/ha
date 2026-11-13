// ld2410_proto.h — LD2410/LD2410C 串口协议的纯逻辑部分（不依赖 Arduino，可在电脑上单测）
// 帧格式依据 HLK LD2410 串口通信协议 + ESPHome components/ld2410 源码核对：
//   上报帧: F4 F3 F2 F1 | len_le16 | 数据 | F8 F7 F6 F5
//   命令帧: FD FC FB FA | len_le16 | cmd_le16 | value... | 04 03 02 01   (len = 2 + value 长度)
//   ACK帧 : FD FC FB FA | len_le16 | (cmd|0x0100)_le16 | status_le16(0=成功) | 返回值 | 04 03 02 01
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

namespace ld2410 {

static constexpr uint8_t CMD_ENABLE_CONF = 0xFF;  // value 01 00
static constexpr uint8_t CMD_END_CONF = 0xFE;
static constexpr uint8_t CMD_SET_MAXDIST = 0x60;  // 最大运动门/最大静止门/无人持续时间
static constexpr uint8_t CMD_READ_PARAMS = 0x61;
static constexpr uint8_t CMD_SET_GATE_SENS = 0x64;
static constexpr uint8_t CMD_READ_VERSION = 0xA0;
static constexpr uint8_t TOTAL_GATES = 9;  // 门 0..8

// 设置合法范围（与 ESPHome ld2410 number 实体范围一致）
static constexpr int MAX_GATE_MIN = 2, MAX_GATE_MAX = 8;
static constexpr int IDLE_MIN = 0, IDLE_MAX = 900;  // 秒
static constexpr int SENS_MIN = 0, SENS_MAX = 100;

struct Report {
  bool occupancy = false, moving = false, still = false;
  uint16_t detection_distance = 0, moving_distance = 0, still_distance = 0;
  uint8_t moving_energy = 0, still_energy = 0;
};

struct Config {
  bool valid = false;
  uint8_t max_move_gate = 0, max_still_gate = 0;
  uint8_t move_sens[TOTAL_GATES] = {0};
  uint8_t still_sens[TOTAL_GATES] = {0};
  uint16_t idle_s = 0;
  bool fw_valid = false;
  char fw[20] = {0};
};

// 组一条命令帧，返回总字节数；out 至少 10+vlen 字节
inline size_t build_cmd(uint8_t cmd, const uint8_t *val, uint8_t vlen, uint8_t *out) {
  size_t i = 0;
  out[i++] = 0xFD; out[i++] = 0xFC; out[i++] = 0xFB; out[i++] = 0xFA;
  out[i++] = (uint8_t)(2 + vlen); out[i++] = 0x00;
  out[i++] = cmd; out[i++] = 0x00;
  for (uint8_t k = 0; k < vlen; k++) out[i++] = val[k];
  out[i++] = 0x04; out[i++] = 0x03; out[i++] = 0x02; out[i++] = 0x01;
  return i;
}

// 0x60 参数：字 0x0000=最大运动门, 0x0001=最大静止门, 0x0002=无人持续时间；每个值 4 字节 LE
inline void build_maxdist_value(uint8_t mg, uint8_t sg, uint16_t idle, uint8_t v[18]) {
  const uint8_t t[18] = {0x00, 0x00, mg, 0, 0, 0, 0x01, 0x00, sg, 0, 0, 0,
                         0x02, 0x00, (uint8_t)(idle & 0xFF), (uint8_t)(idle >> 8), 0, 0};
  memcpy(v, t, 18);
}

// 0x64 参数：字 0x0000=门号(0xFFFF=全部门), 0x0001=运动灵敏度, 0x0002=静止灵敏度
inline void build_gate_sens_value(uint16_t gate, uint8_t mv, uint8_t st, uint8_t v[18]) {
  const uint8_t t[18] = {0x00, 0x00, (uint8_t)(gate & 0xFF), (uint8_t)(gate >> 8), 0, 0,
                         0x01, 0x00, mv, 0, 0, 0, 0x02, 0x00, st, 0, 0, 0};
  memcpy(v, t, 18);
}

enum class FrameKind : uint8_t { NONE, REPORT, ACK };

// 逐字节组帧，两种帧头都认。完成一帧返回 REPORT/ACK，payload 指向 len 之后的数据
class FrameParser {
 public:
  FrameKind feed(uint8_t b) {
    if (len_ == 0) {
      if (b == 0xF4 || b == 0xFD) buf_[len_++] = b;
      return FrameKind::NONE;
    }
    buf_[len_++] = b;
    if (len_ <= 4) {
      const bool rep = buf_[0] == 0xF4 && (len_ < 2 || buf_[1] == 0xF3) && (len_ < 3 || buf_[2] == 0xF2) &&
                       (len_ < 4 || buf_[3] == 0xF1);
      const bool ack = buf_[0] == 0xFD && (len_ < 2 || buf_[1] == 0xFC) && (len_ < 3 || buf_[2] == 0xFB) &&
                       (len_ < 4 || buf_[3] == 0xFA);
      if (!rep && !ack) {
        len_ = 0;
        if (b == 0xF4 || b == 0xFD) buf_[len_++] = b;
      }
      return FrameKind::NONE;
    }
    if (len_ < 6) return FrameKind::NONE;
    const uint16_t plen = (uint16_t)buf_[4] | ((uint16_t)buf_[5] << 8);
    const size_t total = 6UL + plen + 4UL;
    if (plen > 100 || total > sizeof(buf_)) {
      len_ = 0;
      return FrameKind::NONE;
    }
    if (len_ < total) return FrameKind::NONE;
    len_ = 0;
    const uint8_t *t = &buf_[total - 4];
    plen_ = plen;
    if (buf_[0] == 0xF4) {
      if (t[0] == 0xF8 && t[1] == 0xF7 && t[2] == 0xF6 && t[3] == 0xF5) return FrameKind::REPORT;
    } else {
      if (t[0] == 0x04 && t[1] == 0x03 && t[2] == 0x02 && t[3] == 0x01) return FrameKind::ACK;
    }
    return FrameKind::NONE;
  }
  const uint8_t *payload() const { return &buf_[6]; }
  size_t payload_len() const { return plen_; }

 private:
  uint8_t buf_[128];
  size_t len_ = 0;
  size_t plen_ = 0;
};

// 上报帧（基本/工程模式）：[01|02] AA state mov_d(2) mov_e st_d(2) st_e det_d(2) ...
// 与旧固件 parse_target_payload 完全相同的判定
inline bool parse_report(const uint8_t *p, size_t n, Report &r) {
  if (n < 11) return false;
  if (!(p[0] == 0x01 || p[0] == 0x02)) return false;
  if (p[1] != 0xAA) return false;
  const uint8_t tgt = p[2];
  r.moving = (tgt == 0x01 || tgt == 0x03);
  r.still = (tgt == 0x02 || tgt == 0x03);
  r.occupancy = (tgt != 0x00);
  r.moving_distance = (uint16_t)p[3] | ((uint16_t)p[4] << 8);
  r.moving_energy = p[5];
  r.still_distance = (uint16_t)p[6] | ((uint16_t)p[7] << 8);
  r.still_energy = p[8];
  r.detection_distance = (uint16_t)p[9] | ((uint16_t)p[10] << 8);
  return true;
}

// ACK 公共头：p[0]=命令字, p[1]=0x01, p[2..3]=状态(0 成功)
inline bool ack_header(const uint8_t *p, size_t n, uint8_t &cmd, bool &ok) {
  if (n < 4 || p[1] != 0x01) return false;
  cmd = p[0];
  ok = (p[2] == 0 && p[3] == 0);
  return true;
}

// 0x61 ACK: p[4]=AA p[5]=最大门N p[6]=最大运动门 p[7]=最大静止门 p[8..16]=运动灵敏度
//           p[17..25]=静止灵敏度 p[26..27]=无人持续时间(秒, LE)
inline bool parse_params_ack(const uint8_t *p, size_t n, Config &c) {
  if (n < 28 || p[4] != 0xAA) return false;
  c.max_move_gate = p[6];
  c.max_still_gate = p[7];
  for (uint8_t i = 0; i < TOTAL_GATES; i++) {
    c.move_sens[i] = p[8 + i];
    c.still_sens[i] = p[17 + i];
  }
  c.idle_s = (uint16_t)p[26] | ((uint16_t)p[27] << 8);
  c.valid = true;
  return true;
}

// 0xA0 ACK: p[4..5]=固件类型 p[6..11]=版本；格式同 ESPHome ld24xx::format_version_str
inline bool parse_version_ack(const uint8_t *p, size_t n, Config &c) {
  if (n < 12) return false;
  const uint8_t *v = &p[6];
  snprintf(c.fw, sizeof(c.fw), "%u.%02X.%02X%02X%02X%02X", v[1], v[0], v[5], v[4], v[3], v[2]);
  c.fw_valid = true;
  return true;
}

// ---- JSON 行（字段与旧固件逐字相同，只在末尾追加可选的一个附加字段）----
static constexpr size_t MAX_LINE = 250;  // HA state 上限 255，留余量（不含换行）

inline int base_json(const Report &r, char *out, size_t cap) {
  return snprintf(out, cap,
                  "{\"occupancy\":%s,\"moving\":%s,\"still\":%s,"
                  "\"detection_distance\":%u,\"moving_distance\":%u,\"still_distance\":%u,"
                  "\"moving_energy\":%u,\"still_energy\":%u",
                  r.occupancy ? "true" : "false", r.moving ? "true" : "false", r.still ? "true" : "false",
                  (unsigned)r.detection_distance, (unsigned)r.moving_distance, (unsigned)r.still_distance,
                  (unsigned)r.moving_energy, (unsigned)r.still_energy);
}

enum Extra : uint8_t { EX_NONE = 0, EX_CFG, EX_MS, EX_SS, EX_ACK };

// 附加片段（以逗号开头）。cfg_err 非空时输出失败信息
inline int extra_json(Extra ex, const Config &c, const char *cfg_err, uint32_t age_s, const char *ack, char *out,
                      size_t cap) {
  switch (ex) {
    case EX_CFG:
      if (cfg_err && cfg_err[0])
        return snprintf(out, cap, ",\"cfg\":{\"ok\":false,\"err\":\"%s\"}", cfg_err);
      return snprintf(out, cap, ",\"cfg\":{\"ok\":true,\"mg\":%u,\"sg\":%u,\"idle\":%u,\"fw\":\"%s\",\"age\":%lu}",
                      (unsigned)c.max_move_gate, (unsigned)c.max_still_gate, (unsigned)c.idle_s,
                      c.fw_valid ? c.fw : "", (unsigned long)age_s);
    case EX_MS:
    case EX_SS: {
      const uint8_t *a = (ex == EX_MS) ? c.move_sens : c.still_sens;
      return snprintf(out, cap, ",\"%s\":[%u,%u,%u,%u,%u,%u,%u,%u,%u]", ex == EX_MS ? "ms" : "ss", a[0], a[1], a[2],
                      a[3], a[4], a[5], a[6], a[7], a[8]);
    }
    case EX_ACK:
      return snprintf(out, cap, ",\"ack\":\"%s\"", ack ? ack : "");
    default:
      if (cap) out[0] = 0;
      return 0;
  }
}

// 组整行：base + 附加（若超过 MAX_LINE 则丢弃附加，保证 HA 永远拿到合法、<=250 字符的完整上报行）
// 返回行长（不含 '\n'），*extra_used 表示附加是否写入
inline size_t build_line(const Report &r, Extra ex, const Config &c, const char *cfg_err, uint32_t age_s,
                         const char *ack, char *out, size_t cap, bool *extra_used) {
  int n = base_json(r, out, cap);
  if (n < 0 || (size_t)n >= cap) n = 0;
  bool used = false;
  if (ex != EX_NONE) {
    char tmp[160];
    int m = extra_json(ex, c, cfg_err, age_s, ack, tmp, sizeof(tmp));
    if (m > 0 && (size_t)m < sizeof(tmp) && (size_t)(n + m + 1) <= MAX_LINE && (size_t)(n + m + 2) < cap) {
      memcpy(out + n, tmp, (size_t)m);
      n += m;
      used = true;
    }
  }
  out[n++] = '}';
  out[n] = 0;
  if (extra_used) *extra_used = used;
  return (size_t)n;
}

}  // namespace ld2410
