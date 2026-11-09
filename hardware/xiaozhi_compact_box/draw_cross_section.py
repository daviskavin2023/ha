from PIL import Image, ImageDraw, ImageFont

def draw_cross_section():
    w, h = 2000, 1400
    img = Image.new("RGBA", (w, h), "#0E1015")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 44)
    font_sec = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 26)
    font_lbl = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 22)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 18)
    font_mono = ImageFont.truetype("/System/Library/Fonts/Monaco.ttf", 20)

    # 1. Header
    draw.text((70, 40), "小智 AI 小方盒 v3.0 · 侧视装配截面与工程尺寸链验证图 (方案B·终审放行版)", fill="#00E5FF", font=font_title)
    draw.text((70, 100), "物理装配规范: 54.0×76.0×48.0mm 外形，44.0mm 净内腔深度下【底部水平喇叭 28mm】与【后层主控堆叠 15.1mm】避空校核", fill="#9EA3B0", font=font_sec)

    # 2. Geometry & Scale
    # Scale: 1mm = 14px
    # Coordinate system: X = Depth (0 to 48mm), Y = Height (0 to 76mm)
    ox, oy = 220, 180
    scale = 14.0
    wall = 2.0 * scale # 28px

    enc_w = 48.0 * scale # 672px (Outer Depth = 48.0mm)
    enc_h = 76.0 * scale # 1064px (Outer Height = 76.0mm)

    # Outer Shell (Dark Titanium Gray, 2mm wall)
    draw.rounded_rectangle([ox, oy, ox+enc_w, oy+enc_h], radius=30, fill="#161820", outline="#4A5268", width=4)
    # Inner Cavity (Height 72mm, Depth 44mm)
    draw.rounded_rectangle([ox+wall, oy+wall, ox+enc_w-wall, oy+enc_h-wall], radius=15, fill="#0B0C10", outline="#252A36", width=2)

    # 3. SPEAKER 2840 (Horizontal Flat at Bottom, Down-firing)
    # Specs: Length 40mm (into screen width), Width 28.0mm (Depth), Thickness 11.5mm (Height)
    # Placed flat on bottom: X = ox + wall (D=2.0 to 30.0mm), Y = oy + enc_h - wall - 11.5*scale
    spk_w = 28.0 * scale # 28mm depth
    spk_h = 11.5 * scale # 11.5mm height
    spk_x = ox + wall    # Flush against front inner rib
    spk_y = oy + enc_h - wall - spk_h
    draw.rounded_rectangle([spk_x, spk_y, spk_x+spk_w, spk_y+spk_h], radius=8, fill="#FF6D00", outline="#FFE082", width=3)
    draw.text((spk_x+20, spk_y+40), "2840 腔体喇叭 (水平平躺·底面朝下出声)\n长40mm × 宽28.0mm(深) × 厚11.5mm(高)", fill="#000000", font=font_lbl)

    # Acoustic Grille (Down-firing slots at enclosure bottom)
    for gx in range(int(spk_x + 35), int(spk_x + spk_w - 35), 22):
        draw.line([(gx, oy+enc_h-wall), (gx, oy+enc_h)], fill="#FFD54F", width=4)
    draw.text((spk_x+35, oy+enc_h+15), "▼ 底部声学格栅导音槽 (5条·向下出声)", fill="#FFD54F", font=font_sm)

    # 4. FRONT SCREEN: 2.01" IPS Capacitive Touch Screen (Pure Monolithic Black Crystal Panel)
    # Specs: Height 48mm, Thickness 4.5mm (Glass 2.0mm + Board 2.5mm)
    # Embedded flush in front shell: X = ox + wall - 1.2*scale (recessed into front)
    scr_x = ox + wall
    scr_y = oy + wall + (4.0 * scale)
    scr_w = 4.5 * scale # 4.5mm thick
    scr_h = 48.0 * scale # 48mm height
    draw.rounded_rectangle([scr_x, scr_y, scr_x+scr_w, scr_y+scr_h], radius=6, fill="#00E5FF", outline="#E0F7FA", width=2)
    # 2.5D Curved Black Crystal Glass (Monolithic surface, zero exterior holes)
    draw.line([(ox+2, scr_y), (ox+2, scr_y+scr_h)], fill="#00E5FF", width=6)
    draw.text((scr_x+10, scr_y+240), "2.01寸 触控黑晶盖板 + 屏幕模组\n(高 48mm × 厚 4.5mm)\n正面一体纯黑·零开孔设计", fill="#000000", font=font_lbl)

    # 5. REAR MAIN PCB (Vertical along rear inner wall)
    # Specs: Height 68.0mm, Thickness 1.6mm
    # Standoffs = 1.5mm from rear inner wall -> PCB X = ox + enc_w - wall - 1.5mm - 1.6mm
    pcb_w = 1.6 * scale
    pcb_h = 68.0 * scale
    pcb_x = ox + enc_w - wall - (1.5 * scale) - pcb_w
    pcb_y = oy + wall + (2.0 * scale) # 2mm from top inner wall
    draw.rounded_rectangle([pcb_x, pcb_y, pcb_x+pcb_w, pcb_y+pcb_h], radius=2, fill="#1B5E20", outline="#81C784", width=2)
    draw.text((pcb_x-22, pcb_y+420), "主PCB底板 (高 68mm × 宽 48mm × 厚 1.6mm)", fill="#81C784", font=font_sm)

    # Rear Standoffs (M2, 1.5mm height)
    draw.rectangle([pcb_x+pcb_w, pcb_y+(4*scale), ox+enc_w-wall, pcb_y+(8*scale)], fill="#78909C")
    draw.rectangle([pcb_x+pcb_w, pcb_y+pcb_h-(8*scale), ox+enc_w-wall, pcb_y+pcb_h-(4*scale)], fill="#78909C")

    # 6. ESP32-S3 CORE BOARD (Mounted in sockets on PCB front face)
    # Female Sockets: Thickness 8.5mm
    skt_w = 8.5 * scale
    skt_x = pcb_x - skt_w
    skt_y = pcb_y + (2.3 * scale)
    skt_h = 63.4 * scale
    draw.rectangle([skt_x, skt_y, skt_x+skt_w, skt_y+skt_h], fill="#FFA000", outline="#FFD54F")

    # ESP32-S3 Core Board: Thickness 3.5mm, Length 63.39mm
    esp_w = 3.5 * scale
    esp_x = skt_x - esp_w
    esp_y = skt_y
    esp_h = 63.39 * scale
    draw.rounded_rectangle([esp_x, esp_y, esp_x+esp_w, esp_y+esp_h], radius=6, fill="#3F51B5", outline="#C5CAE9", width=2)
    draw.text((esp_x+10, esp_y+360), "ESP32-S3 主控板\n(总长 63.39mm × 厚 3.5mm)", fill="#FFFFFF", font=font_lbl)

    # 7. CRITICAL CLEARANCES (Verification Proof)
    # Total Rear Stack = 1.5mm standoff + 1.6mm PCB + 8.5mm socket + 3.5mm ESP32 = 15.1mm
    # Inner Cavity Depth = 44.0mm
    # Speaker Depth = 28.0mm
    # Bottom Overlap Clearance: 44.0 - 15.1 - 28.0 = +0.9mm!
    gap_bot_px = esp_x - (spk_x + spk_w)
    gap_bot_mm = gap_bot_px / scale # in mm

    dim_y = spk_y + (spk_h / 2)
    draw.line([(spk_x + spk_w, dim_y), (esp_x, dim_y)], fill="#76FF03", width=3)
    draw.line([(spk_x + spk_w, dim_y-15), (spk_x + spk_w, dim_y+15)], fill="#76FF03", width=2)
    draw.line([(esp_x, dim_y-15), (esp_x, dim_y+15)], fill="#76FF03", width=2)
    draw.text((spk_x + spk_w + 12, dim_y - 45), f"底部水平净空 Δ = 44.0 - 15.1 - 28.0 = +{gap_bot_mm:.1f}mm\n(喇叭后沿与主控前沿完全零干涉、零挤压!)", fill="#76FF03", font=font_lbl)

    # 7.2 Middle Chamber Space: Screen rear vs ESP32-S3 front
    gap_mid_px = esp_x - (scr_x + scr_w)
    gap_mid_mm = gap_mid_px / scale
    dim_mid_y = scr_y + (scr_h / 2)
    draw.line([(scr_x + scr_w, dim_mid_y), (esp_x, dim_mid_y)], fill="#00E5FF", width=3)
    draw.line([(scr_x + scr_w, dim_mid_y-15), (scr_x + scr_w, dim_mid_y+15)], fill="#00E5FF", width=2)
    draw.line([(esp_x, dim_mid_y-15), (esp_x, dim_mid_y+15)], fill="#00E5FF", width=2)
    draw.text((scr_x + scr_w + 25, dim_mid_y - 25), f"中腔开阔净深 = {gap_mid_mm:.1f}mm (容纳雷达/DAC/功放/线束)", fill="#00E5FF", font=font_lbl)

    # 7.3 PCB Top/Bottom Margins (2.0mm each)
    draw.text((pcb_x - 140, oy + wall + 8), "顶余量 2.0mm ▲", fill="#81C784", font=font_sm)
    draw.text((pcb_x - 140, oy + enc_h - wall - 25), "底余量 2.0mm ▼", fill="#81C784", font=font_sm)

    # 8. Overall Outer Dimensions
    # Outer Height = 76mm
    draw.line([(ox - 40, oy), (ox - 40, oy + enc_h)], fill="#E2E8F0", width=2)
    draw.line([(ox - 50, oy), (ox - 30, oy)], fill="#E2E8F0", width=2)
    draw.line([(ox - 50, oy + enc_h), (ox - 30, oy + enc_h)], fill="#E2E8F0", width=2)
    draw.text((ox - 190, oy + (enc_h / 2) - 15), "外壳总高 76.0mm\n(内腔净高 72.0mm)", fill="#E2E8F0", font=font_lbl)

    # Outer Depth = 48.0mm
    draw.line([(ox, oy + enc_h + 40), (ox + enc_w, oy + enc_h + 40)], fill="#E2E8F0", width=2)
    draw.line([(ox, oy + enc_h + 30), (ox, oy + enc_h + 50)], fill="#E2E8F0", width=2)
    draw.line([(ox + enc_w, oy + enc_h + 30), (ox + enc_w, oy + enc_h + 50)], fill="#E2E8F0", width=2)
    draw.text((ox + (enc_w / 2) - 120, oy + enc_h + 55), "外壳总深 48.0mm (内腔净深 44.0mm)", fill="#E2E8F0", font=font_lbl)

    # 9. Right Panel Proof Notes
    rx0 = 1000
    draw.rounded_rectangle([rx0, 180, 1940, 1244], radius=25, fill="#151821", outline="#2F3545", width=3)
    draw.text((rx0+40, 220), "【装配截面尺寸链 100% 物理闭环核算】", fill="#FFD600", font=font_sec)

    proofs = [
        ("1. 底部重叠区域避空算式彻底纠偏：",
         "• 外壳总深 48.0mm，壁厚 2.0mm -> 内腔净深严格为 44.0mm；\n"
         "• 2840 喇叭水平平躺于底壳，深度占用 28.0mm (x = 2.0 ~ 30.0mm)；\n"
         "• 后层堆叠：螺柱1.5 + 板厚1.6 + 排母塑高8.5 + 主控3.5 = 15.1mm；\n"
         f"• 底部重叠避让净空：44.0 - 15.1 - 28.0 = +{gap_bot_mm:.1f}mm (正0.9mm，零挤压！)。"),
        
        ("2. 前面板与外观开孔规范对齐：",
         "• 正面：采用纯黑晶一体化 2.01 寸电容屏盖板，正面 0 开孔、侧面 0 开孔；\n"
         "• 出声：声音全部由壳体底部 5 条 1.2mm 声学格栅向下导出；\n"
         "• 脚垫：底壳四角装配 ⌀8×2mm 防滑硅胶脚垫，垫高 2mm 确保声音通透扩散。"),
        
        ("3. PCB 与外壳装配公差完全统一：",
         "• 外壳外轮廓：54.0mm(宽) × 76.0mm(高) × 48.0mm(深)；\n"
         "• 外壳内腔：50.0mm(宽) × 72.0mm(高) × 44.0mm(深)；\n"
         "• PCB 物理尺寸：48.0mm(宽) × 68.0mm(高)，四周各预留 1.0~2.0mm 装配旷量！"),
        
        ("4. 模块与线束容纳空间极其开阔：",
         f"• 屏幕模组背面与 ESP32 主控之间留有整整 {gap_mid_mm:.1f}mm 净宽；\n"
         "• 顶部自然容纳 HLK-LD2410C 毫米波雷达（厚度仅 4mm）；\n"
         "• PCM5102A 与 PAM8302A 模块直插排针，走线全程物理绝缘。")
    ]

    ty = 295
    for title, desc in proofs:
        draw.text((rx0+40, ty), title, fill="#00E5FF", font=font_lbl)
        ty += 40
        for line in desc.split("\n"):
            draw.text((rx0+40, ty), line, fill="#D1D5DB", font=font_sm)
            ty += 28
        ty += 22

    out_img = "/Users/kavin/Desktop/小智小方盒_侧视装配截面图_20261108.png"
    art_img = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/xiaozhi_cross_section_assembly.png"
    img.save(out_img)
    img.save(art_img)
    print("Cross-section assembly image successfully updated at:", out_img)

if __name__ == "__main__":
    draw_cross_section()
