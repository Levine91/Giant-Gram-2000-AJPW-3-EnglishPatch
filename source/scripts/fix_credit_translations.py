"""Translate the three remaining Japanese credit cards across their tile seams."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import decode,SIZE,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
backup=R/'before-credit-translations';backup.mkdir(exist_ok=True)
if not (backup/'TEX.AFS').exists():shutil.copy2(G/'TEX.AFS',backup/'TEX.AFS')
a=(backup/'TEX.AFS').read_bytes();entry=json.loads((R/'game-entries.json').read_text())['spr_gam3'][0]
cards=[(23,None,'ALL JAPAN PRO WRESTLING CO., LTD.'),(25,'VIDEO FOOTAGE COURTESY OF','NIPPON TELEVISION NETWORK CORPORATION'),(27,'PHOTOGRAPHS COURTESY OF','TOKYO SPORTS NEWSPAPER')]
patches=[]
for first,heading,company in cards:
 old=Image.new('RGBA',(512,256));blocks=[]
 for j in range(2):
  off=entry+(first+j)*SIZE;block=a[off:off+SIZE];blocks.append(block);old.paste(decode(block),(j*256,0))
 im=old.copy();mask=np.zeros((256,512),bool)
 for text,rect,size,stroke in [(heading,(0,112,512,136),18,(153,68,0,255)),(company,(0,140,512,176),24,(68,17,34,255))]:
  if text is None:continue
  im.paste((0,0,0,0),rect);mask[rect[1]:rect[3],:]=True
  font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size);bb=font.getbbox(text,stroke_width=1)
  art=Image.new('RGBA',(bb[2]-bb[0]+4,bb[3]-bb[1]+4));ImageDraw.Draw(art).text((2-bb[0],2-bb[1]),text,font=font,fill='white',stroke_width=1,stroke_fill=stroke)
  art=art.crop(art.getbbox())
  if art.width>488:art=art.resize((488,art.height),Image.Resampling.LANCZOS)
  assert art.height<=rect[3]-rect[1]-4
  im.alpha_composite(art,((512-art.width)//2,rect[1]+(rect[3]-rect[1]-art.height)//2))
 final=Image.new('RGBA',(512,256))
 for j,original in enumerate(blocks):
  target=im.crop((j*256,0,(j+1)*256,256));m=mask[:,j*256:(j+1)*256];touched=m.reshape(128,2,128,2).any(axis=(1,3))[::-1]
  adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);out=bytearray(adapted)
  for y,x in zip(*np.nonzero(touched)):
   at=2048+spread(int(y))+(spread(int(x))<<1);out[at]=encoded[at]
  decoded=decode(out);assert np.array_equal(np.asarray(decode(original))[~m],np.asarray(decoded)[~m])
  name=f'credits-spr_gam3-{first+j}.bin';(R/name).write_bytes(out);patches.append([entry+(first+j)*SIZE,name]);final.paste(decoded,(j*256,0))
 final.resize((1024,512)).save(R/f'credits-translated-{first}.png')
(R/'credits-texture-patches.json').write_text(json.dumps(patches))
(R/'credits-translations-report.json').write_text(json.dumps({'cards':cards,'unrelated_pixels_unchanged':True,'tile_seams_preserved':True},indent=2))
print('Three credit cards translated across six tiles; bounds and unchanged artwork verified.')
