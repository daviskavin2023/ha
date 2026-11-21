#!/usr/bin/env python3
"""
厨房多合一传感器极限紧凑型 PCB (52.0 × 52.0 mm，R3 圆角)
- 全直插 THT 封装，0 贴片、0 盘中孔、0 外部飞线
- ESP32-C3 SuperMini (V1601) + HLK-LD2410C + GY-SGP41 + SHT3x + GY-302 (BH1750)
- 含电源滤波电容 C1 (100uF 90°卧放)、C2/C3 (0.1uF 去耦)、预留 R1/R2 I2C 上拉及 5V 外接焊盘
"""

from pathlib import Path
import math
import heapq
import zipfile
import json
import collections

OUT_DIR = Path(__file__).parent
BOARD_W = 52.0
BOARD_H = 52.0
CORNER_R = 3.0
MIN_CLEARANCE = 0.20
VIA_R = 0.40

COMPONENTS = []

def add_comp(ref, fp_name, x, y, pads, value="", pin_labels=None, bbox=None):
    COMPONENTS.append({
        "ref": ref,
        "fp": fp_name,
        "x": round(x, 4),
        "y": round(y, 4),
        "value": value,
        "pads": pads,
        "pin_labels": pin_labels or [],
        "bbox": bbox,  # (x1, y1, x2, y2, label)
    })

def pin_row(n, nets, vertical=True, pitch=2.54, pad_sz=(1.65, 1.65), drill=1.0, pin1_rect=True):
    pads = []
    for i, net in enumerate(nets):
        dx = 0.0 if vertical else round(i * pitch, 4)
        dy = round(i * pitch, 4) if vertical else 0.0
        shape = "rect" if (i == 0 and pin1_rect) else "oval"
        pads.append((str(i + 1), dx, dy, shape, pad_sz[0], pad_sz[1], drill, net))
    return pads

# 1. 四角 M2.2 安装孔 (GND)
for idx, (hx, hy) in enumerate([(3.0, 3.0), (49.0, 3.0), (3.0, 49.0), (49.0, 49.0)], 1):
    add_comp(f"H{idx}", "MountingHole:MountingHole_2.2mm_M2_Pad", hx, hy,
             [("1", 0.0, 0.0, "circle", 4.2, 4.2, 2.2, "GND")])

# 2. ESP32-C3 SuperMini (V1601): 18.0 x 22.52 mm, Type-C 朝上齐平板边, 跨距 15.24 mm
ESP_L_NETS = ["+5V", "GND", "+3V3", "RADAR_RX_IO4", "RADAR_TX_IO3", "NC", "NC", "NC"]
ESP_R_NETS = ["BUZZ_IO5", "I2C_SDA_IO6", "I2C_SCL_IO7", "NC", "NC", "NC", "NC", "NC"]
add_comp("J_ESP_L", "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
         7.88, 3.80, pin_row(8, ESP_L_NETS, vertical=True), value="ESP_L",
         pin_labels=["5V", "G", "3V3", "4", "3", "2", "1", "0"],
         bbox=(6.5, 1.0, 24.5, 23.52, "ESP32-C3 V1601"))
add_comp("J_ESP_R", "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
         23.12, 3.80, pin_row(8, ESP_R_NETS, vertical=True), value="ESP_R",
         pin_labels=["5", "6", "7", "8", "9", "10", "20", "21"])

# 3. HLK-LD2410C 毫米波雷达 (22.0 x 16.0 mm, 天线面朝上, 针脚在左侧)
add_comp("J_RADAR", "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical",
         4.0, 32.0, pin_row(5, ["+5V", "GND", "NC", "RADAR_RX_IO4", "RADAR_TX_IO3"], vertical=True),
         value="LD2410C",
         pin_labels=["5V", "G", "OUT", "RX", "TX"],
         bbox=(2.0, 29.0, 24.0, 45.0, "HLK-LD2410C"))

# 4. 右侧热隔离传感器列 (与 ESP32 保持 >= 4mm 净空)
# 4.1 GY-SGP41 (12 x 12 mm)
add_comp("J_SGP41", "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
         30.0, 6.5, pin_row(4, ["+3V3", "GND", "I2C_SCL_IO7", "I2C_SDA_IO6"], vertical=True),
         value="GY-SGP41",
         pin_labels=["3V3", "G", "SCL", "SDA"],
         bbox=(28.5, 4.5, 40.5, 16.5, "GY-SGP41"))

# 4.2 SHT3x (14 x 11 mm)
add_comp("J_SHT3X", "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
         30.0, 20.5, pin_row(4, ["+3V3", "GND", "I2C_SCL_IO7", "I2C_SDA_IO6"], vertical=True),
         value="SHT3x",
         pin_labels=["3V3", "G", "SCL", "SDA"],
         bbox=(28.5, 18.8, 42.5, 29.8, "SHT3x"))

# 4.3 GY-302 BH1750 (18.5 x 14 mm, 芯片朝上, 针脚在左侧: ADDR, SDA, SCL, GND, VCC)
add_comp("J_BH1750", "Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical",
         29.0, 34.5, pin_row(5, ["GND", "I2C_SDA_IO6", "I2C_SCL_IO7", "GND", "+3V3"], vertical=True),
         value="BH1750",
         pin_labels=["ADR", "SDA", "SCL", "G", "3V3"],
         bbox=(27.5, 32.5, 46.0, 46.5, "GY-302 BH1750"))

# 5. 直插滤波/去耦电容 (100% THT，禁止贴片)
# C1: 100uF/16V 铝电解 (2.50mm 孔距, 90°向右卧放于 ESP32 与雷达间隙)
add_comp("C1", "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm",
         7.5, 26.2,
         [("1", 0.0, 0.0, "rect", 1.8, 1.8, 0.9, "+5V"),
          ("2", 2.50, 0.0, "circle", 1.8, 1.8, 0.9, "GND")],
         value="100uF_16V",
         pin_labels=["+", "-"])

# C3: 0.1uF (104) +5V 去耦独石电容 (2.54mm)
add_comp("C3", "Capacitor_THT:C_Disc_D4.3mm_W1.9mm_P2.54mm",
         20.5, 26.2,
         [("1", 0.0, 0.0, "rect", 1.65, 1.65, 0.9, "+5V"),
          ("2", 2.54, 0.0, "oval", 1.65, 1.65, 0.9, "GND")],
         value="0.1uF_5V")

# C2: 0.1uF (104) +3V3 去耦独石电容 (2.54mm, 靠近 SGP41/SHT3x)
add_comp("C2", "Capacitor_THT:C_Disc_D4.3mm_W1.9mm_P2.54mm",
         45.0, 12.0,
         [("1", 0.0, 0.0, "rect", 1.65, 1.65, 0.9, "+3V3"),
          ("2", 0.0, 2.54, "oval", 1.65, 1.65, 0.9, "GND")],
         value="0.1uF_3V3")

# 6. 预留直插 I2C 上拉电阻位 R1/R2 (1/4W 7.62mm，默认不焊)
add_comp("R1", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Vertical",
         45.0, 18.0,
         [("1", 0.0, 0.0, "rect", 1.65, 1.65, 0.9, "+3V3"),
          ("2", 0.0, 7.62, "oval", 1.65, 1.65, 0.9, "I2C_SDA_IO6")],
         value="4.7k_NP")
add_comp("R2", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Vertical",
         48.0, 18.0,
         [("1", 0.0, 0.0, "rect", 1.65, 1.65, 0.9, "+3V3"),
          ("2", 0.0, 7.62, "oval", 1.65, 1.65, 0.9, "I2C_SCL_IO7")],
         value="4.7k_NP")

# 7. 预留外接 5V 供电焊盘 (2P)
add_comp("J_PWR", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
         45.0, 7.0, pin_row(2, ["+5V", "GND"], vertical=False),
         value="EXT_5V",
         pin_labels=["5V", "G"])

# ---------------------------------------------------------------------------
# 2. 焊盘扁平化 & 网格路由器 (0.25mm 步长，MIN_CLEARANCE = 0.20mm)
# ---------------------------------------------------------------------------
all_pads = []
for comp in COMPONENTS:
    for pin_num, dx, dy, shape, sx, sy, drill, net in comp["pads"]:
        all_pads.append({
            "ref": comp["ref"],
            "pin": pin_num,
            "x": round(comp["x"] + dx, 4),
            "y": round(comp["y"] + dy, 4),
            "shape": shape,
            "sx": sx,
            "sy": sy,
            "drill": drill,
            "net": net,
        })

GRID = 0.25
NX = int(round(BOARD_W / GRID)) + 1
NY = int(round(BOARD_H / GRID)) + 1

def to_grid(x, y):
    return (int(round(x / GRID)), int(round(y / GRID)))

def to_mm(gx, gy):
    return (round(gx * GRID, 4), round(gy * GRID, 4))

def pt_to_pad_edge_dist(px, py, pad):
    hx = pad["sx"] / 2.0
    hy = pad["sy"] / 2.0
    dx = max(0.0, abs(px - pad["x"]) - hx)
    dy = max(0.0, abs(py - pad["y"]) - hy)
    return math.hypot(dx, dy)

# ESP32-C3 顶部陶瓷天线双层禁布区 (x: 10.5..20.5, y: 0.0..7.5)
KEEPOUT_RECT = (10.5, 0.0, 20.5, 7.5)

def in_keepout(px, py, margin=0.0):
    x1, y1, x2, y2 = KEEPOUT_RECT
    return (x1 - margin) <= px <= (x2 + margin) and (y1 - margin) <= py <= (y2 + margin)

pad_near_grid = collections.defaultdict(list)
for idx, p in enumerate(all_pads):
    gx0, gy0 = to_grid(p["x"], p["y"])
    rx = int(math.ceil((p["sx"] / 2.0 + 1.5) / GRID))
    ry = int(math.ceil((p["sy"] / 2.0 + 1.5) / GRID))
    for gx in range(max(0, gx0 - rx), min(NX, gx0 + rx + 1)):
        for gy in range(max(0, gy0 - ry), min(NY, gy0 + ry + 1)):
            pad_near_grid[(gx, gy)].append(idx)

occ = {"F.Cu": {}, "B.Cu": {}}
via_occ = {}

def is_free(layer, gx, gy, net, my_half_w, is_via=False):
    if gx < 3 or gx > NX - 4 or gy < 3 or gy > NY - 4:
        return False
    px, py = to_mm(gx, gy)
    # 圆角板边安全区
    if px < CORNER_R and py < CORNER_R and math.hypot(CORNER_R - px, CORNER_R - py) > CORNER_R - 0.8:
        return False
    if px > BOARD_W - CORNER_R and py < CORNER_R and math.hypot(px - (BOARD_W - CORNER_R), CORNER_R - py) > CORNER_R - 0.8:
        return False
    if px < CORNER_R and py > BOARD_H - CORNER_R and math.hypot(CORNER_R - px, py - (BOARD_H - CORNER_R)) > CORNER_R - 0.8:
        return False
    if px > BOARD_W - CORNER_R and py > BOARD_H - CORNER_R and math.hypot(px - (BOARD_W - CORNER_R), py - (BOARD_H - CORNER_R)) > CORNER_R - 0.8:
        return False
    if in_keepout(px, py, margin=my_half_w + 0.3):
        return False

    for pidx in pad_near_grid.get((gx, gy), ()):
        p = all_pads[pidx]
        if p["net"] != net:
            if pt_to_pad_edge_dist(px, py, p) - my_half_w < MIN_CLEARANCE:
                return False

    v_search = 5
    for dx in range(-v_search, v_search + 1):
        for dy in range(-v_search, v_search + 1):
            vn = via_occ.get((gx + dx, gy + dy))
            if vn is not None and vn != net:
                if math.hypot(dx * GRID, dy * GRID) - VIA_R - my_half_w < MIN_CLEARANCE:
                    return False

    layers_to_check = ("F.Cu", "B.Cu") if is_via else (layer,)
    t_search = 4
    for chk_layer in layers_to_check:
        layer_occ = occ[chk_layer]
        for dx in range(-t_search, t_search + 1):
            for dy in range(-t_search, t_search + 1):
                item = layer_occ.get((gx + dx, gy + dy))
                if item is not None and item[0] != net:
                    if math.hypot(dx * GRID, dy * GRID) - item[1] - my_half_w < MIN_CLEARANCE:
                        return False
    return True

def route_astar(start_xy, goal_xy, net, w):
    my_hw = w / 2.0
    sg = to_grid(*start_xy)
    gg = to_grid(*goal_xy)
    if sg == gg:
        return []

    pq = []
    best = {}
    parent = {}
    for layer in ("F.Cu", "B.Cu"):
        if is_free(layer, sg[0], sg[1], net, my_hw):
            s = (sg[0], sg[1], layer)
            best[s] = 0.0
            heapq.heappush(pq, (abs(sg[0] - gg[0]) + abs(sg[1] - gg[1]), 0.0, sg[0], sg[1], layer))

    found = None
    while pq:
        _, gcost, x, y, layer = heapq.heappop(pq)
        if (x, y) == gg:
            found = (x, y, layer)
            break
        if gcost > best.get((x, y, layer), 1e18):
            continue

        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not is_free(layer, nx, ny, net, my_hw):
                continue
            step_cost = 1.0
            if layer == "F.Cu" and dy != 0:
                step_cost = 1.3
            if layer == "B.Cu" and dx != 0:
                step_cost = 1.3
            if occ[layer].get((nx, ny), (None, 0))[0] == net:
                step_cost = 0.2
            ncost = gcost + step_cost
            ns = (nx, ny, layer)
            if ncost < best.get(ns, 1e18):
                best[ns] = ncost
                parent[ns] = (x, y, layer)
                h = abs(nx - gg[0]) + abs(ny - gg[1])
                heapq.heappush(pq, (ncost + h, ncost, nx, ny, layer))

        other = "B.Cu" if layer == "F.Cu" else "F.Cu"
        if (x, y) != sg and (x, y) != gg:
            if is_free(layer, x, y, net, VIA_R, is_via=True):
                ncost = gcost + 8.0
                ns = (x, y, other)
                if ncost < best.get(ns, 1e18):
                    best[ns] = ncost
                    parent[ns] = (x, y, layer)
                    h = abs(x - gg[0]) + abs(y - gg[1])
                    heapq.heappush(pq, (ncost + h, ncost, x, y, other))

    if found is None:
        return None
    path = []
    cur = found
    while cur in parent:
        prev = parent[cur]
        path.append((prev, cur))
        cur = prev
    path.reverse()
    return path

pads_by_net = collections.defaultdict(list)
for p in all_pads:
    if p["net"] != "NC":
        pads_by_net[p["net"]].append(p)

net_order = sorted(
    [n for n, ps in pads_by_net.items() if len(ps) >= 2],
    key=lambda n: (1 if n in ("+3V3", "+5V") else (2 if n == "GND" else 0), len(pads_by_net[n]))
)

tracks = []
vias = []
failed_links = []

for net in net_order:
    pts = [(p["x"], p["y"]) for p in pads_by_net[net]]
    connected = [pts[0]]
    remaining = pts[1:]
    w = 0.45 if net in ("+5V", "+3V3", "GND") else 0.30
    hw = w / 2.0

    while remaining:
        best_pair = None
        best_d = 1e18
        for c_pt in connected:
            for r_pt in remaining:
                d = abs(c_pt[0] - r_pt[0]) + abs(c_pt[1] - r_pt[1])
                if d < best_d:
                    best_d = d
                    best_pair = (c_pt, r_pt)
        c_pt, r_pt = best_pair
        path = route_astar(c_pt, r_pt, net, w)
        if path is None:
            failed_links.append((net, c_pt, r_pt))
            remaining.remove(r_pt)
            connected.append(r_pt)
            continue

        first_node = path[0][0]
        fx, fy = to_mm(first_node[0], first_node[1])
        if math.hypot(fx - c_pt[0], fy - c_pt[1]) > 1e-4:
            tracks.append({"layer": first_node[2], "x1": c_pt[0], "y1": c_pt[1], "x2": fx, "y2": fy, "w": w, "net": net})
            occ[first_node[2]][(first_node[0], first_node[1])] = (net, hw)

        for (x1, y1, l1), (x2, y2, l2) in path:
            if l1 != l2:
                vx, vy = to_mm(x1, y1)
                vias.append({"x": vx, "y": vy, "net": net})
                via_occ[(x1, y1)] = net
                occ["F.Cu"][(x1, y1)] = (net, VIA_R)
                occ["B.Cu"][(x1, y1)] = (net, VIA_R)
            else:
                mx1, my1 = to_mm(x1, y1)
                mx2, my2 = to_mm(x2, y2)
                tracks.append({"layer": l1, "x1": mx1, "y1": my1, "x2": mx2, "y2": my2, "w": w, "net": net})
                occ[l1][(x1, y1)] = (net, hw)
                occ[l1][(x2, y2)] = (net, hw)

        last_node = path[-1][1]
        lx, ly = to_mm(last_node[0], last_node[1])
        if math.hypot(lx - r_pt[0], ly - r_pt[1]) > 1e-4:
            tracks.append({"layer": last_node[2], "x1": lx, "y1": ly, "x2": r_pt[0], "y2": r_pt[1], "w": w, "net": net})
            occ[last_node[2]][(last_node[0], last_node[1])] = (net, hw)

        remaining.remove(r_pt)
        connected.append(r_pt)

# 合并共线线段
merged = []
for t in tracks:
    if (t["x1"], t["y1"]) == (t["x2"], t["y2"]):
        continue
    if merged:
        prev = merged[-1]
        if prev["layer"] == t["layer"] and prev["net"] == t["net"] and prev["w"] == t["w"] and (prev["x2"], prev["y2"]) == (t["x1"], t["y1"]):
            dx1, dy1 = prev["x2"] - prev["x1"], prev["y2"] - prev["y1"]
            dx2, dy2 = t["x2"] - t["x1"], t["y2"] - t["y1"]
            if abs(dx1 * dy2 - dy1 * dx2) < 1e-6 and (dx1 * dx2 + dy1 * dy2) > 0:
                prev["x2"], prev["y2"] = t["x2"], t["y2"]
                continue
    merged.append(dict(t))
tracks = merged

unique_vias = {}
for v in vias:
    key = (round(v["x"], 4), round(v["y"], 4))
    unique_vias[key] = v
vias = list(unique_vias.values())

# ---------------------------------------------------------------------------
# 3. 简易矢量丝印 + 外框标注
# ---------------------------------------------------------------------------
FONT_3X5 = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"],
    "C": ["111", "100", "100", "100", "111"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["111", "100", "101", "101", "111"], "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"], "J": ["001", "001", "001", "101", "111"],
    "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"], "N": ["101", "111", "111", "111", "101"],
    "O": ["111", "101", "101", "101", "111"], "P": ["111", "101", "111", "100", "100"],
    "Q": ["111", "101", "101", "111", "001"], "R": ["111", "101", "110", "101", "101"],
    "S": ["111", "100", "111", "001", "111"], "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"], "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"], "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"], "Z": ["111", "001", "010", "100", "111"],
    "+": ["000", "010", "111", "010", "000"], "-": ["000", "000", "111", "000", "000"],
    "_": ["000", "000", "000", "000", "111"], ".": ["000", "000", "000", "000", "010"],
    " ": ["000", "000", "000", "000", "000"],
}

silk_strokes = []

def draw_text(x, y, text, scale=0.35):
    cx = x
    for ch in text.upper():
        g = FONT_3X5.get(ch, FONT_3X5[" "])
        for r in range(5):
            for c in range(3):
                if g[r][c] == "1":
                    px1 = cx + c * scale
                    py1 = y + r * scale
                    silk_strokes.append((px1, py1, px1 + scale * 0.7, py1))
        cx += 4 * scale

for comp in COMPONENTS:
    if comp["bbox"]:
        x1, y1, x2, y2, lbl = comp["bbox"]
        silk_strokes.extend([(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)])
        draw_text(x1 + 1.0, y2 - 2.3, lbl, 0.28)
    for i, lbl in enumerate(comp["pin_labels"]):
        if i < len(comp["pads"]):
            _, dx, dy, *_ = comp["pads"][i]
            px, py = comp["x"] + dx, comp["y"] + dy
            draw_text(px + 1.4, py - 0.7, lbl, 0.25)

draw_text(4.5, 24.4, "C1 100uF+", 0.25)
draw_text(18.5, 24.4, "C3", 0.25)
draw_text(44.2, 10.2, "C2", 0.25)
draw_text(44.2, 5.2, "5V_IN", 0.25)

# ---------------------------------------------------------------------------
# 4. 导出 Gerber ZIP & 1:1 SVG 预览
# ---------------------------------------------------------------------------
def fmt(val_mm):
    return int(round(val_mm * 100000))

def write_gerber_cu(layer_name):
    out = [f"G04 KitchenSensor {layer_name}*", "%FSLAX45Y45*%", "%MOMM*%", "%LPD*%"]
    apertures = {}
    ap_id = 10
    def get_ap(kind, *args):
        nonlocal ap_id
        key = (kind, args)
        if key not in apertures:
            apertures[key] = ap_id
            if kind == "C":
                out.append(f"%ADD{ap_id}C,{args[0]:.4f}*%")
            elif kind == "R":
                out.append(f"%ADD{ap_id}R,{args[0]:.4f}X{args[1]:.4f}*%")
            elif kind == "O":
                out.append(f"%ADD{ap_id}O,{args[0]:.4f}X{args[1]:.4f}*%")
            ap_id += 1
        return apertures[key]

    pad_aps = [(p, get_ap("R" if p["shape"] == "rect" else ("O" if p["shape"] == "oval" else "C"),
                          *((p["sx"],) if p["shape"] == "circle" else (p["sx"], p["sy"])))) for p in all_pads]
    via_ap = get_ap("C", 0.8) if vias else None
    trk_aps = [(t, get_ap("C", t["w"])) for t in tracks if t["layer"] == layer_name]

    for p, aid in pad_aps:
        out.append(f"D{aid}*")
        out.append(f"X{fmt(p['x'])}Y{fmt(-p['y'])}D03*")
    if vias:
        out.append(f"D{via_ap}*")
        for v in vias:
            out.append(f"X{fmt(v['x'])}Y{fmt(-v['y'])}D03*")
    for t, aid in trk_aps:
        out.append(f"D{aid}*")
        out.append(f"X{fmt(t['x1'])}Y{fmt(-t['y1'])}D02*")
        out.append(f"X{fmt(t['x2'])}Y{fmt(-t['y2'])}D01*")
    out.append("M02*")
    return "\n".join(out) + "\n"

def write_gerber_mask():
    out = ["G04 KitchenSensor SolderMask*", "%FSLAX45Y45*%", "%MOMM*%", "%LPD*%"]
    apertures = {}
    ap_id = 10
    def get_ap(kind, *args):
        nonlocal ap_id
        key = (kind, args)
        if key not in apertures:
            apertures[key] = ap_id
            if kind == "C":
                out.append(f"%ADD{ap_id}C,{args[0]:.4f}*%")
            elif kind == "R":
                out.append(f"%ADD{ap_id}R,{args[0]:.4f}X{args[1]:.4f}*%")
            elif kind == "O":
                out.append(f"%ADD{ap_id}O,{args[0]:.4f}X{args[1]:.4f}*%")
            ap_id += 1
        return apertures[key]

    for p in all_pads:
        k = "R" if p["shape"] == "rect" else ("O" if p["shape"] == "oval" else "C")
        args = (p["sx"] + 0.1,) if k == "C" else (p["sx"] + 0.1, p["sy"] + 0.1)
        aid = get_ap(k, *args)
        out.append(f"D{aid}*")
        out.append(f"X{fmt(p['x'])}Y{fmt(-p['y'])}D03*")
    out.append("M02*")
    return "\n".join(out) + "\n"

def write_gerber_silk(strokes):
    out = ["G04 KitchenSensor Silkscreen*", "%FSLAX45Y45*%", "%MOMM*%", "%LPD*%", "%ADD10C,0.1200*%", "D10*"]
    for x1, y1, x2, y2 in strokes:
        out.append(f"X{fmt(x1)}Y{fmt(-y1)}D02*")
        out.append(f"X{fmt(x2)}Y{fmt(-y2)}D01*")
    out.append("M02*")
    return "\n".join(out) + "\n"

def write_gerber_outline():
    pts = []
    n_arc = 16
    corners = [
        (BOARD_W - CORNER_R, CORNER_R, math.pi / 2, 0.0),
        (BOARD_W - CORNER_R, BOARD_H - CORNER_R, 0.0, -math.pi / 2),
        (CORNER_R, BOARD_H - CORNER_R, -math.pi / 2, -math.pi),
        (CORNER_R, CORNER_R, math.pi, math.pi / 2),
    ]
    for cx, cy_pcb, a0, a1 in corners:
        cy = -cy_pcb
        for i in range(n_arc + 1):
            ang = a0 + (a1 - a0) * (i / n_arc)
            pts.append((cx + CORNER_R * math.cos(ang), cy + CORNER_R * math.sin(ang)))
    pts.append(pts[0])
    out = ["G04 KitchenSensor R3 Outline*", "%FSLAX45Y45*%", "%MOMM*%", "%LPD*%", "%ADD10C,0.1500*%", "D10*",
           f"X{fmt(pts[0][0])}Y{fmt(pts[0][1])}D02*"]
    for px, py in pts[1:]:
        out.append(f"X{fmt(px)}Y{fmt(py)}D01*")
    out.append("M02*")
    return "\n".join(out) + "\n"

def write_drill():
    holes = collections.defaultdict(list)
    for p in all_pads:
        holes[round(p["drill"], 3)].append((p["x"], -p["y"]))
    for v in vias:
        holes[0.4].append((v["x"], -v["y"]))
    out = ["M48", "METRIC,TZ"]
    tool_map = {}
    for idx, dia in enumerate(sorted(holes.keys()), 1):
        t = f"T{idx:02d}"
        tool_map[dia] = t
        out.append(f"{t}C{dia:.3f}")
    out.append("%")
    for dia in sorted(holes.keys()):
        out.append(tool_map[dia])
        for x, y in holes[dia]:
            out.append(f"X{x:.4f}Y{y:.4f}")
    out.append("M30")
    return "\n".join(out) + "\n"

zip_path = OUT_DIR / "KitchenSensor_52x52_Gerber_JLCPCB.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("Gerber_TopLayer.GTL", write_gerber_cu("F.Cu"))
    zf.writestr("Gerber_BottomLayer.GBL", write_gerber_cu("B.Cu"))
    zf.writestr("Gerber_TopSilkscreenLayer.GTO", write_gerber_silk(silk_strokes))
    zf.writestr("Gerber_BottomSilkscreenLayer.GBO", write_gerber_silk([]))
    zf.writestr("Gerber_TopSolderMaskLayer.GTS", write_gerber_mask())
    zf.writestr("Gerber_BottomSolderMaskLayer.GBS", write_gerber_mask())
    zf.writestr("Gerber_BoardOutlineLayer.GKO", write_gerber_outline())
    zf.writestr("Drill_PTH_Through.DRL", write_drill())

# 生成直观的 1:1 渲染预览 SVG（带真实模块外框、天线禁布区、红蓝双面走线）
S = 14.0  # 14 px/mm for crisp preview
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(BOARD_W*S+100)}" height="{int(BOARD_H*S+120)}" style="background:#0f172a;font-family:-apple-system,sans-serif;">',
    f'<text x="{(BOARD_W*S+100)/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold" fill="#f8fafc">Kitchen Sensor PCB ({BOARD_W}×{BOARD_H} mm · 全直插 · 0飞线)</text>',
    f'<g transform="translate(50,55)">',
    f'<rect x="0" y="0" width="{BOARD_W*S}" height="{BOARD_H*S}" rx="{CORNER_R*S}" fill="#14532d" stroke="#22c55e" stroke-width="2"/>',
]
# Keepout
kx1, ky1, kx2, ky2 = KEEPOUT_RECT
svg.append(f'<rect x="{kx1*S}" y="{ky1*S}" width="{(kx2-kx1)*S}" height="{(ky2-ky1)*S}" fill="#7f1d1d" fill-opacity="0.35" stroke="#ef4444" stroke-dasharray="4,4"/>')
svg.append(f'<text x="{(kx1+kx2)/2*S}" y="{(ky1+ky2)/2*S}" text-anchor="middle" font-size="10" fill="#fca5a5">天线禁布铜区</text>')

# Tracks
for t in tracks:
    col = "#38bdf8" if t["layer"] == "B.Cu" else "#f87171"
    svg.append(f'<line x1="{t["x1"]*S}" y1="{t["y1"]*S}" x2="{t["x2"]*S}" y2="{t["y2"]*S}" stroke="{col}" stroke-width="{t["w"]*S}" stroke-linecap="round" opacity="0.85"/>')

# Vias
for v in vias:
    svg.append(f'<circle cx="{v["x"]*S}" cy="{v["y"]*S}" r="{0.4*S}" fill="#fbbf24"/>')
    svg.append(f'<circle cx="{v["x"]*S}" cy="{v["y"]*S}" r="{0.2*S}" fill="#0f172a"/>')

# Module outlines
for comp in COMPONENTS:
    if comp["bbox"]:
        x1, y1, x2, y2, lbl = comp["bbox"]
        svg.append(f'<rect x="{x1*S}" y="{y1*S}" width="{(x2-x1)*S}" height="{(y2-y1)*S}" rx="4" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-dasharray="5,3" opacity="0.8"/>')
        svg.append(f'<text x="{(x1+x2)/2*S}" y="{(y2-1.2)*S}" text-anchor="middle" font-size="11" font-weight="bold" fill="#ffffff">{lbl}</text>')

# Pads & labels
for p in all_pads:
    px, py = p["x"] * S, p["y"] * S
    if p["shape"] == "rect":
        svg.append(f'<rect x="{px-p["sx"]/2*S}" y="{py-p["sy"]/2*S}" width="{p["sx"]*S}" height="{p["sy"]*S}" fill="#f59e0b"/>')
    else:
        svg.append(f'<circle cx="{px}" cy="{py}" r="{p["sx"]/2*S}" fill="#f59e0b"/>')
    svg.append(f'<circle cx="{px}" cy="{py}" r="{p["drill"]/2*S}" fill="#0f172a"/>')

for comp in COMPONENTS:
    for i, lbl in enumerate(comp["pin_labels"]):
        if i < len(comp["pads"]):
            _, dx, dy, *_ = comp["pads"][i]
            svg.append(f'<text x="{(comp["x"]+dx+1.2)*S}" y="{(comp["y"]+dy+0.4)*S}" font-size="9" fill="#fef08a">{lbl}</text>')

svg.append(f'<text x="{6.5*S}" y="{25.0*S}" font-size="10" fill="#fde047">C1 100uF卧放</text>')
svg.append(f'<text x="{20.0*S}" y="{25.0*S}" font-size="10" fill="#fde047">C3</text>')
svg.append(f'<text x="{44.2*S}" y="{11.0*S}" font-size="10" fill="#fde047">C2</text>')
svg.append(f'<text x="{44.2*S}" y="{5.8*S}" font-size="10" fill="#fde047">5V_IN</text>')
svg.append(f'<text x="{44.5*S}" y="{17.0*S}" font-size="9" fill="#94a3b8">R1 R2</text>')
svg.append('</g>')
svg.append(f'<text x="{(BOARD_W*S+100)/2}" y="{BOARD_H*S+95}" text-anchor="middle" font-size="12" fill="#cbd5e1">红线=顶层(F.Cu) · 蓝线=底层(B.Cu) · 黄色方盘=Pin1 · 白框=模块实占轮廓</text>')
svg.append('</svg>')

svg_path = OUT_DIR / "kitchen_sensor_pcb_preview.svg"
svg_path.write_text("\n".join(svg), encoding="utf-8")

report = {
    "board_size_mm": f"{BOARD_W} x {BOARD_H}",
    "smd_components": 0,
    "tht_components": len(COMPONENTS),
    "total_pads": len(all_pads),
    "routed_segments": len(tracks),
    "vias": len(vias),
    "unrouted_links": len(failed_links),
    "failed_link_details": failed_links,
}
(OUT_DIR / "routing_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
