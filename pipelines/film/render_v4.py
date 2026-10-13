"""Native panorama plus true opaque-geometry visibility masks for projected optical paths.
Orthographic rays are cast toward camera through evaluated solid mesh triangles.
Glass films and enlarged particles are not treated as opaque hardware.
"""
import bpy,os,sys,json,math,time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Sensor_Mechanism_Panorama.blend');s=bpy.context.scene
for o in s.objects:
 if o.name.startswith('Editorial'):o.hide_render=True;o.animation_data_clear()
positions={'L1':(-3.08,.35,1.99),'W1':(-1.8,-.9,1.65),'W2':(1.8,-.8,1.65),'C1':(-2.55,-.43,.84),'C2':(2.85,-.63,1.01),'L2':(3.15,-.45,1.55),'TRAP':(3.04,.35,2.12),'AIR':(0,0,2.2)}
names=['Active L1 illumination','Airborne scatter to C2','W1 footprint scatter to C1','L2 illumination of W2','Separate W2 collection to C2','Selected airborne region -0.55','Selected airborne region 0.55']
paths=[bpy.data.objects[n] for n in names];pulses=[o for o in s.objects if o.name.startswith('Moving light marker')]
# Hardware is static throughout this film; use the evaluated meshes, including modifiers.
s.frame_set(721);dg=bpy.context.evaluated_depsgraph_get();verts=[];polys=[];solidnames=[];owners=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render or o.name.startswith(('Editorial','Animated airborne','Scattering particle','Moving light marker','Studio ground')) or 'pale dust' in o.name or 'sealed reverse-raked optical facet' in o.name:continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();base=len(verts);verts.extend([tuple(o.matrix_world@v.co) for v in me.vertices]);polys.extend([tuple(base+i for i in tr.vertices) for tr in me.loop_triangles]);owners.extend([o.name]*len(me.loop_triangles));solidnames.append(o.name);eo.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,polys,all_triangles=True,epsilon=.00001)
json.dump({'method':'Orthographic camera rays against evaluated opaque hardware triangles; glass films and enlarged illustrative particles excluded. Each visible halo/core is clipped by the ray-tested mask. Hidden guides are dashed and glow-free.','occluders':solidnames,'triangle_count':len(polys)},open(OUT+'/occlusion_method.json','w'),indent=2)
def project(v):
 uv=world_to_camera_view(s,s.camera,Vector(v));return [round(uv.x*1280,4),round((1-uv.y)*720,4)]
def color(o):
 n=o.name
 return ([255,175,88],2) if 'L2' in n or 'W2 collection' in n or n.endswith(('diag','inspect2')) else (([91,255,189],0) if 'L1' in n or n.endswith('main') else ([110,206,255],1))
def blocked(v):return bvh.ray_cast(Vector(v)+toward*.0003,toward,100)[0] is not None
def label_visible(key,p):
 if key in ('W1','W2','AIR'):return not blocked(p)
 hit=bvh.ray_cast(Vector(p)+toward*30,-toward,30.5)
 if hit[0] is None:return True
 owner=owners[hit[2]]
 return owner.startswith(('Main beam trap','Trap ')) if key=='TRAP' else owner.startswith(key+' ')

# Blender's bundled Python has no Pillow; write PNG through Blender image API.
def write_mask(a,path):
 im=bpy.data.images.new('temporary visibility mask',width=1280,height=720,alpha=True)
 rgba=np.ones((720,1280,4),dtype=np.float32);rgba[:,:,:3]=a[::-1]/255
 im.pixels.foreach_set(rgba.ravel());im.filepath_raw=path;im.file_format='PNG';im.save();bpy.data.images.remove(im)
def mask_path(mask,points,channel):
 # 12 px radius includes the full practical soft glow. Footpoint on each
 # source segment supplies actual light depth at every pixel, not a silhouette.
 for a,b in zip(points,points[1:]):
  a=np.array(a);b=np.array(b);pa=np.array(project(a));pb=np.array(project(b));ab=pb-pa;den=float(ab@ab)
  if den<.001:continue
  x0=max(0,int(min(pa[0],pb[0])-13));x1=min(1280,int(max(pa[0],pb[0])+14));y0=max(0,int(min(pa[1],pb[1])-13));y1=min(720,int(max(pa[1],pb[1])+14))
  if x1<=x0 or y1<=y0:continue
  ys,xs=np.mgrid[y0:y1,x0:x1];q=np.stack((xs+.5,ys+.5),-1);t=np.clip(((q-pa)*ab).sum(-1)/den,0,1);foot=pa+t[:,:,None]*ab;offset=q-foot;chosen=(offset**2).sum(-1)<=144
  iy,ix=np.nonzero(chosen);tt=t[iy,ix];off=offset[iy,ix];world=a[None,:]+tt[:,None]*(b-a)[None,:]+off[:,0,None]*right_np[None,:]*pixel_scale-off[:,1,None]*up_np[None,:]*pixel_scale
  for yy,xx,p in zip(iy+y0,ix+x0,world):
   if not blocked(p):mask[yy,xx,channel]=255
os.makedirs(OUT+'/beam_masks',exist_ok=True);os.makedirs(OUT+'/frames24',exist_ok=True)
preview='--preview' in sys.argv
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
subset=[int(x) for x in args[args.index('--indices')+1:]] if '--indices' in args else None
preview=preview or subset is not None
indices=[0,120,240,360,480,600,719,768,1008,1584,2304,2928,3216,3744] if preview else range(4176)
if subset is not None: indices=subset
metadata={} if preview else []
cache={};t0=time.time()
for i in indices:
 s.frame_set(i+1);cam=s.camera;toward=cam.matrix_world.to_quaternion()@Vector((0,0,1));right_np=np.array(cam.matrix_world.to_quaternion()@Vector((1,0,0)));up_np=np.array(cam.matrix_world.to_quaternion()@Vector((0,1,0)));pixel_scale=cam.data.ortho_scale/1280
 # Story anchors must exactly match approved labels; intro label anchors include air channel.
 storypositions={'L1':(-3.08,.35,1.9),'W1':(-1.8,-.9,1.65),'W2':(1.8,-.8,1.65),'C1':(-2.55,-.43,.80),'C2':(2.85,-.63,.9),'L2':(3.15,-.45,1.35),'TRAP':(3.04,.35,1.9)}
 components={k:({'xy':project(p),'visible':label_visible(k,p)} if i<720 else project(p)) for k,p in (positions if i<720 else storypositions).items()}
 active=[o for o in paths if not o.hide_render];key=tuple(round(v,5) for v in list(cam.location)+list(cam.rotation_euler)+[cam.data.ortho_scale])+tuple(o.name for o in active)
 if key in cache:lights0,maskpath=cache[key];lights=[dict(x) for x in lights0]
 else:
  lights=[];mask=np.zeros((720,1280,3),dtype=np.uint8)
  for o in active:
   rgb,ch=color(o);points=[o.matrix_world@Vector(p.co[:3]) for p in o.data.splines[0].points];mask_path(mask,points,ch)
   for a,b in zip(points,points[1:]):
    screen_a=np.array(project(a));screen_b=np.array(project(b));n=max(2,math.ceil(np.linalg.norm(screen_b-screen_a)*2));last=None;run=[]
    for j in range(n+1):
     p=a.lerp(b,j/n);occ=blocked(p);xy=project(p)
     if last is not None and occ!=last:
      run.append(xy);lights.append({'points':[run[0],run[-1]],'color':rgb,'region':'Selected' in o.name,'occluded':last,'mask_channel':ch,'source':o.name});run=[xy]
     else:run.append(xy)
     last=occ
    if len(run)>1:lights.append({'points':[run[0],run[-1]],'color':rgb,'region':'Selected' in o.name,'occluded':last,'mask_channel':ch,'source':o.name})
  maskpath='beam_masks/f%05d.png'%i;write_mask(mask,OUT+'/'+maskpath);cache[key]=(lights,maskpath);lights=[dict(x) for x in lights]
 for o in pulses:
  if not o.hide_render:
   rgb,ch=color(o);p=o.matrix_world.translation;lights.append({'point':project(p),'color':rgb,'occluded':blocked(p),'mask_channel':ch})
 rec={'time':i/24,'components':components,'lights':lights,'light_scale':13.3/cam.data.ortho_scale,'mask_file':maskpath}
 if preview:metadata[str(i)]=rec
 else:metadata.append(rec)
 if i%120==0 or preview:print('MASK_PROGRESS',i,'/4176 elapsed',round(time.time()-t0,1),flush=True)
json.dump(metadata,open(OUT+('/preview_metadata.json' if preview else '/metadata24.json'),'w'))
for o in paths+pulses:
 if o.animation_data:
  for fc in list(o.animation_data.action.fcurves):
   if fc.data_path=='hide_render':o.animation_data.action.fcurves.remove(fc)
 o.hide_render=True
s.display.render_aa='8'
for i in indices:
 dest=OUT+'/frames24/f%05d.png'%i
 if not os.path.exists(dest):
  s.frame_set(i+1);s.render.filepath=dest;bpy.ops.render.render(write_still=True)
 if i%120==0 or preview:print('RENDER_PROGRESS',i,'/4176 elapsed',round(time.time()-t0,1),flush=True)
print('RENDER_COMPLETE',round(time.time()-t0,1),flush=True)
