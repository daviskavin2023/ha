# XiaoZhi MiniCube / TK020F1131_PB

Unique board identity: `xiaozhi-minicube`; release variant:
`xiaozhi-minicube-tk020-pb`. ESP32-S3 N16R8, 16MB flash / octal PSRAM.

Pins follow the v3.1 carrier. Microphone: DIN4/WS5/SCK6. PCM5102A:
BCK7/LRCK15/DATA16. PAM8302A SD9, active high. Display:
MOSI12/DC10/SCK11/CS13. Touch: SDA2/SCL1. Radar OUT8 is read only;
UART17/18 remain reserved for radar and are not reused by a generic lamp tool.

Required audio hardware: PATCH-A01 15k/1k passive attenuator and input coupling.
The firmware does not claim an arbitrary digital volume guarantees no clipping.
SD is low during startup/disabled playback and enabled asynchronously 10ms after
the I2S output is enabled. This is not an AUX insertion detector.

Only the two labeled 4P connectors are used. BL/RST/INT solder points are not
driven. The ST7789 uses its software-reset command. CST816x is probed at 0x15
and polled via the same register layout used by the upstream CST816D board.
Read failures are logged and never treated as a release event. A matching
controller/batch and proper I2C pullups must be verified on actual hardware.
The driver's weak internal pullups do not establish production signal margins.

The 240x296, y-offset=0 display profile is an initial unverified BOM profile,
not a vendor-confirmed resolution/offset. Both height and offset are configurable
through Kconfig. Compilation cannot prove that these values fit the actual glass.

Build with ESP-IDF 6.1 using:

```
python3 scripts/build.py xiaozhi-minicube --name xiaozhi-minicube-tk020-pb
```

No flashing is performed by adding/building this board. Confirm the carrier,
power topology, wiring and panel profile before installing any image.
