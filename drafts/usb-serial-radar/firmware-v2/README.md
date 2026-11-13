# 固件 v2：读取/修改 LD2410 配置（待审草稿，未刷写）

v1（已上线）在 `../firmware/`，**保持不动**，作回滚源码。v2 在本目录，`platformio.ini` 与 v1 逐字节相同（sha256 `2391e9df…`）。

## 改了什么
| 项 | v1 | v2 |
|---|---|---|
| 每秒 JSON 行 | 8 个字段 | 8 个字段完全一样、顺序一样；**没附加信息的行与 v1 逐字节相同** |
| 向雷达发命令 | 从不 | 开机 3 秒后、每 10 分钟、收到 `GET` 时：`0xFF 进配置` → `0xA0 读版本` → `0x61 读参数` → `0xFE 退出`。**开机只读不写** |
| 配置输出 | 无 | 附在正常上报行末尾，每行最多一个附加字段，读到后连发 3 行，之后每 60 秒重发 |
| USB 命令 | 不收 | `GET` / `SET MAXGATE` / `SET SENS`，范围校验，结果以 `ack` 字段回报 |
| 自愈 | 无 | 连续 10 秒收不到雷达上报帧，每 10 秒补发一次 `0xFE 退出配置模式` |

## 附加字段（只出现在个别行，其余行与 v1 相同）
```json
{"occupancy":true,...,"still_energy":45,"cfg":{"ok":true,"mg":8,"sg":6,"idle":300,"fw":"1.02.22062416","age":12}}
{"occupancy":true,...,"still_energy":45,"ms":[50,50,40,30,20,15,15,15,15]}
{"occupancy":true,...,"still_energy":45,"ss":[0,0,40,40,40,40,15,15,15]}
{"occupancy":true,...,"still_energy":45,"ack":"maxgate ok"}
{"occupancy":true,...,"still_energy":45,"cfg":{"ok":false,"err":"noack_ff"}}
```
- `mg`/`sg`：最大运动门/最大静止门（每门 0.75 m，门 8 ≈ 6 m）；`idle`：无人持续时间（秒）；`ms`/`ss`：门 0–8 的运动/静止灵敏度（数值越小越灵敏，HLK 定义）；`fw`：雷达固件版本；`age`：距上次读取的秒数。
- 行长上限 250（HA 状态上限 255）。拼上附加字段若超长，**丢弃附加字段，只发标准行**。主机单测最坏情况 247。

## USB 命令（115200，以换行结尾，不分大小写）
```
GET
SET MAXGATE <运动门 2-8> <静止门 2-8> <无人秒 0-900>
SET SENS <门 0-8 | ALL> <运动 0-100> <静止 0-100>
```
- 超范围 → `ack:"maxgate err range"` / `"sens err range"`，不发给雷达；未知命令 → `"err unknown"`；两次配置操作间隔 < 2 秒 → `"err busy"`；行长 > 63 → `"err toolong"`。
- 设置成功后自动重读，HA 看到的是雷达里的实际值。参数由雷达自己掉电保存。
- 不提供：恢复出厂、重启雷达、改波特率、改蓝牙、改分辨率。

## 文件
- `src/main.cpp`：主循环、配置事务、命令解析
- `src/ld2410_proto.h`：协议纯逻辑（组帧、解析、JSON 拼行），不依赖 Arduino
- `test_host/test_proto.cpp`：电脑端单测（`clang++ -std=c++17 test_host/test_proto.cpp && ./a.out`），已 ALL PASS

## 协议核对来源
- ESPHome `components/ld2410/ld2410.cpp`（dev 分支，2026-11 抓取）：命令字 0xFF/0xFE/0x60/0x61/0x64/0xA0、命令帧头尾 `FD FC FB FA … 04 03 02 01`、0x61 ACK 偏移（缓冲区 [12]/[13] 最大门、[14..22] 运动、[23..31] 静止、[32..33] 无人时间）、版本格式。
- HLK LD2410 串口协议 V1.0x 示例帧（单测里逐字节对照）。

## 编译（box，Mac 没装 PlatformIO）
`pio run` SUCCESS（PlatformIO 6.1.16 / espressif32@6.9.0），RAM 43544 B (13.3%)，Flash 672381 B (10.3%)，`firmware.bin` 672752 B。
产物放在 `backups/esp32-ld2410-7ce8b1a2dbb0/pio-upload-v2-cfg/`（git 忽略，不进仓库），sha256 见 `../10-v2刷写与回滚.md`。
