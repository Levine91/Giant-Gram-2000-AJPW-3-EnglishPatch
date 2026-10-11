"""Two-name approval sample only: one continuous strip per introduction name."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(G/'TEX.AFS').read_bytes();entry=5779456
font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',48)
patches=[]
for tile,y,text in [(41,0,'MITSUHARU MISAWA'),(44,128,'TAMON HONDA')]:
 start=entry+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);target=old.copy()
 strip=Image.new('RGBA',(416,64));d=ImageDraw.Draw(strip);box=d.textbbox((0,0),text,font=font)
 w=box[2]-box[0];h=box[3]-box[1];assert w+10<=416 and h+10<=64
 x=(416-w-4)//2-box[0];top=(64-h-4)//2-box[1]
 d.text((x+4,top+4),text,font=font,fill=(255,180,0,255),stroke_width=3,stroke_fill='black')
 d.text((x,top),text,font=font,fill='black',stroke_width=2,stroke_fill='black')
 ink=Image.new('L',strip.size);ImageDraw.Draw(ink).text((x,top),text,font=font,fill=255)
 gradient=Image.new('RGBA',strip.size);pixels=np.zeros((64,416,4),dtype=np.uint8)
 for row in range(64):
  t=max(0,min(1,(row-(top+box[1]))/max(h-1,1)));c=np.array([255,250,255])*(1-t)+np.array([102,95,126])*t
  if row%3==0:c=np.minimum(255,c+18)
  pixels[row,:,:3]=c;pixels[row,:,3]=255
 gradient=Image.fromarray(pixels);gradient.putalpha(ink);strip.alpha_composite(gradient)
 target.paste((0,0,0,0),(0,y,256,y+128))
 target.paste(strip.crop((0,0,256,64)),(0,y));target.paste(strip.crop((256,0,416,64)),(0,y+64))
 mask=np.zeros((256,256),bool);mask[y:y+128,:]=True;touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
 for yy,xx in zip(*np.nonzero(touched)):
  p=2048+spread(int(yy))+(spread(int(xx))<<1);block[p]=encoded[p]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),'Another wrestler changed'
 name=f'intro-sample-{tile}.bin';(R/name).write_bytes(block);patches.append([start,name]);strip.save(R/f'intro-sample-{tile}.png')
(R/'intro-texture-patches.json').write_text(json.dumps(patches))
print('Prepared exactly two names; other wrestlers preserved pixel-for-pixel.')
