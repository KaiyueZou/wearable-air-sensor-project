import bpy,os,json,hashlib,struct
D=os.path.dirname(os.path.abspath(__file__))
SOURCE=D+'/Accepted_Sensor_Source.blend'
def collect(path):
 bpy.ops.wm.open_mainfile(filepath=path);bpy.context.scene.frame_set(821 if 'Accepted_Sensor_Source' in path else 145);out={}
 for o in bpy.context.scene.objects:
  if not any(c.name.startswith(('10 •','20 •')) for c in o.users_collection):continue
  verts=[list(v.co) for v in o.data.vertices] if o.type=='MESH' else []
  polys=[list(p.vertices) for p in o.data.polygons] if o.type=='MESH' else []
  out[o.name]={'vertices':len(verts),'faces':len(polys),'geometry_sha256':hashlib.sha256(json.dumps([verts,polys],separators=(',',':')).encode()).hexdigest(),'local_location':list(o.location),'local_rotation':list(o.rotation_euler),'local_scale':list(o.scale)}
 return out
original=collect(SOURCE);embedded=collect(D+'/Watch_Sensor_Zoom.blend');assert original==embedded,(set(original)^set(embedded))
json.dump({'exact_sensor_geometry_preserved':True,'hardware_objects':len(original),'uniform_integration_scale':.285,'source':os.path.basename(SOURCE),'object_manifest':original},open(D+'/geometry_validation.json','w'),indent=2)
print('EXACT_GEOMETRY_PASS',len(original))
