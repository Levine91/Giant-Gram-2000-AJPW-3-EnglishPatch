from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(G/'TEX.AFS').read_bytes();patches=[]

def edit(entry,tile,paint):
 start=entry+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 def label(rect,text,size=18,color='white',italic=False,outline=0,bg=(0,0,0,0),align="center"):
  x0,y0,x1,y1=rect;im.paste(bg,rect);mask[y0:y1,x0:x1]=True
  if not text:return
  font=ImageFont.truetype('C:/Windows/Fonts/'+('arialbi.ttf' if italic else 'arialbd.ttf'),size)
  box=font.getbbox(text,stroke_width=outline);w=box[2]-box[0];h=box[3]-box[1]
  art=Image.new('RGBA',(w+2,h+2));ImageDraw.Draw(art).text((1-box[0],1-box[1]),text,font=font,fill=color,stroke_width=outline,stroke_fill='black')
  if text.startswith('Recreate '):
   before='Recreate ';number=text[len(before):len(before)+2]
   ImageDraw.Draw(art).text((1-box[0]+font.getlength(before),1-box[1]),number,font=font,fill='white',stroke_width=1,stroke_fill=(32,0,153,255))
  scale=min(1,(x1-x0-2)/art.width,(y1-y0-2)/art.height)
  if scale<1:art=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
  im.alpha_composite(art,(x0+2 if align=="left" else x0+(x1-x0-art.width)//2,y0+(y1-y0-art.height)//2))
 paint(im,mask,label)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);block=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  at=2048+spread(int(y))+(spread(int(x))<<1);block[at]=encoded[at]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),'Unrelated pixels changed'
 name=f'history-ui-{entry}-{tile}.bin';(R/name).write_bytes(block);patches.append([start,name]);final.save(R/(name+'.png'))

def instructions(im,mask,label):
 label((0,0,172,28),'Record Attendance',18)
 label((0,28,24,56),'') # Japanese people counter; number remains unchanged.
 label((30,132,194,160),'Start Match',19,(170,153,221,255),align='left')
 label((30,160,256,188),'Watch Movie',19,(170,153,221,255),align='left')
 for y,pct in [(192,80),(224,90)]:
  label((0,y,256,y+32),f'Recreate {pct}% or more to clear!',18,(255,255,136,255),True,1)

def target(im,mask,label):
 label((0,0,156,32),'Target Attendance:',16,(255,255,153,255),True,1)
 label((0,32,40,64),'')

def buttons(im,mask,label):
 # The game overlays its unchanged 1–12 counter in the middle gap.
 # Preserve the blue frame and tintable background, including selected state.
 bg=im.getpixel((60,14))
 label((10,8,38,36),'No.',17,'white',bg=bg)
 label((72,8,124,36),'MATCH',17,'white',bg=bg)

edit(2803712,12,instructions);edit(3770368,14,target);edit(4046848,3,buttons)
(R/'history-ui-texture-patches.json').write_text(json.dumps(patches))
print('History attendance, numbered match buttons, and start/movie/80%/90% instructions translated; unrelated pixels preserved.')
