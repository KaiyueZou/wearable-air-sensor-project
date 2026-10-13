import bpy,os,sys,math,json
from mathutils import Vector
D=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,D)
from watch_helpers import *
SRC=D+'/Accepted_Sensor_Source.blend'
bpy.ops.wm.open_mainfile(filepath=SRC);s=bpy.context.scene;s.frame_set(821)
keep=[]
for o in list(s.objects):
 cs=[c.name for c in o.users_collection]
 hardware=any(c.startswith(('10 •','20 •')) for c in cs)
 dynamic=o.name.startswith(('Active L1','Airborne scatter','W1 footprint','L2 illumination','Separate W2','Selected airborne','Animated airborne','Scattering particle','Moving light marker'))
 if hardware or dynamic:
  o.animation_data_clear();o.hide_viewport=False;keep.append(o)
 else:bpy.data.objects.remove(o,do_unlink=True)
for ma in bpy.data.materials:
 ma.animation_data_clear()
 if ma.node_tree:ma.node_tree.animation_data_clear()
rig=bpy.data.objects.new('Accepted sensor assembly | unchanged local geometry',None);s.collection.objects.link(rig);rig.location=(0,2.13,.20);rig.rotation_euler.z=math.pi;rig.scale=(.285,)*3
for o in keep:o.parent=rig
# Finish materials and precision case.
silver=mat('Watch | satin platinum titanium',(.52,.57,.59),.82,.25)
polish=mat('Watch | polished perimeter',(.68,.72,.73),.88,.18)
strap=mat('Watch | charcoal fluoroelastomer',(.028,.038,.047),0,.58)
ribs=mat('Watch | soft strap detailing',(.043,.055,.066),0,.6)
black=mat('Watch | display edge',(.008,.012,.018),.2,.27)
glass=mat('Watch | black display glass',(.009,.022,.031),.32,.16)
white=mat('Watch | warm white markings',(.84,.89,.9),.25,.3)
mute=mat('Watch | dial fine marks',(.22,.32,.37),.3,.38)
accent=mat('Watch | seconds hand pale mint',(.30,.78,.67),.3,.27)
body=roundedbox('Watch | sculpted case',(0,0,.48),(4.5,5.5,.94),silver,.65,.08)
bezel=ring('Watch | precision bezel',4.42,5.42,.56,4.04,5.02,.45,.85,1.02,polish)
# Pocket physically removes body under module, preserving an unobstructed channel.
cut=box('Temporary module bay cutter',(0,2.25,.72),(2.35,1.50,1.24),silver,.025)
for obj in [body,bezel]:
 mod=obj.modifiers.new('Integrated 12 oclock module pocket','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
 bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cut,do_unlink=True)
roundedbox('Watch | ceramic display surround',(0,-.54,1.006),(4.01,3.96,.095),black,.48,.028)
roundedbox('Watch | curved display',(0,-.54,1.056),(3.83,3.78,.10),glass,.43,.025)
# Restrained analog face.
for i in range(60):
 a=i*math.tau/60;r=1.48 if i%5==0 else 1.51
 o=box('Watch | minute index %02d'%i,(r*math.sin(a),-.54+r*math.cos(a),1.116),(.042 if i%5==0 else .014,.16 if i%5==0 else .065,.012),white if i%5==0 else mute,.006);o.rotation_euler.z=-a
for name,angle,length,width,z in [('hour',-math.radians(55),.95,.105,1.139),('minute',math.radians(54),1.26,.072,1.157)]:
 o=box('Watch | '+name+' hand',(math.sin(angle)*length*.42,-.54+math.cos(angle)*length*.42,z),(width,length,.02),white,.035);o.rotation_euler.z=-angle
cylinder('Watch | central pin',(0,-.54,1.181),.09,.027,polish)
a=math.radians(165);o=box('Watch | seconds hand',(math.sin(a)*.50,-.54+math.cos(a)*.50,1.188),(.022,1.7,.012),accent,.008);o.rotation_euler.z=-a
text('Watch | dial signature','A I R',(0,-1.37,1.118),.15,mute)
# Strap sits lower than exposed air-channel mouth.
for side in [-1,1]:
 y=side*4.87
 box('Watch | formed strap '+str(side),(0,y,.28),(2.78,5.25,.40),strap,.28)
 box('Watch | integrated band connector '+str(side),(0,side*2.82,.32),(3.12,.61,.52),strap,.16)
 for i in range(17):
  yy=side*(3.4+i*.22)
  box('Watch | transverse band detail',(0,yy,.487),(2.48,.020,.014),ribs,.009)
 if side==-1:
  for i in range(5):box('Watch | adjustment inset',(0,-4.25-i*.48,.498),(.27,.24,.014),black,.09)
# Crown and side button.
cylinder('Watch | tactile crown',(2.39,.20,.49),.32,.31,polish,(0,math.pi/2,0))
cylinder('Watch | crown face',(2.557,.20,.49),.25,.015,silver,(0,math.pi/2,0))
for i in range(36):
 a=i*math.tau/36;o=cylinder('Watch | crown knurl',(2.39,.20+.309*math.cos(a),.49+.309*math.sin(a)),.011,.27,silver,(0,math.pi/2,0))
box('Watch | side control',(2.245,-.81,.48),(.14,.69,.25),silver,.08)
# An illustrative local cutaway: stationary dry-compartment cover becomes transparent.
cover=mat('Watch | local cutaway cover',(.52,.57,.59),.82,.25);cover.surface_render_method='DITHERED'
for x in [-.82,.82]:
 box('Watch | dry optical bay cover',(x,2.13,.947),(.68,1.10,.12),cover,.045)
 box('Watch | sectioned bay front wall',(x,2.663,.60),(.68,.075,.67),cover,.02)
# Ambient-channel end opening is left free; no cap over sample air.
# Studio: shared blue-black language with accepted sensor rendering.
floor=mat('Studio | deep blue gray',(.018,.028,.039),.05,.65)
box('Studio ground',(0,0,-.16),(200,200,.10),floor,0)
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.15,.20,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.42
light('Key softbox',(-5,1,10),1500,7,(.82,.91,1))
light('Warm edge softbox',(6,5,6),1300,6,(1,.85,.68))
light('Long cool fill',(-2,-7,5),1000,6,(.45,.72,1))
light('Front reflection',(0,9,7),900,5,(1,1,1))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Watch to embedded sensor camera';s.camera=cam;cam.data.type='ORTHO';cam.data.clip_start=.01;cam.data.clip_end=300
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=12;s.cycles.samples=48;s.cycles.use_denoising=False;s.cycles.max_bounces=5;s.cycles.transparent_max_bounces=5
s.render.resolution_x=960;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=16;s.frame_start=1;s.frame_end=320
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.film_transparent=False
# Native geometry is rendered with true depth; light curves cannot shine through solids.
paths=[o for o in keep if o.name.startswith(('Active L1','Airborne scatter','W1 footprint','L2 illumination','Separate W2','Selected airborne'))]
markers=[o for o in keep if o.name.startswith('Moving light marker')]
for o in markers:o.hide_render=True
for o in paths:
 o.hide_render=False
 if o.type=='CURVE':o.data.bevel_depth=.018 if 'Selected' not in o.name else .006
for o in keep:
 if o.name.startswith('Animated airborne'):o.hide_render=False
# Cues: 0-2 exterior; 2-7 approach; 7-8 local reveal; 8-15 optical cycle; 15-19 return; 19-20 exterior.
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
start_target=Vector((0,0,.48));end_target=Vector((0,2.10,.61));start_delta=Vector((9,-12,15));end_delta=Vector((1.3,4.9,5.1))
for f in range(1,321):
 t=(f-1)/16
 zoom=smooth((t-2)/5) if t<15 else 1-smooth((t-15)/4)
 target=start_target.lerp(end_target,zoom);cam.location=target+start_delta.lerp(end_delta,zoom);look(cam,target);cam.data.ortho_scale=15.8*(1-zoom)+3.75*zoom
 cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f);cam.data.keyframe_insert('ortho_scale',frame=f)
 reveal=smooth((t-6.5)/1.3)*(1-smooth((t-15)/.9));alpha=1-reveal;cover.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=alpha;cover.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].keyframe_insert('default_value',frame=f)
 for o in paths:
  name=o.name
  on=(8<=t<11.0 and name.startswith(('Active L1','Airborne scatter','Selected airborne'))) or (11<=t<12.7 and name.startswith(('Active L1','W1 footprint'))) or (12.7<=t<15 and name.startswith(('L2 illumination','Separate W2')))
  o.hide_render=not on;o.keyframe_insert('hide_render',frame=f)
 for i,o in enumerate([o for o in keep if o.name.startswith('Animated airborne')]):
  # Source particle model retained, with slow ambient motion confined to its channel.
  o.location.y=-1.25+((i*.19+t*.20)%2.5);o.keyframe_insert('location',frame=f)
for datablock in [cam,cam.data]:
 for fc in datablock.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
s['Design scope']='Generic smartwatch integration concept; exact accepted sensor meshes preserved under one uniform-scale placement rig. Recess at 12 oclock; local optical-bay cover fades for explanatory cutaway. Illustrative, not validated manufacturing, waterproofness or optical safety.'
s['Sensor source']=SRC
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=D+'/Watch_Sensor_Zoom.blend',compress=True)
for f in [1,145]:
 s.frame_set(f);s.render.filepath=D+'/preview_%03d.png'%f;bpy.ops.render.render(write_still=True)
