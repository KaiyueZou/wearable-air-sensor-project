"""Decode the actual final GIF, verify delivery constraints, and save QA."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib
ROOT=Path(__file__).resolve().parent;O=ROOT/'build'
p=O/'Sensor_360_Labeled_Web.gif';im=Image.open(p)
qa=json.load(open(O/'validation.json'));delays=[];frames=[]
contact=Image.new('RGB',(1440,960));draw=ImageDraw.Draw(contact)
for i in range(im.n_frames):
 im.seek(i);delays.append(im.info.get('duration',0))
 frame=im.convert('RGB');frames.append(hashlib.sha256(frame.tobytes()).hexdigest())
 if i in [0,60,120,180,240,300,360,420]:
  j=i//60;contact.paste(frame.resize((360,240)),((j%4)*360,(j//4)*240))
qa.update(gif_frames=im.n_frames,gif_size=list(im.size),gif_duration_seconds=sum(delays)/1000,gif_delays_ms=sorted(set(delays)),gif_loop=im.info.get('loop'),gif_bytes=p.stat().st_size,mp4_bytes=(O/'Sensor_360_Labeled.mp4').stat().st_size,gif_palette_max_colors=112,gif_bayer_scale=5,decoded_unique_frames=len(set(frames)),native_unique_base_frames=len(set(hashlib.sha256(q.read_bytes()).hexdigest() for q in (O/'base').glob('*.png'))))
qa['label_anchor_center_distance_mean_at_720px']=qa['label_anchor_center_distance_mean_px']*.75
qa['label_anchor_center_distance_max_at_720px']=qa['label_anchor_center_distance_max_px']*.75
assert qa['gif_frames']==480 and qa['gif_duration_seconds']==32 and qa['gif_size']==[720,480] and qa['gif_loop']==0
assert qa['gif_bytes']<18_000_000
assert qa['label_overlaps']==0
assert qa['label_max_frame_jump_at_720px']<4
assert qa['decoded_unique_frames']==480
json.dump(qa,open(O/'validation.json','w'),indent=2)
contact.crop((0,0,1440,480)).save(O/'decoded_preview.jpg',quality=96)
im.seek(0);im.convert('RGB').save(O/'decoded_frame0.png')
print(json.dumps(qa,indent=2))
