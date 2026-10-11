from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
start=4046848+5*SIZE
original=(G/'TEX.AFS').read_bytes()[start:start+SIZE]
old=decode(original);target=old.copy();mask=np.zeros((256,256),bool)
font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',28)
for x,text in [(0,'GIANT BABA'),(136,'STAN HANSEN')]:
 strip=Image.new('RGBA',(160,32));d=ImageDraw.Draw(strip);box=d.textbbox((0,0),text,font=font);w=box[2]-box[0];h=box[3]-box[1]
 left=(160-w-2)//2-box[0];top=(32-h-2)//2-box[1]
 d.text((left+2,top+2),text,font=font,fill=(255,180,0,255),stroke_width=2,stroke_fill='black')
 d.text((left,top),text,font=font,fill='black',stroke_width=1,stroke_fill='black')
 ink=Image.new('L',strip.size);ImageDraw.Draw(ink).text((left,top),text,font=font,fill=255)
 pixels=np.zeros((32,160,4),dtype=np.uint8)
 for row in range(32):
  t=max(0,min(1,(row-top-box[1])/max(h-1,1)));pixels[row,:,:3]=np.array([255,250,255])*(1-t)+np.array([102,95,126])*t;pixels[row,:,3]=255
 gradient=Image.fromarray(pixels);gradient.putalpha(ink);strip.alpha_composite(gradient)
 assert strip.getbbox()[0]>0 and strip.getbbox()[2]<160
 strip=strip.resize((120,32),Image.Resampling.LANCZOS)
 target.paste((0,0,0,0),(x,12,x+120,44));target.paste(strip,(x,12));mask[12:44,x:x+120]=True
# Center the existing VS artwork in the visible gap, not the unequal name slots.
vs=old.crop((120,12,136,44));vb=vs.getbbox()
left_box=target.crop((0,12,120,44)).getbbox();right_box=target.crop((136,12,256,44)).getbbox()
center=(left_box[2]+136+right_box[0])/2
vx=round(center-(vb[0]+vb[2])/2)
target.paste((0,0,0,0),(112,12,138,44));target.paste(vs,(vx,12))
mask[12:44,112:138]=True
assert abs(vx+(vb[0]+vb[2])/2-center)<=0.5
changed=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
adapted=adapt_codebook(target,original,changed,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
for y,x in zip(*np.nonzero(changed)):
 p=2048+spread(int(y))+(spread(int(x))<<1);block[p]=encoded[p]
final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),'Unrelated names changed'
(R/'history-sample.bin').write_bytes(block)
(R/'history-texture-patches.json').write_text(json.dumps([[start,'history-sample.bin']]))
final.crop((0,0,256,48)).resize((1024,192),Image.Resampling.NEAREST).save(R/'history-sample-preview.png')
print('Exactly two sample labels changed; all other pixels preserved.')
