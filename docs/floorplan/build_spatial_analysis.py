"""原始尺寸图几何核对；不将候选方向作为实测覆盖，不操作HA。"""
from pathlib import Path
import json, math
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
P=Path(__file__).resolve().parent
# 端点由1888x1334原始尺寸图目视读取，约±2px；尺寸标注是几何约束。
controls=[('x','客厅横向',4.2,1090,1360),('x','舞台横向',2.4,864,1018),('x','主卫横向',2.0,1025,1154),('x','主卧横向',3.05,1160,1357),('y','主卧床区',2.5,234,395),('y','主卧内通行段',1.1,395,466),('y','客厅纵向',4.15,847,1115),('y','东阳台纵向',4.4,834,1117)]
sc={axis:sum(m*(b-a) for ax,n,m,a,b in controls if ax==axis)/sum(m*m for ax,n,m,a,b in controls if ax==axis) for axis in ['x','y']}
def dist(a,b):return math.hypot((b[0]-a[0])/sc['x'],(b[1]-a[1])/sc['y'])
def az(a,b):return math.degrees(math.atan2((b[0]-a[0])/sc['x'],-(b[1]-a[1])/sc['y']))%360
points={'S02_original_approx':[1000,680],'kitchen_stove_case':[945,594],'kitchen_table_case':[855,710],'kitchen_west_entry_case':[720,710],'S01_original_approx':[1130,1110],'stage_nw_case':[864,850],'stage_sw_case':[864,1110],'LD_case_A':[1210,860],'sofa_seat_case_L':[1190,1075],'sofa_seat_case_R':[1250,1075],'south_curtain_case':[1210,1115]}
measures=[]
for start,ends in [('S02_original_approx',['kitchen_stove_case','kitchen_table_case','kitchen_west_entry_case']),('S01_original_approx',['stage_nw_case','stage_sw_case']),('LD_case_A',['sofa_seat_case_L','sofa_seat_case_R','south_curtain_case'])]:
 for end in ends:measures.append({'from':start,'to':end,'plan_distance_m':round(dist(points[start],points[end]),3),'azimuth_deg_north_clockwise':round(az(points[start],points[end]),1),'status':'conditional_geometry_not_measured_coverage'})
record={'date':'2026-11-09','source':'sources/坐标参考图.png','source_size_px':[1888,1334],'method':'标注尺寸约束下按轴最小二乘估计像素比例；端点约±2px；不改变原示意图的数据坐标','pixels_per_meter':sc,'controls':[{'axis':ax,'label':n,'dimension_m':m,'endpoints_px':[a,b],'residual_m':round((b-a)/sc[ax]-m,4)} for ax,n,m,a,b in controls],'metric_origin_reference_px':[1090,1115],'metric_axes':'east,north','point_reference_px':points,'latest_user_confirmation':{'S12':'电视柜中间；板面正向未确认','K02':'风扇已移至东侧窗帘附近；沿帘位置和离帘距离未确认','old_fan_case_status':'撤回为现址依据，不再参与当前几何计算'},'point_warning':'S01/S02仍是旧图近似位置；LD_case_A是已确认电视柜中段的近似算例，不是实测坐标；板面朝向未知。小数仅为中间结果，建议解读精度0.1-0.3m。','measurements':measures,'nominal_model':{'LD2410C':{'source':'https://www.hlktech.com/Goods-239.html','nominal_max_range_m':6,'nominal_half_angle_deg':60,'range_resolution_m':0.75,'actual_heading':None,'actual_range_settings':None},'HS3':{'source':'https://www.linptech.com/2122161624.html','image':'analysis-sources/linptech-hs3-official-range.jpg','nominal_moving_max_m':8,'nominal_total_angle_deg':120,'manufacturer_test_mount_height_m':[1.2,1.5],'binding_to_S04_or_S13':'unresolved'},'HB01':{'exact_primary_radiation_pattern_verified':False},'es2_model':{'exact_primary_radiation_pattern_verified':False,'warning':'不以es2b/ES5/其他厂家的规格替代linp.sensor_occupy.es2'}}}
(P/'spatial-analysis.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
# 原图叠加几何射线；不绘制未经证实的全屋覆盖圆。
fontpath='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
F=lambda n:ImageFont.truetype(fontpath,n)
im=Image.new('RGB',(1800,1330),'#f4f6f8');d=ImageDraw.Draw(im)
d.text((40,22),'尺寸与探测几何核对 / 2026-11-09',font=F(32),fill='#102b40')
d.text((40,69),'标注尺寸是真实图纸依据；彩色射线是条件算例，不能当作实际覆盖范围。',font=F(21),fill='#566575')
base=Image.open(P/'sources/坐标参考图.png').convert('RGB').crop((690,175,1510,1250));im.paste(base,(32,138))
def xy(p):return (p[0]-690+32,p[1]-175+138)
def ray(a,b,col):d.line([xy(points[a]),xy(points[b])],fill=col,width=3)
def dot(name,text,col,offset=(8,-22)):
 x,y=xy(points[name]);d.ellipse((x-6,y-6,x+6,y+6),fill=col); box=d.textbbox((x+offset[0],y+offset[1]),text,font=F(18));d.rectangle(box,fill='white');d.text((x+offset[0],y+offset[1]),text,font=F(18),fill=col)
for target in ['kitchen_stove_case','kitchen_table_case','kitchen_west_entry_case']:ray('S02_original_approx',target,'#007c83')
for target in ['stage_nw_case','stage_sw_case']:ray('S01_original_approx',target,'#a361c1')
for target in ['sofa_seat_case_L','sofa_seat_case_R','south_curtain_case']:ray('LD_case_A',target,'#1676ca')
# 风扇只确认东帘附近，整段作位置待定边界，不给虚假落点。
d.line([xy((1360,860)),xy((1360,1115))],fill='#d37821',width=5)
dot('S02_original_approx','S02 近似点','#007c83',(-112,-30));dot('S01_original_approx','S01 近似点','#a361c1',(-118,-12));dot('LD_case_A','S12 中段近似','#1676ca',(-90,-26))
x=900;y=138
blocks=[('01 客厅与舞台的尺度','#102b40',['客厅：4.20 × 4.15 m；舞台：2.40 × 4.00 m。','加1.10 m通行带，东西展开总宽7.70 m。','S01到舞台两角的条件距离约4.1–5.8 m；','还要核对偏角，不能按一个6 m圆宣称全覆盖。']),('02 LD2410中段已确认，风扇移至东帘','#1676ca',['S12已确认电视柜中段；朝向仍未知。','A到两处沙发算例约3.3–3.4 m，','到南帘算例约4.0 m；径向间隔约0.6 m。','LD2410距离分辨率0.75 m，不能保证一刀分开。','旧风扇点撤回；橙线为东帘位置待定边界。','朝南假设下，东帘不同段偏角约30–90°。']),('03 厨房：计算所需方位，不盲目扩大距离','#007c83',['S02到灶台/餐桌算例约1.6 m / 2.3 m。','两条射线朝向约327° / 258°，夹角约69°。','因此应核对西北向覆盖，而不是面朝走道。','实际正面、俯仰和HB01方向图仍未确认。']),('04 阳台、卧室：必须补第三维','#a361c1',['阳台东段宽1.80 m，返边深1.50 m，存在转角。','单颗感应不能仅凭标称距离证明转角全覆盖。','S05/S06高0.30 m；胸腔/床沿高度影响遮挡。','不能根据“房间长度小于最大距离”宣布可靠。'])]
for title,col,lines in blocks:
 d.rounded_rectangle((x,y,1758,y+44+len(lines)*31+18),radius=12,fill='white')
 d.text((x+20,y+12),title,font=F(23),fill=col)
 for j,line in enumerate(lines):d.text((x+20,y+53+j*31),line,font=F(21),fill='#243749')
 y+=44+len(lines)*31+36
d.text((40,1250),'来源：用户原始尺寸图、现场确认；海凌科LD2410C产品页；领普人体传感器3官方范围图。',font=F(20),fill='#46596b')
d.text((40,1285),'约64.4像素/米；算例点位置未实测。未改HA、未改任何传感器参数。',font=F(20),fill='#46596b')
out=P/'output';im.save(out/'尺寸与探测几何核对.png')
c=canvas.Canvas(str(out/'pdf/尺寸与探测几何核对.pdf'),pagesize=(1200,887));c.drawImage(str(out/'尺寸与探测几何核对.png'),0,0,1200,887);c.save()
print(json.dumps({'pixels_per_meter':sc,'measurements':measures},ensure_ascii=False,indent=2))
