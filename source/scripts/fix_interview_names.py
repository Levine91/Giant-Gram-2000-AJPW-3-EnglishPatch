"""Translate the remaining two interview name atlases; preserve translated labels."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
backup=R/'before-interview-names';backup.mkdir(exist_ok=True)
if not (backup/'TEX.AFS').exists():shutil.copy2(G/'TEX.AFS',backup/'TEX.AFS')
a=(backup/'TEX.AFS').read_bytes();entry=json.loads((R/'game-entries.json').read_text())['spr_gam3'][0]
rows={1:[],2:[],3:[],31:[]}
for i,name in enumerate(['The Crusher','The Destroyer','D. Bruiser','C. Lisowski','F. V. Erich','B. Brazil']):rows[3].append((0,i*20,name))
message='Enjoy the rest in the full version.'
for i,name in enumerate(['G. Baba','Misawa','Kawada','Taue','Kobashi','Akiyama','S. Hansen','Vader','G. Albright','J. Ace','Hase']):rows[1].append((0,24+i*20,name))
rows[1].append((128,24,'Wolf'))
for i,name in enumerate(['The Killer B.I.','Grace','Hyper','Diablo','Tiger','Omori','Takayama']):rows[1].append((128,104+i*20,name))
for i,name in enumerate(['M. Barton','Ogawa','Honda','Kakihara','Shiga','J. Smith','M. Mossman','J. Tsuruta','Ogami','S. H. Edge','Tigre','Prime G. Baba']):
 if name:rows[2].append((0,i*20,name))
for i,name in enumerate(['The Master A.M.','Mangler D.H.','Cyclops E.C.',None,'Original Wrestler','Rikidozan','S. Williams','B. Sammartino','G. Kiniski','D. L. Jonathan','G. Crusher','B. Brody']):
 if name:rows[2].append((128,i*20,name))
font=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',18);patches=[];images=[];widths=[]
# Original Japanese name ink is 13 pixels high. Arial Bold Italic at 18
# matches that cap height; one baseline accommodates English descenders.
baseline=15
for tile,labels in rows.items():
 off=entry+tile*SIZE;original=a[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 for x,y,name in labels:
  rect=(x,y,x+128,y+20);im.paste((0,0,0,0),rect);mask[y:y+20,x:x+128]=True
  bb=font.getbbox(name,anchor='ls',stroke_width=1)
  assert baseline+bb[1]>=0 and baseline+bb[3]<=20,(name,bb)
  art=Image.new('RGBA',(bb[2]-bb[0]+4,20))
  ImageDraw.Draw(art).text((2-bb[0],baseline),name,font=font,anchor='ls',fill=(255,238,153,255),stroke_width=1,stroke_fill='black')
  bounds=art.getbbox();art=art.crop((bounds[0],0,bounds[2],20))
  natural_width=art.width
  if art.width>124:art=art.resize((124,20),Image.Resampling.LANCZOS)
  assert art.width<=124 and art.height==20
  widths.append({'name':name,'natural_width':natural_width,'width':art.width})
  im.alpha_composite(art,(x+2,y))
 if tile==31:
  # The original sentence is one horizontal banner packed into three
  # consecutive 256-pixel strips, not three separate display lines.
  im.paste((0,0,0,0),(0,0,256,120));mask[:120,:]=True
  face=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30)
  bb=face.getbbox(message,stroke_width=1)
  art=Image.new('RGBA',(bb[2]-bb[0]+4,40))
  ImageDraw.Draw(art).text((2-bb[0],30),message,font=face,anchor='ls',fill=(255,255,153,255),stroke_width=1,stroke_fill='black')
  if art.width>520:art=art.resize((520,40),Image.Resampling.LANCZOS)
  banner=Image.new('RGBA',(528,40));banner.alpha_composite(art,((528-art.width)//2,0))
  assert banner.getbbox()[2]<=528 and banner.getbbox()[3]<40
  for k in range(3):im.alpha_composite(banner.crop((k*256,0,min((k+1)*256,528),40)),(0,k*40))
  rebuilt=Image.new('RGBA',(528,40))
  for k in range(3):rebuilt.paste(im.crop((0,k*40,min(256,528-k*256),(k+1)*40)),(k*256,0))
  assert rebuilt.tobytes()==banner.tobytes()
  banner.resize((1056,80)).save(R/'full-version-message-preview.png')
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
 for yy,xx in zip(*np.nonzero(touched)):
  at=2048+spread(int(yy))+(spread(int(xx))<<1);out[at]=encoded[at]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
 name=f'interview-spr_gam3-{tile}.bin';(R/name).write_bytes(out);final.resize((768,768),Image.Resampling.NEAREST).save(R/(name+'.png'));patches.append([off,name]);images.append(final)
(R/'interview-texture-patches.json').write_text(json.dumps(patches))
(R/'interview-names-report.json').write_text(json.dumps({'labels':rows,'count':sum(map(len,rows.values())),'full_version_message':message,'font_size':18,'original_ink_height':13,'baseline':baseline,'vertical_resizing':False,'widths':widths,'headers_and_other_pixels_preserved':True},indent=2))
print('Translated',sum(map(len,rows.values())),'remaining labels. All fit their cells; existing English and unrelated pixels unchanged.')
