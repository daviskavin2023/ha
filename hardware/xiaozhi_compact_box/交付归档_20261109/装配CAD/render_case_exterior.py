"""Orthographic CPU z-buffer rendering of the delivered CAD meshes."""
from pathlib import Path
import numpy as np
import json,struct
from PIL import Image,ImageDraw,ImageFont
P=Path('/Users/kavin/Desktop/小智小方盒_修复交付_20261109/装配CAD')
report=json.loads((P/'CAD_validation.json').read_text())
def read(name):
    data=(P/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',data,80)[0]
    a=np.array([struct.unpack_from('<12fH',data,84+50*i)[3:12] for i in range(n)],dtype=float).reshape(-1,3,3)
    inv=np.linalg.inv(report['printed_parts'][name]['assembly_to_print'])
    return (np.c_[a.reshape(-1,3),np.ones(n*3)]@inv.T)[:,:3].reshape(-1,3,3)
def cube(b):
    x,y,z,w,h,d=b;p=np.array([[xx,yy,zz] for xx in [x,x+w] for yy in [y,y+h] for zz in [z,z+d]])
    faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]]
    return np.array([p[idx] for a,b,c,d in faces for idx in [[a,b,c],[a,c,d]]])
def cylinder_x(x,y,z,r,h):
    out=[]
    for i in range(48):
        a,b=2*np.pi*i/48,2*np.pi*(i+1)/48
        p=np.array([[x,y+r*np.cos(a),z+r*np.sin(a)],[x,y+r*np.cos(b),z+r*np.sin(b)],
                    [x+h,y+r*np.cos(a),z+r*np.sin(a)],[x+h,y+r*np.cos(b),z+r*np.sin(b)]])
        out.extend([p[[0,1,3]],p[[0,3,2]],np.array([[x,y,z],p[1],p[0]]),np.array([[x+h,y,z],p[2],p[3]])])
    return np.array(out)
scene=[(read('front_shell'),np.array([.80,.84,.89])),(read('rear_shell'),np.array([.83,.86,.91])),
       (read('jack_plate'),np.array([.68,.74,.82])),(cube([12,38,1,36,48,4.5]),np.array([.02,.42,.59])),
       (cylinder_x(58,25,17,3.5,2),np.array([.69,.55,.30])),
       (cylinder_x(60.01,25,17,1.75,.01),np.array([.06,.07,.09]))]
eye=np.array([1,.55,-1.65]);eye/=np.linalg.norm(eye)
right=-np.cross([0,1,0],eye);right/=np.linalg.norm(right)
up=np.cross(right,eye);up/=np.linalg.norm(up)
basis=np.array([right,up,eye]).T
allpts=np.concatenate([a.reshape(-1,3) for a,c in scene]);view=allpts@basis
lo,hi=view[:,:2].min(0),view[:,:2].max(0)
width,height=1200,1300;margin=95
scale=min((width-2*margin)/(hi[0]-lo[0]),(height-220)/(hi[1]-lo[1]))
cx=(width-(hi[0]-lo[0])*scale)/2;cy=135
rgb=np.full((height,width,3),255,dtype=np.uint8);depth=np.full((height,width),-np.inf)
light=np.array([-.5,.8,-1.]);light/=np.linalg.norm(light)
for triangles,color in scene:
    for t in triangles:
        normal=np.cross(t[1]-t[0],t[2]-t[0]);ln=np.linalg.norm(normal)
        if ln<1e-10:continue
        normal/=ln
        if np.dot(normal,eye)<=0:continue
        p=t@basis;p[:,0]=cx+(p[:,0]-lo[0])*scale;p[:,1]=cy+(hi[1]-p[:,1])*scale
        x0,x1=max(0,int(np.floor(p[:,0].min()))),min(width-1,int(np.ceil(p[:,0].max())))
        y0,y1=max(0,int(np.floor(p[:,1].min()))),min(height-1,int(np.ceil(p[:,1].max())))
        if x1<x0 or y1<y0:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
        den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
        if abs(den)<1e-9:continue
        a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
        b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den;c=1-a-b
        z=a*p[0,2]+b*p[1,2]+c*p[2,2]
        target=depth[y0:y1+1,x0:x1+1];mask=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(z>target)
        target[mask]=z[mask]
        brightness=.38+.62*max(0,float(np.dot(normal,light)))
        rgb[y0:y1+1,x0:x1+1][mask]=(np.clip(color*brightness,0,1)*255).astype(np.uint8)
im=Image.fromarray(rgb);draw=ImageDraw.Draw(im)
fp='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
title=ImageFont.truetype(fp,36);note=ImageFont.truetype(fp,20)
draw.text((width/2,48),'60 × 92 × 66 mm 外壳CAD外观',fill='#172033',font=title,anchor='mm')
draw.text((width/2,height-52),'由交付STL网格渲染；颜色和插座外形为示意，未代表实物外观验收。',fill='#334155',font=note,anchor='mm')
im.save(P/'外壳外观.png')
print('PASS: exterior rendered from STL with per-pixel depth test')
