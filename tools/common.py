"""Shared, portable staging and process helpers. Tracked inputs are never overwritten."""
from pathlib import Path
import os, shutil, subprocess, sys, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'config.json').read_text())

def run(cmd, cwd=None, dry=False):
    print(' '.join(map(str, cmd)), flush=True)
    if not dry: subprocess.run(list(map(str,cmd)), cwd=cwd or ROOT, check=True)

def stage(name):
    dest=ROOT/'build'/name
    inputs={}
    for p in (ROOT/'pipelines'/name).glob('*.py'): inputs[p.name]=p
    for p in (ROOT/'assets/fonts').iterdir(): inputs['fonts/'+p.name]=p
    inputs['Sensor_Mechanism_Panorama.blend']=ROOT/'models/Sensor_Mechanism_Panorama.blend'
    if name=='film':
        for p in (ROOT/'source/film').rglob('*'):
            if p.is_file(): inputs[str(p.relative_to(ROOT/'source/film'))]=p
    if name=='watch':
        inputs['Accepted_Sensor_Source.blend']=ROOT/'models/Sensor_Mechanism_Panorama.blend'
        inputs['Watch_Sensor_Zoom.blend']=ROOT/'models/Watch_Sensor_Zoom.blend'
    fingerprint=hashlib.sha256(''.join(k+hashlib.sha256(p.read_bytes()).hexdigest() for k,p in sorted(inputs.items())).encode()).hexdigest()
    stamp=dest/'.input-sha256'
    if stamp.exists() and stamp.read_text()!=fingerprint:
        raise SystemExit(f'Inputs changed for {name}. Remove build/{name} before rebuilding to avoid stale frames.')
    for rel,p in inputs.items():
        out=dest/rel
        if not out.exists(): out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
    stamp.write_text(fingerprint)
    return dest

def blender(dest, script, extra=(), dry=False):
    run([os.environ.get('BLENDER','blender'),'-b','-t',os.environ.get('SENSOR_THREADS','4'),'--python-exit-code','1','--python',dest/script,'--',*extra],dest,dry)

def python(dest,script,extra=(),dry=False):run([sys.executable,dest/script,*extra],dest,dry)
