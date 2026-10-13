"""Compose all 4176 native frames in four workers, then join and verify 174 seconds."""
from concurrent.futures import ProcessPoolExecutor
import subprocess,math,json,sys
from PIL import Image
from compose_v4 import OUT,FrameSource,overlay,chapter_at

def part(index):
 source=FrameSource(OUT/'frames24',OUT/'metadata24.json',24)
 path=OUT/('segment_%02d.mp4'%index)
 command=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
 p=subprocess.Popen(command,stdin=subprocess.PIPE)
 for i in range(index*1044,(index+1)*1044):
  t=i/24;base,meta=source.sample(t);frame=Image.alpha_composite(base,overlay(chapter_at(t),t,meta)).convert('RGB');p.stdin.write(frame.tobytes())
 p.stdin.close();assert p.wait()==0
 print('SEGMENT_COMPLETE',index,flush=True)
 return path

def main():
 missing=[i for i in range(4176) if not (OUT/'frames24'/('f%05d.png'%i)).exists()]
 assert not missing, 'Missing native frames: '+str(missing[:5])
 metadata=json.loads((OUT/'metadata24.json').read_text())
 assert len(metadata)==4176, 'Expected 4176 metadata frames'
 for i,record in enumerate(metadata):
  if record.get('lights'):
   assert record.get('mask_file'), f'Missing depth-mask reference at frame {i}'
  if record.get('mask_file'):
   from pathlib import Path
   mask=Path(record['mask_file'])
   if not mask.is_absolute():mask=OUT/mask
   assert mask.exists(), f'Missing depth mask: {mask}'
 paths=[OUT/('segment_%02d.mp4'%i) for i in range(4)]
 needed=[]
 for i,path in enumerate(paths):
  valid=False
  if '--reuse-completed-segments' in sys.argv and path.exists():
   try:
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(path)]))['streams'][0]
    valid=probe['nb_read_frames']=='1044' and abs(float(probe['duration'])-43.5)<.001
   except Exception:pass
  if not valid:needed.append(i)
 with ProcessPoolExecutor(max_workers=4) as pool:list(pool.map(part,needed))
 listing=OUT/'concat_segments.txt';listing.write_text(''.join("file '%s'\n"%p.name for p in paths))
 result=OUT/'Sensor_Mechanism_Panorama_174s.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(result)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,duration,nb_read_frames','-of','json',str(result)]))
 (OUT/'video_probe.json').write_text(json.dumps(probe,indent=2)+'\n')
 stream=probe['streams'][0]
 assert stream['nb_read_frames']=='4176',stream
 assert abs(float(stream['duration'])-174)<.001,stream
 assert (stream['width'],stream['height'],stream['r_frame_rate'])==(1280,720,'24/1'),stream
 print('FINAL_VIDEO',result,flush=True)
if __name__=='__main__':main()
