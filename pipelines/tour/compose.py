import sys
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
O=ROOT/'build';meta=json.load(open(O/'metadata.json'));N=len(meta);names=list(meta[0]);K=len(names)
font=ImageFont.truetype(str(ROOT/'fonts'/'OpenSans-Semibold.ttf'),34)
anchors=np.array([[m[k]['xy'] for k in names] for m in meta])
width=np.array([font.getlength(k)/2 for k in names]);h=22
# A single circular trajectory optimization for all 480 frames. Component-relative
# preferred offsets, gentle spatial repulsion and temporal regularization avoid
# discrete slots, framewise layout decisions, and visibility-induced jumping.
from scipy.optimize import minimize
offsets={'Laser 1':(-35,-43),'Window 1':(-58,-10),'Window 2':(62,-5),
         'Camera 1':(-42,46),'Camera 2':(42,52),'Laser 2':(30,-40),
         'Beam trap':(60,-46),'Air channel':(0,-65)}
target=anchors+np.array([offsets[k] for k in names])[None,:,:]
pairs=[(a,b) for a in range(K) for b in range(a+1,K)]
def objective(flat):
 p=flat.reshape(N,K,2);g=.12*(p-target);loss=.06*np.sum((p-target)**2)
 offset=p-anchors
 v=offset-np.roll(offset,1,axis=0)
 loss+=200*np.sum(v*v);g+=400*(v-np.roll(v,-1,axis=0))
 acc=np.roll(p,1,axis=0)-2*p+np.roll(p,-1,axis=0)
 loss+=2000*np.sum(acc*acc);g+=4000*(np.roll(acc,1,axis=0)-2*acc+np.roll(acc,-1,axis=0))
 for a,b in pairs:
  diff=p[:,a]-p[:,b];ad=np.sqrt(diff*diff+.01)
  penetration=np.array([(width[a]+width[b])/2+13,h+12])-ad
  axis=np.argmin(penetration,axis=1);r=np.arange(N)
  pen=np.maximum(penetration[r,axis],0)
  loss+=25*np.sum(pen*pen)
  force=-50*pen*diff[r,axis]/ad[r,axis]
  g[r,a,axis]+=force;g[r,b,axis]-=force
 # Keep labels within a bounded neighborhood of their own component.
 delta=p-anchors;dist=np.sqrt(np.sum(delta*delta,axis=2)+1e-8)
 excess=np.maximum(dist-112,0)
 loss+=5*np.sum(excess*excess);g+=10*excess[:,:,None]*delta/dist[:,:,None]
 return loss,g.ravel()
result=minimize(objective,target.ravel(),jac=True,method='L-BFGS-B',options={'maxiter':2200,'ftol':1e-10,'maxcor':15})
pos=result.x.reshape(N,K,2)
print('Circular layout:',result.message,flush=True)
vis=np.array([[float(m[k]['visible']) for k in names] for m in meta])
# Circular majority filtering suppresses brief ray-test flicker; a 0.8-second
# symmetric cosine fade keeps occlusion changes soft, including across the seam.
vis=(sum(np.roll(vis,d,axis=0) for d in range(-3,4))>=4).astype(float)
# Hysteresis: ignore visibility excursions shorter than one second. The circular
# run filter handles the loop boundary identically, without end-frame flicker.
for j in range(K):
 for _ in range(4):
  transitions=np.flatnonzero(vis[:,j]!=np.roll(vis[:,j],1))
  if len(transitions)<2:break
  lengths=np.diff(np.r_[transitions,transitions[0]+N])
  short=np.flatnonzero(lengths<15)
  if not len(short):break
  q=short[np.argmin(lengths[short])];start=transitions[q]
  vis[(start+np.arange(lengths[q]))%N,j]=vis[(start-1)%N,j]
w=np.cos(np.linspace(-np.pi/2,np.pi/2,13))**2;w/=w.sum()
alpha=sum(np.roll(vis,d,axis=0)*a for d,a in zip(range(-6,7),w))
# Rare unavoidable trajectory crossings fade the lower-priority label rather
# than making either label jump. Anticipatory circular padding ensures the text
# has disappeared before contact, then restores it with the same cosine fade.
fallback=np.ones((N,K))
for a,b in pairs:
 crossing=(np.abs(pos[:,a,0]-pos[:,b,0])<(width[a]+width[b])/2+4)&(np.abs(pos[:,a,1]-pos[:,b,1])<h+4)&(alpha[:,a]>.1)&(alpha[:,b]>.1)
 expanded=np.maximum.reduce([np.roll(crossing,d) for d in range(-8,9)])
 fallback[:,b]*=1-expanded
fallback=sum(np.roll(fallback,d,axis=0)*a for d,a in zip(range(-6,7),w))
alpha*=fallback
(O/'frames').mkdir(exist_ok=True)
previous=None
if '--reuse-unchanged' in __import__('sys').argv and (O/'layout.json').exists():
 previous=json.load(open(O/'layout.json'))
subset=[int(x) for x in sys.argv[sys.argv.index("--indices")+1:]] if "--indices" in sys.argv else None
if subset is None:
 missing=[i for i in range(N) if not (O/'base'/f'{i:04d}.png').exists()]
 if missing:raise FileNotFoundError(f'Missing base frames: {missing[:5]}; render the full tour first')
for i in range(N):
 if subset is not None and i not in subset:continue
 if '--preview' in __import__('sys').argv and i not in [0,60,120,180,240,300,360,420]:continue
 if previous and (O/'frames'/f'{i:04d}.png').exists() and np.allclose(previous['alpha'][i],alpha[i],atol=1e-10) and np.allclose(previous['positions'][i],pos[i]) and np.allclose(previous['anchors'][i],anchors[i]):continue
 src=O/'base'/f'{i:04d}.png'
 if not src.exists():continue
 im=Image.open(src).convert('RGB').resize((1920,1280));overlay=Image.new('RGBA',im.size);d=ImageDraw.Draw(overlay)
 for j,k in enumerate(names):
  a=alpha[i,j]
  if a<.01:continue
  x,y=pos[i,j];ax,ay=anchors[i,j];ww=width[j]
  ex=min(max(ax,x-ww/2),x+ww/2);ey=min(max(ay,y-h/2),y+h/2)
  d.line([(ax*2,ay*2),(ex*2,ey*2)],fill=(170,192,200,round(150*a)),width=2)
  d.ellipse((ax*2-4,ay*2-4,ax*2+4,ay*2+4),fill=(200,222,226,round(240*a)))
 for j,k in enumerate(names):
  a=alpha[i,j]
  if a<.01:continue
  x,y=pos[i,j];ww=width[j]
  d.text((x*2,y*2),k,font=font,anchor='mm',fill=(230,238,241,round(245*a)),stroke_width=4,stroke_fill=(14,24,31,round(155*a)))
 im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB').resize((960,640),Image.Resampling.LANCZOS);im.save(O/'frames'/f'{i:04d}.png')
layout={'label_names':names,'positions':pos.tolist(),'anchors':anchors.tolist(),'alpha':alpha.tolist(),'dimensions':[960,640],'frames':N,'fps':15,'duration':32,'layout':'smooth component-relative tracking; global circular trajectory optimization; circular occlusion fades'}
json.dump(layout,open(O/'layout.json','w'))
thumb=Image.new('RGB',(1920,640))
for j,i in enumerate([0,60,120,180,240,300,360,420]):
 if j>=9:break
 p=O/'frames'/f'{i:04d}.png'
 if p.exists():thumb.paste(Image.open(p).resize((480,320)),((j%4)*480,(j//4)*320))
thumb.save(O/'preview.jpg',quality=95)
jumps=np.linalg.norm(np.roll(pos,-1,axis=0)-pos,axis=2)
tracking=np.linalg.norm(np.roll(anchors,-1,axis=0)-anchors,axis=2)
qa={'frames':N,'fps':15,'duration_seconds':32,'label_max_frame_jump_px':float(jumps.max()),'leader_anchor_max_frame_step_px':float(tracking.max()),'max_opacity_step':float(np.abs(np.roll(alpha,-1,axis=0)-alpha).max()),'label_overlaps':0,'seam_anchor_max_step_px':float(tracking[-1].max())}
for a in range(K):
 for b in range(a+1,K):
  overlap=(np.abs(pos[:,a,0]-pos[:,b,0])<(width[a]+width[b])/2+4)&(np.abs(pos[:,a,1]-pos[:,b,1])<h+4)&(alpha[:,a]>.1)&(alpha[:,b]>.1)
  qa['label_overlaps']+=int(overlap.sum())
dist=np.linalg.norm(pos-anchors,axis=2)
qa['label_anchor_center_distance_mean_px']=float(dist.mean())
qa['label_anchor_center_distance_max_px']=float(dist.max())
qa['label_max_frame_jump_at_720px']=float(jumps.max()*.75)
qa['seam_label_max_step_px']=float(jumps[-1].max())
qa['label_max_frame_acceleration_px']=float(np.linalg.norm(np.roll(pos,1,axis=0)-2*pos+np.roll(pos,-1,axis=0),axis=2).max())
qa['per_label_travel_extent_px']={k:(pos[:,j].max(axis=0)-pos[:,j].min(axis=0)).tolist() for j,k in enumerate(names)}
qa['minimum_visibility_run_frames']={}
for j,k in enumerate(names):
 t=np.flatnonzero(vis[:,j]!=np.roll(vis[:,j],1))
 qa['minimum_visibility_run_frames'][k]=int(np.diff(np.r_[t,t[0]+N]).min()) if len(t) else N
qa['prior_max_label_frame_jump_px']=51.115998485603455
json.dump(qa,open(O/'validation.json','w'),indent=2)
print(json.dumps(qa,indent=2))
