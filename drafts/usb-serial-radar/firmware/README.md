# 固件选择

## 结论：**用 Arduino / PlatformIO，不用带 Wi-Fi 的 ESPHome 生产固件**

| 方案 | 可行性 | 说明 |
|---|---|---|
| ESPHome + API | ❌ | 无 Wi-Fi 无法连 HA API |
| ESPHome 仅 logger 打 JSON | ⚠️ | 可关 API，但框架仍常拉 Wi-Fi；需 `reboot_timeout: 0s` 防重启环，体积大 |
| **Arduino 读 LD2410 → UART0 JSON** | ✅ | 不初始化 Wi-Fi/BT；看门狗喂养简单；CH343=USB Serial |

JSON 每秒一行（无多余日志）：
```json
{"occupancy":true,"moving":false,"still":true,"detection_distance":120,"moving_distance":0,"still_distance":120,"moving_energy":0,"still_energy":45}
```

## 编译（Mac）
```bash
cd drafts/usb-serial-radar/firmware
pio run
```

### 产物与刷写偏移（`default_16MB.csv`，box 已 pio run 通过）
| 文件 | 偏移 | 路径 |
|---|---|---|
| bootloader.bin | 0x0 | `.pio/build/esp32-s3/bootloader.bin` |
| partitions.bin | 0x8000 | `.pio/build/esp32-s3/partitions.bin` |
| boot_app0.bin | 0xe000 | `~/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin` |
| firmware.bin | 0x10000 | `.pio/build/esp32-s3/firmware.bin`（**应用镜像，禁止 @0x0 单刷**） |

完整 `esptool.py write_flash` 命令见 `../02-备份与刷写.md`（含 `--chip esp32s3 --flash_mode dio --flash_freq 80m --flash_size 16MB`）。

引脚与原 `ld2410-radar.yaml` 一致：雷达 UART **256000**，ESP TX=17 RX=18；USB JSON 走 **Serial(UART0)@115200**。
