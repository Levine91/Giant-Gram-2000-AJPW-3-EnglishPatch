"""Optically center VS by shifting its existing artwork two pixels left."""
from pathlib import Path
import json,shutil,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import decode,SIZE,OFFSET,spread
from patch_english_menu import encode
B=R/'before-vs-centering';B.mkdir(exist_ok=True)
if not (B/'TEX.AFS').exists():shutil.copy2(G/'TEX.AFS',B/'TEX.AFS')
a=(B/'TEX.AFS').read_bytes();off=1089536+OFFSET;old=a[off:off+SIZE];original=decode(old);im=original.copy()
row=original.crop((0,112,256,136));im.paste((0,0,0,0),(0,112,256,136));im.paste(row.crop((2,0,256,24)),(0,112))
candidate=encode(im,old);out=bytearray(old)
for y in range((256-136)//2,(256-112)//2):
 for x in range(128):p=2048+spread(y)+(spread(x)<<1);out[p]=candidate[p]
final=decode(out);assert final.tobytes()==im.tobytes(),'Artwork changed beyond the intended shift'
(R/'main-vs-centered.bin').write_bytes(out);(R/'main-vs-texture-patches.json').write_text(json.dumps([[off,'main-vs-centered.bin']]))
preview=Image.new('RGBA',(256,192),(30,30,30,255));preview.alpha_composite(final.crop((0,64,256,256)));preview.resize((768,576),Image.Resampling.NEAREST).save(R/'main-vs-centered-preview.png')
print('VS moved two pixels left; exact artwork and every other menu row preserved.')
