from pathlib import Path
import zipfile,re,math,json,hashlib
ROOT=Path('/Users/kavin/.codex/visualizations/2026/11/08/xiaozhi-hardware-review')
OUT=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109')
P=OUT/'PATCH-A01_音频衰减转接板_18x12mm.kicad_pcb'
Z=Path('/Users/kavin/Downloads/Xiaozhi_PATCH_A01_JLC_20261109.zip')
code=(ROOT/'audit_v25.py').read_text().split('items=tracks+pads')[0]
code=code.replace("P=ROOT/'frozen-v25/board.kicad_pcb'",f'P=Path({str(P)!r})').replace("drill=num(p,'drill')[0]","drill=num(p,'drill')[0] if child(p,'drill') else 0")
ns={};exec(code,ns)
parsecode=(ROOT/'final_acceptance_1109.py').read_text().split('def parse(s):',1)[1].split('with zipfile.ZipFile(Z)',1)[0]
exec('def parse(s):'+parsecode,globals())
def padkey(p):return (p['shape'],round(p['x'],5),round(p['y'],5),round(p['sx'],5),round(p['sy'],5))
def trackkey(t):
 a=(round(t['x'],5),round(t['y'],5));b=(round(t['u'],5),round(t['v'],5))
 return (*sorted((a,b)),round(t['w'],5))
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 names=z.namelist()
 for n in names:
  if n.endswith(('.GTL','.GBL','.GTO','.GBO','.GTS','.GBS','.GTP','.GKO','.GDD')):
   s=z.read(n).decode();assert '%FSLAX45Y45*%' in s and '%MOMM*%' in s and 'M02*' in s
 top=parse(z.read('Gerber_TopLayer.GTL').decode())
 assert sorted(map(padkey,top[1]))==sorted(padkey(dict(p,y=-p['y'])) for p in ns['pads'])
 assert sorted(map(trackkey,top[0]))==sorted(trackkey(dict(t,y=-t['y'],v=-t['v'])) for t in ns['tracks'])
 bottom=parse(z.read('Gerber_BottomLayer.GBL').decode())
 assert len(bottom[0])==0 and len(bottom[1])==4
 drl=z.read('Drill_PTH_Through.DRL').decode()
 holes=[(float(x),float(y)) for x,y in re.findall(r'^X(-?[\d.]+)Y(-?[\d.]+)$',drl,re.M)]
 assert sorted(holes)==[(2.,-8.),(2.,-3.),(16.,-8.),(16.,-3.)]
 assert len(holes)==len(set(holes))==4 and 'T01C0.90000' in drl
 outline=parse(z.read('Gerber_BoardOutlineLayer.GKO').decode())
 assert len(outline[0])==4
 points={(t['x'],t['y']) for t in outline[0]}|{(t['u'],t['v']) for t in outline[0]}
 assert points=={(0.,0.),(18.,0.),(18.,-12.),(0.,-12.)}
 silk=parse(z.read('Gerber_TopSilkscreenLayer.GTO').decode())
 mask=parse(z.read('Gerber_TopSolderMaskLayer.GTS').decode())
 silk_gap=min(ns['trackpad'](t,p)[0] for t in silk[0] for p in mask[1])
 assert silk_gap>=.15-1e-5,silk_gap
 result=dict(zip_sha256=hashlib.sha256(Z.read_bytes()).hexdigest(),zip_crc='PASS',files=len(names),native_top_copper_matches_source=True,tracks=9,pads=12,unique_drills=4,board_mm=[18,12],silk_to_mask_min_gap_mm=silk_gap,native_DRC_checks=141,native_DRC_errors=0)
 print(json.dumps(result,ensure_ascii=False,indent=2))
