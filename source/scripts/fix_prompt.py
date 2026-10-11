"""Render the prompt across its two actual atlas interiors, excluding the frame."""
from pathlib import Path
import sys,struct,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parent
sys.path.insert(0,str(GAME/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(ROOT/'before-final-fix/TEX.AFS').read_bytes()
entry=4046848;length=811008;tile=9;start=entry+tile*SIZE
original=archive[start:start+SIZE];old=decode(original);target=old.copy()
# The second interior begins at x=72, not x=64 (outside the frame).
parts=[(88,12,256,36),(72,68,232,92)]
strip=Image.new('RGBA',(328,24),(17,0,51,255))
face=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',18)
draw=ImageDraw.Draw(strip);text='Confirm these participants?'
bbox=draw.textbbox((0,0),text,font=face);width=bbox[2]-bbox[0];height=bbox[3]-bbox[1]
assert width<strip.width-24 and height<=20
x=(strip.width-width)//2;y=(24-height)//2
draw.text((x-bbox[0],y-bbox[1]),text,font=face,fill='white')
mask=np.zeros((256,256),dtype=bool);cursor=0
for x0,y0,x1,y1 in parts:
 width=x1-x0;target.paste(strip.crop((cursor,0,cursor+width,24)),(x0,y0));mask[y0:y1,x0:x1]=True;cursor+=width
assert cursor==strip.width
touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):
 pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=encoded[pos]
final=decode(block)
assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),'Frame or adjacent art changed'
(ROOT/'prompt-fixed.bin').write_bytes(block)
(ROOT/'prompt_patch.json').write_text(json.dumps({'archive_offset':start,'sprite_offset':tile*SIZE,'entry':entry,'length':length}))
strip.save(ROOT/'prompt-preview.png');final.save(ROOT/'prompt-atlas.png')
print('Prompt rebuilt with continuous typography and original frame preserved.')
