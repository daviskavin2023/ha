#include "../src/ld2410_proto.h"
#include <assert.h>
#include <stdio.h>
using namespace ld2410;
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL line %d: %s\n", __LINE__, #c); fails++; } } while (0)
static void feed_all(FrameParser &p, const uint8_t *b, size_t n, FrameKind &last) {
  last = FrameKind::NONE;
  for (size_t i = 0; i < n; i++) { FrameKind k = p.feed(b[i]); if (k != FrameKind::NONE) last = k; }
}
int main() {
  // 1. 命令帧：与协议文档示例一致 —— 使能配置 FD FC FB FA 04 00 FF 00 01 00 04 03 02 01
  uint8_t f[40]; const uint8_t v1[2] = {1, 0};
  size_t n = build_cmd(CMD_ENABLE_CONF, v1, 2, f);
  const uint8_t exp_ff[] = {0xFD,0xFC,0xFB,0xFA,0x04,0x00,0xFF,0x00,0x01,0x00,0x04,0x03,0x02,0x01};
  CHECK(n == sizeof(exp_ff) && memcmp(f, exp_ff, n) == 0);
  n = build_cmd(CMD_READ_PARAMS, nullptr, 0, f);
  const uint8_t exp_61[] = {0xFD,0xFC,0xFB,0xFA,0x02,0x00,0x61,0x00,0x04,0x03,0x02,0x01};
  CHECK(n == sizeof(exp_61) && memcmp(f, exp_61, n) == 0);
  n = build_cmd(CMD_END_CONF, nullptr, 0, f);
  const uint8_t exp_fe[] = {0xFD,0xFC,0xFB,0xFA,0x02,0x00,0xFE,0x00,0x04,0x03,0x02,0x01};
  CHECK(n == sizeof(exp_fe) && memcmp(f, exp_fe, n) == 0);
  // 0x60 协议示例：最大运动门8 静止门8 无人5秒 →
  // FD FC FB FA 14 00 60 00 00 00 08 00 00 00 01 00 08 00 00 00 02 00 05 00 00 00 04 03 02 01
  uint8_t v[18]; build_maxdist_value(8, 8, 5, v); n = build_cmd(CMD_SET_MAXDIST, v, 18, f);
  const uint8_t exp_60[] = {0xFD,0xFC,0xFB,0xFA,0x14,0x00,0x60,0x00,0x00,0x00,0x08,0x00,0x00,0x00,0x01,0x00,0x08,0x00,0x00,0x00,0x02,0x00,0x05,0x00,0x00,0x00,0x04,0x03,0x02,0x01};
  CHECK(n == sizeof(exp_60) && memcmp(f, exp_60, n) == 0);
  // 0x64 协议示例：全部门 运动40 静止40 →
  // FD FC FB FA 14 00 64 00 00 00 FF FF 00 00 01 00 28 00 00 00 02 00 28 00 00 00 04 03 02 01
  build_gate_sens_value(0xFFFF, 40, 40, v); n = build_cmd(CMD_SET_GATE_SENS, v, 18, f);
  const uint8_t exp_64[] = {0xFD,0xFC,0xFB,0xFA,0x14,0x00,0x64,0x00,0x00,0x00,0xFF,0xFF,0x00,0x00,0x01,0x00,0x28,0x00,0x00,0x00,0x02,0x00,0x28,0x00,0x00,0x00,0x04,0x03,0x02,0x01};
  CHECK(n == sizeof(exp_64) && memcmp(f, exp_64, n) == 0);

  // 2. 0x61 ACK 示例（协议文档）：
  // FD FC FB FA 1C 00 61 01 00 00 AA 08 08 08 14 14 14 14 14 14 14 14 14 19 19 19 19 19 19 19 19 19 05 00 04 03 02 01
  const uint8_t ack61[] = {0xFD,0xFC,0xFB,0xFA,0x1C,0x00,0x61,0x01,0x00,0x00,0xAA,0x08,0x08,0x06,
    50,50,40,30,20,15,15,15,15, 0,0,40,40,40,40,15,15,15, 0x2C,0x01, 0x04,0x03,0x02,0x01};
  FrameParser p; FrameKind k;
  // 前面混一段上报帧和垃圾字节
  const uint8_t rep[] = {0x00,0xF4,0xF4,0xF3,0xF2,0xF1,0x0D,0x00,0x02,0xAA,0x03,0x8C,0x00,0x37,0x5E,0x01,0x2D,0x5E,0x01,0x55,0x00,0xF8,0xF7,0xF6,0xF5};
  feed_all(p, rep, sizeof(rep), k); CHECK(k == FrameKind::REPORT);
  Report r; CHECK(parse_report(p.payload(), p.payload_len(), r));
  CHECK(r.occupancy && r.moving && r.still && r.moving_distance == 140 && r.moving_energy == 55 && r.still_distance == 350 && r.still_energy == 45 && r.detection_distance == 350);
  feed_all(p, ack61, sizeof(ack61), k); CHECK(k == FrameKind::ACK);
  uint8_t cmd; bool ok; CHECK(ack_header(p.payload(), p.payload_len(), cmd, ok) && cmd == 0x61 && ok);
  Config c; CHECK(parse_params_ack(p.payload(), p.payload_len(), c));
  CHECK(c.max_move_gate == 8 && c.max_still_gate == 6 && c.idle_s == 300 && c.move_sens[0] == 50 && c.move_sens[8] == 15 && c.still_sens[2] == 40 && c.still_sens[8] == 15);
  // 失败 ACK
  const uint8_t ackfail[] = {0xFD,0xFC,0xFB,0xFA,0x04,0x00,0x64,0x01,0x01,0x00,0x04,0x03,0x02,0x01};
  feed_all(p, ackfail, sizeof(ackfail), k); CHECK(k == FrameKind::ACK);
  CHECK(ack_header(p.payload(), p.payload_len(), cmd, ok) && cmd == 0x64 && !ok);
  // 版本 ACK：FD FC FB FA 0C 00 A0 01 00 00 00 01 02 01 16 24 06 22 04 03 02 01 → V1.02.22062416
  const uint8_t ackver[] = {0xFD,0xFC,0xFB,0xFA,0x0C,0x00,0xA0,0x01,0x00,0x00,0x00,0x01,0x02,0x01,0x16,0x24,0x06,0x22,0x04,0x03,0x02,0x01};
  feed_all(p, ackver, sizeof(ackver), k); CHECK(k == FrameKind::ACK);
  CHECK(parse_version_ack(p.payload(), p.payload_len(), c)); printf("fw=%s\n", c.fw);
  CHECK(strcmp(c.fw, "1.02.22062416") == 0);

  // 3. 无附加字段的行与 v1 printf 逐字节一致
  char a[300], b[300]; bool used;
  build_line(r, EX_NONE, c, "", 0, "", a, sizeof(a), &used);
  snprintf(b, sizeof(b), "{\"occupancy\":%s,\"moving\":%s,\"still\":%s,\"detection_distance\":%u,\"moving_distance\":%u,\"still_distance\":%u,\"moving_energy\":%u,\"still_energy\":%u}",
           "true","true","true",350u,140u,350u,55u,45u);
  CHECK(strcmp(a, b) == 0 && !used);

  // 4. 最坏长度：距离 65535、能量 255、灵敏度全 100、空闲 900、age 很大
  Report w; w.occupancy = w.moving = w.still = false; w.detection_distance = w.moving_distance = w.still_distance = 65535; w.moving_energy = w.still_energy = 255;
  Config wc = c; for (int i = 0; i < 9; i++) { wc.move_sens[i] = 255; wc.still_sens[i] = 255; } wc.max_move_gate = wc.max_still_gate = 255; wc.idle_s = 65535; strcpy(wc.fw, "255.FF.FFFFFFFF");
  const Extra exs[] = {EX_NONE, EX_CFG, EX_MS, EX_SS, EX_ACK};
  for (Extra e : exs) {
    size_t L = build_line(w, e, wc, "", 4294967u, "maxgate err noack_ff", a, sizeof(a), &used);
    printf("extra=%d len=%zu used=%d\n", (int)e, L, used); CHECK(L <= MAX_LINE); CHECK(e == EX_NONE || used);
  }
  size_t L = build_line(w, EX_CFG, wc, "noack_ff", 0, "", a, sizeof(a), &used); CHECK(L <= MAX_LINE && used);
  // 典型行示例
  for (Extra e : exs) { build_line(r, e, c, "", 12, "get ok", a, sizeof(a), &used); printf("%s  (%zu)\n", a, strlen(a)); }
  // 5. 截断/伪帧不触发
  const uint8_t junk[] = {0xFD,0xFC,0xFB,0xFA,0xFF,0x00,0x61};
  feed_all(p, junk, sizeof(junk), k); CHECK(k == FrameKind::NONE);
  feed_all(p, rep, sizeof(rep), k); CHECK(k == FrameKind::REPORT);
  printf(fails ? "FAILED %d\n" : "ALL PASS\n", fails);
  return fails != 0;
}
