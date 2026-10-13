import bpy,os,sys,time
D=os.path.dirname(os.path.abspath(__file__));bpy.ops.wm.open_mainfile(filepath=D+'/Watch_Sensor_Zoom.blend');s=bpy.context.scene
os.makedirs(D+'/frames',exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];start=int(args[0]) if args else 1;end=int(args[1]) if len(args)>1 else 320
for f in range(start,end+1):
 dest=D+'/frames/f%04d.png'%f
 if os.path.exists(dest):continue
 s.frame_set(f);s.render.filepath=dest;bpy.ops.render.render(write_still=True);print('WATCH_FRAME',f,flush=True)
