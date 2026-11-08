import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

def create_assembly_guide():
    width = 2400
    height = 2200
    img = Image.new("RGBA", (width, height), "#1E1E24")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 68)
        font_sub = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        font_sec = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 44)
        font_lbl = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
        font_sm = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 26)
        font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 28)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_sec = font_title
        font_lbl = font_title
        font_sm = font_title
        font_mono = font_title

    # Header
    draw.text((80, 50), "小智 AI 桌面中控完全体 · PCB 布局与模块装配基准", fill="#00E5FF", font=font_title)
    draw.text((80, 135), "版本: v1.0 旗舰双模版 | 板框尺寸: 80mm × 75mm (双层沉金黑色) | 嘉立创 0 元免费打样标准", fill="#A0A5B5", font=font_sub)

    # Draw Main PCB Board Area
    # Scale: 1mm = 20px -> 80mm = 1600px, 75mm = 1500px
    pcb_x0, pcb_y0 = 100, 240
    pcb_w, pcb_h = 1500, 1400
    pcb_x1, pcb_y1 = pcb_x0 + pcb_w, pcb_y0 + pcb_h

    # PCB Board shadow & body
    draw.rounded_rectangle([pcb_x0+8, pcb_y0+8, pcb_x1+8, pcb_y1+8], radius=35, fill="#0A0A0C")
    draw.rounded_rectangle([pcb_x0, pcb_y0, pcb_x1, pcb_y1], radius=35, fill="#121316", outline="#383D48", width=4)

    # Golden border (沉金边框线)
    draw.rounded_rectangle([pcb_x0+20, pcb_y0+20, pcb_x1-20, pcb_y1-20], radius=25, outline="#C5A059", width=2)

    # 4 Corner M3 Mounting Holes
    for hx, hy in [(pcb_x0+60, pcb_y0+60), (pcb_x1-60, pcb_y0+60), (pcb_x0+60, pcb_y1-60), (pcb_x1-60, pcb_y1-60)]:
        draw.ellipse([hx-32, hy-32, hx+32, hy+32], fill="#C5A059", outline="#EAD598", width=3)
        draw.ellipse([hx-18, hy-18, hx+18, hy+18], fill="#1E1E24")
        draw.text((hx-20, hy+38), "M3螺丝", fill="#A0A5B5", font=font_sm)

    # --- TOP AREA: Ports & Inputs ---
    # Type-C DC 5V Input
    tc_x0, tc_y0, tc_w, tc_h = pcb_x0 + 120, pcb_y0 + 35, 240, 120
    draw.rounded_rectangle([tc_x0, tc_y0, tc_x0+tc_w, tc_y0+tc_h], radius=15, fill="#252830", outline="#00E5FF", width=3)
    draw.text((tc_x0+25, tc_y0+20), "Type-C 5V供电", fill="#00E5FF", font=font_lbl)
    draw.text((tc_x0+35, tc_y0+65), "独立主电源口", fill="#FFFFFF", font=font_sm)

    # 100uF Bulk Filter Capacitor
    cap_cx, cap_cy = tc_x0 + tc_w + 70, tc_y0 + 60
    draw.ellipse([cap_cx-40, cap_cy-40, cap_cx+40, cap_cy+40], fill="#303542", outline="#FFD600", width=3)
    draw.text((cap_cx-25, cap_cy-18), "100µF", fill="#FFD600", font=font_lbl)
    draw.text((cap_cx-45, cap_cy+50), "滤波防重启电容", fill="#A0A5B5", font=font_sm)

    # PJ-324M 3.5mm Headphone Jack (Top Right)
    pj_x0, pj_y0, pj_w, pj_h = pcb_x1 - 380, pcb_y0 + 35, 280, 130
    draw.rounded_rectangle([pj_x0, pj_y0, pj_x0+pj_w, pj_y0+pj_h], radius=15, fill="#252830", outline="#00E676", width=3)
    draw.text((pj_x0+20, pj_y0+18), "PJ-324M 3.5mm", fill="#00E676", font=font_lbl)
    draw.text((pj_x0+20, pj_y0+60), "有源音箱/耳机插口", fill="#FFFFFF", font=font_sm)
    draw.text((pj_x0+20, pj_y0+90), "(插线大音箱, 拔线小喇叭)", fill="#76FF03", font=font_sm)

    # --- MIDDLE UPPER AREA: LD2410C & Audio DAC / AMP ---
    # LD2410C Human Presence Radar Socket (5-Pin Header)
    ld_x0, ld_y0, ld_w, ld_h = pcb_x0 + 70, pcb_y0 + 200, 320, 250
    draw.rounded_rectangle([ld_x0, ld_y0, ld_x0+ld_w, ld_y0+ld_h], radius=18, fill="#1B2230", outline="#2979FF", width=2)
    draw.text((ld_x0+20, ld_y0+20), "LD2410C 雷达母座", fill="#82B1FF", font=font_sec)
    draw.text((ld_x0+20, ld_y0+75), "5-Pin 单排母插槽", fill="#FFFFFF", font=font_lbl)
    draw.text((ld_x0+20, ld_y0+120), "1: 5V (必须接5V)\n2: GND\n3: OUT (GPIO 8)\n4: TX (GPIO 17)\n5: RX (GPIO 18)", fill="#A0A5B5", font=font_mono)
    draw.text((ld_x0+20, ld_y0+210), "【天线朝前/上方安装】", fill="#FF9100", font=font_sm)

    # PCM5102A Audio DAC Socket (Right Side)
    pcm_x0, pcm_y0, pcm_w, pcm_h = pcb_x1 - 440, pcb_y0 + 200, 360, 330
    draw.rounded_rectangle([pcm_x0, pcm_y0, pcm_x0+pcm_w, pcm_y0+pcm_h], radius=18, fill="#2C1A35", outline="#E040FB", width=2)
    draw.text((pcm_x0+20, pcm_y0+18), "PCM5102A 解码母座", fill="#EA80FC", font=font_sec)
    draw.text((pcm_x0+20, pcm_y0+68), "紫色高保真 DAC 模块", fill="#FFFFFF", font=font_lbl)
    draw.text((pcm_x0+20, pcm_y0+110), "VCC -> 5V (纯净动力)\nGND / FLT / DMP / SCL -> 地\nBCK -> GPIO 7\nDIN -> GPIO 16\nLCK -> GPIO 15\nL/R -> 接至 3.5mm 与功放", fill="#CE93D8", font=font_mono)

    # PAM8302A Low Noise Amp Socket
    amp_x0, amp_y0, amp_w, amp_h = pcb_x1 - 440, pcm_y0 + pcm_h + 30, 360, 250
    draw.rounded_rectangle([amp_x0, amp_y0, amp_x0+amp_w, amp_y0+amp_h], radius=18, fill="#1F2A24", outline="#00C853", width=2)
    draw.text((amp_x0+20, amp_y0+18), "PAM8302A 功放母座", fill="#69F0AE", font=font_sec)
    draw.text((amp_x0+20, amp_y0+65), "TI 原装超低底噪功放", fill="#FFFFFF", font=font_lbl)
    draw.text((amp_x0+20, amp_y0+105), "A+ <- PJ-324 常闭开关\nA- <- 模拟地 AGND\n5V / GND <- 系统电源\nVO+ / VO- -> 接小喇叭", fill="#B9F6CA", font=font_mono)

    # Speaker Terminal Socket (XH2.54 2P)
    spk_x0, spk_y0, spk_w, spk_h = pcb_x1 - 440, amp_y0 + amp_h + 30, 360, 130
    draw.rounded_rectangle([spk_x0, spk_y0, spk_x0+spk_w, spk_y0+spk_h], radius=15, fill="#2A2418", outline="#FFAB00", width=2)
    draw.text((spk_x0+20, spk_y0+15), "喇叭接线座 (2-Pin)", fill="#FFD740", font=font_lbl)
    draw.text((spk_x0+20, spk_y0+55), "接 4Ω 3W 被动振膜腔体喇叭", fill="#FFFFFF", font=font_sm)
    draw.text((spk_x0+20, spk_y0+88), "插耳机时自动断开闭嘴", fill="#76FF03", font=font_sm)

    # --- CENTER MAIN CORE: ESP32-S3 DevKitC-1 Socket ---
    esp_x0, esp_y0, esp_w, esp_h = pcb_x0 + 440, pcb_y0 + 200, 560, 800
    draw.rounded_rectangle([esp_x0, esp_y0, esp_x0+esp_w, esp_y0+esp_h], radius=20, fill="#1C1D24", outline="#FF5252", width=3)
    draw.text((esp_x0+45, esp_y0+25), "ESP32-S3 主控核心插槽", fill="#FF5252", font=font_sec)
    draw.text((esp_x0+75, esp_y0+75), "标准 2×22P 双排母底座", fill="#FFFFFF", font=font_lbl)

    # Dual Pin Header representation
    hdr_l_x = esp_x0 + 40
    hdr_r_x = esp_x0 + esp_w - 70
    hdr_y_start = esp_y0 + 130
    hdr_h_step = 28

    # Left Header Pins
    draw.rounded_rectangle([hdr_l_x-10, hdr_y_start-10, hdr_l_x+40, hdr_y_start+22*hdr_h_step], radius=8, fill="#2D303E", outline="#5C6BC0", width=2)
    # Right Header Pins
    draw.rounded_rectangle([hdr_r_x-10, hdr_y_start-10, hdr_r_x+40, hdr_y_start+22*hdr_h_step], radius=8, fill="#2D303E", outline="#5C6BC0", width=2)

    for i in range(22):
        py = hdr_y_start + i * hdr_h_step + 10
        draw.ellipse([hdr_l_x+8, py-7, hdr_l_x+22, py+7], fill="#FFD600")
        draw.ellipse([hdr_r_x+8, py-7, hdr_r_x+22, py+7], fill="#FFD600")

    draw.text((esp_x0+120, esp_y0+220), "ESP32-S3-N16R8\n双核 240MHz\n16M Flash / 8M PSRAM", fill="#9FA8DA", font=font_lbl)
    draw.text((esp_x0+130, esp_y0+420), "【USB 口朝下方安装】\n【免焊 IN-OUT】\n由底板 5V 统一安全供电\n彻底告别倒灌烧板！", fill="#00E676", font=font_lbl)

    # --- BOTTOM AREA: 2.01 inch Screen & Microphone ---
    # 2.01 Inch Screen Socket (2x 4-Pin MX1.25 / 2.54 Headers)
    scr_x0, scr_y0, scr_w, scr_h = pcb_x0 + 70, pcb_y1 - 320, 560, 260
    draw.rounded_rectangle([scr_x0, scr_y0, scr_x0+scr_w, scr_y0+scr_h], radius=20, fill="#232130", outline="#FF4081", width=3)
    draw.text((scr_x0+25, scr_y0+20), "2.01寸 IPS 触控屏接座", fill="#FF4081", font=font_sec)
    draw.text((scr_x0+25, scr_y0+75), "TK020F1131 (ST7789 + CST816)", fill="#FFFFFF", font=font_lbl)
    draw.text((scr_x0+25, scr_y0+120), "上插座 (SPI显示): MOSI(12), DC(10), SCK(11), CS(13)\n下插座 (电源触控): GND, 3V3, SCL(1), SDA(2)", fill="#FF80AB", font=font_mono)
    draw.text((scr_x0+25, scr_y0+195), "【立面安装 / 屏幕朝前作为正面大脸蛋】", fill="#FFD54F", font=font_lbl)

    # INMP441 Digital Microphone Socket (Bottom Center)
    mic_x0, mic_y0, mic_w, mic_h = pcb_x0 + 670, pcb_y1 - 320, 360, 260
    draw.rounded_rectangle([mic_x0, mic_y0, mic_x0+mic_w, mic_y0+mic_h], radius=20, fill="#1E2A38", outline="#00E5FF", width=3)
    draw.text((mic_x0+25, mic_y0+20), "INMP441 硅麦插槽", fill="#00E5FF", font=font_sec)
    draw.text((mic_x0+25, mic_y0+75), "全向数字 I2S 麦克风", fill="#FFFFFF", font=font_lbl)
    draw.text((mic_x0+25, mic_y0+120), "VDD -> 3.3V\nGND / L/R -> 地 (选左声道)\nSD -> GPIO 4\nWS -> GPIO 5\nSCK -> GPIO 6", fill="#80D8FF", font=font_mono)
    draw.text((mic_x0+25, mic_y0+215), "【开孔朝前最佳收音】", fill="#69F0AE", font=font_sm)

    # --- RIGHT PANEL: Hardware Verification & Checklist ---
    p_x0 = pcb_x1 + 60
    draw.rounded_rectangle([p_x0, pcb_y0, width-80, pcb_y1], radius=25, fill="#16181F", outline="#2F3342", width=3)
    draw.text((p_x0+35, pcb_y0+30), "嘉立创打样与防坑指南", fill="#FFD600", font=font_sec)

    tips = [
        ("1. 为什么不用焊 IN-OUT？", "底板自带 Type-C 独立电源，5V 大总线直通 ESP32 的 5V 受电引脚。开发板连烙铁都不用碰，彻底杜绝短路倒灌！"),
        ("2. 为什么接 220V 音箱不杂音？", "模拟地与数字地在电源入口处单点汇合 (星型接地)，PCM5102A 的 Line Out 零底噪，背景漆黑。"),
        ("3. 耳机与外放智能自动切换：", "插上 3.5mm 耳机/大音箱线，PJ-324 物理弹片瞬间弹开断路，小功放与小喇叭断电闭嘴，全硬件秒切！"),
        ("4. 嘉立创 0 元打样参数：", "板厚 1.6mm | 阻焊颜色：哑光黑 (或高级紫) | 沉金 / 有铅喷锡 | 外层铜厚 1oz | 尺寸 80×75mm (完全在免费额度内)"),
        ("5. 全插拔积木式设计：", "所有核心模块全部插在 2.54 排母上！手残党无需焊接微小贴片，10 分钟电烙铁点几下即刻组装完毕！")
    ]

    ty = pcb_y0 + 110
    for title, desc in tips:
        draw.text((p_x0+35, ty), title, fill="#00E5FF", font=font_lbl)
        ty += 45
        # wrap text
        words = desc
        draw.text((p_x0+35, ty), words, fill="#C5C8D6", font=font_sm)
        ty += 70

    # Output paths
    out_png = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_pcb_assembly_guide.png"
    artifact_png = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/xiaozhi_pcb_assembly_guide.png"
    img.save(out_png)
    img.save(artifact_png)
    print("Assembly guide generated at:", out_png)

if __name__ == "__main__":
    create_assembly_guide()
