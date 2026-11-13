from pathlib import Path
import json, shutil, hashlib, html
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'sources'
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
photos=['73e28b34-ef2c-4c1c-95a5-3561638276df','e6f3423f-fb9b-4c11-8cf2-ba8417684222','52fe74b1-c047-4d15-bc30-03b5f30eaeac','6b5051d4-3604-436c-9086-a4a576f39ee5','9f84e4f1-8dd8-4766-923e-c1c97ba42d17','731ecc5f-fa84-4927-8a13-5ba931a5ed36','4344442a-fa97-4b8b-806f-7472a89836a4','ed9e62fd-706f-49ce-befe-567e870a6910','d68d4fd8-f0a2-4f8b-ad9a-135142582ea5','cd462cd5-e937-4c24-a410-e34342e2619f','e588e80c-6d67-480e-bdc0-7d761bcc8083','703c9f40-cdc9-42f3-a8ad-e1fa167b7e86','0d0a3423-cb37-4442-b7c7-1da7bb5b4eb6']
for i,p in enumerate(photos,1):
 src=Path('/var/folders/k9/ngy5zdnn51l0w3nfvk5s971c0000gn/T')/f'codex-clipboard-{p}.png'
 dst=SRC/f'实景-{i:02}.png'
 if src.exists() and not dst.exists(): shutil.copy2(src,dst)

def E(f):return 'exports/automations/'+f+'.json'
points=[]
def point(i,name,room,kind,pos,source,entity=None,entity_source=None,location='approximate',notes=''):
 points.append(dict(id=i,name=name,room_id=room,kind=kind,position_px=pos,position_status=location,position_sources=source,entity_id=entity,entity_status='local_export_unverified' if entity else 'unbound',entity_source=entity_source,height_m=None,heading_deg=None,coverage_polygon=None,notes=notes))
point('S01','客厅领普','living','presence',[1130,1110],['原图：客厅领普','实景-02/06/07'],'binary_sensor.linp_cn_1130732284_hb01_occupancy_status_p_2_1',E('1736664474841'),notes='南侧沙发后墙；照片支持所在墙面，安装高度与朝向未测。')
point('S02','厨房领普','kitchen','presence',[1000,680],['原图：厨房领普','实景-01'],'binary_sensor.linp_cn_1134456435_hb01_occupancy_status_p_2_1',E('1736917627387'),notes='厨房东侧操作台/玻璃隔断附近。')
point('S03','走道感应','corridor','motion',[1055,490],['实景-04/05/12'],'event.linp_cn_blt_3_1k0llp3d0c400_hs1bb2_motion_detected_e_2_1008',E('1736919300667'),notes='新照片确认在走道北端顶面、单杠上方；不是装在单杠上，平面坐标仍近似。')
point('S04','客厅阳台梁上感应','balcony','motion',[1435,1030],['原图：阳台梁上','实景-09','本轮对话平面图红框确认（45473191）','本轮出阳台梁上实景（a6f47d52，同实景-09）'],'event.linp_cn_blt_3_1k0m2afv4cg01_hs1bb2_motion_detected_e_2_1008',E('1736918907451'),'user_confirmed_approximate',notes='用户红框确认在客厅出阳台后的东侧阳台段横梁立面、近下缘。梁位已确认，像素为示意落点非实测，替换前版北端角点与待定标签。型号及实体仍未实物核对，旧导出仅作为候选；高度与朝向未测。')
point('S05','书房领普','study','presence',None,['原图：书房领普','实景-10'],'binary_sensor.linp_cn_1130160808_hb01_occupancy_status_p_2_1',E('1736919449440'),'user_confirmed_relative',notes='用户确认：照片所示梳妆台侧墙，离地30cm；插座上方，附近有椅背与柜体。实景相对位置已确认，不要求重复标图。墙面方位与平面精确坐标未标定，旧南侧门口坐标已撤销。')
point('S06','主人房领普','master','presence',None,['原图：主人房领普','实景-11'],'binary_sensor.linp_cn_1207295174_hb01_occupancy_status_p_2_1',E('zhurenfang_motion_light_on'),'room_located',notes='照片标注设备在空调下方、靠床尾通道的墙面，明显低于空调插座；撤销前版北侧床头点。墙面方位、离地高度待确认。')
point('S07','悦悦房感应','yueyue','presence',[1150,754],['原图：悦悦房领普'],'binary_sensor.linp_cn_blt_3_1qa5uknk4cg01_es2_occupancy_status_p_2_1078',E('yueyue_motion_light_on'),notes='图纸写领普；自动化导出为ES2，型号与物理设备待核对。')
point('S08','厨房补充PIR','kitchen','motion',None,[E('1736917627387')],'event.linp_cn_blt_3_1k0stsh8sk400_hs1bb2_motion_detected_e_2_1008',E('1736917627387'),'unlocated','导出说明原走廊感应2已移厨房；未在照片中确认安装点。')
point('S09','主卫存在感应','master_bath','presence',None,[E('1736920400997')],'binary_sensor.linp_cn_1114869602_hb01_occupancy_status_p_2_1',E('1736920400997'),'unlocated')
point('S10','客卫存在感应','guest_bath','presence',None,[E('1740457164269')],'binary_sensor.linp_cn_1130167279_hb01_occupancy_status_p_2_1',E('1740457164269'),'unlocated')
point('S11','玄关PIR','entrance','motion',None,[E('1736917740057')],'event.linp_cn_blt_3_1k0srr2vokk00_hs1bb2_motion_detected_e_2_1008',E('1736917740057'),'unlocated')
point('S12','客厅 LD2410（USB串口）','living','presence',None,['docs/2026-11-08-全屋人体存在感应拓扑与客厅双雷达布防基准.md','PRD-2026-10-29-ESP32客厅雷达.md'],location='unlocated',notes='文档记录/候选位置：电视柜近走道端；未确认实际摆放及现用实体，不画作已安装点。')
point('D01','入户门磁','entrance','door',None,[E('1736917740057')],'binary_sensor.isa_cn_blt_3_1k06muhhs4o00_dw2hl_contact_state_p_2_2',E('1736917740057'),'unlocated','入户门已知在西侧；门磁在门框哪一侧未知。')
point('L01','客厅主灯','living','light',[1200,995],['实景-06/07'],'switch.bean_cn_1124140556_blns2_on_p_3_1',E('1736664474841'),notes='水晶吸顶灯；照片投影到平面的示意位置。')
point('L02','舞台灯','stage','light',[940,995],['实景-02/03/07'],'switch.bean_cn_1124140556_blns2_on_p_2_1',E('1749716052814'),notes='圆形吸顶灯；回路与照片灯具对应需最终确认。')
point('L03','厨房顶灯组','kitchen','light',[855,630],['实景-01/04'],'switch.bean_cn_1122794638_blns1_on_p_2_1',E('1736917627387'),notes='照片可见多块方形灯板；组点，不表示每块灯板独立受控。')
point('L04','走道筒灯组','corridor','light',[1055,620],['实景-04/05'],'switch.bean_cn_1124143167_blns1_on_p_2_1',E('1736919300667'),notes='照片可见顶面小圆灯；数量与单灯坐标未测。')
# 只知回路、不知灯具安装点的设备保留空坐标。
for i,name,room,entity,ref in [
 ('L05','客厅灯带左路','living','switch.bean_cn_1124140065_blns2_on_p_2_1','1736664474841'),
 ('L06','书房灯','study','switch.bean_cn_1122794165_blns1_on_p_2_1','1736919449440'),
 ('L07','主人房走廊灯','master_hall','switch.bean_cn_1124140146_blns2_on_p_3_1','1736919449440'),
 ('L08','主卫灯','master_bath','switch.bean_cn_1124140372_blns2_on_p_2_1','1736920400997'),
 ('L09','悦悦房大灯候选','yueyue','switch.bean_cn_1124141619_blns1_on_p_2_1','yueyue_motion_light_on')]:
 point(i,name,room,'light',None,[E(ref)],entity,E(ref),'unlocated','本地导出记录回路，未确认灯具具体安装位置。')
for i,name,room in [('L10','乐乐房照明','lele'),('L11','主人房主灯/壁灯','master'),('L12','客卫照明','guest_bath'),('L13','玄关照明','entrance'),('L14','阳台照明','balcony')]:
 point(i,name,room,'light',None,['待补充现场核对'],location='unlocated',notes='区域占位记录；灯具数量、位置及实体均待核对，不作为可调用控制项。')
point('S13','客厅阳台墙面感应','balcony','sensor_unclassified',[1285,1120],['实景-08','实景-13：用户红线确认','用户确认：两颗设备都在客厅外同一个阳台'],location='user_confirmed_approximate',notes='用户确认在拐角后的南侧阳台段，客厅南侧沙发墙室外侧（该阳台段北侧瓷砖墙），洗衣机旁。墙段已确认，像素为示意落点非实测；型号、HA实体、离地高度及朝向待核对。')
for p in points:
 if p['id'] in ['S05','S06']:
  p['mounting_surface']={'S04':'beam_vertical_face_near_lower_edge','S05':'wall_beside_vanity','S06':'wall_below_ac_near_bed_foot','S13':'tiled_wall_beside_washing_machines'}[p['id']]
  p['diagram_label_anchor_px']={'S04':[1420,930],'S05':[905,355],'S06':[1260,340],'S13':[1420,1080]}[p['id']]
  p['diagram_label_is_installation_point']=False
issues=[dict(id='ISSUE-BALCONY-001',status='reported_unresolved',priority='high',source='用户2026-11-08本轮反馈',statement='阳台感应误触频繁、运行不稳定，是重点问题区',point_ids=['S04','S13'],scope_status='用户确认两颗均在客厅外同一个阳台；未确认分别有哪些误触表现，问题暂按区域记录',root_cause=None,observed_environment=['实景-08：洗衣机、衣架、拖把、玻璃门、置物架','实景-09：晾晒衣物、晾衣杆、开放护栏、玻璃门'],environment_causality_verified=False,next_evidence=['核对两颗感应各自HA实体、型号与误触表现','只读对照事件历史、灯光历史与自动化trace','记录误触发生时间与当时人员、洗衣和晾晒情况'],parameter_change_authorized=False)]
rooms=[('study','书房',[840,200,1015,470]),('master_bath','主卫',[1020,235,1160,395]),('master','主人房',[1198,200,1360,465]),('master_hall','主卧内走道',[1015,395,1198,465]),('guest_bath','客卫',[838,475,1015,568]),('kitchen','厨房 / 餐桌',[710,580,1015,805]),('entrance','玄关',[700,655,805,805]),('corridor','走道',[1020,470,1090,840]),('lele','乐乐房',[1095,475,1360,645]),('yueyue','悦悦房',[1095,655,1360,838]),('stage','舞台',[860,815,1015,1110]),('living','客厅',[1025,850,1360,1110]),('balcony','东侧阳台',[1370,840,1480,1225])]
data=dict(schema_version='0.1.0',revision='2026-11-08-draft-33',status='review_required',orientation={'top':'north','right':'east','bottom':'south','left':'west','source':'用户本次确认：主入口西、客厅出阳台东、沙发南'},coordinate_system={'type':'drawing_pixel','reference':'sources/坐标参考图.png','reference_size':[1888,1334],'origin':'top_left','x_axis':'east','y_axis':'south','metric_transform':None,'warning':'底图归一化像素坐标；未完成尺寸标定，禁止当作毫米或米。SVG显示坐标为x-650+55,y-150+110。'},rooms=[dict(id=i,name=n,bounds_px=b,bounds_status='schematic') for i,n,b in rooms],points=points,issues=issues,safety={'read_only_dataset':True,'service_calls_allowed':False,'production_verified':False,'unknown_is_not_absent':True,'coverage_is_not_measured':True},sources=['sources/户型尺寸原图.pdf']+[f'sources/实景-{i:02}.png' for i in range(1,14)])
for r in data['rooms']:
 if r['id']=='balcony':
  r['name']='客厅外L形阳台（东段与南侧返边）'
  r['bounds_px']=[1120,840,1480,1225]
  r['polygon_px']=[[1365,840],[1480,840],[1480,1225],[1120,1225],[1120,1115],[1365,1115]]
  r['polygon_status']='schematic_from_original_plan'
for p in points:
 if p['id']=='A05':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='near_living_sensor_S01'
  p['confirmation_source']='placement-confirmations.json#A05'
 if p['id']=='A04':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='tv_cabinet_area_unspecified'
  p['confirmation_source']='placement-confirmations.json#A04'
 if p['id']=='A03':
  p['position_status']='user_confirmed_approximate'
  p['mounting_surface']='living_ceiling_mount_opposite_screen'
  p['confirmation_source']='placement-confirmations.json#A03'
 if p['id']=='A02':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='beside_kitchen_sink_cabinet'
  p['confirmation_source']='placement-confirmations.json#A02'
 if p['id']=='A01':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='kitchen_balcony_floor'
  p['confirmation_source']='placement-confirmations.json#A01'
 if p['id']=='K02':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='living_floor_standing_near_balcony'
  p['confirmation_source']='placement-confirmations.json#K02'
 if p['id']=='K01':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='kitchen_floor_standing'
  p['confirmation_source']='placement-confirmations.json#K01'
 if p['id']=='F02':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='guest_bath_wall'
  p['confirmation_source']='placement-confirmations.json#F02'
 if p['id']=='F01':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='master_bath_wall'
  p['confirmation_source']='placement-confirmations.json#F01'
 if p['id']=='L09':
  p['position_status']='user_confirmed_relative'
  p['fixture']='yueyue_main_ceiling_light'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L09'
 if p['id']=='L10':
  p['position_status']='user_confirmed_relative'
  p['fixture']='lele_main_ceiling_light'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L10'
 if p['id']=='L11':
  p['control_relation_status']='user_confirmed_but_registry_conflict'
  p['confirmation_source']='placement-confirmations.json#L11'
  p['notes'] += ' 用户说明主人房双开控制吸顶灯，另有单开控制走道灯；注册表键映射与该现场描述冲突，待核。'
 if p['id']=='L06':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='study_ceiling'
  p['fixture']='central_ceiling_light'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L06'
 if p['id']=='L05':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='curtain_side_linear_path'
  p['fixture']='linear_light_strip'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L05'
 if p['id']=='L04':
  p['position_status']='user_confirmed_approximate'
  p['mounting_surface']='corridor_ceiling'
  p['fixture']='downlight_group'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L04'
 if p['id']=='L03':
  p['position_status']='user_confirmed_approximate'
  p['mounting_surface']='kitchen_ceiling'
  p['fixture']='square_light_panel_group'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L03'
 if p['id']=='L02':
  p['position_status']='user_confirmed_approximate'
  p['mounting_surface']='stage_ceiling'
  p['fixture']='round_ceiling_light'
  p['relative_position']='stage_area_center_approximate'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L02'
 if p['id']=='L01':
  p['position_status']='user_confirmed_approximate'
  p['mounting_surface']='living_ceiling'
  p['fixture']='crystal_ceiling_light'
  p['relative_position']='above_sofa'
  p['control_relation_status']='user_confirmed_entity_candidate_from_local_export'
  p['confirmation_source']='placement-confirmations.json#L01'
 if p['id']=='S02':
  p['height_m']=1.5
  p['height_source']='用户回答1.5，按米记录'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S02'
 if p['id']=='S04':
  p['height_m']=2.6
  p['height_source']='用户答2.6；推断单位为米，待纠正'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S04'
 if p['id']=='S13':
  p['height_m']=1.0
  p['height_source']='用户明确说明离地100cm'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S13'
 if p['id']=='S12':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='tv_console_outlet'
  p['confirmation_source']='placement-confirmations.json#S12'
 if p['id']=='S11':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='unknown_at_entrance'
  p['confirmation_source']='placement-confirmations.json#S11'
 if p['id']=='S10':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='guest_bath_ceiling_above_toilet'
  p['confirmation_source']='placement-confirmations.json#S10'
 if p['id']=='S09':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='master_bath_ceiling_above_toilet'
  p['confirmation_source']='placement-confirmations.json#S09'
 if p['id']=='S08':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='kitchen_ceiling'
  p['confirmation_source']='placement-confirmations.json#S08'
 if p['id']=='S07':
  p['position_status']='user_confirmed_relative'
  p['mounting_surface']='desk_surface'
  p['confirmation_source']='placement-confirmations.json#S07'
 if p['id']=='S06':
  p['height_m']=0.3
  p['height_source']='用户明确说明离地30cm'
  p['confirmation_source']='placement-confirmations.json#S06'
 if p['id']=='S05':
  p['height_m']=0.3
  p['height_source']='用户明确说明离地30cm'
  p['confirmation_source']='placement-confirmations.json#S05'
 if p['id']=='S02':
  p['height_m']=1.5
  p['height_source']='用户回答1.5，按米记录'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S02'
 if p['id']=='S04':
  p['mounting_surface']='beam_vertical_face_near_lower_edge'
  p['confirmation_source']='placement-confirmations.json#S04'
 if p['id']=='S02':
  p['height_m']=1.5
  p['height_source']='用户回答1.5，按米记录'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S02'
 if p['id']=='S04':
  p['height_m']=2.6
  p['height_source']='用户答2.6；推断单位为米，待纠正'
  p['height_reference']='测量基准未说明'
  p['confirmation_source']='placement-confirmations.json#S04'
 if p['id']=='S13':
  p['mounting_surface']='exterior_face_of_living_south_wall'
  p['confirmation_source']='placement-confirmations.json#S13'
# 最新用户现场位置优先于旧照片/旧文档。
latest=json.loads((ROOT/'placement-confirmations.json').read_text())
for cp in latest['confirmations']:
 if cp['point_id'] in ('S12','K02'):
  for p in points:
   if p['id']==cp['point_id']:
    p['notes']=cp['relative_position']+'；'+cp['position_accuracy']
    p['relative_position']=cp['relative_position']
    if 'connection_method' in cp:p['connection_method']=cp['connection_method']
    if 'binding_status' in cp:p['binding_status']=cp['binding_status']
    if cp['point_id']=='S12' and cp.get('entity_id'):
     p['ha_device_id']=cp['ha_device_id']
     p['entity_id']=cp.get('entity_id')
     p['entity_status']=cp.get('binding_status')
     p['entity_source']=cp.get('binding_source','ld2410-ble-binding-2026-11-09.json')
     p['temporary_test_location']=cp.get('temporary_test_location')
    p['position_status']='user_confirmed_relative'
    p['heading_deg']=cp.get('heading_deg')
(ROOT/'home-layout.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# 原始尺寸图渲染统一为坐标参考尺寸。
Image.open(SRC/'户型尺寸原图.png').resize((1888,1334)).save(SRC/'坐标参考图.png')

W,H=1640,1320
pdfmetrics.registerFont(TTFont('CN','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
c=canvas.Canvas(str(OUT/'pdf/全屋平面与设备点位.pdf'),pagesize=(W,H))
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="#f5f7fb"/>']
def col(v):
 from reportlab.lib.colors import HexColor
 return HexColor(v)
def rect(x,y,w,h,fill='#ffffff',stroke=None):
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
 c.setFillColor(col(fill));c.setStrokeColor(col(stroke or fill));c.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
def line(x1,y1,x2,y2,color='#334155',sw=3,dash=False):
 svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{sw}" fill="none"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
 c.setStrokeColor(col(color));c.setLineWidth(sw);c.setDash([7,5] if dash else []);c.line(x1,H-y1,x2,H-y2);c.setDash([])
def txt(x,y,t,size=17,color='#334155'):
 svg.append(f'<text x="{x}" y="{y}" font-family="Arial Unicode MS, PingFang SC, sans-serif" font-size="{size}" fill="{color}">{html.escape(t)}</text>')
 c.setFillColor(col(color));c.setFont('CN',size);c.drawString(x,H-y,t)
def circ(x,y,r,fill,stroke=None):
 svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
 c.setFillColor(col(fill));c.setStrokeColor(col(stroke or fill));c.setLineWidth(1);c.circle(x,H-y,r,fill=1,stroke=bool(stroke))
def X(x):return x-650+55
def Y(y):return y-150+110
rect(0,0,W,H,'#f5f7fb')
txt(50,49,'全屋空间与设备点位',30,'#12263d');txt(50,81,'2 栋 03 户型  /  HA 基础数据草稿 v0.33  /  2026-11-08',17)
rect(40,105,870,1155);rect(935,105,665,1155)
# 区域用原图轮廓描绘；不将区域框当作墙。
for rid,n,(x1,y1,x2,y2) in rooms:
 rect(X(x1),Y(y1),x2-x1,y2-y1,'#eef4f7' if rid in ['living','stage','kitchen'] else '#f6f4ef')
 
 if rid == 'kitchen': txt(X(870),Y(772),n,17)
 elif rid == 'corridor': txt(X(x1)+8,Y(550),n,15)
 else: txt(X(x1)+10,Y(y1)+28,n,17)
# 墙线，门洞处留白。阳台不填补不存在的墙。
walls=[(790,190,1400,190),(790,190,790,280),(830,280,830,470),(790,280,830,280),(1400,190,1400,470),(1365,280,1365,465),(970,190,970,395),(1020,230,1160,230),(1020,230,1020,395),(1020,395,1092,395),(1158,230,1158,395),(830,470,1015,470),(1090,470,1480,470),(1480,470,1480,680),(1365,650,1480,680),(1090,470,1090,580),(1090,640,1365,640),(1090,650,1090,670),(1090,730,1090,840),(1090,840,1365,840),(1365,680,1365,840),(830,470,830,568),(830,568,965,568),(1015,470,1015,510),(1015,565,1015,800),(700,605,830,605),(700,605,700,655),(700,750,700,810),(700,810,860,810),(860,810,860,1115),(860,1115,1365,1115),(1365,840,1480,840),(1480,840,1480,1225),(1120,1225,1480,1225),(1120,1120,1120,1225)]
for a,b,d,e in walls:line(X(a),Y(b),X(d),Y(e),'#344356',5)
# 舞台台阶边缘：开放区域，不画作隔墙。
line(X(860),Y(810),X(1015),Y(810),'#baa58b',2,True)
line(X(1015),Y(810),X(1015),Y(1115),'#baa58b',2,True)
# 窗与通道
for a,b,d,e in [(875,1115,1005,1115),(1150,1115,1345,1115),(1365,885,1365,1090),(1195,190,1350,190),(840,190,965,190)]:line(X(a),Y(b),X(d),Y(e),'#65b4ca',5)
# 家具：表达遮挡位置，不作为实测家具尺寸。
rect(X(1170),Y(990),140,110,'#e3d3bb','#baa58b');txt(X(1185),Y(1055),'沙发',18)
rect(X(1160),Y(855),155,24,'#dde2ea','#9eabba');txt(X(1160),Y(902),'电视 / 背景墙',14)
rect(X(1110),Y(958),40,85,'#e7edf2','#bcc9d5');rect(X(1180),Y(952),68,38,'#e7edf2','#bcc9d5')
rect(X(810),Y(670),80,58,'#e3d3bb');txt(X(815),Y(704),'餐桌',14)
line(X(1365),Y(940),X(1365),Y(1085),'#bc8aa1',8);txt(X(1390),Y(1160),'窗帘',14,'#97667f')
# 方位和入口
txt(65,150,'北 N ↑',19,'#183b56');txt(65,177,'西 ←       → 东',14);txt(65,202,'南 ↓',14)
line(X(660),Y(705),X(712),Y(705),'#183b56',3);txt(X(620),Y(685),'主入口 · 西',15)
# 用户确认的梁位仅作平面示意。
line(X(1365),Y(1030),X(1480),Y(1030),'#94a3b8',2,True)
txt(X(1380),Y(1065),'出阳台横梁',12,'#64748b')
# 不画未经测量的雷达覆盖扇形。
for p in points:
 if not p['position_px']:continue
 x,y=p['position_px'];x,y=X(x),Y(y)
 color='#087f8c' if p['id'].startswith('S') else '#b77912'
 circ(x,y,16,color);txt(x-12,y+5,p['id'],12,'#ffffff')
# 仅房间可定位：展示空心标签，禁止将锚点当作安装位置。
for p in points:
 if 'diagram_label_anchor_px' not in p: continue
 x,y=p['diagram_label_anchor_px'];x,y=X(x),Y(y)
 circ(x,y,19,'#ffffff','#c56a27');txt(x-16,y+5,p['id']+'?',11,'#a45c10')
 txt(x-44,y+38,{'S04':'梁位待定','S13':'墙位待定','S05':'侧墙 · 离地30cm'}.get(p['id'],'墙位待定'),12,'#a45c10')
txt(X(1160),Y(1180),'南侧阳台段 · S13已确认',14,'#087f8c')
# 家电干扰线索点（不作为自动化控制对象）
for x,y,n in [(1100,884,'风扇'),(977,790,'风扇')]:
 circ(X(x),Y(y),8,'#b486a0');txt(X(x)+12,Y(y)+5,n,13,'#865974')
txt(62,1230,'示意重绘：门洞、家具与点位非测绘精度；以尺寸原图为准。',15)
# 侧栏
sx=962
txt(sx,145,'图例与核对状态',23,'#12263d')
circ(sx+12,178,11,'#087f8c');txt(sx+34,185,'S  感应点：原图 / 照片定位，坐标近似',16)
circ(sx+12,210,11,'#b77912');txt(sx+34,217,'L  灯具 / 灯组：照片投影，坐标近似',16)
txt(sx,251,'空心 S? = 仅知房间，不代表安装点。',17,'#a45c10')
txt(sx,280,'实体取自本地导出；尚未核对生产 HA 注册表。',16)
line(sx,299,1570,299,'#dbe3eb',1)
txt(sx,334,'已落图感应点',21,'#12263d')
labels=['S01 客厅领普 · 南侧沙发墙','S02 厨房领普 · 东侧操作台附近','S03 走道感应 · 单杠上方顶面','S04 阳台感应 · 出阳台横梁 / 约2.6m（单位推断）','S05 书房感应 · 梳妆台侧墙 / 离地30cm（确认）','S06 主人房感应 · 空调下方墙 / 离地30cm（确认）','S07 悦悦房感应 · 书桌上（用户确认）','S13 墙面感应 · 南侧阳台段北墙（用户确认）']
for j,t in enumerate(labels):txt(sx,362+j*30,t,16)
txt(sx,626,'已落图灯具 / 灯组',21,'#12263d')
for j,p in enumerate([p for p in points if p['id'] in ['L01','L02','L03','L04']]):txt(sx,660+j*33,p['id']+'  '+p['name'],17)
line(sx,779,1570,779,'#dbe3eb',1)
txt(sx,816,'已登记、待定位',21,'#12263d')
for j,t in enumerate(['S08 厨房天花感应（已确认） · S09 主卫感应','S10 客卫感应 · S11 玄关 PIR','S12 LD2410 · 电视柜中间插座（用户确认；朝向未定） · D01入户门磁','L07-L14 其他照明回路 / 区域占位','卧室、卫生间、阳台灯具尚缺安装点']):txt(sx,850+j*30,t,16)
txt(sx,1038,'阳台：误触 / 不稳定重点区',21,'#b45309')
for j,t in enumerate(['用户确认问题；根因尚未查明','S04 梁上 + S13 墙面：同一个客厅阳台','洗衣机、晾晒衣物等仅记环境线索','不据照片断定干扰原因，不修改硬件参数']):txt(sx,1073+j*30,t,16)
txt(sx,1231,'坐标、实体与来源见 home-layout.json',16,'#087f8c')
svg.append('</svg>');(OUT/'全屋平面与设备点位.svg').write_text('\n'.join(svg))
c.showPage()
# 第二页保留原尺寸图供对照。
rect(0,0,W,H,'#ffffff');txt(50,55,'尺寸原图 / 定位依据',29);txt(50,90,'保留用户原始尺寸标注；不把示意重绘作为施工或测距依据。',18)
im=Image.open(SRC/'坐标参考图.png');iw,ih=im.size;scale=min(1540/iw,1170/ih)
c.drawImage(str(SRC/'坐标参考图.png'),50,35,width=iw*scale,height=ih*scale,preserveAspectRatio=True)
c.showPage()
# 第三页：新证据与纠正说明。
rect(0,0,W,H,'#ffffff');txt(50,55,'实景校正记录 / v0.5',29)
txt(50,92,'撤销无法由照片确认的平面坐标，保留照片相对位置；阳台问题按用户反馈登记。',18)
cards=[(8,'阳台墙面感应 S13：洗衣机旁；与梁上为两颗独立设备'),(9,'阳台梁上感应S04：出阳台横梁立面；红框已确认'),(10,'书房感应S05：梳妆台侧墙，离地30cm（用户确认）'),(11,'主人房感应S06：空调下方墙、床尾通道侧，离地30cm（用户确认）'),(12,'走道感应：单杠上方顶面，不在单杠上')]
for j,(i,title) in enumerate(cards):
 x=50+(j%2)*795;y=130+(j//2)*380
 im=Image.open(SRC/f'实景-{i:02}.png');iw,ih=im.size;k=min(740/iw,310/ih)
 c.drawImage(str(SRC/f'实景-{i:02}.png'),x,H-y-ih*k,width=iw*k,height=ih*k)
 txt(x,y+334,f'实景-{i:02}  '+title,15)
txt(845,970,'阳台问题：用户报告误触频繁、运行不稳定。',19,'#b45309')
txt(845,1010,'仅记录环境，不以照片推断故障根因。',17)
txt(845,1050,'安装高度、方向、实体绑定仍待核对。',17)
c.showPage();c.save()
# 台账 Markdown
lines=['# 全屋点位台账 v0.5','','> 日期：2026-11-08。本地文档与自动化导出核对，未访问生产 HA。所有实体绑定仍需注册表核对。','','| 编号 | 名称 | 坐标状态 | HA 实体候选 | 来源 / 说明 |','|---|---|---|---|---|']
for p in points:
 lines.append('| '+ ' | '.join([p['id'],p['name'],('用户确认墙段/示意坐标' if p['position_status']=='user_confirmed_approximate' else '近似定位') if p['position_px'] else ('照片位置已确认/离地30cm' if p['position_status']=='user_confirmed_relative' else ('仅知房间/照片相对位置' if p['position_status']=='room_located' else '待定位')),f"`{p['entity_id']}`" if p['entity_id'] else '未绑定','；'.join(p['position_sources'])+'；'+p['notes']])+' |')
lines += ['', '## 阳台重点问题', '', '用户确认：阳台误触频繁、运行不稳定。根因未查明。照片中的洗衣机、晾晒衣物等只作为环境记录，不是已证实的干扰源。两颗均在同一客厅阳台：S04梁上、S13墙面；各自误触表现及实体绑定待确认，详见home-layout.json的issues。']
(ROOT/'点位台账.md').write_text('\n'.join(lines)+'\n')
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.iterdir() if p.is_file()}
(ROOT/'sources.sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('generated',len(points),'points,',sum(bool(p['position_px']) for p in points),'positioned')
