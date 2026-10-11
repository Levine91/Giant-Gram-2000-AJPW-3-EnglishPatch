"""Align tournament names and the two split-atlas confirmation prompts."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-tournament-alignment';B.mkdir(exist_ok=True)
for n in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/n).exists():shutil.copy2(G/n,B/n)
a=(B/'TEX.AFS').read_bytes();program=(B/'1ST_READ.BIN').read_bytes()
patches=[]
# Both color passes, including both tag partners. The delay slot executes
# before the existing renderer; no shared font or unrelated screen changes.
for off in [0x40d22,0x40d6c,0x40fe4,0x410ea,0x411cc,0x4120a]:
 assert program[off:off+2]==b'\x09\x00'
 patches.append([off,'0476']) # add #4,r6
(R/'tournament-program-patches.json').write_text(json.dumps(patches))
textures=[]
for off,kind in [(4046848+9*SIZE,'participants'),(5779456+35*SIZE,'results')]:
 block=a[off:off+SIZE];old=decode(block);im=old.copy()
 if kind=='participants':
  parts=[(88,12,256,36),(72,67,232,91)]
  width=328;word='Confirm these participants?';font='arialbd.ttf';size=18
  # The second piece is 55 atlas pixels below the first, not 56.
  # Recover the bottom horizontal frame that an earlier clear erased.
  for y in range(92,96):
   im.paste(old.getpixel((100,y-55)),(72,y,230,y+1))
  im.paste((17,0,51,170),(72,66,232,92))
 else:
  parts=[(128,12,256,36),(0,67,120,91)]
  width=248;word='View results only?';font='arialbi.ttf';size=22
  # Clear the old text's final white fragment, inside the right border.
  im.paste((17,0,51,170),(0,66,122,92))
 strip=Image.new('RGBA',(width,24),(17,0,51,170))
 face=ImageFont.truetype('C:/Windows/Fonts/'+font,size)
 stroke=1 if kind=='results' else 0
 bb=face.getbbox(word,stroke_width=stroke)
 x=(width-(bb[2]-bb[0]))//2-bb[0];y=(24-(bb[3]-bb[1]))//2-bb[1]
 ImageDraw.Draw(strip).text((x,y),word,font=face,fill='white',stroke_width=stroke,stroke_fill='black')
 cursor=0
 for x0,y0,x1,y1 in parts:
  im.paste(strip.crop((cursor,0,cursor+x1-x0,24)),(x0,y0));cursor+=x1-x0
 assert cursor==width
 mask=np.any(np.asarray(im)!=np.asarray(old),axis=2)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,block,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
 for yy,xx in zip(*np.nonzero(touched)):
  p=2048+spread(int(yy))+(spread(int(xx))<<1);out[p]=encoded[p]
 final=decode(out)
 cellmask=np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
 assert np.array_equal(np.asarray(old)[~cellmask],np.asarray(final)[~cellmask])
 name=f'tournament-{kind}.bin';(R/name).write_bytes(out);textures.append([off,name])
 # Reassemble the actual 55-pixel atlas displacement for visual inspection.
 if kind=='participants':
  preview=Image.new('RGBA',(336,36));preview.paste(final.crop((84,6,256,42)),(0,0));preview.paste(final.crop((72,61,236,97)),(172,0))
 else:
  preview=Image.new('RGBA',(260,36));preview.paste(final.crop((124,6,256,42)),(0,0));preview.paste(final.crop((0,61,128,97)),(132,0))
 preview.resize((preview.width*3,108),Image.Resampling.NEAREST).save(R/f'tournament-{kind}-fixed.png')
(R/'tournament-texture-patches.json').write_text(json.dumps(textures))
print('Six roster draw calls shifted four pixels; both split prompts repaired.')
