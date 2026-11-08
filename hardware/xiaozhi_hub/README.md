# 小智 AI 桌面中控完全体 · PCB 制造与装配手册 (v1.0 旗舰双模版)

## 一、交付文件清单

1. **嘉立创一键打样包**：
   - 本地路径: `/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/Xiaozhi_Hub_JLCPCB_Order.zip`
   - 包含文件: `xiaozhi_hub.kicad_pcb` + `xiaozhi_pcb_assembly_guide.png`
2. **KiCad 原生设计文件** (嘉立创 / 立创EDA 100% 原生识别):
   - 本地路径: `/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_hub.kicad_pcb`
3. **超高清装配接线指南图**:
   - 本地路径: `/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_pcb_assembly_guide.png`

---

## 二、嘉立创 0 元免费打样步骤 (只需 1 分钟)

1. 打开浏览器进入 **[嘉立创官网 (jlc.com)](https://www.jlc.com)** 或打开 **嘉立创下单小助手** / 微信小程序。
2. 点击 **【PCB 下单】** -> 点击 **【上传 PCB / Gerber 文件】**。
3. 选择上传我为你生成的打样包:
   `Xiaozhi_Hub_JLCPCB_Order.zip` (或直接上传 `xiaozhi_hub.kicad_pcb`)。
4. 嘉立创系统会自动解析出长宽尺寸 (**80mm × 75mm**) 与层数 (**2 层板**)。
5. **打样参数推荐勾选**：
   - **板子数量**: 5 片 (默认)
   - **板子厚度**: 1.6mm (默认标准)
   - **阻焊颜色**: **哑光黑** (沉稳高级) 或 **紫色** (极客风)
   - **表面处理**: **有铅喷锡** 或 **沉金** (每月免费券支持免费打样)
6. 提交订单时勾选**【使用每月免费打样券】** -> 实付 **0 元顺丰包邮**！

---

## 三、立创 EDA 网页版导入查看 3D 图 (可选)

如果你想在刚才注册的 **[立创 EDA 网页 (lceda.cn)](https://lceda.cn)** 预览 3D 效果：
1. 点击顶部菜单 **【文件】 -> 【打开】 -> 【KiCad】**。
2. 选中并上传 `xiaozhi_hub.kicad_pcb`。
3. 点击菜单栏 **【视图】 -> 【3D 视图】**，即可在浏览器中 360 度立体旋转查看整块板子！

---

## 四、硬件引脚与模块功能速查表

| 模块名称 | 接口类型 | 对应 ESP32-S3 针脚 | 供电轨 | 关键作用与注意事项 |
| :--- | :--- | :--- | :--- | :--- |
| **主电源** | 2-Pin 5V / Type-C | 5V & GND (跨接 100µF 电容) | 5V 主轨 | 独立大铜皮供电，彻底杜绝短路倒灌 |
| **ESP32-S3** | 2×22P 双排母 | 标准 DevKitC 针脚 | 5V 受电 | **免焊 IN-OUT**，插上直接工作 |
| **2.01寸触控彩屏** | 2×4P 插座 | SPI: IO12, 10, 11, 13<br>I2C: IO1, IO2 | 3.3V 纯净轨 | ST7789 高亮动态大眼睛 + CST816 触摸 |
| **INMP441 麦克风** | 1×6P 单排母 | SD: IO4, WS: IO5, SCK: IO6 | 3.3V 纯净轨 | 前沿开孔拾音，L/R 接地选左声道 |
| **LD2410C 雷达** | 1×5P 单排母 | OUT: IO8, RX: IO17, TX: IO18 | 5V 主轨 | 人体存在感知，天线朝前/上方安装 |
| **PCM5102A 解码** | 1×6P+1×3P 排母 | BCK: IO7, DIN: IO16, LCK: IO15 | 5V 主轨 | 发烧级 I2S DAC，模拟地星型隔离 |
| **PAM8302A 功放** | 1×5P 排母 | A+: 音频信号, SD: IO9 | 5V 主轨 | TI 超低底噪功放，拔线后驱动喇叭 |
| **PJ-324M 接口** | 5-Pin 耳机座 | Pin1: AGND, Pin2: L, Pin3: R<br>Pin4/5: 机械断开开关触点 | 纯音频通路 | **插线 220V 音箱响，拔线小喇叭响** |
| **全频腔体喇叭** | 1×2P 插座 | VO+ / VO- | 来自功放 | 4Ω 3W/5W 带被动低音振膜腔体音箱 |
