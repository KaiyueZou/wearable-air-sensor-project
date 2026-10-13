import bpy,json,os,math
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=OUT+'/Sensor_Mechanism_Panorama.blend')
s=bpy.context.scene;s.frame_set(721)
keep=[o for o in s.objects if o.type=='MESH' and any(c.name.startswith(('10 •','20 •')) for c in o.users_collection)]
assert len(keep)==51,len(keep)
hardware=keep[:]
paths=[bpy.data.objects[n] for n in ['Active L1 illumination','Airborne scatter to C2']]
particles=[o for o in s.objects if o.name.startswith('Animated airborne particle ') or o.name=='Scattering particle at selected region']
assert len(particles)==15
keep+=paths+particles
source_names=sorted(o.name for o in keep)
# Bake the exact native source curves into portable GLB meshes, without altering endpoints.
for o in paths:
 bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.hide_viewport=False;o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Give schematic paths a modest emissive core; actual scene geometry handles occlusion.
for o in paths:
 m=o.active_material;m.animation_data_clear();m.node_tree.animation_data_clear()
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 bs.inputs['Alpha'].default_value=0.9
 bs.inputs['Emission Strength'].default_value=3.0
 o['role']='Illustrative clean-state optical path, not a physical optical simulation'
for o in particles:o['role']='Enlarged illustrative particle, frozen at source frame 721'
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for o in keep:
 o.animation_data_clear();o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
for m in bpy.data.materials:
 m.animation_data_clear()
 if m.node_tree:m.node_tree.animation_data_clear()
bpy.context.view_layer.update()
pts=[o.matrix_world@Vector(p) for o in hardware for p in o.bound_box]
lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));center=(lo+hi)/2
root=bpy.data.objects.new('Air Sensor | accepted v4 clean assembly',None);s.collection.objects.link(root)
root['source']='Sensor_Mechanism_Panorama.blend / accepted v4 / clean frame 721'
root['note']='Conceptual cutaway geometry; source scale preserved. No watch or presentation objects.'
groups={}
for o in keep:
 group_name=next(c.name for c in o.users_collection if c.name.startswith(('10 •','20 •'))) if o in hardware else ('30 • Clean measurement optical paths' if o in paths else '40 • Illustrative airborne particles')
 if group_name not in groups:
  group=bpy.data.objects.new(group_name,None);s.collection.objects.link(group);group.parent=root;groups[group_name]=group
 mat=o.matrix_world.copy();o.parent=groups[group_name];o.matrix_world=mat;o.location-=center
s.name='Air Sensor | Clean Assembly'
bpy.ops.object.select_all(action='DESELECT')
for o in keep+[root]+list(groups.values()):o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=OUT+'/Air_Sensor_Latest.glb',export_format='GLB',use_active_scene=True,use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True,export_yup=True)
json.dump({'source_object_names':source_names,'hardware_objects':51,'optical_paths':2,'illustrative_particles':15,'state':'Clean measurement at source frame 721, static geometry','source_bounds':[list(lo),list(hi)],'centering_offset':list(center),'source_scene_units':'METRIC, scale_length=1.0 (concept model; source dimensions preserved)','excluded':'Studio, camera, lights, editorial text, contamination, inactive diagnostic paths, watch context'},open(OUT+'/export_report.json','w'),indent=2)
# Verify by independently importing the written GLB into an empty Blender scene.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT+'/Air_Sensor_Latest.glb')
s=bpy.context.scene
meshes=[o for o in s.objects if o.type=='MESH'];assert len(meshes)==68,len(meshes)
assert sorted(o.name for o in meshes)==source_names
pts=[o.matrix_world@Vector(p) for o in meshes for p in o.bound_box]
lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
assert max((hi-lo))<9 and (lo+hi).length<1,(lo,hi)
assert len([o for o in meshes if o.name.startswith('C1 |')])==4
print('ROUNDTRIP_VALID',len(meshes),'BOUNDS',list(lo),list(hi))
print('EXPORT_COMPLETE')
