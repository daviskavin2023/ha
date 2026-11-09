import os

def generate_compact_kicad_pcb():
    # Board dimensions: 48mm x 60mm
    # Compact vertical backpack board for the 52mm x 64mm mini box!
    
    content = """(kicad_pcb (version 20211014) (generator "xiaozhi_compact_builder")

  (general
    (thickness 1.6)
  )

  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
    (47 "F.CrtYd" user "F.Courtyard")
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0.05)
    (solder_mask_min_width 0.1)
  )

  (net 0 "")
  (net 1 "GND")
  (net 2 "+5V")
  (net 3 "+3V3")
  (net 4 "MIC_SD_IO4")
  (net 5 "MIC_WS_IO5")
  (net 6 "MIC_SCK_IO6")
  (net 7 "DAC_BCK_IO7")
  (net 8 "RADAR_OUT_IO8")
  (net 9 "AMP_SD_IO9")
  (net 10 "LCD_DC_IO10")
  (net 11 "LCD_SCK_IO11")
  (net 12 "LCD_MOSI_IO12")
  (net 13 "LCD_CS_IO13")
  (net 14 "DAC_LCK_IO15")
  (net 15 "DAC_DIN_IO16")
  (net 16 "RADAR_RX_IO17")
  (net 17 "RADAR_TX_IO18")
  (net 18 "TOUCH_SCL_IO1")
  (net 19 "TOUCH_SDA_IO2")
  (net 20 "AUDIO_L_OUT")
  (net 21 "AUDIO_R_OUT")
  (net 22 "AMP_IN_SIG")
  (net 23 "SPK_P")
  (net 24 "SPK_N")

  ;; Board Outline (48mm x 60mm)
  (gr_line (start 3 0) (end 45 0) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 45 0) (mid 47.121 0.879) (end 48 3) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 48 3) (end 48 57) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 48 57) (mid 47.121 59.121) (end 45 60) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 45 60) (end 3 60) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 3 60) (mid 0.879 59.121) (end 0 57) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 0 57) (end 0 3) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 0 3) (mid 0.879 0.879) (end 3 0) (layer "Edge.Cuts") (width 0.15))

  ;; 4x M2 Mounting Holes (2.2mm drill, 4.5mm pad)
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 3 3)
    (pad "1" thru_hole circle (at 0 0) (size 4.5 4.5) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 45 3)
    (pad "1" thru_hole circle (at 0 0) (size 4.5 4.5) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 3 57)
    (pad "1" thru_hole circle (at 0 0) (size 4.5 4.5) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 45 57)
    (pad "1" thru_hole circle (at 0 0) (size 4.5 4.5) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))

  ;; Silkscreen Titles
  (gr_text "XiaoZhi MiniCube v1.0" (at 24 6) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18) bold)))
  (gr_text "48x60mm Box PCB" (at 24 9) (layer "F.SilkS")
    (effects (font (size 0.9 0.9) (thickness 0.15))))

  ;; ESP32-S3 Socket (2x22 Pin Header)
  ;; Left rail at x=12.57, Right rail at x=35.43, y from 3.0 to 56.34
"""

    left_nets = [
        (3, "+3V3"), (3, "+3V3"), (0, "EN"), (4, "MIC_SD_IO4"), (5, "MIC_WS_IO5"), (6, "MIC_SCK_IO6"),
        (7, "DAC_BCK_IO7"), (14, "DAC_LCK_IO15"), (15, "DAC_DIN_IO16"), (16, "RADAR_RX_IO17"),
        (17, "RADAR_TX_IO18"), (8, "RADAR_OUT_IO8"), (0, "IO3"), (0, "IO46"), (9, "AMP_SD_IO9"),
        (10, "LCD_DC_IO10"), (11, "LCD_SCK_IO11"), (12, "LCD_MOSI_IO12"), (13, "LCD_CS_IO13"),
        (0, "IO14"), (2, "+5V"), (1, "GND")
    ]
    right_nets = [
        (1, "GND"), (0, "TX"), (0, "RX"), (18, "TOUCH_SCL_IO1"), (19, "TOUCH_SDA_IO2"),
        (0, "IO42"), (0, "IO41"), (0, "IO40"), (0, "IO39"), (0, "IO38"), (0, "IO37"),
        (0, "IO36"), (0, "IO35"), (0, "IO0"), (0, "IO45"), (0, "IO48"), (0, "IO47"),
        (0, "IO21"), (0, "IO20"), (0, "IO19"), (1, "GND"), (1, "GND")
    ]

    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu") (at 12.57 3)
    (fp_text reference "J_ESP_L" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(left_nets):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu") (at 35.43 3)
    (fp_text reference "J_ESP_R" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(right_nets):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # Screen SPI Header (Left side x=3, y=14)
    lcd_spi = [(12, "LCD_MOSI_IO12"), (10, "LCD_DC_IO10"), (11, "LCD_SCK_IO11"), (13, "LCD_CS_IO13")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu") (at 3 14)
    (fp_text reference "J_LCD_SPI" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(lcd_spi):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # Screen Power/I2C (Left side x=3, y=26)
    lcd_pwr = [(1, "GND"), (3, "+3V3"), (18, "TOUCH_SCL_IO1"), (19, "TOUCH_SDA_IO2")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu") (at 3 26)
    (fp_text reference "J_LCD_PWR" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(lcd_pwr):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # LD2410C Radar (Left side x=3, y=38)
    radar = [(2, "+5V"), (1, "GND"), (8, "RADAR_OUT_IO8"), (16, "RADAR_RX_IO17"), (17, "RADAR_TX_IO18")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu") (at 3 38)
    (fp_text reference "J_RADAR" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(radar):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # DAC Socket (Right side x=45, y=14)
    dac = [(2, "+5V"), (1, "GND"), (7, "DAC_BCK_IO7"), (15, "DAC_DIN_IO16"), (14, "DAC_LCK_IO15"), (1, "GND")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu") (at 45 14)
    (fp_text reference "J_DAC" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(dac):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # AMP Socket (Right side x=45, y=32)
    amp = [(22, "AMP_IN_SIG"), (1, "GND"), (9, "AMP_SD_IO9"), (1, "GND"), (2, "+5V")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu") (at 45 32)
    (fp_text reference "J_AMP" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(amp):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # Speaker Header (Right side x=45, y=47)
    spk = [(23, "SPK_P"), (24, "SPK_N")]
    content += """  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu") (at 45 47)
    (fp_text reference "J_SPK" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(spk):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # MIC Header (Bottom side x=18 to 30.7, y=57)
    mic = [(3, "+3V3"), (1, "GND"), (4, "MIC_SD_IO4"), (1, "GND"), (5, "MIC_WS_IO5"), (6, "MIC_SCK_IO6")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu") (at 17.65 57)
    (fp_text reference "J_MIC" (at 6.35 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(mic):
        content += f"""    (pad "{i+1}" thru_hole oval (at {i*2.54:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # Close file
    content += ")\n"

    out_kicad = "/Users/kavin/Documents/LCEDA-Pro/projects/xiaozhi_compact_box.kicad_pcb"
    desktop_kicad = "/Users/kavin/Desktop/xiaozhi_compact_box.kicad_pcb"
    with open(out_kicad, "w", encoding="utf-8") as f:
        f.write(content)
    with open(desktop_kicad, "w", encoding="utf-8") as f:
        f.write(content)
    print("Compact KiCad PCB generated at:", out_kicad)

if __name__ == "__main__":
    generate_compact_kicad_pcb()
