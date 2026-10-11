from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook,read_labels
from patch_english_menu import encode
entries=json.loads((R/'caw-entries.json').read_text())|json.loads((R/'game-entries.json').read_text());a=(G/'TEX.AFS').read_bytes();jobs={}
entries['spr_sys']=[978944,110592]
def add(file,tile,rect,text,size=16,color='white',align='center'):
 jobs.setdefault((file,tile),[]).append((rect,text,size,color,align))
for file in ['spr_gam','spr_gam5']:
 add(file,13,(0,100,64,128),'Learning',20,(255,230,140,255))
for file in ['spr_gam','spr_gam5']:
 for rect,text in [((28,164,88,188),'Select'),((120,164,200,188),'Confirm'),((148,132,208,156),'Back')]:add(file,12,rect,text,18,(255,221,68,255),'left')
 add(file,14,(0,176,96,200),'Moves Left',18)
 add(file,19,(0,192,96,216),'Accuracy',18)
for file,tile in [('spr_sys',5),('spr_gam',10),('spr_gam5',10)]:add(file,tile,(0,96,256,112),'CHALLENGERS WANTED!',14)
for x0,x1,names in [(0,100,['Move Fusion','Delete Moves','Quotes','Taunt','Tag Moves','Signature Name','Double Team']),(100,192,['Tactics','Name','Body Type','Catchphrase','Height','Weight'])]:
 for i,n in enumerate(names):add('spr_cmk',6,(x0,i*32,x1,i*32+32),n,24)
for i,l in enumerate(['Training','Save','Retire']):add('spr_cmk2',41,(16,48+i*32,96,80+i*32),l,24)
for i,l in enumerate(['Shop','Load','Suspend']):add('spr_cmk2',41,(104,48+i*32,208,80+i*32),l,24)
for rect,text in [((60,0,128,32),'Mask'),((136,0,208,32),'Chest'),((56,32,128,64),'Elbow'),((136,32,208,64),'Wrist'),((56,64,128,96),'Waist'),((128,64,208,96),'Knee'),((56,96,128,128),'Feet')]:add('spr_cmk2',13,rect,text,24,'yellow')
for rect,text in [((52,120,112,148),'Select'),((144,120,224,148),'Confirm'),((0,160,60,188),'Back')]:add('spr_cmk2',10,rect,text,24,'yellow','left')
for rect,text in [((136,64,256,96),'Locker Room'),((136,128,256,156),'Status'),((136,156,256,184),'Move List')]:add('spr_cmk2',29,rect,text,24,'yellow','left')
add('spr_cmk2',23,(0,112,88,160),'Move List',24,'yellow','right')
# Dialog fragments must be drawn as single continuous sentences before splitting.
stitches={('spr_cmk2',6):[((0,0,256,32),(0,32,176,64),'Are you sure you want to overwrite this slot?',24,'white')],('spr_cmk2',5):[((0,128,256,160),(0,160,192,192),'Are you sure you want to exit Create-A-Wrestler?',24,'white'),((0,224,256,240),(0,240,96,256),'(Remember to save your game!)',16,'yellow')]}
for key in stitches:jobs.setdefault(key,[])
patches=[]
original_labels={}
for i,batch in enumerate(json.loads((G/'English_CAW/label_batches.json').read_text())):
 original_labels.update(read_labels(G/f'English_CAW/labels_{i}_mask.png',[batch[:20],batch[20:]] if len(batch)>20 else [batch]))

# Reuse one alphabet from the original first sheet, rather than differently drawn batches.
glyphs={}
first_batch=json.loads((G/'English_CAW/label_batches.json').read_text())[0]
for name in first_batch:
 source=original_labels[name];alpha=np.asarray(source.getchannel('A'))
 columns=np.flatnonzero((alpha>100).any(0))
 groups=np.split(columns,np.where(np.diff(columns)>1)[0]+1)
 letters=name.replace(' ','')
 if len(groups)!=len(letters):continue
 for ch,cols in zip(letters,groups):
  if ch not in glyphs:glyphs[ch]=source.crop((int(cols[0]),0,int(cols[-1])+1,source.height))
def legacy_text(text):
 assert all(ch==' ' or ch in glyphs for ch in text),text
 w=sum(16 if ch==' ' else glyphs[ch].width+3 for ch in text)-3
 art=Image.new('RGBA',(w,40));x=0
 for ch in text:
  if ch==' ':x+=16;continue
  art.alpha_composite(glyphs[ch],(x,0));x+=glyphs[ch].width+3
 return art

def render(text,size,color,width,height):
 if text=='CHALLENGERS WANTED!':
  f=ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf',56)
  def banner(word):
   box=f.getbbox(word);im=Image.new('L',(box[2]-box[0]+20,box[3]-box[1]+4));ImageDraw.Draw(im).text((4-box[0],2-box[1]),word,font=f,fill=255)
   im=im.transform((im.width+12,im.height),Image.Transform.AFFINE,(1,.23,-im.height*.23,0,1,0),Image.Resampling.BICUBIC)
   return im.crop(im.getbbox())
  ref=banner('PRESS START BUTTON');ink=banner(text)
  w=round(ink.width*220/ref.width);ink=ink.resize((w,10),Image.Resampling.LANCZOS)
  from PIL import ImageFilter
  alpha=Image.new('L',(w+2,12));alpha.paste(ink,(1,1));art=Image.new('RGBA',alpha.size,'black');art.putalpha(alpha.filter(ImageFilter.MaxFilter(3)));white=Image.new('RGBA',art.size,'white');white.putalpha(alpha);art.alpha_composite(white)
  assert art.width<=256
  return art,6
 if file in ['spr_gam','spr_gam5'] and tile in [12,14,19]:
  f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',17);cap=f.getbbox('H');box=f.getbbox(text)
  art=Image.new('RGBA',(box[2]-box[0]+4,max(box[3],f.getbbox('Ag')[3])-cap[1]+4))
  ImageDraw.Draw(art).text((2-box[0],2-cap[1]),text,font=f,fill=color,stroke_width=1,stroke_fill='black')
  assert art.width<=width,(text,art.width,width)
  return art,2+(cap[3]-cap[1])/2
 if (file,tile) in [('spr_cmk',6),('spr_cmk2',41),('spr_cmk2',10),('spr_cmk2',29),('spr_cmk2',23)]:
  source=legacy_text(text)
  top,cap=0,32
  # Shared cap height and width scale; never squeeze individual words to fit.
  bubble=(file,tile) in [('spr_cmk',6),('spr_cmk2',41)]
  size=18 if bubble else 20
  sx=.54 if bubble else .72
  w=round(source.width*size/cap*sx);h=round(source.height*size/cap)
  art=Image.new('RGBA',(w,h),color)
  art.putalpha(source.getchannel('A').resize((w,h),Image.Resampling.LANCZOS))
  assert w<=width-2,(text,w,width)
  return art,top*size/cap+size/2
 f=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',size);f.set_variation_by_axes([400,75])
 cap=f.getbbox('H');b=f.getbbox(text);stroke=1 if text=='Learning' else 0
 top=cap[1];h=max(f.getbbox('Ag')[3],b[3])-top+2+stroke*2
 art=Image.new('RGBA',(b[2]-b[0]+2+stroke*2,h))
 ImageDraw.Draw(art).text((1+stroke-b[0],1+stroke-top),text,font=f,fill=color,stroke_width=stroke,stroke_fill=(210,40,0,255))
 scale=.625 if (file,tile) in [('spr_cmk',6),('spr_cmk2',41)] else .70 if (file,tile) in [('spr_cmk2',10),('spr_cmk2',29),('spr_cmk2',23)] else 1
 art=art.resize((round(art.width*scale),art.height),Image.Resampling.LANCZOS)
 assert art.width<=width-2,(text,art.width,width)
 return art,1+stroke+(cap[3]-cap[1])/2
for (file,tile),labels in jobs.items():
 off=entries[file][0]+tile*SIZE;original=a[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 if file=='spr_cmk2' and tile==23:
  im.paste((0,0,0,0),(0,112,144,160));im.paste(old.crop((57,200,112,248)),(89,112));mask[112:160,:144]=True
 # Clear all edited regions before painting, because neighboring source rectangles overlap.
 for (x0,y0,x1,y1),text,size,color,align in labels:
  im.paste((0,0,0,0),(x0,y0,x1,y1));mask[y0:y1,x0:x1]=True
 for (x0,y0,x1,y1),text,size,color,align in labels:
  art,cy=render(text,size,color,x1-x0,y1-y0)
  cx=(x0+x1)/2;center_y=109 if text=='Learning' else 105 if text=='CHALLENGERS WANTED!' else (y0+y1)/2
  if file=='spr_cmk' and tile==6:
   cx=52 if x0==0 else 142 if text=='Catchphrase' else 140
   center_y=y0+18+(2 if text=='Tag Moves' else 0)
  if file=='spr_cmk2' and tile==41:cx=52 if x0==16 else 148;center_y=y0+18
  if file=='spr_cmk2' and tile==13:cx=92 if x0<128 else 164;center_y=y0+16
  if file=='spr_cmk2' and tile==10:center_y=136 if y0==120 else 176
  if file=='spr_cmk2' and tile==29:center_y=y0+12
  if file=='spr_cmk2' and tile==23:center_y=132
  x=round(cx-art.width/2)
  if align=='left':x=(148 if tile==29 else x0+2)
  if align=='right':x=x1-art.width-4
  im.alpha_composite(art,(x,round(center_y-cy)))
 for p,q,text,size,color in stitches.get((file,tile),[]):
  w=p[2]-p[0]+q[2]-q[0];h=p[3]-p[1];strip=Image.new('RGBA',(w,h));art,cy=render(text,size,color,w,h);shift=(-8 if tile==5 and color=='white' else 4 if color=='yellow' else 0);strip.alpha_composite(art,((w-art.width)//2+shift,round(h/2-cy)))
  for rect in [p,q]:
   x0,y0,x1,y1=rect;im.paste((0,0,0,0),rect);mask[y0:y1,x0:x1]=True
  # Clear the unused tail of the overwrite dialog's formerly separate question.
  if tile==6:im.paste((0,0,0,0),(176,32,256,64));mask[32:64,176:256]=True
  im.paste(strip.crop((0,0,p[2]-p[0],h)),(p[0],p[1]));im.paste(strip.crop((p[2]-p[0],0,w,h)),(q[0],q[1]))
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];ad=adapt_codebook(im,original,touched,'4444');enc=encode(im,ad);block=bytearray(ad)
 for yy,xx in zip(*np.nonzero(touched)):
  pos=2048+spread(int(yy))+(spread(int(xx))<<1);block[pos]=enc[pos]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),(file,tile)
 name=f'caw-polish-{file}-{tile}.bin';(R/name).write_bytes(block);patches.append([off,name]);final.save(R/(name+'.png'))
(R/'caw-polish-texture-patches.json').write_text(json.dumps(patches))
print('Prepared',len(patches),'CAW texture fixes; unrelated art preserved.')
