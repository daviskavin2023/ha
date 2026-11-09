from pathlib import Path
import math, json, hashlib, shutil, re, contextlib, io

ROOT = Path('/Users/kavin/.codex/visualizations/2026/11/08/xiaozhi-hardware-review')
DESK = Path('/Users/kavin/Desktop')
OUT = DESK / '小智小方盒_修复交付_20261109'
OUT.mkdir(exist_ok=True)
BACK = OUT / '修改前备份'
BACK.mkdir(exist_ok=True)
PRD = DESK / '小智AI小方盒_PRD与硬件规格说明书_v3.1_20261109.md'
LEDGER = DESK / '小智小方盒_接线总清单与销项台账_v3.1_20261109.md'
ZIP = DESK / '小智小方盒_JLC单一钻孔生产包_v3.1_20261109.zip'
SOURCE = DESK / '小智小方盒_过程历史与审核归档_20261108/小智小方盒_v3.1修订_20261109/小智小方盒_v3.1_待原生DRC.kicad_pcb'
for p in [PRD, LEDGER]:
    if not (BACK / p.name).exists(): shutil.copy2(p, BACK / p.name)
sha = hashlib.sha256(ZIP.read_bytes()).hexdigest()

# Reuse the geometry primitives, not the old audit's output generation.
code = (ROOT / 'audit_v25.py').read_text().split('items=tracks+pads')[0]
code = code.replace("P=ROOT/'frozen-v25/board.kicad_pcb'", f'P=Path({str(SOURCE)!r})')
ns = {}
exec(code, ns)
padlist = ns['pads']
functional = [p for p in padlist if not p['ref'].startswith('VIA')]

# PATCH-A01 is an independently wired passive attenuator. No main-board copper
# or unknown vendor module footprint is silently changed.
nets = {1:'GND', 2:'MIX_IN', 3:'ATTENUATED', 4:'AMP_IN_P_AC', 5:'AMP_IN_N_AC'}
parts = [
 ('J1','WIRE_IN',[(1,2,3,2),(2,2,8,1)],'wire'),
 ('J2','WIRE_OUT',[(1,16,3,4),(2,16,8,5)],'wire'),
 ('RA','15k_1pct',[(1,5.05,3,2),(2,6.95,3,3)],'smd'),
 ('RB','1k_1pct',[(1,8.5,4.05,3),(2,8.5,5.95,1)],'smdv'),
 ('CP','1uF_X7R_25V',[(1,11.05,3,3),(2,12.95,3,4)],'smd'),
 ('CN','1uF_X7R_25V',[(1,11.05,8,1),(2,12.95,8,5)],'smd'),
]
segments = [
 (2,3,5.05,3,2),(6.95,3,8.5,3,3),(8.5,3,11.05,3,3),
 (8.5,3,8.5,4.05,3),(8.5,5.95,8.5,8,1),
 (2,8,8.5,8,1),(8.5,8,11.05,8,1),
 (12.95,3,16,3,4),(12.95,8,16,8,5),
]
board = ['(kicad_pcb (version 20211014) (generator pcbnew)',
 ' (general (thickness 1.0)) (paper "A4")',
 ' (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "b.silkscreen") (37 "F.SilkS" user "f.silkscreen") (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user))',
 ' (setup (pad_to_mask_clearance 0.05))', ' (net 0 "")']
board += [f' (net {n} "{name}")' for n,name in nets.items()]
items=[]
for ref,value,pp,kind in parts:
    board.append(f' (footprint "XiaozhiRepair:{kind}" (layer "F.Cu") (at 0 0)')
    tx = sum(p[1] for p in pp)/2; ty = sum(p[2] for p in pp)/2
    # Labels never pass across solder-mask openings. Value remains machine readable.
    lx,ly = {'J1':(2,5.5),'J2':(16,5.5),'RA':(6,1.5),'RB':(10,5), 'CP':(12,1.5),'CN':(12,10)}[ref]
    board += [f'  (fp_text reference "{ref}" (at {lx} {ly}) (layer "F.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1))))',
              f'  (fp_text value "{value}" (at {tx} {ty}) (layer "F.SilkS") hide (effects (font (size 0.6 0.6) (thickness 0.1))))']
    for pin,x,y,n in pp:
        if kind=='wire':
            board.append(f'  (pad "{pin}" thru_hole circle (at {x} {y}) (size 1.8 1.8) (drill 0.9) (layers *.Cu *.Mask) (net {n} "{nets[n]}"))')
            shape,sx,sy,drill='circle',1.8,1.8,.9
        else:
            sx,sy=(1.4,1.2) if kind=='smdv' else (1.2,1.4)
            board.append(f'  (pad "{pin}" smd rect (at {x} {y}) (size {sx} {sy}) (layers "F.Cu" "F.Paste" "F.Mask") (net {n} "{nets[n]}"))')
            shape,drill='rect',0
        items.append(dict(kind='pad',ref=ref,pin=str(pin),x=x,y=y,sx=sx,sy=sy,shape=shape,drill=drill,net=n,name=nets[n],layer='F.Cu'))
    board.append(' )')
for x,y,u,v,n in segments:
    board.append(f' (segment (start {x} {y}) (end {u} {v}) (width 0.3) (layer "F.Cu") (net {n}))')
    items.append(dict(kind='track',x=x,y=y,u=u,v=v,w=.3,net=n,layer='F.Cu'))
for a,b in [((0,0),(18,0)),((18,0),(18,12)),((18,12),(0,12)),((0,12),(0,0))]:
    board.append(f' (gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (layer "Edge.Cuts") (width 0.05))')
board.append(')')
(OUT/'PATCH-A01_音频衰减转接板_18x12mm.kicad_pcb').write_text('\n'.join(board)+'\n')

# Validate every copper pair and intended connected component on the patch.
parent=list(range(len(items)))
def find(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
shorts=[];clearances=[];min_gap=999
for i,a in enumerate(items):
    for j in range(i+1,len(items)):
        b=items[j];g=ns['gap'](a,b)
        if g is None:continue
        d,_=g
        if a['net']==b['net']:
            if d<=1e-7: parent[find(i)]=find(j)
        else:
            min_gap=min(min_gap,d)
            if d<=1e-7:shorts.append((i,j,d))
            elif d<.2-1e-7:clearances.append((i,j,d))
groups={n:len({find(i) for i,a in enumerate(items) if a['net']==n}) for n in nets}
assert not shorts and not clearances and all(x==1 for x in groups.values()), (shorts,clearances,groups)
edge_min=min(min(a['x']-a['sx']/2,18-a['x']-a['sx']/2,a['y']-a['sy']/2,12-a['y']-a['sy']/2) for a in items if a['kind']=='pad')
assert edge_min>=.3

ratio_nom=1000/(15000+1000)
ratio_worst=1010/(14850+1010)
gain=10**(23.5/20)
calc = dict(design='PATCH-A01',main_zip_sha256=sha,main_zip_changed=False,
 patch_copper_short_pairs=shorts,patch_clearance_below_020=clearances,
 patch_min_foreign_copper_gap_mm=min_gap,patch_min_pad_edge_mm=edge_min,
 patch_network_connected_components=groups,
 attenuation_no_load_db=20*math.log10(ratio_nom),
 attenuation_ratio_max_1pct_resistors=ratio_worst,
 amp_input_vrms_nominal_2p1V_no_load=2.1*ratio_nom,
 amp_input_vrms_2p2V_budget_1pct_no_load=2.2*ratio_worst,
 amp_output_w_into_8ohm_2p1V_typical_gain=(2.1*ratio_nom*gain)**2/8,
 gain_db_is_typical_not_guaranteed_max=23.5,
 physical_tests_performed=False,native_eda_drc_performed_on_patch=False)
(OUT/'修复计算与几何验证.json').write_text(json.dumps(calc,ensure_ascii=False,indent=2)+'\n')

# Top-view copper layout, physical mm scaling. Circuit SVG is a review artifact,
# not an untraceable replacement Gerber.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620">',
 '<rect width="900" height="620" fill="#fff"/><g font-family="Arial, sans-serif" fill="#172033">',
 '<text x="32" y="36" font-size="23">PATCH-A01 — 15k / 1k audio attenuator</text>',
 '<text x="32" y="63" font-size="16">18 × 12 mm, top view; 1 µF non-polar input coupling on both legs</text>',
 '<rect x="70" y="105" width="720" height="480" rx="3" fill="#e9f4ed" stroke="#375b45" stroke-width="2"/>']
def xy(x,y): return 70+x*40,105+y*40
for x,y,u,v,n in segments:
    x,y=xy(x,y);u,v=xy(u,v)
    svg.append(f'<path d="M{x},{y} L{u},{v}" stroke="#b11f31" stroke-width="12" fill="none"/>')
for ref,value,pp,kind in parts:
    for pin,x,y,n in pp:
        x,y=xy(x,y)
        if kind=='wire':svg.append(f'<circle cx="{x}" cy="{y}" r="36" fill="#caa742"/><circle cx="{x}" cy="{y}" r="18" fill="white"/>')
        else:svg.append(f'<rect x="{x-24}" y="{y-24}" width="48" height="48" fill="#caa742" stroke="#374151"/>')
    x,y=xy(sum(p[1] for p in pp)/2,sum(p[2] for p in pp)/2)
    label={'J1':'J1: MIX / GND','J2':'J2: IN+ / IN−','RA':'RA 15k','RB':'RB 1k','CP':'CP 1µF','CN':'CN 1µF'}[ref]
    svg.append(f'<text x="{x}" y="{y-42}" font-size="17" text-anchor="middle">{label}</text>')
svg.append('</g></svg>')
(OUT/'PATCH-A01_布线实图.svg').write_text('\n'.join(svg))

conn=['# 底板全部物理引脚表（自动从参考PCB提取）','',
 '观察方向：从元件/顶层面看；坐标mm，原点为板框左上，x向右、y向下。按下列坐标定位，不能按图片左右推断模块端子方向。',
 '这是底板定义，不是商家模块的实物脚序。所有外购模块按丝印功能线束对接；PJ座采用面板安装、绝缘导线连接，取消对未核实7×3mm孔位直插适配的要求。',
 '', '| 接口 | Pin | x | y | 网络 |','|---|---|---:|---:|---|']
for p in functional:
    conn.append(f"| {p['ref']} | {p['pin']} | {p['x']:.2f} | {p['y']:.2f} | {p['name']} |")
(OUT/'底板全部120焊盘逐脚表.md').write_text('\n'.join(conn)+'\n')
(OUT/'底板引脚数据.json').write_text(json.dumps(functional,ensure_ascii=False,indent=2)+'\n')

audio='''# PATCH-A01：实际音频修复接线

本补丁保留底板原有R1/R2=1k混音电阻和全部铜线，新增独立18×12mm无源衰减板。现有v3.1主板ZIP不需要因为本补丁重新手改Gerber。小板也可以按以下同一电路焊成绝缘线束；未生成小板生产Gerber，需在嘉立创EDA导入源板、复核原生DRC后导出。

## 电路及BOM

```
底板 J_AMP_IN.1 (MIX) ─ RA 15kΩ ──●── CP 1µF ─ 功放 IN+
                                │
                               RB 1kΩ
                                │
底板 J_AMP_IN.2 (GND) ────────────●── CN 1µF ─ 功放 IN−
```

RA、RB：0805、1%、≥0.1W；CP、CN：0805、1µF、X7R、25V、无极性。不要把功放IN−直接短接电源地来旁路CN。若模块内部已有输入耦合电容，新增电容与其串联，有效电容变小；实际低频截止需结合模块原电容复核，不能把1µF标作已经测得的系统截止频率。

| 补丁焊盘 | 连接对象 |
|---|---|
| J1.1 MIX_IN | 底板 J_AMP_IN.1 |
| J1.2 GND | 底板 J_AMP_IN.2 |
| J2.1 AMP_IN_P_AC | 功放模块按丝印识别的 IN+ |
| J2.2 AMP_IN_N_AC | 功放模块按丝印识别的 IN− |

**必须取消原来底板J_AMP_IN.1/.2直接到模块IN+/IN−的两根线，以本补丁替换；不能旁路或并接原信号线。** 功放VIN、GND、SD、BTL输出仍按主板功能表连接。外部AUX在PJ插座前取DAC原始左右声道，不经过本衰减器；只适配有源音箱线路输入，不直接驱动低阻耳机，也不接市电端子。

## 计算与适用范围

忽略原混音电阻和负载影响时，分压为1/(15+1)=0.0625，约−24.08dB。原两颗1k混音电阻的源阻抗以及功放输入负载会进一步减小中频幅度。PCM5102A 2.1Vrms满幅时，功放输入约0.131Vrms；按23.5dB典型增益，8Ω输出约0.48W。这里选择语音余量，不再把1.5W/10%失真当额定清晰输出。

1%电阻极限组合、高阻负载及2.2Vrms工程预算时输入约0.140Vrms；2.2V是额外预算假设，不是TI保证的输出上限。PAM资料只给23.5dB典型增益，没有保证的最大偏差，因此不能据此承诺所有成品绝不削顶。需结合实际模块验证增益和满幅波形。数字音量从低开始；不再使用“−12到−6dB保证不削顶”的规定。

几何检查见JSON：全部5个网络各自连通，异网短路0、低于0.20mm间距0。此结果是静态设计筛查，未运行本小板原生EDA DRC，未焊接/通电。

## 关断控制

原板GPIO9→SD保持。先确认模块SD上拉电路，再决定下拉阻值，不能直接添加与未知板载上拉分压后仍达不到低电平的弱下拉。默认关断、I2S稳定后延时≥10ms再使能的固件动作还未集成到可编译固件；插座无独立检测脚，也未实现插线即SD静音。机械常闭触点切断声音不等于功放已关断，不承诺零底噪。

## 官方依据

- https://www.diodes.com/datasheet/download/PAM8302A.pdf ：增益、输入耦合、SD时序。
- https://www.ti.com/lit/ds/symlink/pcm5102a.pdf ：2.1Vrms满幅线路输出。
'''
(OUT/'音频硬件修复与BOM.md').write_text(audio)

screen='''# 屏幕接口补全方案（线束，不擅改采购转接板）

原板SPI：MOSI=IO12、DC=IO10、SCK=IO11、CS=IO13；触控SCL=IO1、SDA=IO2。保持已有有效接线。

| 新增信号 | 已有底板可取线点 | 实施条件/状态 |
|---|---|---|
| LCD_RST | J_ESP_L.20，IO14 | GPIO未与现有功能网冲突。转接板确有3.3V逻辑RST端子时可接；该端子定义待采购板资料。 |
| TP_RST | J_ESP_R1.18 或R2.18，IO21 | 二选一取线，禁止误接主控EN；待确认触控复位脚与有效电平。 |
| TP_INT | J_ESP_R1.9 或R2.9，IO39 | 预留独立输入；待确认INT端子、触发方式和驱动。不能写成已验证轮询免INT。 |
| BL逻辑 | J_ESP_R1.10 或R2.10，IO38 | 仅限转接板明示为3.3V逻辑输入的BL/PWM，不连接LED_A/K。若仅有LED裸背光，需另设计恒流/限流及MOS驱动。 |
| I2C上拉 | SCL、SDA各经4.7k至3.3V | BOM标DNP（暂不装）。确认模块已有上拉值再决定安装；并联后上拉过强需复核灌电流/上升时间。 |

这些IO在参考底板是独立SPARE网，不占用MIC/DAC/雷达现有信号；不得改用N16R8占用的IO35/36/37或启动配置脚0/3/45/46。

GPIO预留不等于已完成屏幕适配。ST7789和CST816D芯片名不能确定Tiky转接板的端子、背光供电、分辨率/偏移、上拉和复位电路。当前资料有240×296和240×300差异，不能任取一个写死为验收值。等待具体商品/厂商转接板图后才能完成驱动与复位时序，不提供伪装成已验证固件的配置。
'''
(OUT/'屏幕接口补全.md').write_text(screen)

power='''# 电源与结构验收约束

## 电源

保留底板5V和3.3V网络，不把“拔掉电源后烧录”称为电路互锁。主控开发板具体USB/稳压器电路未提供，不能凭ESP32-S3芯片型号猜测USB隔离。硬件防倒灌未销项；不得在未核实前并接PC USB VBUS与外部5V。

LDO输入电流约等于3.3V输出电流加静态电流，不能用功率守恒折算为5V侧较小电流。例如3.3V/0.5A、输入5V：LDO耗散约(5−3.3)×0.5=0.85W，尚未含其他支路。实际负载须分别计入ESP32峰值、屏幕与触控、INMP441；5V支路另算雷达、DAC、功放。2A是供电容量建议，不是已测峰值。

热验收记录输入/各支路电流、USB/模块端电压、环境温度、稳压器确切型号及封装、持续Wi-Fi发送+录放音+最高背光负载。闭壳运行至热平衡，记录温度随时间。依据器件结温/热阻和实际板散热条件判定，不再使用“15分钟表面65°C就是通过”的通用阈值。

## 结构

冻结尺寸暂为外壳54×76×48、内腔50×72×44、主板48×68×1.6mm。左右各1mm、上下各2mm仅是名义间隙。

按现有声明，后层15.1mm+喇叭深28mm，占43.1mm，44mm内深仅剩0.9mm名义间隙。该数未计入焊锡、翘曲、壳体/模块公差和线束，不能叫“绝对零干涉”。新增18×12×1.0mm音频小板需绝缘固定；本体、元件、焊脚与线束均需纳入最终包络。

PJ-324M改为面板安装、柔性五线连接到底板焊盘，不依赖未确认的主板7×3mm五孔直插。面板开孔/螺母空间仍须依据采购件机械图，不猜孔径。

旧截面图和效果图只标记为概念参考；没有完整模块尺寸就不绘制一张自称验收通过的新示意图。完整装配CAD、Wi-Fi天线区域与雷达正前方净空仍未验收。不要为制造“已修复”而任意加深外壳或伪造模块外形。
'''
(OUT/'电源与装配约束.md').write_text(power)

new_prd=f'''# 小智小方盒 PRD v3.1 修订1（2026-11-09）

## 当前交付状态

现有主板加工包：`{ZIP.name}`；SHA-256：`{sha}`。**本次未修改主板ZIP，不宣称整机通过、工业生产100%放行或新增硬件已实测。** 已有裸板文件的几何复核结论保留；当前整机仍需下列设计/实物事项闭环。

主板2层、48×68mm、R3、板厚1.6mm、1oz；实际工艺需与板厂确认。加工包8文件、184个唯一钻孔。按已执行的Gerber复核：底层填充名义板边距约0.360mm、顶层丝印与阻焊开窗最小间距约0.325mm，撤回1.257mm全板最小值。先前原生DRC与当前ZIP修改的对应范围见独立验收报告；不冒称本ZIP未经改动的原生导出。

## 本次实际修复

1. 音频新增PATCH-A01：15k/1k衰减、正负输入各1µF隔直。提供布线源文件、实体布线图、BOM和计算记录。主板原R1/R2继续1k，无需改已有主板铜线。必须用补丁替换功放输入的原两根直连线。
2. 屏幕复位/中断/背光逻辑新增独立GPIO取线点方案，未将未知模组端子猜作已确认。明细见屏幕接口补全文件。
3. 补齐主板全部120个元件焊盘的逐脚表，包括J_AMP_OUT、J_PWR_5V、PJ及三组ESP插座；每脚有顶层坐标定位。
4. PJ座统一面板安装、五线连接，其他外购模块统一按丝印功能接线；取消未经证实的直插适配结论。
5. 修正LDO输入电流/耗散计算，撤回通用65°C判据与已经实现硬件互锁的说法。

## 接线执行基准

- 完整底板脚位：`小智小方盒_修复交付_20261109/底板全部120焊盘逐脚表.md`。
- DAC：底板J_DAC_IN.1=5V、.2=GND、.3=BCK(IO7)、.4=DIN(IO16)、.5=LRCK(IO15)、.6=GND（接模块SCK须确认它是PCM系统时钟脚）；模块供电接模块规定输入，不能把5V接裸芯片3.3V供电脚。
- 雷达：底板1→VCC、2→GND、3→OUT(IO8)、4(IO17/主控RX)→模块TX、5(IO18/主控TX)→模块RX。模块真实排针顺序按对应版本确认，不再无证据断言一定反插烧毁。
- 麦克风：J_MIC 1=3.3V、2=GND、3=SD(IO4)、4=L/R接地、5=WS(IO5)、6=SCK(IO6)。
- 功放：VIN由J_AMP_IN.5，电源GND由.4，SD由.3(IO9)；音频.1/.2经过PATCH-A01；模块OUT+/.−对应J_AMP_OUT.1/.2，再至J_SPK.1/.2。BTL负端不接地。
- PJ：底板1=音频GND、2=TIP、3=TIP常闭、4=RING、5=RING常闭。定义是载板接线端，不代替商家焊片编号。未插线2–3/4–5导通、插线断开，需在采购件记录实测。
- 电源：J_PWR_5V.1=5V、.2=GND；C1方孔+5V、圆孔GND，外壳负极条纹对应GND，脚长只作辅助辨认。
- AUX只连接有源音箱线路输入；不将220V接本板，不把PCM5102A当低阻耳机功放。

## 仍未完成的验收

采购模块丝印/机械版本、屏幕转接电路、可编译及实际运行固件、供电硬件隔离、闭壳热验证、完整装配CAD及试装尚无充分证据；逐项见同版台账。对这些项目不给“100%”“绝对”“零底噪”的承诺。

修复交付目录：`{OUT}`。旧图仅概念参考。原生嘉立创工程：`/Users/kavin/Documents/LCEDA-Pro/projects/Xiaozhi_v31_Verified_20261109.eprj2`；本轮未操作工程，不将其冒称新增补丁已集成版本。
'''
PRD.write_text(new_prd)

ledger=f'''# 接线与销项台账 v3.1 修订1

日期2026-11-09。沿用独立最终验收的编号，不把待测移出清单后当作通过。主板ZIP SHA-256：`{sha}`（未改动）。

| 编号 | 已落实的修改/证据 | 当前状态 | 仍需完成 |
|---|---|---|---|
| F02/V06/F02-H | 主板8文件、184唯一孔、四角90°弧、钻孔匹配参考源板；独立脚本复核结果保留 | 文件几何子项通过 | 板厂DFM不由本脚本代替 |
| W/C/N | 当前参考主板无异网铜接触、0.20mm间距筛查无违规；本次主板铜线未变 | 原通过项保留 | 模块功能不由铜线连通证明 |
| F01/丝印 | PRD改为实测范围：覆铜约0.360mm、丝印约0.325mm；删除1.257mm错误值 | 文档纠错已销项 | 当前ZIP不是未经修改的原生导出 |
| F08 | 新增PATCH-A01实际PCB源板、15k/1k硬件分压、双输入隔直、BOM和计算；五网连续且异网间距通过0.20mm筛查 | 设计补丁已交付，未整机销项 | 嘉立创导入/原生DRC、焊接、实际增益/失真；补丁未集成主板ZIP |
| F13/F14/F18 | 明确IO14/21/39/38取线点，I2C上拉列DNP条件；删除无根据恒亮/轮询已验证声明 | 接口预留方案已补，未销项 | Tiky准确转接板资料、背光驱动、固件集成与编译运行 |
| F04~F07/F10~F12 | 全120焊盘脚位表；模块功能线束对接；PJ改面板安装五线连接 | 底板接线定义已修复，实物未销项 | 确认采购模块供电/信号丝印、PJ触点通断、机械开孔与线束包络 |
| F16 | 撤回硬件防倒灌/互锁已经完成的说法，明确当前仅操作隔离 | 未销项 | 主控具体电源原理图，适配的实际隔离设计及验证 |
| F17 | 输入电流按LDO模型，给0.85W示例，删除通用65°C/15分钟通过条件 | 计算错误已修复，热验收未销项 | 器件型号、负载、压降、热平衡实测 |
| M03~M06 | 列明0.9mm仅名义余量、新增小板/线束需要计入；PJ取消底板直插依赖；旧图降为概念参考 | 误导结论已修复，装配未销项 | 全模块图纸/包络、天线净空、装配CAD及试装 |
| D01 | 撤回8项全部闭环/整机100%放行，补齐缺失接口表和状态 | 文档矛盾已销项 | 随实测更新以上固定编号，不提前打勾 |

## 修改前备份与交付物

修改前PRD/台账保存在`{BACK}`。修复目录内有音频转接PCB源文件、SVG布线图、完整120焊盘表、音频BOM、屏幕接口方案、电源/装配约束和可重复计算脚本结果。没有新增“可直接投产ZIP”。
'''
LEDGER.write_text(ledger)
shutil.copy2(PRD, OUT/PRD.name)
shutil.copy2(LEDGER, OUT/LEDGER.name)

summary='''# 本次修复交付入口

已修改桌面原PRD与原台账，修改前版本在“修改前备份”。主板v3.1制造ZIP未改。

- `音频硬件修复与BOM.md`：新增音频衰减及隔直电路的完整接法。
- `PATCH-A01_音频衰减转接板_18x12mm.kicad_pcb`：可导入嘉立创EDA的实际小板布线源文件，非Gerber生产包。
- `PATCH-A01_布线实图.svg`：对应源文件的顶层布线图。
- `底板全部120焊盘逐脚表.md`：载板每个元件脚的信号与物理位置。
- `屏幕接口补全.md`、`电源与装配约束.md`：已知可实施部分与尚缺材料的边界。
- `修复计算与几何验证.json`：小板间距/连通/幅度计算结果，原生DRC和实测明确为false。

状态以台账固定编号为准。设计补丁已形成文件；屏幕转接板、模块实物、供电隔离、配套固件和装配/热测试未被伪报完成。
'''
(OUT/'先看这里.md').write_text(summary)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='交付SHA256.json'}
(OUT/'交付SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(calc,ensure_ascii=False,indent=2))
print('written:',OUT)
