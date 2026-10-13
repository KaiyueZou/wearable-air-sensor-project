import bpy,os,sys
D=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,D);from watch_helpers import text,mat
bpy.ops.wm.open_mainfile(filepath=D+'/Watch_Sensor_Zoom.blend');s=bpy.context.scene
# Keep this asset focused on placement. One particle-measurement stage suffices.
for o in s.objects:
 if o.name.startswith(('Active L1','Airborne scatter','W1 footprint','L2 illumination','Separate W2','Selected airborne')):
  o.animation_data_clear()
  for f in [1,128,240,320]:
   on=128<=f<240 and o.name.startswith(('Active L1','Airborne scatter','Selected airborne'))
   o.hide_render=not on;o.keyframe_insert('hide_render',frame=f)
  for fc in o.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='CONSTANT'
 # Make ambient particle positions cycle exactly in 20 seconds.
 if o.name.startswith('Animated airborne'):
  idx=int(o.name.split()[-1]);o.animation_data_clear()
  for f in range(1,321):o.location.y=-1.25+((idx*.19+(f-1)/16*.125)%2.5);o.keyframe_insert('location',frame=f)
cam=s.camera
m=mat('Concept cutaway | quiet caption',(.83,.90,.93),0,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.83,.90,.93,1);p.inputs['Emission Strength'].default_value=1
rig=bpy.data.objects.new('Concept caption camera rig',None);s.collection.objects.link(rig);rig.parent=cam;rig.location=(0,0,-2)
for axis in range(3):
 d=rig.driver_add('scale',axis).driver;v=d.variables.new();v.name='ortho';v.type='SINGLE_PROP';v.targets[0].id_type='CAMERA';v.targets[0].id=cam.data;v.targets[0].data_path='ortho_scale';d.expression='ortho/960'
o=text('Concept cutaway label','Concept cutaway',(-438,310,0),21,m,align='LEFT');o.parent=rig;o.visible_shadow=False
font=D+'/fonts/OpenSans-Regular.ttf';o.data.font=bpy.data.fonts.load(font)
for f,hide in [(1,True),(106,False),(257,True),(320,True)]:o.hide_render=hide;o.keyframe_insert('hide_render',frame=f)
for fc in o.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='CONSTANT'
s.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=D+'/Watch_Sensor_Zoom.blend',compress=True)
