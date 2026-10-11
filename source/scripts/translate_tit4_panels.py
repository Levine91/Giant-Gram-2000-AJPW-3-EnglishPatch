"""Localize the six ranking/VM tutorial tiles without changing their sprite layout."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-tit4-panels';B.mkdir(exist_ok=True)
for name in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/name).exists():shutil.copy2(G/name,B/name)
a=(B/'TEX.AFS').read_bytes();base=2379776
images={t:decode(a[base+t*SIZE:base+(t+1)*SIZE]) for t in range(5,11)};masks={t:np.zeros((256,256),bool) for t in images};labels=[]
styles={'gold':((255,255,153,255),(221,136,0,255)),'goldblue':((255,255,153,255),(0,0,255,255)),'green':((255,255,255,255),(0,221,102,255)),'white':((255,255,255,255),(136,102,0,255)),'blue':((255,255,255,255),(0,0,255,255)),'cream':((255,255,187,255),(153,34,0,255)),'yellow':((255,255,0,255),(0,0,0,255))}
def art(text,w,h,style,size,italic=True):
 font=ImageFont.truetype('C:/Windows/Fonts/'+('arialbi.ttf' if italic else 'arialbd.ttf'),size)
 box=font.getbbox(text,stroke_width=1);out=Image.new('RGBA',(box[2]-box[0]+4,box[3]-box[1]+4));fill,edge=styles[style]
 ImageDraw.Draw(out).text((2-box[0],2-box[1]),text,font=font,fill=fill,stroke_width=1,stroke_fill=edge)
 out=out.crop(out.getbbox());out=out.resize((min(w-2,round(out.width*h/out.height)),h),Image.Resampling.LANCZOS)
 return out
def put(tile,rect,text,style,height,italic=True,bg=False):
 x,y,x1,y1=rect;im=images[tile]
 if bg:
  # Restore the original gold button fill by the most common color per row.
  for yy in range(y,y1):
   values,counts=np.unique(np.asarray(im)[yy,x:x1],axis=0,return_counts=True);color=tuple(values[np.argmax(counts)]);im.paste(color,(x,yy,x1,yy+1))
 else:im.paste((0,0,0,0),rect)
 masks[tile][y:y1,x:x1]=True
 if text:
  out=art(text,x1-x,height,style,40,italic);im.alpha_composite(out,(x+(x1-x-out.width)//2,y+(y1-y-height)//2))
 labels.append({'tile':tile,'rect':rect,'text':text,'lettering_height':height,'style':style})
def packed(tile,y,step,width,text,style,height):
 wide=Image.new('RGBA',(width,step));out=art(text,width,height,style,64);wide.alpha_composite(out,((width-out.width)//2,(step-height)//2))
 for k in range((width+255)//256):
  w=min(256,width-k*256);put(tile,(0,y+k*step,w,y+(k+1)*step),'',style,height);images[tile].paste(wide.crop((k*256,0,k*256+w,step)),(0,y+k*step))
 labels.append({'tile':tile,'text':text,'packed_width':width,'lettering_height':height,'style':style})
put(5,(0,0,128,32),'MOST DEFENSES','gold',28)
put(5,(0,32,160,64),'RANKING','gold',28)
put(5,(0,64,80,96),'Defenses','gold',22)
put(5,(96,64,200,96),'Wrestler','gold',22)
for j,text in enumerate(['Nickname','Name','Signature Move 1','Signature Move 2']):put(5,(4,132+j*32,120,156+j*32),text,'white',20,False,True)
packed(6,0,32,432,'CURRENT CHAMPION','goldblue',30)
for rect,text in [((0,64,176,96),'TITLE DEFENSES!'),((216,64,256,96),'NO.'),((0,96,64,128),''),((192,96,256,128),'FIRST')]:put(6,rect,text,'goldblue',30)
for j,(text,w) in enumerate([('STRIKING KING',104),('SUPLEX KING',224),('TECHNICAL KING',176),('COMICAL KING',152)]):put(6,(0,128+j*32,w,160+j*32),text,'green',30)
put(7,(24,72,192,144),'COMPATIBLE!','blue',60)
packed(7,144,40,480,'Play in the arcade, too!','blue',32)
# Match the original gold emphasis on the arcade portion of the sentence.
wide=Image.new('RGBA',(480,40));left=art('Play in the ',180,32,'blue',40);right=art('arcade, too!',250,32,'cream',40);total=left.width+right.width+8;xx=(480-total)//2;wide.alpha_composite(left,(xx,4));wide.alpha_composite(right,(xx+left.width+8,4))
images[7].paste(wide.crop((0,0,256,40)),(0,144));images[7].paste(wide.crop((256,0,480,40)),(0,184))
put(8,(0,0,256,256),'','blue',32)
put(8,(0,40,224,80),'Train your wrestler','blue',32)
packed(8,88,72,512,'BECOME A CHAMPION!','cream',62)
put(9,(0,0,256,256),'','blue',32)
packed(9,0,48,384,'Save your trained wrestler to a VM','blue',32)
put(9,(0,96,256,136),'Triple Crown / World Tag','blue',32)
packed(9,144,48,320,'Aim for the championship!','cream',32)
put(10,(0,144,256,176),'Never remove the VM','yellow',20,False)
put(10,(0,176,232,208),'while loading a file.','yellow',20,False)
put(10,(0,224,256,256),'Connect VM below the monitor','blue',22,False)
patches=[];finals={}
for tile,im in images.items():
 off=base+tile*SIZE;old=a[off:off+SIZE];mask=masks[tile];touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,old,touched,'4444');enc=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=enc[p]
 final=decode(out);assert np.array_equal(np.asarray(decode(old))[~mask],np.asarray(final)[~mask]),tile
 name=f'tit4-translated-{tile}.bin';(R/name).write_bytes(out);patches.append([off,name]);finals[tile]=final
sheet=Image.new('RGB',(768,560),(40,40,40));d=ImageDraw.Draw(sheet)
for j,(tile,im) in enumerate(finals.items()):x=j%3*256;y=j//3*280;sheet.paste(im,(x,y),im);d.text((x,y+258),str(tile),fill='white')
sheet.save(R/'tit4-translated-review.png');(R/'tit4-texture-patches.json').write_text(json.dumps(patches));(R/'tit4-translation-report.json').write_text(json.dumps(labels,indent=2))
print('Six translated panels encoded; untouched artwork verified.')
