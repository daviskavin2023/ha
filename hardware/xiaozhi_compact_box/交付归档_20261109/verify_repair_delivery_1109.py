"""Read the delivered PCB back from disk, independently of its generator state."""
from pathlib import Path
import re,json,math,hashlib,xml.etree.ElementTree as ET
ROOT=Path('/Users/kavin/.codex/visualizations/2026/11/08/xiaozhi-hardware-review')
OUT=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109')
P=OUT/'PATCH-A01_音频衰减转接板_18x12mm.kicad_pcb'
code=(ROOT/'audit_v25.py').read_text().split('items=tracks+pads')[0]
code=code.replace("P=ROOT/'frozen-v25/board.kicad_pcb'",f'P=Path({str(P)!r})')
code=code.replace("drill=num(p,'drill')[0]", "drill=num(p,'drill')[0] if child(p,'drill') else 0")
ns={};exec(code,ns)
assert len(ns['pads'])==12 and len(ns['tracks'])==9
expected={('J1','1'):2,('J1','2'):1,('J2','1'):4,('J2','2'):5,
 ('RA','1'):2,('RA','2'):3,('RB','1'):3,('RB','2'):1,
 ('CP','1'):3,('CP','2'):4,('CN','1'):1,('CN','2'):5}
assert {(p['ref'],p['pin']):p['net'] for p in ns['pads']}==expected
items=ns['pads']+ns['tracks'];parent=list(range(len(items)));gaps=[]
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for i,a in enumerate(items):
 for j,b in enumerate(items[i+1:],i+1):
  value=ns['gap'](a,b)
  if value is None:continue
  gap,_=value
  if a['net']==b['net']:
   if gap<=1e-7:parent[find(i)]=find(j)
  else:
   assert gap>=.2-1e-7,(a,b,gap)
   gaps.append(gap)
groups={n:len({find(i) for i,a in enumerate(items) if a['net']==n}) for n in range(1,6)}
assert set(groups.values())=={1}
# Solder mask: explicit 0.05mm expansion leaves the two 0805 pads separated.
for a in ns['pads']:
 for b in ns['pads']:
  if a is b or a['ref']!=b['ref']:continue
  assert ns['gap'](a,b)[0]-.1>=.15-1e-7
# Every source pad must agree with the complete carrier interface table.
pins=json.loads((OUT/'底板引脚数据.json').read_text())
assert len(pins)==120
assert len({(p['ref'],p['pin']) for p in pins})==120
by={(p['ref'],p['pin']):p for p in pins}
for ref,pin,net in [('J_AMP_OUT','1',23),('J_AMP_OUT','2',24),('J_PWR_5V','1',2),('J_PWR_5V','2',1),('J_PJ324M','1',1)]:
 assert by[ref,pin]['net']==net
for ref,pin,name in [('J_ESP_L','20','SPARE_IO14'),('J_ESP_R1','18','SPARE_IO21'),('J_ESP_R1','9','SPARE_IO39'),('J_ESP_R1','10','SPARE_IO38')]:
 assert by[ref,pin]['name']==name
ET.parse(OUT/'PATCH-A01_布线实图.svg')
z=Path('/Users/kavin/Desktop/小智小方盒_JLC单一钻孔生产包_v3.1_20261109.zip')
assert hashlib.sha256(z.read_bytes()).hexdigest()=='b61b19d6c207f1cb4f51cc37d07f56fd66c94c07339798e21026e00268cd3354'
print(json.dumps(dict(readback_PCB='PASS',patch_networks=groups,min_gap_mm=min(gaps),interface_pad_count=len(pins),new_screen_GPIO_points='PASS',main_manufacturing_zip_unchanged=True,svg_XML='PASS'),ensure_ascii=False,indent=2))
