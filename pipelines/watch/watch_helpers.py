import bpy, math
from mathutils import Vector

def mat(name,color,metal=0,rough=.35):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m

def box(name,loc,dims,material,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel: mod=o.modifiers.new('Precision edge radius','BEVEL');mod.width=bevel;mod.segments=5
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');o.data.materials.append(material)
 return o

def rr_points(w,h,r,n=12):
 out=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(n+1):
   th=math.radians(a+i*90/n);out.append((cx+r*math.cos(th),cy+r*math.sin(th)))
 return out

def ring(name,w,h,r,iw,ih,ir,z0,z1,material):
 outer=rr_points(w,h,r);inner=rr_points(iw,ih,ir);N=len(outer)
 vs=[(x,y,z) for z in [z0,z1] for pts in [outer,inner] for x,y in pts];fs=[]
 for i in range(N):
  j=(i+1)%N
  fs += [(i,j,2*N+j,2*N+i),(N+j,N+i,3*N+i,3*N+j),(2*N+i,2*N+j,3*N+j,3*N+i),(j,i,N+i,N+j)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 b=o.modifiers.new('Micro polished edges','BEVEL');b.width=.035;b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def cylinder(name,loc,radius,depth,material,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=loc,rotation=rotation);o=bpy.context.object;o.name=name;o.data.materials.append(material)
 mod=o.modifiers.new('Rounded edge','BEVEL');mod.width=.025;mod.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def text(name,body,loc,size,material,align='CENTER'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x=align;cu.size=size;cu.extrude=0
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;cu.materials.append(material);return o

def look(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def light(name,loc,power,size,color=(1,1,1)):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;look(o,(0,0,0));return o

def roundedbox(name,loc,dims,material,r=.4,edge=.04):
 w,h,depth=dims;pts=rr_points(w,h,r,16);N=len(pts);vs=[(x,y,z) for z in [-depth/2,depth/2] for x,y in pts];fs=[tuple(reversed(range(N))),tuple(range(N,2*N))]
 for i in range(N):j=(i+1)%N;fs.append((i,j,N+j,N+i))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.location=loc;me.materials.append(material)
 b=o.modifiers.new('Radiused finish edge','BEVEL');b.width=edge;b.segments=4;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
