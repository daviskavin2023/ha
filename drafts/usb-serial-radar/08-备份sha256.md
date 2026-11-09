# ESP32-S3 LD2410 (7C:E8:B1:A2:DB:B0) 备份校验

## 整片备份（刷写前）
- 文件: `fullflash-20261110-012256.bin`（16MB，**勿提交 git**）
- PVE: `/root/backups/esp32-ld2410-7ce8b1a2dbb0/fullflash-20261110-012256.bin`
- sha256: `b5f0f88a1d13f5919cd44de82554010b77c7e8bc787e82c97ef7649c05227301`

## 上线固件（dio_opi，2026-11-10）
- flash: `--flash_mode dio --flash_freq 80m --flash_size 16MB`
- 偏移: bootloader@0x0 partitions@0x8000 boot_app0@0xe000 firmware@0x10000
- bootloader.bin 14032 / partitions.bin 3072 / boot_app0.bin 8192 / firmware.bin 669312
- 产物目录（本地未入 git）: `backups/.../pio-upload-dio/`

## PVE / HA 配置备份
- `138.conf.bak.20261110-014036`
- HA `configuration.yaml.bak.20261110-064929`（在 HA 主机；含密钥的副本勿提交）

## 直通 by-id
`/dev/serial/by-id/usb-1a86_USB_Single_Serial_5D33083851-if00`
