import math
from PIL import Image, ImageDraw, ImageFont

def render_3d_product():
    w, h = 2000, 1500
    img = Image.new("RGBA", (w, h), "#0D0E12")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
        font_sub = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
        font_lbl = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 26)
        font_sm = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_lbl = font_title
        font_sm = font_title

    # Header
    draw.text((70, 50), "小智 AI 桌面中控完全体 · 成品立体 3D 效果图", fill="#00E5FF", font=font_title)
    draw.text((70, 130), "哑光黑沉金 PCB + 2.01寸 动态表情屏 + 桌面立体架构 (80mm × 75mm)", fill="#8A8F9E", font=font_sub)

    # Perspective 3D Desk Surface (Desktop plane)
    desk_pts = [(100, 1350), (1900, 1350), (1600, 800), (400, 800)]
    draw.polygon(desk_pts, fill="#14161D", outline="#1F232E")

    # Ambient Glow from screen
    for r in range(350, 0, -20):
        alpha = int(25 * (1 - r/350))
        glow_box = [900 - r, 700 - r, 900 + r, 700 + r]
        draw.ellipse(glow_box, fill=(0, 229, 255, alpha))

    # --- 1. Isometric 3D PCB Base Board (平躺在桌上的 PCB 底座) ---
    # Center (950, 1000)
    # Isometric transformation helper
    def iso(x, y, z):
        # x: -40 to 40 (mm), y: -37.5 to 37.5 (mm), z: height in mm
        scale = 13.0
        # 30 deg isometric angle
        iso_x = 950 + (x - y) * math.cos(math.radians(25)) * scale
        iso_y = 960 + (x + y) * math.sin(math.radians(25)) * scale - z * scale * 1.5
        return (iso_x, iso_y)

    # PCB Board 4 corners at z=0 (thickness 1.6mm -> z=0 to z=2)
    pcb_c_bot = [iso(-40, -37.5, 0), iso(40, -37.5, 0), iso(40, 37.5, 0), iso(-40, 37.5, 0)]
    pcb_c_top = [iso(-40, -37.5, 3), iso(40, -37.5, 3), iso(40, 37.5, 3), iso(-40, 37.5, 3)]

    # Board thickness side polygons
    draw.polygon([pcb_c_bot[2], pcb_c_top[2], pcb_c_top[1], pcb_c_bot[1]], fill="#0A0B0E", outline="#C5A059")
    draw.polygon([pcb_c_bot[3], pcb_c_top[3], pcb_c_top[2], pcb_c_bot[2]], fill="#0D0E12", outline="#C5A059")
    # Top surface (Matte Black with Gold edge)
    draw.polygon(pcb_c_top, fill="#181A22", outline="#C5A059", width=3)

    # 4 Corner M3 Gold Pads
    for hx, hy in [(-36, -33.5), (36, -33.5), (-36, 33.5), (36, 33.5)]:
        cx, cy = iso(hx, hy, 3.2)
        draw.ellipse([cx-12, cy-7, cx+12, cy+7], fill="#C5A059", outline="#EAD598", width=2)
        draw.ellipse([cx-5, cy-3, cx+5, cy+3], fill="#0D0E12")

    # --- 2. ESP32-S3 Module (Lying Flat behind the screen) ---
    # Centered at x=0, y=5, z=5 to 14
    esp_b = [iso(-14, -8, 6), iso(14, -8, 6), iso(14, 28, 6), iso(-14, 28, 6)]
    esp_t = [iso(-14, -8, 12), iso(14, -8, 12), iso(14, 28, 12), iso(-14, 28, 12)]
    draw.polygon([esp_b[2], esp_t[2], esp_t[1], esp_b[1]], fill="#16181F", outline="#3F4659")
    draw.polygon([esp_b[3], esp_t[3], esp_t[2], esp_b[2]], fill="#1A1C24", outline="#3F4659")
    draw.polygon(esp_t, fill="#232733", outline="#4E576F", width=2)
    # ESP32 Silver Metal Shield Can
    can_t = [iso(-11, 6, 14), iso(11, 6, 14), iso(11, 25, 14), iso(-11, 25, 14)]
    draw.polygon(can_t, fill="#7A8296", outline="#BAC1D4", width=2)
    tx, ty = iso(0, 15, 14.5)
    draw.text((tx-35, ty-10), "ESP32-S3", fill="#FFFFFF", font=font_sm)

    # --- 3. PCM5102A & PAM8302A & Speaker (Right / Back) ---
    # Purple PCM5102A Board at x=25, y=0, z=6
    pcm_t = [iso(20, -12, 10), iso(36, -12, 10), iso(36, 8, 10), iso(20, 8, 10)]
    draw.polygon(pcm_t, fill="#5C2575", outline="#B560DC", width=2)
    px, py = iso(28, -2, 10.5)
    draw.text((px-30, py-8), "PCM5102A", fill="#E1BEE7", font=font_sm)

    # Black Speaker Box (Under/Beside PCB)
    spk_t = [iso(18, 12, 8), iso(37, 12, 8), iso(37, 32, 8), iso(18, 32, 8)]
    draw.polygon(spk_t, fill="#121317", outline="#FFAB00", width=2)
    sx, sy = iso(27.5, 22, 8.5)
    draw.text((sx-35, sy-8), "4Ω 3W 腔体", fill="#FFD54F", font=font_sm)

    # LD2410C Radar (Left Upper, x=-26, y=-8, standing vertically)
    rd_b = iso(-28, -8, 6)
    rd_t = iso(-28, -8, 25)
    draw.line([rd_b, rd_t], fill="#2979FF", width=12)
    draw.text((rd_t[0]-40, rd_t[1]-30), "LD2410C雷达", fill="#82B1FF", font=font_sm)

    # 100uF Blue Bulk Capacitor at Left Top
    c_x, c_y = iso(-25, -28, 6)
    draw.ellipse([c_x-15, c_y-25, c_x+15, c_y+5], fill="#1565C0", outline="#64B5F6", width=2)
    draw.text((c_x-20, c_y-45), "100µF", fill="#FFD600", font=font_sm)

    # PJ-324M 3.5mm Headphone Jack (Top Right Corner)
    pj_b = iso(28, -32, 6)
    draw.rounded_rectangle([pj_b[0]-25, pj_b[1]-20, pj_b[0]+25, pj_b[1]+20], radius=8, fill="#1E232F", outline="#00E676", width=2)
    draw.ellipse([pj_b[0]-8, pj_b[1]-8, pj_b[0]+8, pj_b[1]+8], fill="#0A0B0E", outline="#C5A059", width=2)
    draw.text((pj_b[0]+35, pj_b[1]-12), "3.5mm 自动切换插口", fill="#00E676", font=font_lbl)

    # --- 4. THE HERO: 2.01-Inch Screen Standing at Front Edge ---
    # Width: 42mm, Height: 52mm, angled at ~75 degrees toward viewer
    scr_base_l = iso(-22, -15, 6)
    scr_base_r = iso(22, -15, 6)
    # Height goes up along z (upwards in 3D)
    scr_top_l = (scr_base_l[0], scr_base_l[1] - 320)
    scr_top_r = (scr_base_r[0], scr_base_r[1] - 320)

    # Screen Bezel / Backing Plate (Matte CNC Black)
    scr_poly = [scr_base_l, scr_base_r, scr_top_r, scr_top_l]
    draw.polygon(scr_poly, fill="#14171E", outline="#00E5FF", width=4)

    # Screen Display Area (IPS Active Display)
    inset_x = 18
    inset_y = 20
    disp_bl = (scr_base_l[0] + inset_x, scr_base_l[1] - inset_y)
    disp_br = (scr_base_r[0] - inset_x, scr_base_r[1] - inset_y)
    disp_tr = (scr_top_r[0] - inset_x, scr_top_r[1] + inset_y)
    disp_tl = (scr_top_l[0] + inset_x, scr_top_l[1] + inset_y)
    draw.polygon([disp_bl, disp_br, disp_tr, disp_tl], fill="#050811")

    # Animated Big Eyes inside Screen (小智灵动大眼睛)
    eye_cx1 = (disp_tl[0] + disp_tr[0]) / 2 - 70
    eye_cx2 = (disp_tl[0] + disp_tr[0]) / 2 + 70
    eye_cy = (disp_tl[1] + disp_bl[1]) / 2 - 20

    # Draw Cyan Glow Eyes
    draw.rounded_rectangle([eye_cx1-35, eye_cy-55, eye_cx1+35, eye_cy+55], radius=25, fill="#00E5FF", outline="#E0F7FA", width=4)
    draw.rounded_rectangle([eye_cx2-35, eye_cy-55, eye_cx2+35, eye_cy+55], radius=25, fill="#00E5FF", outline="#E0F7FA", width=4)
    # Eye highlights (pupil sparks)
    draw.ellipse([eye_cx1-15, eye_cy-35, eye_cx1+5, eye_cy-15], fill="#FFFFFF")
    draw.ellipse([eye_cx2-15, eye_cy-35, eye_cx2+5, eye_cy-15], fill="#FFFFFF")

    # Status Bar on Screen (WiFi icon, time)
    disp_w_center = (disp_tl[0] + disp_tr[0]) / 2
    draw.text((disp_w_center-50, disp_tl[1]+15), "12:58 · Wi-Fi", fill="#80D8FF", font=font_sm)
    draw.text((disp_w_center-85, disp_bl[1]-45), "主人，我在听...", fill="#00E5FF", font=font_lbl)

    # INMP441 Microphone (Right under screen, facing front)
    mic_pt = iso(0, -28, 4)
    draw.rounded_rectangle([mic_pt[0]-25, mic_pt[1]-15, mic_pt[0]+25, mic_pt[1]+15], radius=6, fill="#212632", outline="#00E5FF", width=2)
    draw.ellipse([mic_pt[0]-4, mic_pt[1]-4, mic_pt[0]+4, mic_pt[1]+4], fill="#FFD600")
    draw.text((mic_pt[0]-50, mic_pt[1]+22), "数字硅麦(拾音孔)", fill="#00E5FF", font=font_sm)

    # 3.5mm Cable Illustration connecting to Active Speaker (Left or Right)
    cable_start = (pj_b[0], pj_b[1])
    cable_end = (1750, 400)
    # Draw curve
    cable_mid1 = (pj_b[0] + 150, pj_b[1] - 80)
    cable_mid2 = (1500, 500)
    draw.line([cable_start, cable_mid1, cable_mid2, cable_end], fill="#3949AB", width=6)
    draw.text((1500, 350), "3.5mm AUX 音频线\n-> 直连 220V 有源大音箱！", fill="#7986CB", font=font_lbl)

    # Save outputs
    out_3d_png = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_hub_3d_render.png"
    artifact_3d_png = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/xiaozhi_hub_3d_render.png"
    desktop_3d_png = "/Users/kavin/Desktop/xiaozhi_hub_3d_render.png"

    img.save(out_3d_png)
    img.save(artifact_3d_png)
    img.save(desktop_3d_png)
    print("3D Product Render saved to Desktop:", desktop_3d_png)

if __name__ == "__main__":
    render_3d_product()
