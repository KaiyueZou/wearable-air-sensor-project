#!/usr/bin/env python3
"""Single entry point for the concept's three visual pipelines and clean GLB export."""
import argparse, json, os, sys, subprocess, hashlib, struct
from pathlib import Path
from common import ROOT,CONFIG,run,stage,blender,python

def encode(name,d,gif=False,dry=False):
    c=CONFIG['pipelines'][name];fps=c['fps']
    pattern=d/('frames/%04d.png' if name=='tour' else 'frames/f%04d.png')
    if not dry:
        missing=[i for i in range(0 if name=='tour' else 1, c['frames']+(0 if name=='tour' else 1)) if not Path(str(pattern)%i).exists()]
        if missing: raise SystemExit(f'Missing {name} render frames: {missing[:5]}; render the complete sequence first.')
    common=['ffmpeg','-hide_banner','-loglevel','warning','-y','-framerate',str(fps),'-i',str(pattern)]
    if not gif:
        run([*common,'-c:v','libx264','-threads','4','-crf','20' if name=='tour' else '19','-pix_fmt','yuv420p','-movflags','+faststart',d/c['output']],d,dry);return
    filt='scale=720:480:flags=lanczos' if name=='tour' else 'fps=12,scale=800:600:flags=lanczos'
    palette=d/'palette.png';colors='112' if name=='tour' else '256'
    run([*common,'-vf',filt+',palettegen=stats_mode='+('diff' if name=='tour' else 'full')+':max_colors='+colors,'-frames:v','1','-update','1',palette],d,dry)
    filename='Sensor_360_Labeled_Web.gif' if name=='tour' else 'Watch_Sensor_Zoom.gif'
    run([*common,'-i',palette,'-lavfi',f'[0:v]{filt}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle','-loop','0',d/filename],d,dry)
    if name=='tour':python(d.parent,'validate.py',dry=dry)

def validate():
    expected=json.loads((ROOT/'release/manifest.json').read_text())['files']
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ('build','__pycache__','.git','.venv')) and p.relative_to(ROOT).as_posix() not in ('release/manifest.json','release/SHA256SUMS.txt')}
    assert actual==set(expected),('Unexpected/missing files',sorted(actual^set(expected)))
    for rel,rec in expected.items():
        p=ROOT/rel;assert p.stat().st_size==rec['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256'],rel
    for name,c in CONFIG['pipelines'].items():
        p=ROOT/'media'/c['output'];data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(p)]));assert len(data['streams'])==1
        s=data['streams'][0];assert s['codec_name']=='h264' and [s['width'],s['height']]==c['resolution'];assert int(s['nb_read_frames'])==c['frames'];assert abs(float(s['duration'])-c['duration'])<.001;assert s['r_frame_rate']==str(c['fps'])+'/1'
        print(name,'media PASS',c['frames'],'decoded frames')
    p=ROOT/'models/Air_Sensor_Latest.glb';b=p.read_bytes();magic,version,size=struct.unpack_from('<4sII',b);assert magic==b'glTF' and version==2 and size==len(b)
    n,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a;g=json.loads(b[20:20+n]);assert len(g['meshes'])==68 and not g.get('animations') and not g.get('cameras')
    print('GLB PASS: 51 hardware + 2 optical paths + 15 particles; release hashes PASS')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['prepare','build','render','compose','gif','export','validate','smoke']);ap.add_argument('pipeline',nargs='?',choices=['film','tour','watch']);ap.add_argument('--indices',type=int,nargs='+',help='Zero-based film/tour render indices; watch indices are one-based');ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    if a.command=='validate':validate();return
    if a.command=='export':
        d=stage('export');blender(d,'export_sensor.py',dry=a.dry_run);return
    if a.command=='smoke':
        smoke(a.dry_run);return
    if not a.pipeline:ap.error('pipeline is required')
    name=a.pipeline;d=stage(name);dry=a.dry_run
    if a.command=='prepare':print(d);return
    if a.command=='build':
        if name=='film':blender(d,'build_v4.py',dry=dry)
        elif name=='watch':blender(d,'build_watch.py',dry=dry);blender(d,'prepare_render.py',dry=dry);blender(d,'verify_geometry.py',dry=dry)
        else:ap.error('Tour derives directly from the canonical sensor; use render tour')
    elif a.command=='render':
        indices=a.indices
        if indices and any(i < (1 if name=='watch' else 0) or i >= CONFIG['pipelines'][name]['frames']+(1 if name=='watch' else 0) for i in indices):ap.error('frame index out of range')
        if name=='watch':
            for start,end in ([(i,i) for i in indices] if indices else [(1,320)]):blender(d,'render_watch.py',[str(start),str(end)],dry)
        else:blender(d,'render_v4.py' if name=='film' else 'render.py',(['--indices',*map(str,indices)] if indices else []),dry)
    elif a.command=='compose':
        if name=='film':python(d,'compose_final_parallel.py',dry=dry);python(d,'export_label_layout.py',dry=dry);blender(d,'finalize_editable_v4.py',dry=dry)
        elif name=='tour':python(d,'compose.py',dry=dry);encode(name,d/'build',dry=dry)
        else:encode(name,d,dry=dry)
    elif a.command=='gif':
        if name=='film':ap.error('Film has no GIF release; use the short loops')
        encode(name,d/'build' if name=='tour' else d,gif=True,dry=dry)

def smoke(dry):
    # Real native renders and compositor checks; no claim of a complete rerender.
    d=stage('film');blender(d,'render_v4.py',['--indices','0','1008'],dry)
    python(d,'compose_v4.py',['--preview','--metadata',str(d/'preview_metadata.json'),'--indices','0','1008'],dry)
    t=stage('tour');blender(t,'render.py',['--indices','0'],dry)
    # Compositor needs the complete orbit metadata but can render only requested frames.
    python(t,'compose.py',['--indices','0'],dry)
    w=stage('watch');blender(w,'verify_geometry.py',dry=dry);blender(w,'render_watch.py',['145','145'],dry)
    e=stage('export');blender(e,'export_sensor.py',dry=dry)
    if not dry:
        from PIL import Image
        for path in [d/'frames24/f00000.png',d/'frames24/f01008.png',t/'build/frames/0000.png',w/'frames/f0145.png']:
            with Image.open(path) as im:im.verify()
        print('SMOKE PASS: film base + optical mask + compositor, tour native + labels, watch native + 51-mesh geometry, GLB round trip')
if __name__=='__main__':main()
