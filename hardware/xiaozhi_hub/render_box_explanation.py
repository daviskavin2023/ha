import os
from PIL import Image, ImageDraw, ImageFont

def render_box_explanation():
    w, h = 2000, 1200
    img = Image.new("RGBA", (w, h), "#101216")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 56)
        font_sec = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        font_lbl = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
        font_sm = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)
    except:
        font_title = ImageFont.load_default()
        font_sec = font_title
        font_lbl = font_title
        font_sm = font_title

    # Header
    draw.text((80, 50), "为什么会像个盒子？两种形态直观对比图", fill="#00E5FF", font=font_title)
    draw.text((80, 125), "左边是你觉得臃肿的【底盘摊平版】 VS 右边是你想要的【立体小方盒版】", fill="#9E9E9E", font=font_sec)

    # --- LEFT SIDE: THE FLAT PLATFORM (用户觉得臃肿的) ---
    draw.rounded_rectangle([80, 200, 920, 1100], radius=25, fill="#181B22", outline="#FF5252", width=3)
    draw.text((120, 230), "❌ 之前的【平铺底盘形态】", fill="#FF5252", font=font_sec)
    draw.text((120, 280), "缺点: 零件全平铺在底板上，像个托盘，占桌面8cm×7.5cm", fill="#E57373", font=font_sm)

    # Draw flat base
    draw.rounded_rectangle([150, 800, 850, 950], radius=15, fill="#252A36", outline="#C5A059", width=2)
    draw.text((380, 860), "8cm × 7.5cm 黑色大底板 (平摊在桌上)", fill="#C5A059", font=font_lbl)

    # Draw standing screen in front
    draw.rounded_rectangle([250, 420, 550, 800], radius=15, fill="#050811", outline="#00E5FF", width=3)
    draw.text((320, 580), "2.01寸屏幕\n(立在前面)", fill="#00E5FF", font=font_lbl)

    # Draw modules scattered on base
    draw.rounded_rectangle([580, 550, 750, 780], radius=8, fill="#37474F", outline="#78909C", width=2)
    draw.text((610, 640), "ESP32-S3\n(平躺在后面)", fill="#ECEFF1", font=font_sm)

    draw.rounded_rectangle([760, 600, 840, 780], radius=8, fill="#4A148C", outline="#BA68C8", width=2)
    draw.text((770, 670), "解码板", fill="#E1BEE7", font=font_sm)

    # --- RIGHT SIDE: THE COMPACT BOX (用户想要的微型小盒子) ---
    draw.rounded_rectangle([1000, 200, 1920, 1100], radius=25, fill="#181B22", outline="#00E676", width=3)
    draw.text((1040, 230), "✅ 你想要的【一体化微型小方盒】", fill="#00E676", font=font_sec)
    draw.text((1040, 280), "优点: 像一个小闹钟/小电视，所有零件叠在屏幕后面装进壳子里！", fill="#81C784", font=font_sm)

    # Draw 3D Box view
    # Front Face (Screen): width 360, height 450
    bx0, by0 = 1250, 420
    bw, bh, bdepth = 380, 480, 180

    # Back side / box body (Perspective extrusion to upper right)
    box_pts_top = [(bx0, by0), (bx0 + bdepth, by0 - 80), (bx0 + bw + bdepth, by0 - 80), (bx0 + bw, by0)]
    box_pts_right = [(bx0 + bw, by0), (bx0 + bw + bdepth, by0 - 80), (bx0 + bw + bdepth, by0 + bh - 80), (bx0 + bw, by0 + bh)]

    draw.polygon(box_pts_top, fill="#21252E", outline="#3E4554")
    draw.polygon(box_pts_right, fill="#191C24", outline="#3E4554")

    # Front Bezel (Screen face)
    draw.rounded_rectangle([bx0, by0, bx0+bw, by0+bh], radius=20, fill="#15171E", outline="#00E5FF", width=4)

    # Screen Display Area
    draw.rounded_rectangle([bx0+25, by0+25, bx0+bw-25, by0+bh-25], radius=15, fill="#050811")

    # Big Eyes inside
    eye_y = by0 + bh//2 - 20
    draw.rounded_rectangle([bx0+90, eye_y-45, bx0+145, eye_y+45], radius=20, fill="#00E5FF")
    draw.rounded_rectangle([bx0+235, eye_y-45, bx0+290, eye_y+45], radius=20, fill="#00E5FF")
    draw.ellipse([bx0+105, eye_y-30, bx0+120, eye_y-15], fill="#FFFFFF")
    draw.ellipse([bx0+250, eye_y-30, bx0+265, eye_y-15], fill="#FFFFFF")

    draw.text((bx0+110, by0+bh-70), "小智 AI 桌面中控", fill="#80D8FF", font=font_lbl)

    # Callout Arrows explaining the interior
    draw.line([(bx0+bw+100, by0+100), (bx0+bw+bdepth-20, by0+40)], fill="#FFD600", width=3)
    draw.text((bx0+bw+110, by0+80), "盒子后脑勺仅厚 3.5厘米\n所有板子(ESP32、解码、雷达、喇叭)\n像千层饼一样竖着叠在屏幕正背后！", fill="#FFD600", font=font_lbl)

    draw.line([(bx0+bw+100, by0+300), (bx0+bw+bdepth-30, by0+260)], fill="#00E676", width=3)
    draw.text((bx0+bw+110, by0+280), "后壳只留2个孔:\n1. 5V 电源插孔\n2. 3.5mm 音箱插孔", fill="#00E676", font=font_lbl)

    draw.text((1150, 960), "整机尺寸: 宽 5 厘米 × 高 6 厘米 × 厚 3.5 厘米\n摆在桌上就是一个小方块/微型小电视，零多余底盘！", fill="#FFFFFF", font=font_sec)

    out_png = "/Users/kavin/Desktop/xiaozhi_box_vs_flat.png"
    artifact_png = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/xiaozhi_box_vs_flat.png"
    img.save(out_png)
    img.save(artifact_png)
    print("Saved comparison to:", out_png)

if __name__ == "__main__":
    render_box_explanation()
