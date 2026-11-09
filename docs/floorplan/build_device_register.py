"""从只读快照建立逐设备核对底册，不修改HA。重复生成保留用户核对字段。"""
from pathlib import Path
import json
from collections import Counter
P=Path(__file__).resolve().parent
snapshot=json.loads((P/'ha-inventory-2026-11-08.json').read_text())
layout=json.loads((P/'home-layout.json').read_text())
placement=json.loads((P/'placement-confirmations.json').read_text())
confirmations={c['point_id']:c for c in placement.get('confirmations',[])}
areas={a['area_id']:a['name'] for a in snapshot['areas']}
entities={e['entity_id']:e for e in snapshot['entities']}
bydevice={}
for e in snapshot['entities']:bydevice.setdefault(e['device_id'],[]).append(e)
oldpath=P/'device-placement-register.json'
old=json.loads(oldpath.read_text()) if oldpath.exists() else {'devices':[]}
prior={d['ha_device_id']:d for d in old['devices']}
software_makers={'Home Assistant','hacs.xyz','piitaya','kalkih','custom-cards','frenck','DerTrolli','Clooos','thomasloven','basnijholt, RubenKelevra, th3w1zard1, protyposis','fineembs','DigiLive','Nabu Casa Inc.','make-all'}
rows=[]
for n,d in enumerate(snapshot['devices'],1):
 name=d['name_by_user'] or d['name'] or '(未命名)'
 model=d['model'] or ''
 if d['manufacturer'] in software_makers or name in ['Sun','Backup','谷歌翻译 en com','Forecast','Repairs'] or model in ['plugin','integration','Tuya Scene']:
  kind='software_or_scene';status='not_applicable';scope='软件/服务/场景，无独立物理安装点'
 elif d['manufacturer']=='HONOR' or '手表' in name:
  kind='mobile_device';status='portable';scope='移动设备，记录归属/常用区域，不固定坐标'
 elif model.endswith('(unsupported)') or '44:7B:' in name:
  kind='identity_review';status='pending_identity';scope='可能为遥控目标或重复发现记录，先核对身份，不擅自合并'
 else:
  kind='physical_device_candidate';status='pending_user_confirmation';scope='待逐一确认物理位置'
 eps=bydevice.get(d['id'],[])
 refs=[]
 for p in layout['points']:
  e=entities.get(p['entity_id'])
  if e and e['device_id']==d['id']:refs.append({'point_id':p['id'],'binding_status':'candidate_from_existing_layout','location_status':p['position_status']})
 confirmed_points=[]
 for ref in refs:
  c=confirmations.get(ref['point_id'])
  if c:
   confirmed_points.append({k:c[k] for k in ['point_id','room_id','mounting_surface','relative_position','height_m','controls_or_loads','binding_status','user_statement'] if k in c})
 for c in placement.get('confirmations',[]):
  if c.get('ha_device_id')==d['id'] and not any(x['point_id']==c['point_id'] for x in confirmed_points):
   confirmed_points.append({k:c[k] for k in ['point_id','room_id','mounting_surface','relative_position','height_m','controls_or_loads','binding_status','user_statement'] if k in c})
  if c.get('entity_id') in {e['entity_id'] for e in eps} and not any(x['point_id']==c['point_id'] for x in confirmed_points):
   confirmed_points.append({k:c[k] for k in ['point_id','room_id','mounting_surface','relative_position','height_m','controls_or_loads','binding_status','user_statement'] if k in c})
 if confirmed_points and kind=='physical_device_candidate':
  if all(str(x.get('point_id','')).startswith('L') for x in confirmed_points):
   status='load_location_confirmed_panel_location_unconfirmed';scope='用户已确认灯具/负载与该HA开关关系；开关面板本身位置尚未确认'
  else:
   status='partially_placed_from_user_confirmation';scope='已有用户确认的实物点位；精确坐标、高度或HA实体绑定按点位记录'
 if d['name']=='LD2410 Living Room Radar':
  c=confirmations.get('S12')
  if c:
   confirmed_points.append({k:c[k] for k in ['point_id','room_id','mounting_surface','relative_position','height_m','binding_status','user_statement'] if k in c})
   status='partially_placed_from_user_confirmation';scope='用户确认设备在客厅电视柜插座处；HA后台区域当前为厨房，待核对区域映射'
 if refs and not confirmed_points and kind=='physical_device_candidate':
  status='plan_or_photo_candidate_unconfirmed';scope='图纸/实景中有候选点位，但尚未逐项得到用户确认；不作为已确认实装位置'
 if any(x.get('point_id')=='A06' for x in confirmed_points):
  kind='software_or_scene';status='not_applicable';scope='用户确认该记录对应手机App端，没有独立物理安装位置'
 if confirmed_points and status=='pending_identity':
  status='located_identity_review';scope='位置已有确认；设备身份/实体映射仍需复核'
 rec={'record_id':f'H{n:03}','ha_device_id':d['id'],'ha_name':name,'manufacturer':d['manufacturer'],'model':d['model'],'backend_area_id':d['area_id'],'backend_area_name':areas.get(d['area_id']), 'classification':kind,'placement_status':status,'scope_note':scope,'layout_point_candidates':refs,'confirmed_floorplan_points':confirmed_points,'entities':[{'entity_id':e['entity_id'],'name':e['name'] or e['original_name'],'disabled_by':e['disabled_by'],'category':e['entity_category']} for e in eps], 'user_confirmed':{'physical_identity':None,'room_id':None,'wall_or_surface':None,'relative_position':None,'height_m':None,'heading_deg':None,'controls_or_loads':None,'confirmation_source':None},'notes':[]}
 if d['id'] in prior:
  for key in ['record_id','user_confirmed','notes']:rec[key]=prior[d['id']][key]
 rows.append(rec)
report={'schema_version':'0.1.0','source_snapshot':'ha-inventory-2026-11-08.json','captured_at':snapshot['captured_at'],'method':'每条HA设备记录单独建档；后台区域不是用户确认的安装位置；实体数量不等于实物数量','devices':rows,'physical_point_confirmations':json.loads((P/'placement-confirmations.json').read_text())['confirmations'] if (P/'placement-confirmations.json').exists() else [],'open_questions':[{'id':'Q027','point_id':'S02','status':'user_confirmed_height','user_answer':'1.5米','certainty':'explicit_response_normalized_from_m_or_cm_prompt','measurement_reference':'测量至设备中心/底边未说明'},{'id':'Q026','point_id':'S04','status':'height_unit_inferred','user_answer':'2.6','certainty':'interpreted_as_meters_from_question_context','next':'用户可随时纠正单位或测量基准'},{'id':'Q025','point_id':'S13','status':'user_confirmed_height','user_answer':'离地100cm','certainty':'explicit_user_confirmation','measurement_reference':'未说明设备中心/底边等测量基准'},{'id':'Q024','point_id':'AC01-AC03','status':'room_names_already_in_backend','user_answer':'3台空调的名字/房间在后台都有，不要重复问房间','certainty':'backend_registry_snapshot','backend_findings':'主人房、乐乐房、悦悦房各一台；客厅投影仪插座下还有一个climate域插座实体，不将其误计为空调本体'},{'id':'Q023','point_id':'A07','status':'partially_confirmed','user_answer':'美的净水机在厨房水槽处','certainty':'explicit_user_statement','backend_findings':'后台设备净水机，区域未分配'},{'id':'Q022','point_id':'A06','status':'non_physical_app_endpoint','user_answer':'第二台Tuya智能红外遥控器指手机App','certainty':'explicit_user_statement','backend_findings':'设备记录046213bdc0dfe97f580f9b1a45e00f63无明确房间区域'},{'id':'Q021','point_id':'A05','status':'user_confirmed_relative_location','user_answer':'客厅Tuya智能红外遥控器在客厅感应S01旁边','certainty':'explicit_user_confirmation','backend_findings':'设备IDfe35dd94b353fba5054ea9e8d347c642；快照未见remote/climate控制实体'},{'id':'Q020','point_id':'A04','status':'partially_confirmed','user_answer':'电视柜区域；柜内或柜面不明确','certainty':'user_confirmed_area_detail_open','backend_findings':'HA设备电视盒子（Tuya TV-box unsupported），无后台区域','next':'有需要时再确认柜内/柜面'},{'id':'Q019','point_id':'A03','status':'user_confirmed_location','user_answer':'投影仪与插座位于幕布/背景墙对面、插座在设备旁','certainty':'explicit_user_confirmation','backend_findings':'HA有两个同名投影仪插座设备；映射到受保护sixwgh设备switch.sixwgh_cn_1208359541_v8icm1_on_p_2_1','next':'后续核对时按设备ID区分同名插座'},{'id':'Q018','point_id':'A02','status':'user_confirmed_location','user_answer':'RX600Pro在厨房水槽/橱柜旁','certainty':'explicit_user_confirmation','backend_findings':'HA注册表设备RX600Pro，型号Midea Dishwasher、区域厨房','next':'核对投影仪/电视设备所在位置'},{'id':'Q017','point_id':'A01','status':'user_confirmed_location','user_answer':'米家洗衣机在厨房侧生活阳台，紧邻S13','certainty':'explicit_user_confirmation','backend_findings':'注册表设备米家洗衣机 洗烘12kg，后台区域阳台','next':'继续核对其他大型家电与插座位置'},{'id':'Q016','point_id':'K02','status':'user_confirmed_physical_relation','user_answer':'靠阳台的客厅落地风扇由客厅风扇插座控制','certainty':'explicit_user_confirmation','backend_findings':'HA注册表设备969866bd3ee01948f20abc590dfb6a53，实体switch.wiing_cn_1169602959_bm1_on_p_2_1已对应'},{'id':'Q015','point_id':'K01','status':'user_labeled_photo_registry_name_match','user_answer':'厨房风扇已在实景照片中标注，无需重复询问','certainty':'photo_and_registry_name_match_plug_match_unverified','backend_findings':'设备厨房风扇插座，实体switch.wiing_cn_1169934703_v7icm_on_p_2_1；照片显示厨房落地扇','next':'后续有机会现场核对插头与插座是否为同一设备'},{'id':'Q015','point_id':'K01','status':'photo_review_corrected','user_answer':'实景照片已标出厨房风扇，应按图记录，勿重复询问','certainty':'user_labeled_photo','backend_findings':'HA注册表有厨房风扇插座wiing.plug.v7icm，当前图稿点位S08名称误导；照片显示厨房落地扇位置','next':'把厨房风扇插座按设备实体单独挂到该落地风扇候选，先核对正确HA entity'},{'id':'Q014','point_id':'F02','status':'user_confirmed_mounting_surface','user_answer':'客卫排气扇墙面安装','certainty':'explicit_user_statement','backend_findings':'客卫排气扇注册表候选switch.bean_cn_1124140333_blns2_on_p_3_1','next':'核对厨房风扇插座当前控制的实物'},{'id':'Q013','point_id':'F01','status':'user_confirmed_mounting_surface','user_answer':'主卫排气扇墙面安装','certainty':'explicit_user_statement','backend_findings':'主卫排气扇注册表候选switch.bean_cn_1124140372_blns2_on_p_2_1','next':'核对客卫排气扇安装面与位置'},{'id':'Q012','point_id':'L09','status':'user_confirmed_physical_relation','user_answer':'悦悦房大吸顶灯由客房灯开关控制','certainty':'user_confirmed_entity_candidate_from_local_export_unverified','backend_findings':'本地候选switch.bean_cn_1124141619_blns1_on_p_2_1','next':'核对卫生间排气扇及其面板位置'},{'id':'Q011','point_id':'L10','status':'user_confirmed_physical_relation','user_answer':'乐乐房大吸顶灯对应乐乐灯开关','certainty':'user_confirmed_entity_candidate_from_local_export_unverified','backend_findings':'HA注册表候选实体switch.bean_cn_1124141619_blns1_on_p_2_1','next':'核对悦悦房/客房灯回路'},{'id':'Q010','point_id':'L11','status':'user_report_registry_conflict','user_answer':'主人房双开两键都控制大吸顶灯；没有另一灯','certainty':'explicit_user_statement','backend_findings':'注册表主人房双开左键=主人房灯，右键=主人房走廊灯；不一致，待只读核实','next':'保留冲突，不通过自动化或试错切换确认'},{'id':'Q009','point_id':'L11','status':'user_confirmed_physical_relation','user_answer':'主人房有两个开关：双开控制吸顶灯，单开控制走道灯；实体键位映射待核','certainty':'user_confirmed_entity_candidate_from_registry_name_unverified','backend_findings':'HA设备注册表有主人房大吸顶灯与主人房双开；具体按键回路映射须核对','next':'确认主人房双开另一回路实际控制的灯具'},{'id':'Q008','point_id':'L06','status':'user_confirmed_physical_relation','user_answer':'书房房间中央吸顶灯由书房灯开关控制','certainty':'user_confirmed_entity_candidate_from_local_export_unverified','backend_findings':'本地导出候选switch.bean_cn_1122794165_blns1_on_p_2_1','next':'核对主人房灯具和回路'},{'id':'Q007','point_id':'L05','status':'user_confirmed_physical_relation','user_answer':'客厅窗帘内侧灯带由客厅灯带开关控制','certainty':'user_confirmed_entity_candidate_from_local_export_unverified','backend_findings':'本地导出候选switch.bean_cn_1124140065_blns2_on_p_2_1','next':'核对客厅筒灯/灯带等剩余回路和实体'},{'id':'Q006','point_id':'L04','status':'user_confirmed_physical_relation','user_answer':'走道筒灯由走廊灯开关控制；此前否定为打错','certainty':'user_confirmed_entity_candidate_from_local_export_unverified','backend_findings':'本地导出候选switch.bean_cn_1124143167_blns1_on_p_2_1','next':'继续确认其他灯具与开关的负载对应'},{'id':'Q005','point_id':'L03','status':'user_confirmed_physical_relation','user_answer':'厨房方形灯板由厨房灯开关控制','certainty':'physical_load_relation_confirmed_entity_from_local_export_unverified','backend_findings':'本地导出候选switch.bean_cn_1122794638_blns1_on_p_2_1','next':'确认走道筒灯与走廊灯回路'},{'id':'Q004','point_id':'L02','status':'user_confirmed_physical_relation','user_answer':'舞台圆形吸顶灯由L02舞台灯开关控制','certainty':'physical_load_relation_confirmed_entity_from_local_export_unverified','backend_findings':'本地导出候选实体switch.bean_cn_1124140556_blns2_on_p_2_1','next':'确认厨房灯组开关与客厅领普/墙开实体'} ,{'id':'Q003','point_id':'L01','status':'user_confirmed_physical_relation','user_answer':'是，沙发正上方水晶吸顶灯由客厅主灯控制','certainty':'physical_load_relation_confirmed_entity_from_local_export_unverified','backend_findings':'本地图纸将L01候选实体记为switch.bean_cn_1124140556_blns2_on_p_3_1','next':'确认照片中舞台圆吸顶灯的控制回路'},{'id':'Q002','point_id':'S12','status':'registry_area_mismatch','user_answer':'电视柜插座','backend_findings':'HA设备LD2410 Living Room Radar的area_id当前为厨房；用户确认设备放在客厅电视柜插座处','certainty':'user_confirmed_location_backend_area_unresolved','next':'只读核对该设备对应实体及后台区域，避免误改区域或映射'},{'id':'Q001','point_id':'S13','status':'partially_answered','user_answer':'墙面设备名称为阳台感应，不记得1或2；触发次数更多的应该是1','certainty':'user_recollection_tentative','backend_findings':'HS1BB2名为阳台传感器，查询24小时62条移动事件；ES2名为阳台感应2，此查询未返回历史，不能直接比较或据此唯一绑定','next':'确认墙面与梁上设备分别对应HS1BB2还是ES2'}]}
oldpath.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# HA全设备逐项落位核对表','','来源：2026-11-08实时只读注册表；93条设备记录，不能直接当作93件实物。后台区域仅作线索，可能过时。','','| 编号 | 后台名称 | 型号 | 后台区域（未确认） | 类别 | 落位状态 | 已有图纸候选 |','|---|---|---|---|---|---|---|']
labels={'software_or_scene':'软件/场景','mobile_device':'移动设备','identity_review':'身份待核对','physical_device_candidate':'实物候选'}
for r in rows:md.append('| '+' | '.join([r['record_id'],r['ha_name'],r['model'] or '',r['backend_area_name'] or '未分配/区域不明',labels[r['classification']],r['placement_status'],','.join(x['point_id'] for x in r['layout_point_candidates']) or '无'])+' |')
md+=['','## 已确认实物安装资料','','S05书房感应：梳妆台侧墙，离地30cm；S06主人房感应：空调下方、床尾通道侧墙，离地30cm；S07悦悦房感应：书桌桌面；S08厨房补充感应：厨房天花；S09主卫感应：马桶正上方天花；S10客卫感应：马桶正上方天花；S11玄关感应：玄关门口区域（安装面待定）；S12客厅第二雷达：电视柜插座处（用户确认，后台区域需核对）。十六处位置或灯具控制关系已确认；主人房面板实体映射存在冲突，详见placement-confirmations.json。','','## 当前核对：客厅阳台两颗感应','','- 用户确认：两颗均在客厅外同一阳台，墙面S13在洗衣机旁、南侧阳台段的北侧瓷砖墙（客厅沙发墙室外侧，用户红线确认）；梁上S04在客厅出阳台后的东侧阳台段横梁立面，用户红框确认梁位。','- 用户记忆：触发次数更多的“应该是阳台感应1”，是辨认线索，不是实体绑定已确认。','- 后台HS1BB2：阳台传感器，近24小时62条移动事件。','- 后台ES2：阳台感应2，查询窗口未返回历史；有人状态及部分属性更新时间较旧。不能把无历史当成0次触发或无人。','- S04原有HS1BB2映射只作为候选，S13未绑定；须确认物理设备与型号，不能反向根据旧图证明映射。','','## 完成标准','','每件实物记录房间、墙面/天花/梁/柜等安装面、相对位置、主实体；高度和方向可后补。开关还要区分开关面板位置与它控制的灯/负载位置。软件服务无需画物理点，移动设备不编造固定坐标，疑似重复记录先核对身份。']
(P/'全设备落位核对表.md').write_text('\n'.join(md)+'\n')
print(dict(Counter(r['classification'] for r in rows)))
