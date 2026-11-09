"""Parametric mechanical prototype; input budgets are not measured components."""
from pathlib import Path
import json,math,itertools,struct,collections,hashlib
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax1,gp_Ax2,gp_Vec,gp_Trsf
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge,BRepBuilderAPI_MakeWire,BRepBuilderAPI_MakeFace,BRepBuilderAPI_Transform
from OCP.GC import GC_MakeArcOfCircle
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.STEPControl import STEPControl_Writer,STEPControl_Reader,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

OUT=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109/装配CAD')
OUT.mkdir(exist_ok=True)
W,H,D=60.,92.,66.
WALL,SPLIT=2.,30.
PCB_X,PCB_Y=6.,12.
PCB_FRONT,PCB_BACK=59.4,61.
MAGNETS=[(4.3,4.3),(W-4.3,4.3),(4.3,H-4.3),(W-4.3,H-4.3)]
PCB_HOLES=[(PCB_X+x,PCB_Y+68-y) for x,y in [(3,3),(45,3),(3,65),(45,65)]]
TRAY_HOLES=[(8,60),(52,60),(8,80),(52,80),(30,28)]
SCREEN_HOLES=[(9.5,36),(50.5,36),(9.5,88),(50.5,88)]

def box(x,y,z,dx,dy,dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()
def cyl(x,y,z,r,h,axis=(0,0,1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()
def fuse(a,b):
    op=BRepAlgoAPI_Fuse(a,b);op.Build();assert op.IsDone();return op.Shape()
def cut(a,b):
    op=BRepAlgoAPI_Cut(a,b);op.Build();assert op.IsDone();return op.Shape()
def rr(x,y,z,w,h,d,r):
    wire=BRepBuilderAPI_MakeWire()
    p=[(x+r,y),(x+w-r,y),(x+w,y+r),(x+w,y+h-r),
       (x+w-r,y+h),(x+r,y+h),(x,y+h-r),(x,y+r)]
    mids=[(x+w-r+r/math.sqrt(2),y+r-r/math.sqrt(2)),
          (x+w-r+r/math.sqrt(2),y+h-r+r/math.sqrt(2)),
          (x+r-r/math.sqrt(2),y+h-r+r/math.sqrt(2)),
          (x+r-r/math.sqrt(2),y+r-r/math.sqrt(2))]
    def point(t):return gp_Pnt(t[0],t[1],z)
    for i in range(8):
        a,b=p[i],p[(i+1)%8]
        edge=BRepBuilderAPI_MakeEdge(point(a),point(b)) if i%2==0 else BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(point(a),point(mids[i//2]),point(b)).Value())
        wire.Add(edge.Edge())
    face=BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    return BRepPrimAPI_MakePrism(face,gp_Vec(0,0,d)).Shape()
def compound(shapes):
    b=BRep_Builder();c=TopoDS_Compound();b.MakeCompound(c)
    for s in shapes:b.Add(c,s)
    return c
def volume(s):
    p=GProp_GProps();BRepGProp.VolumeProperties_s(s,p);return p.Mass()
def solid_count(s):
    e=TopExp_Explorer(s,TopAbs_SOLID);n=0
    while e.More():n+=1;e.Next()
    return n
def overlap(a,b):
    op=BRepAlgoAPI_Common(a,b);op.Build();assert op.IsDone();return max(0,volume(op.Shape()))

# Nominal dimensions transcribed from the previous BOM. Larger boxes explicitly
# budget connector/lead space; missing manufacturer drawings remain assumptions.
modules={
 'carrier_pcb':dict(nominal=[6,12,59.4,48,68,1.6],budget=[6,12,59.4,48,68,1.6],source='source PCB outline and mounting-hole coordinates'),
 'esp32_s3':dict(nominal=[16.2,11.635,47.4,28,63.39,3.5],budget=[13.5,10.5,46.4,32,66,4.5],source='old BOM; includes either ESP rail spacing, exact board unmeasured'),
 'screen_adapter':dict(nominal=[12,38,1,36,48,4.5],budget=[9,36,1,42,52,12.5],source='old BOM + user TK020F1131_PB rear image; connector depth budget, not measured'),
 'radar':dict(nominal=[19,8,2.5,22,16,4],budget=[18,7,1.5,24,18,6],source='old BOM LD2410C-P; rotated in plane to face front below display'),
 'speaker':dict(nominal=[10,3,10,40,11.5,28],budget=[9,2,9,42,13.5,30],source='old BOM 2840; downward outlet, foam clearance included'),
 'dac':dict(nominal=[22,38,17,32,18,8],budget=[20,36,16,36,22,12],source='old BOM PCM5102A 32x18; height/connector allowance is design budget'),
 'amp':dict(nominal=[22.4,20,32,24,15,8],budget=[20.4,18,31.5,28,19,12],source='old BOM PAM8302A 24x15; height/connector allowance is design budget'),
 'microphone':dict(nominal=[5,22,18,10,16,18],budget=[3.5,20,16,14,20,22],source='no verified module outline; reserved 22x20x14 envelope for pre-soldered header and leads'),
 'audio_patch':dict(nominal=[21,67,22,18,12,3],budget=[19,65,16,22,16,9],source='actual PATCH-A01 source PCB 18x12; solder/wire allowance'),
 'pj324m':dict(nominal=[42,20,12,16,10,10],budget=[38,18,9,20,16,16],source='unverified purchased jack; universal bay and blank adapter plate'),
 'c1':dict(nominal=[5.5,22.5,45.9,5,5,11],budget=[4.5,21.5,44.9,7,7,13],source='old BOM diameter5 x11; moved off carrier with short leads at radar 5V/GND'),
}

conflicts=[];gaps=[]
for (an,a),(bn,b) in itertools.combinations(modules.items(),2):
    aa,bb=a['budget'],b['budget']
    span=[min(aa[i]+aa[i+3],bb[i]+bb[i+3])-max(aa[i],bb[i]) for i in range(3)]
    if all(x>1e-7 for x in span):conflicts.append((an,bn,span))
    else:gaps.append((math.sqrt(sum(max(0,-x)**2 for x in span)),an,bn))
assert not conflicts,conflicts

front=cut(rr(0,0,0,W,H,SPLIT,6),rr(2,2,2,W-4,H-4,SPLIT+1,4))
rear=cut(rr(0,0,SPLIT,W,H,D-SPLIT,6),rr(2,2,SPLIT-.1,W-4,H-4,D-SPLIT-1.9,4))
# Adhesive/screw-retained screen seat: 1mm front lip, larger rear recess.
front=cut(front,rr(12.9,38.9,-.1,34.2,46.2,2.3,6.1))
front=cut(front,rr(11.8,37.8,1,36.4,48.4,1.2,7.2))
# Thin plastic radar radome; no LCD or metal in front of it.
front=cut(front,rr(18,7,1.2,24,18,1,2))
# Alignment tongue. 0.30mm radial clearance to the rear cavity.
base=cut(rr(1.8,1.8,28.5,W-3.6,H-3.6,1.5,4.2),rr(3.3,3.3,28.4,W-6.6,H-6.6,1.8,2.7))
tongue=cut(rr(2.3,2.3,30,W-4.6,H-4.6,2,3.7),rr(3.3,3.3,29.9,W-6.6,H-6.6,2.2,2.7))
front=fuse(fuse(front,base),tongue)
for x,y in MAGNETS:
    front=fuse(front,cyl(x,y,26,3.1,4))
    front=cut(front,cyl(x,y,27.8,2.1,2.3))
    rear=fuse(rear,cyl(x,y,30,3.1,4))
    rear=cut(rear,cyl(x,y,29.9,2.1,2.3))
for x,y in MAGNETS:
    front=cut(front,cyl(x,y,30,3.5,2.2))
for x,y in PCB_HOLES:
    rear=fuse(rear,cyl(x,y,61,2.5,3.1))
    rear=cut(rear,cyl(x,y,60.9,.8,2.6))

# Front-side tray supports; the center support occupies the gap below the screen.
for x,y in TRAY_HOLES:
    if (x,y)==(30,28):
        front=fuse(front,cyl(x,y,1.9,3,26.1))
        front=cut(front,cyl(x,y,23.6,.8,4.5))
    else:
        front=fuse(front,box(1.8 if x<30 else x,y-3,23,6.2,6,5))
        front=fuse(front,cyl(x,y,23,3,5))
        front=cut(front,cyl(x,y,23.6,.8,4.5))
for x,y in SCREEN_HOLES:
    front=fuse(front,cyl(x,y,1.9,2.5,3.6))
    front=cut(front,cyl(x,y,2.6,.8,3))

# Downward sound grille, 4-point removable speaker clamps, and 2mm external feet.
for x in range(14,49,4):
    for z in [14,20,26,32]:front=cut(front,box(x-1.2,-.1,z-1.2,2.4,2.3,2.4))
for x in [7,53]:
    front=fuse(front,box(x-2,1.8,8,4,8.2,20))
    front=fuse(front,box(x-2,8,28,4,2,12))
    for z in [10,38]:
        # Both clamps travel with the front. Raised rear rails clear the rear
        # corner magnet bosses, so the speaker cannot lock the halves together.
        front=fuse(front,cyl(x,8,z,2,6.5,axis=(0,1,0)))
        front=cut(front,cyl(x,9,z,.8,6,axis=(0,1,0)))
for x in [5.5,54.5]:
    front=fuse(front,cyl(x,-2,5.5,4,2.2,axis=(0,1,0)))
    rear=fuse(rear,cyl(x,-2,D-5.5,4,2.2,axis=(0,1,0)))

# Side microphone support: universal envelope instead of invented module holes.
mic_frame=fuse(box(2.4,18.5,16,16.5,1.5,22),box(2.4,40,16,16.5,1.5,22))
mic_frame=fuse(mic_frame,box(17.7,18.5,16,1.2,23,22))
mic_frame=fuse(mic_frame,box(1.8,18.5,16,1.2,23,12))
front=fuse(front,mic_frame)
for y in [27,30,33]:
    for z in [24,27,30]:front=cut(front,cyl(-.1,y,z,.7,2.3,axis=(1,0,0)))

# Replaceable jack plate. Blank center avoids guessing the purchased thread size.
front=cut(front,box(57.9,16,8,2.3,18,18))
front=cut(front,box(59,11.9,3.9,1.2,26.2,26.2))
for y,z in itertools.product([14,36],[6,28]):
    front=fuse(front,cyl(55,y,z,2.8,3.2,axis=(1,0,0)))
    front=cut(front,cyl(54.9,y,z,.8,5.3,axis=(1,0,0)))
jack_plate=fuse(box(59,12.1,4.1,1,25.8,25.8),box(58,16.2,8.2,1.1,17.6,17.6))
for y,z in itertools.product([14,36],[6,28]):
    jack_plate=cut(jack_plate,cyl(57.9,y,z,1.1,2.3,axis=(1,0,0)))
jack_plate_blank=jack_plate
jack_plate=cut(jack_plate,cyl(57.9,25,17,6,2.3,axis=(1,0,0)))
# Universal internal jack cradle: the body is retained by two small straps,
# so the access hole does not pretend to match an unmeasured screw thread.
jack_cradle=fuse(box(38,17,8,19.8,18,1),box(38,17,9,19.8,1.5,16.5))
jack_cradle=fuse(jack_cradle,box(38,34.5,9,20.2,1.5,16.5))
jack_cradle=fuse(jack_cradle,box(37,17,8,1.1,19,17.5))
for x in [43,53]:
    for y in [18.5,32]:jack_cradle=cut(jack_cradle,box(x-.8,y,7.9,1.6,2.5,1.3))
front=fuse(front,jack_cradle)
front=cut(front,box(57.7,10,30,2.4,30,1))

# Rear cable gland and tie points: power and 3-wire UART exit independently of
# the unknown development-board USB-connector positions.
rear=cut(rear,rr(22,3,63.9,16,9,2.3,2))
for x in [19,41]:rear=cut(rear,box(x-1,3.5,63.9,2,6,2.3))
# C1 open cradle attached to rear left wall; strap retention, no forced snap fit.
cradle=cut(cyl(8,25,45.9,3.9,11.5),cyl(8,25,45.8,2.7,11.7))
cradle=cut(cradle,box(8,20.8,45.8,4.2,8.4,11.7))
cradle=fuse(cradle,box(1.8,23.5,45.9,3.3,3,11.5))
rear=fuse(rear,cradle)
rear=cut(rear,box(2.3,22.6,50,3.2,1.2,2))
rear=cut(rear,box(2.3,26.2,55,3.2,1.2,2))
# The speaker crosses the split: interrupt only the inner bottom tongue rather
# than forcing its housing into the 1mm alignment rim. Re-open magnet pockets
# after adding the front speaker-support anchors.
front=cut(front,box(8.5,2,28.4,43,1.6,3.8))
for x,y in MAGNETS:front=cut(front,cyl(x,y,27.8,2.1,2.3))

tray=rr(4,16,28,52,71,2,2)
tray=cut(tray,box(3.9,18,27.9,16,24,2.2))
tray=cut(tray,box(54.5,11,27.9,1.6,28.3,2.2))
for x,y in MAGNETS[2:]:tray=cut(tray,cyl(x,y,27.9,3.5,2.2))
for x,y in TRAY_HOLES:tray=cut(tray,cyl(x,y,27.9,1.1,2.2))
for x,y in [(12,37),(52,37),(12,50),(52,50),(17,22),(47,22),(17,32),(47,32),(18,68),(42,68),(18,77),(42,77)]:
    tray=cut(tray,box(x-.8,y-1.7,27.9,1.6,3.4,2.2))
# Separate flat-printable spacer pads avoid supports on a two-sided tray.
spacers={'amp_spacer':box(22.4,20,30,24,15,1.5),
         'patch_spacer':box(21,67,25,18,12,3),
         'dac_spacer':box(22,38,25,32,18,3)}
spacers['amp_spacer']=cut(spacers['amp_spacer'],cyl(30,28,29.9,2.2,1.7))

screen_retainer=cut(rr(7,34,5.5,46,56,2,2),rr(13,39,5.4,34,46,2.2,4))
screen_retainer=cut(screen_retainer,box(46,40,5.4,7.2,41,2.2))
for x,y in SCREEN_HOLES:screen_retainer=cut(screen_retainer,cyl(x,y,5.4,1.1,2.2))
speaker_bars={}
for z in [10,38]:
    bar=box(5,14.5,z-1.5,50,2,3)
    for x in [7,53]:bar=cut(bar,cyl(x,14.4,z,1.1,2.2,axis=(0,1,0)))
    speaker_bars[f'speaker_bar_{int(z)}']=bar

carrier=rr(6,12,59.4,48,68,1.6,3)
for x,y in PCB_HOLES:carrier=cut(carrier,cyl(x,y,59.3,1.1,1.8))
parts={'front_shell':front,'rear_shell':rear,'module_tray':tray,
       'screen_retainer':screen_retainer,'jack_plate':jack_plate,**speaker_bars,**spacers}
nominal={n:box(*m['nominal']) for n,m in modules.items()}
nominal['carrier_pcb']=carrier
nominal['screen_adapter']=rr(12,38,1,36,48,4.5,7)
nominal['c1']=cyl(8,25,45.9,2.5,11)
nominal['pj324m']=fuse(nominal['pj324m'],cyl(58,25,17,3.5,2,axis=(1,0,0)))
nominal['esp_socket_left']=box(16.23,15.39,50.9,2.54,55.88,8.5)
nominal['esp_socket_right_25p4']=box(41.63,15.39,50.9,2.54,55.88,8.5)
nominal['R1']=cyl(30.85,67,58.15,1.25,6.3,axis=(1,0,0))
nominal['R2']=cyl(30.85,63,58.15,1.25,6.3,axis=(1,0,0))
padfile=OUT.parent/'底板引脚数据.json'
padgroups=collections.defaultdict(list)
for pad in json.loads(padfile.read_text()):
    ref=pad['ref']
    if ref.startswith('J_') and not ref.startswith('J_ESP'):
        padgroups[ref].append((PCB_X+pad['x'],PCB_Y+68-pad['y']))
for ref,points in padgroups.items():
    x0,x1=min(x for x,y in points),max(x for x,y in points)
    y0,y1=min(y for x,y in points),max(y for x,y in points)
    nominal['pigtail_'+ref]=box(x0-1.5,y0-1.5,56.4,x1-x0+3,y1-y0+3,3)
for i,(x,y) in enumerate(MAGNETS,1):
    nominal[f'magnet_front_{i}']=cyl(x,y,27.8,2,2)
    nominal[f'magnet_rear_{i}']=cyl(x,y,30.2,2,2)

component_material_conflicts=[]
for mn,model in nominal.items():
    for pn,plastic in parts.items():
        v=overlap(model,plastic)
        if v>1e-5:component_material_conflicts.append(dict(module=mn,part=pn,volume_mm3=v))
assert not component_material_conflicts,component_material_conflicts

hardware={};heads={};fastener_specs=[]
for i,(x,y) in enumerate(PCB_HOLES,1):
    head=cyl(x,y,57.9,2,1.5);heads[f'pcb_M2x4_{i}']=head
    hardware[f'pcb_M2x4_{i}']=fuse(head,cyl(x,y,59.4,1,4))
for i,(x,y) in enumerate(TRAY_HOLES,1):
    head=cyl(x,y,30,2,1.5);heads[f'tray_M2x6_{i}']=head
    hardware[f'tray_M2x6_{i}']=fuse(head,cyl(x,y,24,1,6))
for i,(x,y) in enumerate(SCREEN_HOLES,1):
    head=cyl(x,y,7.5,2,1.5);heads[f'screen_M2x4_{i}']=head
    hardware[f'screen_M2x4_{i}']=fuse(head,cyl(x,y,3.5,1,4))
for i,(x,z) in enumerate(itertools.product([7,53],[10,38]),1):
    head=cyl(x,16.5,z,2,1.5,axis=(0,1,0));heads[f'speaker_M2x6_{i}']=head
    hardware[f'speaker_M2x6_{i}']=fuse(head,cyl(x,10.5,z,1,6,axis=(0,1,0)))
for i,(y,z) in enumerate(itertools.product([14,36],[6,28]),1):
    head=cyl(60,y,z,2,1.5,axis=(1,0,0));heads[f'plate_M2x4_{i}']=head
    hardware[f'plate_M2x4_{i}']=fuse(head,cyl(56,y,z,1,4,axis=(1,0,0)))
head_conflicts=[]
for hn,head in heads.items():
    for mn,model in nominal.items():
        if overlap(head,model)>1e-5:head_conflicts.append((hn,mn))
assert not head_conflicts,head_conflicts

# The primary mechanical criterion: printable parts must be proper solids,
# and removable parts must not occupy material inside another printed part.
print_conflicts=[]
for (an,a),(bn,b) in itertools.combinations(parts.items(),2):
    v=overlap(a,b)
    if v>1e-5:
        common=BRepAlgoAPI_Common(a,b).Shape();bb=Bnd_Box();BRepBndLib.Add_s(common,bb)
        lo,hi=bb.CornerMin(),bb.CornerMax()
        print_conflicts.append(dict(a=an,b=bn,volume_mm3=v,bounds=[lo.X(),lo.Y(),lo.Z(),hi.X(),hi.Y(),hi.Z()]))
assert not print_conflicts,print_conflicts

opening_checks=[]
front_group=compound([s for n,s in parts.items() if n!='rear_shell'])
for distance in [1,2,5,10,20]:
    move=gp_Trsf();move.SetTranslation(gp_Vec(0,0,-distance))
    shifted=BRepBuilderAPI_Transform(front_group,move,True).Shape()
    v=overlap(shifted,rear)
    opening_checks.append(dict(front_shift_z_mm=-distance,printed_intersection_mm3=v))
assert all(x['printed_intersection_mm3']<1e-5 for x in opening_checks),opening_checks

def export(name,s,stl=True):
    assert BRepCheck_Analyzer(s).IsValid(),name
    assert solid_count(s)==1,(name,solid_count(s))
    vol=volume(s);assert vol>0,name
    step=OUT/(name+'.step')
    writer=STEPControl_Writer();assert writer.Transfer(s,STEPControl_AsIs)==IFSelect_RetDone
    assert writer.Write(str(step))==IFSelect_RetDone
    reader=STEPControl_Reader();assert reader.ReadFile(str(step))==IFSelect_RetDone
    reader.TransferRoots();read=reader.OneShape()
    assert BRepCheck_Analyzer(read).IsValid()
    assert abs(volume(read)-vol)<max(.001,vol*1e-7)
    if stl:
        rotation=gp_Trsf()
        if name=='rear_shell':rotation.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),math.pi)
        elif name.startswith('jack_plate'):rotation.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,1,0)),-math.pi/2)
        elif name.startswith('speaker_bar'):rotation.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(1,0,0)),math.pi/2)
        oriented=BRepBuilderAPI_Transform(s,rotation,True).Shape()
        bounds=Bnd_Box();BRepBndLib.Add_s(oriented,bounds);lo=bounds.CornerMin()
        move=gp_Trsf();move.SetTranslation(gp_Vec(-lo.X(),-lo.Y(),-lo.Z()))
        orient=BRepBuilderAPI_Transform(oriented,move,True).Shape()
        rotation.PreMultiply(move)
        BRepMesh_IncrementalMesh(orient,.08,False,.15,True).Perform()
        writer=StlAPI_Writer();writer.ASCIIMode=False
        assert writer.Write(orient,str(OUT/(name+'.stl')))
        matrix=[[rotation.Value(i,j) for j in range(1,5)] for i in range(1,4)]+[[0,0,0,1]]
    return dict(volume_mm3=vol,valid_BRep=True,solids=1,step_roundtrip=True,assembly_to_print=matrix)

reports={n:export(n,s) for n,s in parts.items()}
reports['jack_plate_blank_spare']=export('jack_plate_blank_spare',jack_plate_blank)
gauge=rr(8,34,0,44,56,2,3)
gauge=cut(gauge,rr(12.9,38.9,-.1,34.2,46.2,2.3,6.1))
gauge=cut(gauge,rr(11.8,37.8,1,36.4,48.4,1.2,7.2))
reports['screen_fit_gauge']=export('screen_fit_gauge',gauge)
writer=STEPControl_Writer()
for n,s in {**parts,**nominal,**hardware}.items():assert writer.Transfer(s,STEPControl_AsIs)==IFSelect_RetDone
assert writer.Write(str(OUT/'assembly_with_nominal_modules.step'))==IFSelect_RetDone

# Source-derived solder tails and actual plug heights are not falsely modeled
# as exact hardware: reserve a common connector zone behind the removable tray.
params=dict(outer_body_mm=[W,H,D],internal_mm=[W-4,H-4,D-4],wall_mm=2,
 pcb_mm=[48,68,1.6],pcb_origin_xy=[6,12],pcb_front_z=59.4,pcb_back_z=61,
 pcb_standoff_mm=3,pcb_mount_centers_xy=PCB_HOLES,tray_mount_centers_xy=TRAY_HOLES,
 seam_tongue_radial_gap_mm=.3,magnet_pocket_diameter_mm=4.2,
 magnet_pocket_depth_mm=2.2,nominal_magnets_mm=[4,2],foot_height_mm=2,
 speaker_nominal_depth_to_core_budget_gap_mm=46.4-38,
 speaker_budget_to_core_budget_gap_mm=46.4-39,
 amp_budget_to_core_budget_gap_mm=46.4-43.5,
 body_sizes_are_unmeasured_BOM_inputs=True,jack_access_hole_mm=12,
 jack_retention='universal internal cradle with straps; not threaded panel hole',
 screw_reference={'head_diameter_mm':4,'head_height_mm':1.5,'M2x4_qty':12,'M2x6_qty':9,'pilot_mm':1.6},
 carrier_connection_policy='only ESP rows use 8.5mm sockets; all other carrier ends are insulated solder pigtails <=3mm; inline connectors at module side',
 C1_connection='off-board at rear left cradle; short 5V/GND branch from J_RADAR pins 1/2; original C1 footprint not populated',
 modules=modules)
(OUT/'mechanical_parameters.json').write_text(json.dumps(params,ensure_ascii=False,indent=2)+'\n')
(OUT/'CAD_validation.json').write_text(json.dumps(dict(printed_parts=reports,
 module_budget_pair_intersections=conflicts,printed_part_intersections=print_conflicts,
 nominal_module_to_printed_material_intersections=component_material_conflicts,
 screw_head_to_nominal_component_intersections=head_conflicts,
 printed_front_opening_translation_checks=opening_checks,
 minimum_module_budget_distance_mm=min(gaps),physical_test=False,
 RF_antenna_position_not_measured=True,
 carrier_pad_table_sha256=hashlib.sha256(padfile.read_bytes()).hexdigest(),
 generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
print('CAD export finished:',OUT)
