import os
import zipfile

def generate_standard_gerber():
    # Board dimensions: 80mm x 75mm
    # Standard RS-274X format generated for JLCPCB
    
    # 1. Edge.Cuts (GKO / GML)
    gko = """G04 Board Outline*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,0.150000*%
D10*
X0Y0D02*
X8000000Y0D01*
X8000000Y7500000D01*
X0Y7500000D01*
X0Y0D01*
M02*
"""

    # 2. Drill file (DRL / Excellon)
    # 4x M3 mounting holes at (4,4), (76,4), (4,71), (76,71) - Dia 3.2mm
    # 1.0mm holes for 2.54 pin headers
    # 1.2mm holes for PJ-324
    drl = """M48
; DRILL file for JLCPCB
METRIC,TZ
T1C3.200
T2C1.000
T3C1.200
T4C0.900
%
T1
X4000Y4000
X76000Y4000
X4000Y71000
X76000Y71000
T2
"""
    # Add ESP32 Left rail (22 pins at x=28.57, y=22.0 + i*2.54)
    for i in range(22):
        py = int((22.0 + i * 2.54) * 1000)
        drl += f"X28570Y{py}\n"
    # ESP32 Right rail (22 pins at x=51.43, y=22.0 + i*2.54)
    for i in range(22):
        py = int((22.0 + i * 2.54) * 1000)
        drl += f"X51430Y{py}\n"
    # Screen SPI (4 pins at x=10+i*2.54, y=58)
    for i in range(4):
        px = int((10.0 + i * 2.54) * 1000)
        drl += f"X{px}Y58000\n"
    # Screen PWR (4 pins at x=10+i*2.54, y=65)
    for i in range(4):
        px = int((10.0 + i * 2.54) * 1000)
        drl += f"X{px}Y65000\n"
    # MIC (6 pins at x=33.65+i*2.54, y=71)
    for i in range(6):
        px = int((33.65 + i * 2.54) * 1000)
        drl += f"X{px}Y71000\n"
    # Radar (5 pins at x=10+i*2.54, y=20)
    for i in range(5):
        px = int((10.0 + i * 2.54) * 1000)
        drl += f"X{px}Y20000\n"
    # DAC In (6 pins at x=68, y=22+i*2.54)
    for i in range(6):
        py = int((22.0 + i * 2.54) * 1000)
        drl += f"X68000Y{py}\n"
    # DAC Out (3 pins at x=73, y=25+i*2.54)
    for i in range(3):
        py = int((25.0 + i * 2.54) * 1000)
        drl += f"X73000Y{py}\n"
    # AMP (5 pins at x=68, y=44+i*2.54)
    for i in range(5):
        py = int((44.0 + i * 2.54) * 1000)
        drl += f"X68000Y{py}\n"
    # Speaker (2 pins at x=68, y=60+i*2.54)
    for i in range(2):
        py = int((60.0 + i * 2.54) * 1000)
        drl += f"X68000Y{py}\n"
    # Power (2 pins at x=10, y=8+i*2.54)
    drl += "X10000Y8000\nX10000Y10540\n"
    
    # PJ-324 5 pins (T3: 1.2mm)
    drl += "T3\n"
    drl += "X68000Y8000\nX71500Y8000\nX64500Y8000\nX71500Y11000\nX64500Y11000\n"
    
    # Cap (T4: 0.9mm)
    drl += "T4\n"
    drl += "X18750Y8000\nX21250Y8000\n"
    drl += "M30\n"

    # 3. Top Copper (GTL)
    gtl = """G04 Top Copper Layer*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.700000*%
%ADD11C,2.000000*%
%ADD12C,6.000000*%
%ADD13C,0.800000*%
D12*
X400000Y400000D03*
X7600000Y400000D03*
X400000Y7100000D03*
X7600000Y7100000D03*
D10*
"""
    # Flash pads for pin headers
    for i in range(22):
        py = int((22.0 + i * 2.54) * 100000)
        gtl += f"X2857000Y{py}D03*\nX5143000Y{py}D03*\n"
    for i in range(4):
        px = int((10.0 + i * 2.54) * 100000)
        gtl += f"X{px}Y5800000D03*\nX{px}Y6500000D03*\n"
    for i in range(6):
        px = int((33.65 + i * 2.54) * 100000)
        gtl += f"X{px}Y7100000D03*\n"
    for i in range(5):
        px = int((10.0 + i * 2.54) * 100000)
        gtl += f"X{px}Y2000000D03*\n"
    for i in range(6):
        py = int((22.0 + i * 2.54) * 100000)
        gtl += f"X6800000Y{py}D03*\n"
    for i in range(3):
        py = int((25.0 + i * 2.54) * 100000)
        gtl += f"X7300000Y{py}D03*\n"
    for i in range(5):
        py = int((44.0 + i * 2.54) * 100000)
        gtl += f"X6800000Y{py}D03*\n"
    for i in range(2):
        py = int((60.0 + i * 2.54) * 100000)
        gtl += f"X6800000Y{py}D03*\n"
    
    # 5V Power bus tracks
    gtl += """D13*
X1000000Y800000D02*
X1875000Y800000D01*
X1000000Y800000D02*
X1000000Y2000000D01*
X1875000Y800000D02*
X2857000Y2000000D01*
X2857000Y7280000D01*
X1875000Y800000D02*
X6800000Y2200000D01*
X6800000Y5416000D01*
M02*
"""

    # 4. Bottom Copper (GBL - Ground Plane)
    gbl = """G04 Bottom Copper Layer*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.700000*%
%ADD12C,6.000000*%
%ADD14C,0.500000*%
D12*
X400000Y400000D03*
X7600000Y400000D03*
X400000Y7100000D03*
X7600000Y7100000D03*
D14*
X200000Y200000D02*
X7800000Y200000D01*
X7800000Y7300000D01*
X200000Y7300000D01*
X200000Y200000D01*
M02*
"""

    # 5. Top Solder Mask (GTS)
    gts = """G04 Top Solder Mask*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,1.850000*%
%ADD12C,6.200000*%
D12*
X400000Y400000D03*
X7600000Y400000D03*
X400000Y7100000D03*
X7600000Y7100000D03*
D10*
"""
    for i in range(22):
        py = int((22.0 + i * 2.54) * 100000)
        gts += f"X2857000Y{py}D03*\nX5143000Y{py}D03*\n"
    for i in range(4):
        px = int((10.0 + i * 2.54) * 100000)
        gts += f"X{px}Y5800000D03*\nX{px}Y6500000D03*\n"
    for i in range(6):
        px = int((33.65 + i * 2.54) * 100000)
        gts += f"X{px}Y7100000D03*\n"
    for i in range(5):
        px = int((10.0 + i * 2.54) * 100000)
        gts += f"X{px}Y2000000D03*\n"
    for i in range(6):
        py = int((22.0 + i * 2.54) * 100000)
        gts += f"X6800000Y{py}D03*\n"
    for i in range(3):
        py = int((25.0 + i * 2.54) * 100000)
        gts += f"X7300000Y{py}D03*\n"
    for i in range(5):
        py = int((44.0 + i * 2.54) * 100000)
        gts += f"X6800000Y{py}D03*\n"
    for i in range(2):
        py = int((60.0 + i * 2.54) * 100000)
        gts += f"X6800000Y{py}D03*\n"
    gts += "M02*\n"

    # 6. Bottom Solder Mask (GBS)
    gbs = gts.replace("Top", "Bottom")

    # 7. Top Silkscreen (GTO)
    gto = """G04 Top Silkscreen*
%FSLAX25Y25*%
%MOMM*%
%LPD*%
%ADD10C,0.150000*%
D10*
X1000000Y400000D02*
X7000000Y400000D01*
M02*
"""
    gbo = "G04 Bottom Silkscreen*\nM02*\n"

    # Write files
    base_dir = "/Users/kavin/Projects/yulaiwo/3038-网关-ha/hardware/xiaozhi_hub/gerber_files"
    os.makedirs(base_dir, exist_ok=True)
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
        with open(os.path.join(base_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)
            
    # Zip package for JLCPCB
    zip_path = "/Users/kavin/Desktop/Gerber_XiaoZhi_Hub_JLCPCB.zip"
    with zipfile.ZipFile(zip_path, 'w') as z:
        for fname in files.keys():
            z.write(os.path.join(base_dir, fname), arcname=fname)
            
    print("Standard Gerber ZIP created at:", zip_path)

if __name__ == "__main__":
    generate_standard_gerber()
