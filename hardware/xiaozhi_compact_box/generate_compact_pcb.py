import os
import zipfile

def generate_compact_box_pcb():
    # Compact Box PCB Dimensions: 48mm wide x 60mm tall
    # Perfectly fits behind the 2.01" screen inside the 52mm x 64mm mini box!
    # Origin (0,0) to (48, 60)
    
    # 1. Edge Cuts (GKO)
    gko = """G04 Board Outline (48mm x 60mm with R3 corners)*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,0.150000*%
D10*
X300000Y0D02*
X4500000Y0D01*
X4800000Y300000D01*
X4800000Y5700000D01*
X4500000Y6000000D01*
X300000Y6000000D01*
X0Y5700000D01*
X0Y300000D01*
X300000Y0D01*
M02*
"""

    # 2. Drill file (DRL)
    # 4 Corner M2 mounting holes at (3,3), (45,3), (3,57), (45,57) - Dia 2.2mm
    # ESP32 Left rail at x=12.57, y=2.54*i + 3.0 (22 pins)
    # ESP32 Right rail at x=35.43, y=2.54*i + 3.0 (22 pins)
    # Pitch between rails = 22.86mm (standard 900mil)
    drl = """M48
; DRILL file for Compact XiaoZhi Box PCB
METRIC,TZ
T1C2.200
T2C1.000
T3C1.200
T4C0.900
%
T1
X3000Y3000
X45000Y3000
X3000Y57000
X45000Y57000
T2
"""
    # ESP32-S3 Left rail (22 pins)
    for i in range(22):
        py = int((3.0 + i * 2.54) * 1000)
        drl += f"X12570Y{py}\n"
    # ESP32-S3 Right rail (22 pins)
    for i in range(22):
        py = int((3.0 + i * 2.54) * 1000)
        drl += f"X35430Y{py}\n"
        
    # Screen SPI Header (4 pins at x=3, y=16+i*2.54)
    for i in range(4):
        py = int((16.0 + i * 2.54) * 1000)
        drl += f"X3000Y{py}\n"
    # Screen I2C/Power Header (4 pins at x=3, y=28+i*2.54)
    for i in range(4):
        py = int((28.0 + i * 2.54) * 1000)
        drl += f"X3000Y{py}\n"
        
    # Radar Header (5 pins at x=3, y=40+i*2.54)
    for i in range(5):
        py = int((40.0 + i * 2.54) * 1000)
        drl += f"X3000Y{py}\n"

    # MIC Header (6 pins at x=18+i*2.54, y=57)
    for i in range(6):
        px = int((18.0 + i * 2.54) * 1000)
        drl += f"X{px}Y57000\n"

    # DAC In Header (6 pins at x=45, y=14+i*2.54)
    for i in range(6):
        py = int((14.0 + i * 2.54) * 1000)
        drl += f"X45000Y{py}\n"

    # AMP Header (5 pins at x=45, y=32+i*2.54)
    for i in range(5):
        py = int((32.0 + i * 2.54) * 1000)
        drl += f"X45000Y{py}\n"

    # Speaker Header (2 pins at x=45, y=47+i*2.54)
    for i in range(2):
        py = int((47.0 + i * 2.54) * 1000)
        drl += f"X45000Y{py}\n"

    # Type-C 5V IN (2 pins at x=20, y=3)
    drl += "X20000Y3000\nX22540Y3000\n"

    # PJ-324 3.5mm Headphone Jack (T3: 1.2mm at x=28, y=3)
    drl += "T3\n"
    drl += "X28000Y3000\nX31500Y3000\nX24500Y3000\nX31500Y6000\nX24500Y6000\n"

    # 100uF Cap (T4: 0.9mm at x=16, y=3)
    drl += "T4\n"
    drl += "X16000Y3000\nX16000Y5540\n"
    drl += "M30\n"

    # 3. Top Copper (GTL)
    gtl = """G04 Top Copper Layer*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.700000*%
%ADD11C,2.000000*%
%ADD12C,4.500000*%
%ADD13C,0.800000*%
D12*
X300000Y300000D03*
X4500000Y300000D03*
X300000Y5700000D03*
X4500000Y5700000D03*
D10*
"""
    # Flash ESP32 pins
    for i in range(22):
        py = int((3.0 + i * 2.54) * 100000)
        gtl += f"X1257000Y{py}D03*\nX3543000Y{py}D03*\n"
    # Screen
    for i in range(4):
        py = int((16.0 + i * 2.54) * 100000)
        gtl += f"X300000Y{py}D03*\n"
    for i in range(4):
        py = int((28.0 + i * 2.54) * 100000)
        gtl += f"X300000Y{py}D03*\n"
    # Radar
    for i in range(5):
        py = int((40.0 + i * 2.54) * 100000)
        gtl += f"X300000Y{py}D03*\n"
    # MIC
    for i in range(6):
        px = int((18.0 + i * 2.54) * 100000)
        gtl += f"X{px}Y5700000D03*\n"
    # DAC & AMP
    for i in range(6):
        py = int((14.0 + i * 2.54) * 100000)
        gtl += f"X4500000Y{py}D03*\n"
    for i in range(5):
        py = int((32.0 + i * 2.54) * 100000)
        gtl += f"X4500000Y{py}D03*\n"
    for i in range(2):
        py = int((47.0 + i * 2.54) * 100000)
        gtl += f"X4500000Y{py}D03*\n"
        
    # 5V Power Tracks (0.8mm width)
    gtl += """D13*
X2000000Y300000D02*
X1600000Y300000D01*
X1600000Y300000D02*
X1257000Y5380000D01*
X2000000Y300000D02*
X4500000Y1400000D01*
X4500000Y4216000D01*
X1600000Y300000D02*
X300000Y4000000D01*
M02*
"""

    # 4. Bottom Copper (GBL - Ground Plane)
    gbl = """G04 Bottom Copper Layer*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.700000*%
%ADD12C,4.500000*%
%ADD14C,0.500000*%
D12*
X300000Y300000D03*
X4500000Y300000D03*
X300000Y5700000D03*
X4500000Y5700000D03*
D14*
X150000Y150000D02*
X4650000Y150000D01*
X4650000Y5850000D01*
X150000Y5850000D01*
X150000Y150000D01*
M02*
"""

    # 5. Top Solder Mask (GTS)
    gts = """G04 Top Solder Mask*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.850000*%
%ADD12C,4.700000*%
D12*
X300000Y300000D03*
X4500000Y300000D03*
X300000Y5700000D03*
X4500000Y5700000D03*
D10*
"""
    for i in range(22):
        py = int((3.0 + i * 2.54) * 100000)
        gts += f"X1257000Y{py}D03*\nX3543000Y{py}D03*\n"
    for i in range(4):
        py = int((16.0 + i * 2.54) * 100000)
        gts += f"X300000Y{py}D03*\n"
    for i in range(4):
        py = int((28.0 + i * 2.54) * 100000)
        gts += f"X300000Y{py}D03*\n"
    for i in range(5):
        py = int((40.0 + i * 2.54) * 100000)
        gts += f"X300000Y{py}D03*\n"
    for i in range(6):
        px = int((18.0 + i * 2.54) * 100000)
        gts += f"X{px}Y5700000D03*\n"
    for i in range(6):
        py = int((14.0 + i * 2.54) * 100000)
        gts += f"X4500000Y{py}D03*\n"
    for i in range(5):
        py = int((32.0 + i * 2.54) * 100000)
        gts += f"X4500000Y{py}D03*\n"
    for i in range(2):
        py = int((47.0 + i * 2.54) * 100000)
        gts += f"X4500000Y{py}D03*\n"
    gts += "M02*\n"

    # 6. Bottom Solder Mask (GBS)
    gbs = gts.replace("Top", "Bottom")

    # 7. Silkscreens
    gto = """G04 Top Silkscreen*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,0.150000*%
D10*
X500000Y100000D02*
X4300000Y100000D01*
M02*
"""
    gbo = "G04 Bottom Silkscreen*\nM02*\n"

    # Base folder
    box_gerber_dir = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_compact_box/gerber"
    os.makedirs(box_gerber_dir, exist_ok=True)
    files = {
        "Gerber_BoardOutline.GKO": gko,
        "Gerber_TopCopper.GTL": gtl,
        "Gerber_BottomCopper.GBL": gbl,
        "Gerber_TopSolderMask.GTS": gts,
        "Gerber_BottomSolderMask.GBS": gbs,
        "Gerber_TopSilkscreen.GTO": gto,
        "Gerber_BottomSilkscreen.GBO": gbo,
        "Drill_Plated.DRL": drl
    }
    for fname, content in files.items():
        with open(os.path.join(box_gerber_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    # Output ZIP to Desktop
    desktop_zip = "/Users/kavin/Desktop/Gerber_XiaoZhi_CompactBox_JLCPCB.zip"
    repo_zip = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_compact_box/Gerber_XiaoZhi_CompactBox_JLCPCB.zip"
    with zipfile.ZipFile(desktop_zip, 'w') as z:
        for fname in files.keys():
            z.write(os.path.join(box_gerber_dir, fname), arcname=fname)
    with zipfile.ZipFile(repo_zip, 'w') as z:
        for fname in files.keys():
            z.write(os.path.join(box_gerber_dir, fname), arcname=fname)

    print("Compact Box Gerber generated on Desktop:", desktop_zip)

if __name__ == "__main__":
    generate_compact_box_pcb()
