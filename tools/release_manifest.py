"""Inventory the selected tracked release, excluding generated caches and Git internals."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
records={}
for p in sorted(ROOT.rglob('*')):
    rel=p.relative_to(ROOT)
    if not p.is_file() or any(part in ('build','__pycache__','.git','.venv') for part in rel.parts) or rel.as_posix() in ('release/manifest.json','release/SHA256SUMS.txt'):continue
    records[rel.as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'release/manifest.json').write_text(json.dumps({'schema_version':1,'files':records},indent=2)+'\n')
(ROOT/'release/SHA256SUMS.txt').write_text(''.join(f'{v["sha256"]}  {k}\n' for k,v in records.items()))
print(f'Inventoried {len(records)} files')
