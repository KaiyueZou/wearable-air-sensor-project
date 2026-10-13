"""Losslessly remove Blender PNG metadata and unused alpha; retain exact RGB bits."""
from pathlib import Path
from PIL import Image,ImageChops
OUT=Path(__file__).resolve().parent
before=after=0
for p in (OUT/'beam_masks').glob('*.png'):
 before+=p.stat().st_size
 with Image.open(p) as im:rgb=im.convert('RGB')
 tmp=p.with_suffix('.tmp.png');rgb.save(tmp,optimize=True)
 with Image.open(tmp) as check:assert ImageChops.difference(rgb,check).getbbox() is None
 tmp.replace(p);after+=p.stat().st_size
print('MASK_BYTES',before,'->',after)
