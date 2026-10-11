from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(G/'TEX.AFS').read_bytes();entries=json.loads((R/'game-entries.json').read_text());patches=[]

def edit(file,tile,paint):
 start=entries[file][0]+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 def label(rect,text,size=10,color=(255,221,68,255),align='center',clear=None,impact=False):
  x0,y0,x1,y1=rect;area=clear or rect;im.paste((0,0,0,0),area);a,b,c,d=area;mask[b:d,a:c]=True
  if not text:return
  f=ImageFont.truetype('C:/Windows/Fonts/'+('impact.ttf' if impact else 'arialbd.ttf'),size);box=f.getbbox(text,stroke_width=1);w=box[2]-box[0];h=box[3]-box[1]
  art=Image.new('RGBA',(w+2,h+2));ImageDraw.Draw(art).text((1-box[0],1-box[1]),text,font=f,fill=color,stroke_width=1,stroke_fill='black')
  if impact:
   ink=Image.new('L',art.size);ImageDraw.Draw(ink).text((1-box[0],1-box[1]),text,font=f,fill=255)
   grad=Image.new('RGBA',art.size);gd=ImageDraw.Draw(grad)
   for yy in range(art.height):
    t=yy/max(1,art.height-1);color2=tuple(round(a*(1-t)+b*t) for a,b in zip((255,83,48),(255,239,210)))
    gd.line((0,yy,art.width,yy),fill=(*color2,255))
   grad.putalpha(ink);art.alpha_composite(grad)
  if art.width>x1-x0-4:art=art.resize((x1-x0-4,art.height),Image.Resampling.LANCZOS)
  assert art.height<=y1-y0-2
  im.alpha_composite(art,(x0+2 if align=='left' else x0+(x1-x0-art.width)//2,y0+(y1-y0-art.height)//2))
 paint(im,mask,label)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);block=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1);block[p]=encoded[p]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),(file,tile,'Unrelated art changed')
 name=f'history-polish-{file}-{tile}.bin';(R/name).write_bytes(block);patches.append([start,name]);final.save(R/(name+'.png'))

def pause(im,mask,label):
 label((12,200,120,224),'Match Select',10,clear=(0,200,176,224))
def prompts(im,mask,label):
 for rect,text in [((28,164,88,188),'Select'),((120,164,200,188),'Confirm'),((148,132,208,156),'Back')]:label(rect,text,10,align='left')
def hud(im,mask,label):
 # This small label is also sampled independently during a match.
 label((176,192,232,216),'Popularity',10,'white')
 label((216,224,256,248),'',10,'white')
 # Keep the opening parenthesis next to the separately drawn label on results.
 label((244,224,256,248),'(',13,'white')
def remaining(im,mask,label):label((24,208,64,240),'Left',16,'white',clear=(20,208,64,244))
def rules(im,mask,label):
 for rect,text in [((0,0,256,48),'NO TIME LIMIT'),((0,48,176,96),'/ ONE FALL'),((0,96,144,144),'30 MIN'),((0,144,144,192),'60 MIN'),((0,192,184,240),'/ BEST OF 3')]:label(rect,text,30,(255,153,119,255),impact=True,clear=(0,192,184,256) if rect[1]==192 else None)
edit('spr_gam5',9,pause)
for file in ['spr_gam','spr_gam5']:
 edit(file,12,prompts);edit(file,14,remaining);edit(file,19,hud)
edit('spr_gam4',2,hud);edit('spr_gam2',39,rules)
(R/'history-polish-texture-patches.json').write_text(json.dumps(patches))
print('Verified',len(patches),'corrected texture blocks; unrelated pixels preserved.')
