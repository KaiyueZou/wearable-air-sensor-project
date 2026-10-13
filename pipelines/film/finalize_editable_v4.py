"""Add editable, camera-locked typography with zoom compensation to the Blender file."""
import bpy,os,json,math
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Sensor_Mechanism_Panorama.blend');s=bpy.context.scene;cam=s.camera
for o in list(s.objects):
 if o.name.startswith(('Editorial v2','Editorial v3','Editorial v4')):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('Editorial v4 • editable typography');s.collection.children.link(col)
rig=bpy.data.objects.new('Editorial v4 • camera-locked pixel rig',None);col.objects.link(rig);rig.parent=cam;rig.location=(0,0,-9)
for axis in range(3):
 d=rig.driver_add('scale',axis).driver;v=d.variables.new();v.name='ortho';v.type='SINGLE_PROP';v.targets[0].id_type='CAMERA';v.targets[0].id=cam.data;v.targets[0].data_path='ortho_scale';d.expression='ortho/1280'
for oldfont in list(bpy.data.fonts):
 if 'OpenAI' in oldfont.name:bpy.data.fonts.remove(oldfont,do_unlink=True)
fonts={k:bpy.data.fonts.load(OUT+'/fonts/OpenSans-'+('Semibold' if k=='medium' else k.capitalize())+'.ttf') for k in ['regular','medium','semibold']}
materials={}
def material(rgb):
 key=tuple(rgb)
 if key not in materials:
  m=bpy.data.materials.new('Editorial v4 • ink '+str(len(materials)));m.diffuse_color=(*rgb,1);m.roughness=1;m.specular_intensity=0;m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=1;materials[key]=m
 return materials[key]
def pixel(x,y,z=0):return (x-640+cam.data.shift_x*1280,360-y,z)
def visible(o,start,end):
 for f,on in [(1,False),(round(start*24)+1,True),(round(end*24)+1,False)]:
  o.hide_render=not on;o.hide_viewport=not on;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
def text(name,body,x,y,size,rgb,font='regular'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=fonts[font];cu.size=size*1.3;cu.space_line=1.2;cu.materials.append(material(rgb));o=bpy.data.objects.new(name,cu);col.objects.link(o);o.parent=rig;o.location=pixel(x,y+size*.81,.02);return o
entries=json.load(open(OUT+'/editorial_layout.json'))
for n,e in enumerate(entries):
 o=text('Editorial v4 • caption %03d'%n,e['text'],e['x'],e['y'],e['size'],e['color'],e.get('font','regular'));o.data.space_character=1+e.get('tracking',0)/max(1,e['size']);visible(o,e.get('start',0),e.get('end',174))
# Borderless backing isolates the caption column from model geometry during closeups.
me=bpy.data.meshes.new('Editorial v4 backing');me.from_pydata([pixel(884,100,-.1),pixel(1260,100,-.1),pixel(1260,632,-.1),pixel(884,632,-.1)],[],[(0,1,2,3)]);o=bpy.data.objects.new('Editorial v4 • caption backing',me);col.objects.link(o);o.parent=rig;me.materials.append(material((.0115,.0176,.0232)))
# Geometry-following, independently editable labels and leaders sampled at native24fps.
records=json.load(open(OUT+'/label_layout24.json'))
labels={};leaders={}
for key in ['L1','W1','W2','C1','C2','L2','TRAP','AIR']:
 labels[key]=text('Editorial v4 • component '+key,key,0,0,17,(.94,.95,.95),'medium')
 cu=bpy.data.curves.new('Editorial v4 leader '+key,'CURVE');cu.dimensions='3D';cu.bevel_depth=.5;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(2);cu.materials.append(material((.43,.52,.55)));o=bpy.data.objects.new('Editorial v4 • leader '+key,cu);col.objects.link(o);o.parent=rig;leaders[key]=o
last_shown={}
for i,record in enumerate(records):
 fr=i+1;shown={}
 for rec in record['labels']:
  key=rec['key'];shown[key]=1;o=labels[key];o.location=pixel(rec['x'],rec['y']+13.77,.02);o.keyframe_insert('location',frame=fr)
  ax,ay=rec['anchor'];cx=rec['x']+rec['w']/2;cy=rec['y']+9;edge=rec['x']+rec['w']+8 if ax>cx else rec['x']-8;elbow=edge+12 if ax>cx else edge-12
  sp=leaders[key].data.splines[0]
  for pt,xy in zip(sp.points,[(edge,cy),(elbow,cy),(ax,ay)]):pt.co=(*pixel(*xy,.01),1);pt.keyframe_insert('co',frame=fr)
 for key in labels:
  on=key in shown
  if i==0 or last_shown.get(key)!=on:
   for o in [labels[key],leaders[key]]:o.hide_render=not on;o.hide_viewport=not on;o.keyframe_insert('hide_render',frame=fr);o.keyframe_insert('hide_viewport',frame=fr)
 last_shown={key:key in shown for key in labels}
for o in col.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path.startswith('hide_') else 'LINEAR'
s.display.render_aa='8';s['Video delivery']='Native 24fps geometry:4176 frames / 174 seconds. No frame blending. 30-second360-degree introduction; unchanged approved story. Exact depth-masked glow/hidden guides/fades via compose_v4.py; matching editable camera-locked text and tracked labels included.'
s.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Sensor_Mechanism_Panorama.blend',compress=True)
print('EDITABLE_V4_READY',s.frame_end,s.render.fps,len(col.objects))
