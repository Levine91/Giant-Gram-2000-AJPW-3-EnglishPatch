"""Localize championship atlas cells using the existing game texture pipeline."""
from pathlib import Path
import ast,json,shutil,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
R=Path(__file__).resolve().parent; G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-champion-panels'; B.mkdir(exist_ok=True)
for name in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/name).exists(): shutil.copy2(G/name,B/name)
a=(B/'TEX.AFS').read_bytes(); base=5779456
images={i:decode(a[base+i*SIZE:base+(i+1)*SIZE]) for i in [6,7,12,32,33]}
masks={i:np.zeros((256,256),bool) for i in images}
labels=[]
def lettering(text,w,h,style='gold',size=32,fixed=False):
 f=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',size)
 box=f.getbbox(text,stroke_width=1)
 ink=Image.new('L',(box[2]-box[0]+4,box[3]-box[1]+4))
 ImageDraw.Draw(ink).text((2-box[0],2-box[1]),text,font=f,fill=255)
 edge=ink.filter(ImageFilter.MaxFilter(3)); art=Image.new('RGBA',ink.size)
 outline=Image.new('RGBA',ink.size,{'gold':(170,68,0,255),'cream':(85,34,0,255),'white':(0,0,0,255),'blue':(0,34,255,255)}[style]);outline.putalpha(edge);art.alpha_composite(outline)
 fill=Image.new('RGBA',ink.size,{'gold':(255,221,0,255),'cream':(255,255,187,255),'white':(255,255,255,255),'blue':(255,255,255,255)}[style])
 if style=='gold':
  d=ImageDraw.Draw(fill)
  for y in range(ink.height):d.line((0,y,ink.width,y),fill=(255,int(170+85*np.sin(np.pi*y/max(1,ink.height-1))),0,255))
 fill.putalpha(ink);art.alpha_composite(fill);art=art.crop(art.getbbox())
 if fixed:
  # Match the original 28-pixel Japanese ink height plus its outline.
  # Long English labels compress horizontally only; all caps share a baseline.
  assert 29<=art.height<=30,(text,art.height)
  art=art.resize((min(w-2,art.width),30),Image.Resampling.LANCZOS)
 else:
  scale=min(1,(w-4)/art.width,(h-4)/art.height)
  art=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
 return art
def put(tile,rect,text,style='gold',size=32,fixed=False):
 x,y,x1,y1=rect; im=images[tile];im.paste((0,0,0,0),rect);masks[tile][y:y1,x:x1]=True
 if text:
  art=lettering(text.upper() if fixed else text,x1-x,y1-y,style,38 if fixed else size,fixed);im.alpha_composite(art,(x+(x1-x-art.width)//2,y+(y1-y-art.height)//2))
 labels.append({'tile':tile,'rect':rect,'text':text})
# The current-champion heading is one 432-pixel strip packed into two rows.
banner=Image.new('RGBA',(432,32));art=lettering('CURRENT CHAMPION',432,32,size=38);banner.alpha_composite(art,((432-art.width)//2,(32-art.height)//2))
put(6,(0,0,256,64),'')
images[6].alpha_composite(banner.crop((0,0,256,32)),(0,0));images[6].alpha_composite(banner.crop((256,0,432,32)),(0,32))
for rect,text in [((0,64,176,96),'Title Defenses!'),((216,64,256,96),'No.'),((0,96,64,128),''),((192,96,256,128),'First'),((0,128,240,160),'Triple Crown Champion'),((0,160,256,192),'World Tag Champions')]:put(6,rect,text,fixed=True)
put(7,(0,0,256,64),'')
for rect,text in [((0,0,32,32),'No.'),((112,0,208,32),'Final Match'),((0,32,256,64),'Challenge the Champion')]:put(7,rect,text,fixed=True)
put(7,(48,76,208,96),'Win to take the title!','white',16)
put(7,(16,96,248,116),'Win or lose, the game ends.','white',16)
for rect,text in [((4,132,120,156),'Nickname'),((4,164,120,188),'Name'),((4,196,120,220),'Signature Move 1'),((4,228,120,252),'Signature Move 2'),((132,228,248,252),'Partner')]:put(7,rect,text,'white',20)
put(7,(128,192,152,216),'VS',size=20)
put(12,(64,224,208,256),'Select Next Match','blue',20)
# Two adjacent full tiles form this 512x256 title.
wide=Image.new('RGBA',(512,256))
for text,rect in [('CURRENT',(0,24,512,120)),('CHAMPIONS',(0,128,512,224))]:
 art=lettering(text,rect[2],rect[3]-rect[1],'cream',100);wide.alpha_composite(art,((512-art.width)//2,rect[1]+(rect[3]-rect[1]-art.height)//2))
for tile in [32,33]:images[tile]=wide.crop(((tile-32)*256,0,(tile-31)*256,256));masks[tile][:]=True
patches=[];decoded={}
for tile,im in images.items():
 off=base+tile*SIZE;old=a[off:off+SIZE];mask=masks[tile];touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,old,touched,'4444');enc=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=enc[p]
 final=decode(out);assert np.array_equal(np.asarray(decode(old))[~mask],np.asarray(final)[~mask]),tile
 name=f'champion-panels-{tile}.bin';(R/name).write_bytes(out);patches.append([off,name]);decoded[tile]=final
(R/'champion-panels-texture-patches.json').write_text(json.dumps(patches))
sheet=Image.new('RGB',(1024,800),(45,45,45))
for col,tile in enumerate([6,7,12]):sheet.paste(decoded[tile],(col*320,0),decoded[tile])
for tile in [32,33]:sheet.paste(decoded[tile],((tile-32)*256,300),decoded[tile])
assembled=Image.new('RGBA',(432,32));assembled.paste(decoded[6].crop((0,0,256,32)),(0,0));assembled.paste(decoded[6].crop((0,32,176,64)),(256,0));sheet.paste(assembled,(0,600),assembled)
sheet.save(R/'champion-panels-review.png')
(R/'champion-panels-report.json').write_text(json.dumps({'labels':labels,'blocks':list(images),'outside_pixels_unchanged':True,'in_game_tested':False},indent=2))
print('Prepared five championship texture blocks; unrelated pixels preserved.')
