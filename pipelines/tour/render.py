import bpy, math, json, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'build');os.makedirs(OUT+'/base',exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'Sensor_Mechanism_Panorama.blend'))
s=bpy.context.scene;s.frame_set(1);cam=s.camera
# Freeze the accepted clean introductory geometry; remove editorial overlays and light diagrams only.
for o in s.objects:
 if o.name.startswith('Editorial'):o.animation_data_clear();o.hide_render=True
 if o.type=='CURVE' or o.name.startswith(('Moving light marker','Animated airborne','Scattering particle')):
  o.animation_data_clear();o.hide_render=True
cam.animation_data_clear();cam.data.animation_data_clear();cam.data.shift_x=0;cam.data.shift_y=0;cam.data.ortho_scale=12.8
s.render.resolution_x=960;s.render.resolution_y=640;s.render.resolution_percentage=100;s.display.render_aa='16'
positions={'Laser 1':(-3.08,.35,1.99),'Window 1':(-1.8,-.9,1.65),'Window 2':(1.8,-.8,1.65),'Camera 1':(-2.55,-.43,.84),'Camera 2':(2.85,-.63,1.01),'Laser 2':(3.15,-.45,1.55),'Beam trap':(3.04,.35,2.12),'Air channel':(0,0,2.2)}
codes={'Laser 1':'L1','Laser 2':'L2','Camera 1':'C1','Camera 2':'C2'}
dg=bpy.context.evaluated_depsgraph_get();verts=[];polys=[];owners=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render or o.name.startswith(('Editorial','Animated airborne','Scattering particle','Moving light marker','Studio ground')) or 'pale dust' in o.name or 'sealed reverse-raked optical facet' in o.name:continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();base=len(verts);verts.extend([tuple(o.matrix_world@v.co) for v in me.vertices]);polys.extend([tuple(base+i for i in tr.vertices) for tr in me.loop_triangles]);owners.extend([o.name]*len(me.loop_triangles));eo.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,polys,all_triangles=True,epsilon=.00001)
meta=[]; N=480
preview='--preview' in sys.argv
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
subset=[int(x) for x in args[args.index('--indices')+1:]] if '--indices' in args else None
for i in range(N):
 a=math.atan2(-14,7)+math.tau*i/N;target=Vector((0,0,1.1));cam.location=target+Vector((math.sqrt(245)*math.cos(a),math.sqrt(245)*math.sin(a),7.9));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
 toward=cam.matrix_world.to_quaternion()@Vector((0,0,1));components={}
 for name,p in positions.items():
  uv=world_to_camera_view(s,cam,Vector(p));xy=[uv.x*960,(1-uv.y)*640]
  if name.startswith('Window') or name=='Air channel':visible=bvh.ray_cast(Vector(p)+toward*.0003,toward,100)[0] is None
  else:
   hit=bvh.ray_cast(Vector(p)+toward*30,-toward,30.5)
   owner=owners[hit[2]] if hit[0] is not None else ''
   visible=not owner or (owner.startswith(('Main beam trap','Trap ')) if name=='Beam trap' else owner.startswith(codes[name]+' '))
  components[name]={'xy':xy,'visible':visible}
 meta.append(components)
 if ((subset is None and not preview) or (subset is not None and i in subset) or (preview and i in [0,30,60,90,120,150,180,210])) and not os.path.exists(OUT+'/base/%04d.png'%i):
  s.render.filepath=OUT+'/base/%04d.png'%i;bpy.ops.render.render(write_still=True)
 if i%30==0:print('TOUR_PROGRESS',i,flush=True)
json.dump(meta,open(OUT+'/metadata.json','w'))
