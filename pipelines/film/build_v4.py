"""Add a native 30-second 360-degree introduction without changing approved story poses."""
import bpy,os,math
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
SOURCE=OUT+'/Approved_v3.blend'
bpy.ops.wm.open_mainfile(filepath=SOURCE)
s=bpy.context.scene;cam=s.camera
for o in list(s.objects):
 if o.name.startswith('Editorial'):bpy.data.objects.remove(o,do_unlink=True)
for action in bpy.data.actions:
 for fc in action.fcurves:
  for key in fc.keyframe_points:
   key.co.x+=720;key.handle_left.x+=720;key.handle_right.x+=720
for marker in s.timeline_markers:marker.frame+=720
s.timeline_markers.new('360° component introduction',frame=1)
s.frame_end=4176;s.name='07 • Sensor panorama and occlusion-aware optics'
s.frame_set(721)
prev=None
for fr in range(1,721):
 u=(fr-1)/720;u=u*u*(3-2*u);a=math.atan2(-14,7)+math.tau*u
 target=Vector((0,0,1.1));cam.location=target+Vector((math.sqrt(245)*math.cos(a),math.sqrt(245)*math.sin(a),7.9))
 e=(target-cam.location).to_track_quat('-Z','Y').to_euler('XYZ',prev) if prev else (target-cam.location).to_track_quat('-Z','Y').to_euler();prev=e.copy();cam.rotation_euler=e
 for p in ['location','rotation_euler']:cam.keyframe_insert(p,frame=fr)
 cam.data.ortho_scale=13.3;cam.data.keyframe_insert('ortho_scale',frame=fr)
# Equivalent rotation angles are unwrapped through the story start to avoid a spin at 30 s.
for fc in cam.animation_data.action.fcurves:
 if fc.data_path=='rotation_euler':
  ks=[k for k in fc.keyframe_points if k.co.x<=720];last=ks[-1].co.y
  for k in [k for k in fc.keyframe_points if k.co.x>=721]:
   delta=round((last-k.co.y)/math.tau)*math.tau;k.co.y+=delta;k.handle_left.y+=delta;k.handle_right.y+=delta;last=k.co.y
 for k in fc.keyframe_points:
  if k.co.x<=720:k.interpolation='LINEAR'
paths=['Active L1 illumination','Airborne scatter to C2','W1 footprint scatter to C1','L2 illumination of W2','Separate W2 collection to C2','Selected airborne region -0.55','Selected airborne region 0.55']
for name in paths:
 o=bpy.data.objects[name];o.data.bevel_depth=.008 if 'Selected' not in name else .003
 m=o.data.materials[0];rgb=tuple(m.diffuse_color[:3]);m.diffuse_color=(*rgb,.9);p=m.node_tree.nodes.get('Principled BSDF')
 if p:p.inputs['Alpha'].default_value=.9;p.inputs['Emission Strength'].default_value=5
 o['V4 presentation']='Bright visible ray diagram. Final compositor tests opaque geometry before adding faint dashed hidden-view guides.'
s['Refinement']='V4: 30-second full 360° component introduction; approved 144-second mechanism unchanged; brighter visible beams; ray-tested faint dashed hidden-view guide convention.'
s['Optical presentation']='Hidden paths are camera-occlusion guides, not physical transmission through solids. Transparent window films are excluded from opaque mask. Physical trap and path endpoints preserved.'
s.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=OUT+'/Sensor_Mechanism_Panorama.blend',compress=True)
