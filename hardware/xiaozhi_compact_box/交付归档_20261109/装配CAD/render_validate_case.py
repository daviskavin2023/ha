from pathlib import Path
import json,struct,collections,itertools,math,runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

P=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109/装配CAD')
report=json.loads((P/'CAD_validation.json').read_text())
params=json.loads((P/'mechanical_parameters.json').read_text())
font=font_manager.FontProperties(fname='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
plt.rcParams['font.family']=font.get_name()
font_manager.fontManager.addfont(font.get_file())
plt.rcParams['axes.unicode_minus']=False

def triangles(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,80)[0]
    assert len(raw)==84+50*n,(path,len(raw),n)
    a=np.empty((n,3,3),dtype=float)
    for i in range(n):a[i]=np.array(struct.unpack_from('<12fH',raw,84+50*i)[3:12]).reshape((3,3))
    return a

mesh_report={};meshes={}
for name,entry in report['printed_parts'].items():
    a=triangles(P/(name+'.stl'));meshes[name]=a
    edges=collections.Counter();degenerate=0
    for tri in a:
        pts=[tuple(round(float(v),5) for v in p) for p in tri]
        if len(set(pts))!=3:
            degenerate+=1;continue
        for i in range(3):edges[tuple(sorted((pts[i],pts[(i+1)%3])))]+=1
    bad={k:v for k,v in edges.items() if v!=2}
    assert not bad,(name,len(bad),list(bad.items())[:3])
    assert degenerate==0,(name,degenerate)
    vol=float(np.sum(np.einsum('ij,ij->i',a[:,0],np.cross(a[:,1],a[:,2])))/6)
    assert vol>0,(name,vol)
    assert abs(vol-entry['volume_mm3'])/entry['volume_mm3']<.003,(name,vol,entry)
    lo,hi=a.reshape((-1,3)).min(0),a.reshape((-1,3)).max(0)
    assert lo[2]>=-1e-5 and lo[2]<.001,(name,lo)
    mesh_report[name]=dict(triangles=len(a),watertight_edges=True,nonmanifold_edges=0,
        degenerate_triangles=0,signed_volume_mm3=vol,
        printed_bbox_mm=(hi-lo).tolist(),bed_z_min_mm=float(lo[2]))
(P/'STL_mesh_validation.json').write_text(json.dumps(mesh_report,ensure_ascii=False,indent=2)+'\n')

labels={'carrier_pcb':'主板','esp32_s3':'ESP32主控','screen_adapter':'屏幕/转接板',
 'radar':'雷达','speaker':'喇叭','dac':'DAC','amp':'功放','microphone':'麦克风',
 'audio_patch':'音频补丁','pj324m':'音频插座','c1':'电容C1'}
colors={'carrier_pcb':'#3d9a78','esp32_s3':'#607d8b','screen_adapter':'#03b7d7',
 'radar':'#ca8368','speaker':'#efb641','dac':'#9a77bf','amp':'#df6f75',
 'microphone':'#65a1b7','audio_patch':'#56b88d','pj324m':'#b8a571','c1':'#54756d'}

fig,axs=plt.subplots(1,2,figsize=(12,9),facecolor='white')
for ax in axs:
    ax.set_aspect('equal');ax.grid(alpha=.12);ax.set_ylim(-5,99);ax.set_ylabel('高度 Y / mm')
axs[0].add_patch(FancyBboxPatch((0,0),60,92,boxstyle='round,pad=0,rounding_size=6',fill=False,lw=2,color='#1f2937'))
axs[0].add_patch(Rectangle((6,12),48,68,fill=False,ls='--',color='#607d8b',lw=1))
for n in ['speaker','radar','screen_adapter','microphone','dac','amp','audio_patch','pj324m','c1']:
    x,y,z,w,h,d=params['modules'][n]['budget']
    axs[0].add_patch(Rectangle((x,y),w,h,facecolor=colors[n],edgecolor=colors[n],alpha=.20))
    axs[0].text(x+w/2,y+h/2,labels[n],ha='center',va='center',fontsize=8,color='#172033')
axs[0].set_xlim(-5,66);axs[0].set_xlabel('宽度 X / mm');axs[0].set_title('正面投影：60 × 92 mm主体',fontsize=13)
axs[0].text(30,-4,'主板48 × 68 mm保持不变',ha='center',fontsize=9)
axs[1].add_patch(Rectangle((0,0),66,92,fill=False,lw=2,color='#1f2937'))
for n in ['carrier_pcb','esp32_s3','screen_adapter','radar','speaker','dac','amp','microphone','audio_patch','c1']:
    x,y,z,w,h,d=params['modules'][n]['budget']
    axs[1].add_patch(Rectangle((z,y),d,h,facecolor=colors[n],edgecolor=colors[n],alpha=.40))
    axs[1].text(z+d/2,y+h/2,labels[n],ha='center',va='center',fontsize=8,color='#172033')
axs[1].axvline(30,lw=1,ls='--',color='#64748b');axs[1].text(30,94,'磁吸分模面',ha='center',fontsize=9)
axs[1].set_xlim(-4,71);axs[1].set_xlabel('深度 Z / mm，左为正面');axs[1].set_title('侧面投影：66 mm深',fontsize=13)
fig.suptitle('小智小方盒：模块包络与分层布局',fontsize=18,x=.5,y=.97)
fig.text(.5,.025,'不同横向位置投影会叠加；干涉以三维布尔/包络检查为准。模块尺寸来自BOM及预留量，未实物测量。',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.09,1,.94));fig.savefig(P/'装配尺寸与分层.png',dpi=180);plt.close(fig)

def cube_faces(b):
    x,y,z,w,h,d=b
    p=np.array(list(itertools.product([x,x+w],[y,y+h],[z,z+d])))
    return [p[idx] for idx in [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]]

fig=plt.figure(figsize=(12,10),facecolor='white');ax=fig.add_subplot(111,projection='3d')
# Plot axes are X, depth Z, vertical Y. Printed meshes are restored from their
# bed-oriented coordinates before applying the explicitly exploded offsets.
for name,a in meshes.items():
    if name=='jack_plate_blank_spare':continue
    inv=np.linalg.inv(np.array(report['printed_parts'][name]['assembly_to_print']))
    flat=np.c_[a.reshape((-1,3)),np.ones(a.shape[0]*3)]@inv.T
    pts=flat[:,:3].reshape((-1,3,3))
    offset=-30 if name in ['front_shell','screen_retainer','jack_plate','speaker_bar_10','speaker_bar_38'] else 30 if name=='rear_shell' else 0
    pts[:,:,2]+=offset
    view=pts[:,:,[0,2,1]]
    col='#e6edf5' if name=='rear_shell' else '#f2e4cf' if name=='front_shell' else '#6cb6aa'
    poly=Poly3DCollection(view,facecolor=col,edgecolor='none',alpha=.24 if name.endswith('shell') else .9)
    ax.add_collection3d(poly)
for n,m in params['modules'].items():
    b=list(m['nominal']);b[2]+= -30 if n in ['screen_adapter','radar','speaker','microphone','pj324m'] else 30 if n in ['carrier_pcb','esp32_s3','c1'] else 0
    faces=[a[:,[0,2,1]] for a in cube_faces(b)]
    ax.add_collection3d(Poly3DCollection(faces,facecolors=colors[n],edgecolors='#334155',linewidths=.3,alpha=.8))
    ax.text(b[0]+b[3]/2,b[2]+b[5]/2,b[1]+b[4]/2,labels[n],fontsize=8,color='#172033')
ax.set_xlim(-2,63);ax.set_ylim(-34,99);ax.set_zlim(-4,96)
ax.set_box_aspect((65,133,100));ax.view_init(elev=23,azim=-54)
ax.set_xlabel('宽度 X / mm');ax.set_ylabel('深度 Z / mm');ax.set_zlabel('高度 Y / mm')
ax.set_title('装配分解预览：前壳 / 托架 / 后壳',fontsize=18,pad=18)
fig.text(.5,.04,'壳体来自实际CAD网格；彩色模块为尺寸占位。前后组各移开30 mm便于观察，不代表实际间隙。',ha='center',fontsize=10)
fig.savefig(P/'装配分解预览.png',dpi=160,bbox_inches='tight');plt.close(fig)

runpy.run_path(str(Path(__file__).with_name('render_case_exterior.py')),run_name='__main__')
print('PASS: all STL edges closed, positive mesh volumes, bed-oriented; 3 previews rendered')
