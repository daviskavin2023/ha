import os

def generate_clean_drc_pcb():
    # PCB Dimensions: 50.0mm wide x 68.0mm tall
    # Clearance: Housing inner height = 72mm, board height = 68mm -> 4mm vertical margin!
    # Solves ALL review findings:
    # 1. REMOVES all manually hardcoded conflicting tracks that caused shorts!
    # 2. Fully correct Netlist bindings for every single pad.
    # 3. Dual-rail ESP32 headers (22.86mm inner, 25.40mm outer).
    # 4. R1 & R2 1k resistors included.
    # 5. PAM8302 input (5P) and output (2P) included.
    # 6. DAC digital in (6P) and analog out (3P) included.
    
    content = """(kicad_pcb (version 20211014) (generator "xiaozhi_clean_drc_builder")

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
  (net 25 "TIP_SW")
  (net 26 "RING_SW")

  ;; ==========================================
  ;; 1. BOARD OUTLINE (50mm x 68mm)
  ;; ==========================================
  (gr_line (start 3 0) (end 47 0) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 47 0) (mid 49.121 0.879) (end 50 3) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 50 3) (end 50 65) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 50 65) (mid 49.121 67.121) (end 47 68) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 47 68) (end 3 68) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 3 68) (mid 0.879 67.121) (end 0 65) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 0 65) (end 0 3) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 0 3) (mid 0.879 0.879) (end 3 0) (layer "Edge.Cuts") (width 0.15))

  ;; 4x M2 Mounting Holes
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 3 3)
    (pad "1" thru_hole circle (at 0 0) (size 4.0 4.0) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 47 3)
    (pad "1" thru_hole circle (at 0 0) (size 4.0 4.0) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 3 65)
    (pad "1" thru_hole circle (at 0 0) (size 4.0 4.0) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))
  (footprint "MountingHole:MountingHole_2.2mm_M2_Pad" (layer "F.Cu") (at 47 65)
    (pad "1" thru_hole circle (at 0 0) (size 4.0 4.0) (drill 2.2) (layers *.Cu *.Mask) (net 1 "GND")))

  ;; Silkscreen Titles
  (gr_text "XiaoZhi MiniCube v2.4 Final" (at 25 4) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18) bold)))
  (gr_text "Dual-Rail 22.86 / 25.40mm" (at 25 6.5) (layer "F.SilkS")
    (effects (font (size 0.8 0.8) (thickness 0.12))))

  ;; ==========================================
  ;; 2. ESP32-S3 DUAL-RAIL SOCKET (2x22 Pins)
  ;; Left rail at x=11.5, y from 10.0 to 63.34
  ;; Right rail Inner at x=34.36 (22.86mm), Outer at x=36.90 (25.40mm)
  ;; ==========================================
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

    # ESP32 Left Rail
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu") (at 11.5 10)
    (fp_text reference "J_ESP_L" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(left_nets):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ESP32 Right Rail Inner (22.86mm)
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu") (at 34.36 10)
    (fp_text reference "J_ESP_R1" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
"""
    for i, (nid, nname) in enumerate(right_nets):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ESP32 Right Rail Outer (25.40mm)
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu") (at 36.90 10)
    (fp_text reference "J_ESP_R2" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
"""
    for i, (nid, nname) in enumerate(right_nets):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ==========================================
    # 3. SCREEN & RADAR HEADERS (Left Side x=3.0)
    # ==========================================
    lcd_spi = [(12, "LCD_MOSI_IO12"), (10, "LCD_DC_IO10"), (11, "LCD_SCK_IO11"), (13, "LCD_CS_IO13")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu") (at 3.0 12)
    (fp_text reference "J_LCD_SPI" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(lcd_spi):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    lcd_pwr = [(1, "GND"), (3, "+3V3"), (18, "TOUCH_SCL_IO1"), (19, "TOUCH_SDA_IO2")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu") (at 3.0 24)
    (fp_text reference "J_LCD_PWR" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(lcd_pwr):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    radar = [(2, "+5V"), (1, "GND"), (8, "RADAR_OUT_IO8"), (16, "RADAR_RX_IO17"), (17, "RADAR_TX_IO18")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu") (at 3.0 36)
    (fp_text reference "J_RADAR" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(radar):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ==========================================
    # 4. DAC HEADERS (Digital In & Analog Out)
    # ==========================================
    dac_in = [(2, "+5V"), (1, "GND"), (7, "DAC_BCK_IO7"), (15, "DAC_DIN_IO16"), (14, "DAC_LCK_IO15"), (1, "GND")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu") (at 45.0 12)
    (fp_text reference "J_DAC_IN" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(dac_in):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    dac_out = [(20, "AUDIO_L_OUT"), (1, "GND"), (21, "AUDIO_R_OUT")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical" (layer "F.Cu") (at 41.0 12)
    (fp_text reference "J_DAC_OUT" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
"""
    for i, (nid, nname) in enumerate(dac_out):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ==========================================
    # 5. PAM8302A AMP & OUTPUT HEADERS
    # ==========================================
    amp_in = [(22, "AMP_IN_SIG"), (1, "GND"), (9, "AMP_SD_IO9"), (1, "GND"), (2, "+5V")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu") (at 45.0 30)
    (fp_text reference "J_AMP_IN" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(amp_in):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    amp_out = [(23, "SPK_P"), (24, "SPK_N")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical" (layer "F.Cu") (at 41.0 30)
    (fp_text reference "J_AMP_OUT" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
"""
    for i, (nid, nname) in enumerate(amp_out):
        content += f"""    (pad "{i+1}" thru_hole oval (at 0 {i*2.54:.2f}) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # J_SPK 2840 Speaker Output Connector
    content += """  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu") (at 45.0 46)
    (fp_text reference "J_SPK" (at 0 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
    (pad "1" thru_hole oval (at 0 0) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net 23 "SPK_P"))
    (pad "2" thru_hole oval (at 0 2.54) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net 24 "SPK_N"))
  )\n"""

    # ==========================================
    # 6. R1 & R2 1k RESISTORS
    # ==========================================
    content += """  (footprint "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" (layer "F.Cu") (at 28.0 14)
    (fp_text reference "R1_1k" (at 0 -1.8) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" thru_hole circle (at -3.81 0) (size 1.6 1.6) (drill 0.9) (layers *.Cu *.Mask) (net 25 "TIP_SW"))
    (pad "2" thru_hole circle (at 3.81 0) (size 1.6 1.6) (drill 0.9) (layers *.Cu *.Mask) (net 22 "AMP_IN_SIG"))
  )\n"""

    content += """  (footprint "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal" (layer "F.Cu") (at 28.0 18)
    (fp_text reference "R2_1k" (at 0 -1.8) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.08))))
    (pad "1" thru_hole circle (at -3.81 0) (size 1.6 1.6) (drill 0.9) (layers *.Cu *.Mask) (net 26 "RING_SW"))
    (pad "2" thru_hole circle (at 3.81 0) (size 1.6 1.6) (drill 0.9) (layers *.Cu *.Mask) (net 22 "AMP_IN_SIG"))
  )\n"""

    # ==========================================
    # 7. PJ-324M 3.5mm JACK
    # ==========================================
    content += """  (footprint "Connector_Audio:Jack_3.5mm_PJ324M_Horizontal" (layer "F.Cu") (at 34.0 4.0)
    (fp_text reference "J_PJ324M" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "1" thru_hole circle (at 0 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 1 "GND"))
    (pad "2" thru_hole circle (at 3.5 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 20 "AUDIO_L_OUT"))
    (pad "3" thru_hole circle (at -3.5 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 21 "AUDIO_R_OUT"))
    (pad "4" thru_hole circle (at 3.5 3.0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 25 "TIP_SW"))
    (pad "5" thru_hole circle (at -3.5 3.0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 26 "RING_SW"))
  )\n"""

    # ==========================================
    # 8. C1 CAPACITOR & 5V POWER TERMINAL
    # ==========================================
    content += """  (footprint "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm" (layer "F.Cu") (at 8.0 4.0)
    (fp_text reference "C1_100uF" (at 0 -2.8) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
    (pad "1" thru_hole rect (at -1.25 0) (size 1.8 1.8) (drill 0.9) (layers *.Cu *.Mask) (net 2 "+5V"))
    (pad "2" thru_hole circle (at 1.25 0) (size 1.8 1.8) (drill 0.9) (layers *.Cu *.Mask) (net 1 "GND"))
  )\n"""

    content += """  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu") (at 15.0 4.0)
    (fp_text reference "J_PWR_5V" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
    (pad "1" thru_hole rect (at 0 0) (size 1.8 1.8) (drill 1.0) (layers *.Cu *.Mask) (net 2 "+5V"))
    (pad "2" thru_hole circle (at 2.54 0) (size 1.8 1.8) (drill 1.0) (layers *.Cu *.Mask) (net 1 "GND"))
  )\n"""

    # ==========================================
    # 9. MIC HEADER (Bottom Center x=18.65, y=65.0)
    # ==========================================
    mic = [(3, "+3V3"), (1, "GND"), (4, "MIC_SD_IO4"), (1, "GND"), (5, "MIC_WS_IO5"), (6, "MIC_SCK_IO6")]
    content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu") (at 18.65 65)
    (fp_text reference "J_MIC" (at 6.35 -1.5) (layer "F.SilkS") (effects (font (size 0.7 0.7) (thickness 0.1))))
"""
    for i, (nid, nname) in enumerate(mic):
        content += f"""    (pad "{i+1}" thru_hole oval (at {i*2.54:.2f} 0) (size 1.6 1.6) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    content += "  )\n"

    # ==========================================
    # 10. DUAL-RAIL BRIDGES (Inner to Outer Rail)
    # Only connecting matching nets on bottom layer
    # ==========================================
    tracks = []
    for i in range(22):
        py = 10.0 + i * 2.54
        tracks.append(f"""  (segment (start 34.36 {py:.2f}) (end 36.90 {py:.2f}) (width 0.35) (layer "B.Cu") (net {right_nets[i][0]}))\n""")

    content += "".join(tracks)
    content += ")\n"

    # Save to desktop & LCEDA
    out_pcb = "/Users/kavin/Desktop/【唯一文件】小智AI小方盒_v2.0_20261108.kicad_pcb"
    lceda_pcb = "/Users/kavin/Documents/LCEDA-Pro/projects/【唯一文件】小智AI小方盒_v2.0_20261108.kicad_pcb"
    with open(out_pcb, "w", encoding="utf-8") as f:
        f.write(content)
    with open(lceda_pcb, "w", encoding="utf-8") as f:
        f.write(content)

    print("Clean unrouted netlist PCB saved at:", out_pcb)

if __name__ == "__main__":
    generate_clean_drc_pcb()
