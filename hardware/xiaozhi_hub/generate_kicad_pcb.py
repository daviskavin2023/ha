import os
import sys
import zipfile

def generate_kicad_pcb():
    # Board dimensions: 80mm x 75mm
    # Origin at top-left: (0,0) to (80, 75)
    
    pcb_content = """(kicad_pcb (version 20211014) (generator "xiaozhi_pcb_generator")

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
    (pad_to_paste_clearance -0.05)
    (pad_to_paste_clearance_ratio 0)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (usegerberextensions true)
      (usegerberattributes true)
      (usegerberadvancedattributes true)
      (creategerberjobfile true)
      (svguseinch false)
      (svgprecision 6)
      (excludeedgelayer true)
      (plotframeref false)
      (viasonmask false)
      (mode 1)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (dxfpolygonmode true)
      (dxfimperialunits true)
      (dxfusepcbnewfont true)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (sketchpadsonfab false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "")
    )
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

  ;; ==========================================
  ;; BOARD OUTLINE (80mm x 75mm with rounded corners)
  ;; ==========================================
  (gr_line (start 4 0) (end 76 0) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 76 0) (mid 78.828 1.172) (end 80 4) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 80 4) (end 80 71) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 80 71) (mid 78.828 73.828) (end 76 75) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 76 75) (end 4 75) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 4 75) (mid 1.172 73.828) (end 0 71) (layer "Edge.Cuts") (width 0.15))
  (gr_line (start 0 71) (end 0 4) (layer "Edge.Cuts") (width 0.15))
  (gr_arc (start 0 4) (mid 1.172 1.172) (end 4 0) (layer "Edge.Cuts") (width 0.15))

  ;; ==========================================
  ;; 4x M3 MOUNTING HOLES (3.2mm drill, 6mm pad)
  ;; ==========================================
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (at 4 4)
    (pad "1" thru_hole circle (at 0 0) (size 6 6) (drill 3.2) (layers *.Cu *.Mask) (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (at 76 4)
    (pad "1" thru_hole circle (at 0 0) (size 6 6) (drill 3.2) (layers *.Cu *.Mask) (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (at 4 71)
    (pad "1" thru_hole circle (at 0 0) (size 6 6) (drill 3.2) (layers *.Cu *.Mask) (net 1 "GND"))
  )
  (footprint "MountingHole:MountingHole_3.2mm_M3_Pad" (layer "F.Cu")
    (at 76 71)
    (pad "1" thru_hole circle (at 0 0) (size 6 6) (drill 3.2) (layers *.Cu *.Mask) (net 1 "GND"))
  )

  ;; ==========================================
  ;; SILKSCREEN TEXT LABELS
  ;; ==========================================
  (gr_text "XiaoZhi AI Desk Hub v1.0" (at 40 4) (layer "F.SilkS")
    (effects (font (size 1.8 1.8) (thickness 0.25) bold))
  )
  (gr_text "Type-C 5V IN" (at 12 7) (layer "F.SilkS")
    (effects (font (size 1.0 1.0) (thickness 0.15)))
  )
  (gr_text "PJ-324M 3.5mm" (at 68 7) (layer "F.SilkS")
    (effects (font (size 1.0 1.0) (thickness 0.15)))
  )
  (gr_text "RADAR LD2410C" (at 12 15) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18)))
  )
  (gr_text "ESP32-S3 [USB DOWN]" (at 40 18) (layer "F.SilkS")
    (effects (font (size 1.4 1.4) (thickness 0.2) bold))
  )
  (gr_text "PCM5102A DAC" (at 68 18) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18)))
  )
  (gr_text "PAM8302A AMP" (at 68 40) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18)))
  )
  (gr_text "SPK 4R/3W" (at 68 56) (layer "F.SilkS")
    (effects (font (size 1.1 1.1) (thickness 0.18)))
  )
  (gr_text "2.01 Inch LCD (ST7789)" (at 18 53) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18)))
  )
  (gr_text "MIC INMP441" (at 40 68) (layer "F.SilkS")
    (effects (font (size 1.2 1.2) (thickness 0.18)))
  )

  ;; ==========================================
  ;; J1: ESP32-S3 DevKitC (2x22 Pin 2.54mm, pitch 22.86mm)
  ;; Centered at x=40, Left rail x=28.57, Right rail x=51.43
  ;; y starts at 22.0 to 75.34 (22 pins, step 2.54)
  ;; ==========================================
"""

    # Left Rail of ESP32-S3 (22 Pins)
    # y = 22.0 + i*2.54
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

    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu")
    (at 28.57 22)
    (fp_text reference "J1_L" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
"""
    for i, (nid, nname) in enumerate(left_nets):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical" (layer "F.Cu")
    (at 51.43 22)
    (fp_text reference "J1_R" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
"""
    for i, (nid, nname) in enumerate(right_nets):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J2 & J3: 2.01 Inch Screen Sockets (2x 1x4 2.54mm)
    # At (12, 58) and (12, 65)
    # ==========================================
    lcd_spi = [(12, "LCD_MOSI_IO12"), (10, "LCD_DC_IO10"), (11, "LCD_SCK_IO11"), (13, "LCD_CS_IO13")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu")
    (at 10 58)
    (fp_text reference "J_LCD_SPI" (at 3.81 -1.8) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(lcd_spi):
        px = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at {px:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    lcd_pwr = [(1, "GND"), (3, "+3V3"), (18, "TOUCH_SCL_IO1"), (19, "TOUCH_SDA_IO2")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical" (layer "F.Cu")
    (at 10 65)
    (fp_text reference "J_LCD_PWR" (at 3.81 -1.8) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(lcd_pwr):
        px = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at {px:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J4: INMP441 Microphone Socket (1x6 2.54mm)
    # At (35, 71)
    # Pin 1: VDD(3V3), 2: GND, 3: SD, 4: L/R(GND), 5: WS, 6: SCK
    # ==========================================
    mic_pins = [(3, "+3V3"), (1, "GND"), (4, "MIC_SD_IO4"), (1, "GND"), (5, "MIC_WS_IO5"), (6, "MIC_SCK_IO6")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu")
    (at 33.65 71)
    (fp_text reference "J_MIC" (at 6.35 -1.8) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(mic_pins):
        px = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at {px:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J5: LD2410C Radar Socket (1x5 2.54mm)
    # At (10, 20)
    # Pin 1: 5V, 2: GND, 3: OUT, 4: TX, 5: RX
    # ==========================================
    radar_pins = [(2, "+5V"), (1, "GND"), (8, "RADAR_OUT_IO8"), (16, "RADAR_RX_IO17"), (17, "RADAR_TX_IO18")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu")
    (at 10 20)
    (fp_text reference "J_RADAR" (at 5.08 -1.8) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(radar_pins):
        px = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at {px:.2f} 0) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J6: PCM5102A DAC Socket (1x6 Input side + 1x3 Output side)
    # Input side at (68, 22)
    # Pin 1: 5V, 2: GND, 3: BCK, 4: DIN, 5: LCK, 6: GND(SCL/FMT)
    # ==========================================
    dac_in = [(2, "+5V"), (1, "GND"), (7, "DAC_BCK_IO7"), (15, "DAC_DIN_IO16"), (14, "DAC_LCK_IO15"), (1, "GND")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical" (layer "F.Cu")
    (at 68 22)
    (fp_text reference "J_DAC_IN" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(dac_in):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # DAC Output Side (L, AGND, R)
    dac_out = [(20, "AUDIO_L_OUT"), (1, "GND"), (21, "AUDIO_R_OUT")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical" (layer "F.Cu")
    (at 73 25)
    (fp_text reference "J_DAC_OUT" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(dac_out):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # U1: PAM8302A Amp Socket (1x5 2.54mm)
    # At (68, 44)
    # Pin 1: A+(AMP_IN_SIG), 2: A-(GND), 3: SD(AMP_SD), 4: GND, 5: 5V
    # ==========================================
    amp_pins = [(22, "AMP_IN_SIG"), (1, "GND"), (9, "AMP_SD_IO9"), (1, "GND"), (2, "+5V")]
    pcb_content += """  (footprint "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical" (layer "F.Cu")
    (at 68 44)
    (fp_text reference "U_AMP" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(amp_pins):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J8: Speaker Header (1x2 2.54mm / XH2.54)
    # At (68, 60)
    # ==========================================
    spk_pins = [(23, "SPK_P"), (24, "SPK_N")]
    pcb_content += """  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu")
    (at 68 60)
    (fp_text reference "J_SPK" (at 0 -2.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
"""
    for i, (nid, nname) in enumerate(spk_pins):
        py = i * 2.54
        pcb_content += f"""    (pad "{i+1}" thru_hole oval (at 0 {py:.2f}) (size 1.7 1.7) (drill 1.0) (layers *.Cu *.Mask) (net {nid} "{nname}"))\n"""
    pcb_content += "  )\n"

    # ==========================================
    # J7: PJ-324M 3.5mm Headphone Jack (5-Pin with auto-switch)
    # At (68, 8)
    # Pin 1: GND, Pin 2: L, Pin 3: R, Pin 4: Sw_L (to AMP_IN), Pin 5: Sw_R (to AMP_IN)
    # ==========================================
    pcb_content += """  (footprint "Connector_Audio:Jack_3.5mm_PJ324M_Horizontal" (layer "F.Cu")
    (at 68 8)
    (fp_text reference "J_AUDIO_3V5" (at 0 -3.0) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.15))))
    (pad "1" thru_hole circle (at 0 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 1 "GND"))
    (pad "2" thru_hole circle (at 3.5 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 20 "AUDIO_L_OUT"))
    (pad "3" thru_hole circle (at -3.5 0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 21 "AUDIO_R_OUT"))
    (pad "4" thru_hole circle (at 3.5 3.0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 22 "AMP_IN_SIG"))
    (pad "5" thru_hole circle (at -3.5 3.0) (size 2.0 2.0) (drill 1.2) (layers *.Cu *.Mask) (net 22 "AMP_IN_SIG"))
  )\n"""

    # ==========================================
    # C1: 100uF Bulk Filter Capacitor (Radial, lead pitch 2.54mm)
    # At (18, 8)
    # ==========================================
    pcb_content += """  (footprint "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm" (layer "F.Cu")
    (at 20 8)
    (fp_text reference "C1_100uF" (at 0 -3.2) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "1" thru_hole rect (at -1.25 0) (size 1.8 1.8) (drill 0.9) (layers *.Cu *.Mask) (net 2 "+5V"))
    (pad "2" thru_hole circle (at 1.25 0) (size 1.8 1.8) (drill 0.9) (layers *.Cu *.Mask) (net 1 "GND"))
  )\n"""

    # ==========================================
    # J9: Type-C 5V IN / Screw Terminal (Pitch 2.54mm 2Pin)
    # At (10, 8)
    # ==========================================
    pcb_content += """  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical" (layer "F.Cu")
    (at 10 8)
    (fp_text reference "J_PWR_5V" (at 0 -2.2) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
    (pad "1" thru_hole rect (at 0 0) (size 2.0 2.0) (drill 1.0) (layers *.Cu *.Mask) (net 2 "+5V"))
    (pad "2" thru_hole circle (at 2.54 0) (size 2.0 2.0) (drill 1.0) (layers *.Cu *.Mask) (net 1 "GND"))
  )\n"""

    # ==========================================
    # POWER TRACKS (5V and 3.3V, wide tracks: 0.6mm ~ 0.8mm)
    # ==========================================
    # 5V Rail from J_PWR (10,8) -> C1 (18.75,8) -> Radar (10,20) -> ESP32 5V (28.57, 72.8) -> DAC (68,22) -> AMP (68, 54.16)
    pcb_content += """  (segment (start 10 8) (end 18.75 8) (width 0.8) (layer "F.Cu") (net 2))
  (segment (start 10 8) (end 10 20) (width 0.8) (layer "F.Cu") (net 2))
  (segment (start 18.75 8) (end 28.57 20) (width 0.8) (layer "F.Cu") (net 2))
  (segment (start 28.57 20) (end 28.57 72.8) (width 0.8) (layer "B.Cu") (net 2))
  (segment (start 18.75 8) (end 68 22) (width 0.8) (layer "F.Cu") (net 2))
  (segment (start 68 22) (end 68 54.16) (width 0.8) (layer "F.Cu") (net 2))
"""

    # Close kicad_pcb
    pcb_content += ")\n"

    out_kicad = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_hub.kicad_pcb"
    artifact_kicad = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/xiaozhi_hub.kicad_pcb"
    with open(out_kicad, "w", encoding="utf-8") as f:
        f.write(pcb_content)
    with open(artifact_kicad, "w", encoding="utf-8") as f:
        f.write(pcb_content)

    print("KiCad PCB generated at:", out_kicad)

    # Package into a ready-to-order zip
    out_zip = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/Xiaozhi_Hub_JLCPCB_Order.zip"
    artifact_zip = "/Users/kavin/.gemini/antigravity/brain/f79a527e-0167-44c2-8026-8a1673c08e4f/Xiaozhi_Hub_JLCPCB_Order.zip"
    with zipfile.ZipFile(out_zip, 'w') as z:
        z.write(out_kicad, arcname="xiaozhi_hub.kicad_pcb")
        z.write("/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_pcb_assembly_guide.png", arcname="xiaozhi_pcb_assembly_guide.png")
    with zipfile.ZipFile(artifact_zip, 'w') as z:
        z.write(out_kicad, arcname="xiaozhi_hub.kicad_pcb")
        z.write("/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/xiaozhi_pcb_assembly_guide.png", arcname="xiaozhi_pcb_assembly_guide.png")
    print("Order package generated at:", out_zip)

if __name__ == "__main__":
    generate_kicad_pcb()
