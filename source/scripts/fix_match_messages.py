"""Translate shared match sprites while preserving adjacent art and atlas geometry."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import decode,SIZE,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(G/'TEX.AFS').read_bytes();entries=json.loads((R/'game-entries.json').read_text());entries['spr_sys']=[978944,110592]
jobs={}
def add(file,tile,rect,text,size=14,color='white',outline=1):
 jobs.setdefault((file,tile),[]).append((rect,text,size,color,outline))
for file in ['spr_gam','spr_gam5','spr_sys']:
 tile=5 if file=='spr_sys' else 10
 for rect,text,size in [((0,0,64,16),'Win Streak!',10),((88,0,144,16),'First Win!',10),((152,0,248,16),'Challengers Wanted!',9)]:add(file,tile,rect,text,size)
for file in ['spr_gam','spr_gam5']:
 add(file,10,(0,16,224,36),'Press all 3 buttons for a reversal!',12,(255,221,68,255))
 add(file,10,(0,200,88,224),'PIN',19,(255,221,68,255))
 add(file,10,(0,232,160,256),'RING IN / OUT',18,(255,221,68,255))
 add(file,15,(0,144,160,166),'Kenji Wakabayashi',15,'white',3)
 add(file,15,(0,166,160,184),'Commentary (Nippon TV)',11,'white',2)
 add(file,22,(0,0,256,64),'THREE COUNT!',30,'white',2)
 add(file,22,(0,64,256,128),'SUBMISSION',30,'white',2)
 add(file,22,(0,128,256,192),'',30,'white',2)
 add(file,22,(0,192,128,256),'',30)
 add(file,23,(0,0,256,64),'TIME LIMIT',30,'white',2)
 add(file,23,(0,64,256,128),'DRAW',30,'white',2)

left=['Lateral Press','Cradle Pin','Leg-Hook Pin','German Suplex','Dragon Suplex','Tiger Suplex','Northern Lights','Victory Roll']
right=['Jackknife Pin','Neck Pin','Submission','Referee Stop','Time Limit','Scarf Hold']
for file,tile,summary,extra in [('spr_gam',17,19,20),('spr_gam5',17,19,20),('spr_gam4',0,2,3)]:
 for i,text in enumerate(left):add(file,tile,(0,i*32,128,i*32+32),text,14)
 for i,text in enumerate(right):add(file,tile,(128,i*32,256,i*32+32),text,14)
 add(file,tile,(160,224,184,248),'m',17)
 add(file,tile,(192,224,216,248),'s',17)
 # The attendance line wraps across three atlas strips. Keep its underline.
 add(file,summary,(8,224,112,248),'Attendance',16)
 add(file,summary,(192,224,216,248),'',16)
 add(file,summary,(216,224,256,248),'',16)
 add(file,summary,(176,192,232,216),'',16)
 for i,text in enumerate(['Tiger Suplex 85','Back Suplex','Leg-Trap Jackknife','Forward Roll','Trapping Suplex','Ground Cobra','Side Cradle','Rolling Cradle']):add(file,extra,(0,i*32,128,(i+1)*32),text,14)
 add(file,extra,(160,0,224,24),'Draw',15)

credit_only='--credit-only' in sys.argv
if credit_only:jobs={key:val for key,val in jobs.items() if key[1]==15}
patches=json.loads((R/'match-texture-patches.json').read_text()) if credit_only else []
if credit_only:
 offsets={entries[file][0]+tile*SIZE for file,tile in jobs};patches=[p for p in patches if p[0] not in offsets]
for (file,tile),labels in jobs.items():
 start=entries[file][0]+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 for rect,text,size,color,outline in labels:
  x0,y0,x1,y1=rect;im.paste((0,0,0,0),rect);mask[y0:y1,x0:x1]=True
  if not text:continue
  font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size);d=ImageDraw.Draw(im);box=d.textbbox((0,0),text,font=font,stroke_width=outline)
  while box[2]-box[0]>x1-x0-2 or box[3]-box[1]>y1-y0-2:
   size-=1;assert size>=8,(file,tile,text);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size);box=d.textbbox((0,0),text,font=font,stroke_width=outline)
  d.text((x0+(x1-x0-box[2]+box[0])//2-box[0],y0+(y1-y0-box[3]+box[1])//2-box[1]),text,font=font,fill=color,stroke_width=outline,stroke_fill=(221,0,0,255) if tile==15 else 'black')
 if (file in ['spr_gam','spr_gam5'] and tile==19) or (file=='spr_gam4' and tile==2):
  strip=Image.new('RGBA',(96,24));d=ImageDraw.Draw(strip);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',16)
  d.text((0,2),'(Popularity',font=font,fill='white',stroke_width=1,stroke_fill='black')
  im.paste(strip.crop((0,0,40,24)),(216,224));im.paste(strip.crop((40,0,96,24)),(176,192))
 if file in ['spr_gam','spr_gam5'] and tile==22:
  strip=Image.new('RGBA',(384,64));d=ImageDraw.Draw(strip);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32);text='REFEREE STOP';box=d.textbbox((0,0),text,font=font,stroke_width=2)
  d.text(((384-box[2]+box[0])//2-box[0],(64-box[3]+box[1])//2-box[1]),text,font=font,fill='white',stroke_width=2,stroke_fill='black')
  im.paste(strip.crop((0,0,256,64)),(0,128));im.paste(strip.crop((256,0,384,64)),(0,192))
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);block=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  at=2048+spread(int(y))+(spread(int(x))<<1);block[at]=encoded[at]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),(file,tile)
 name=f'match-{file}-{tile}.bin';(R/name).write_bytes(block);final.save(R/name.replace('.bin','.png'));patches.append([start,name])
(R/'match-texture-patches.json').write_text(json.dumps(patches))
print('Verified',len(patches),'match texture blocks; adjacent art unchanged.')
