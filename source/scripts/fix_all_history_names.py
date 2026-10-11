"""Roll out approved History Mode lettering; no additional emulator tests."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
FONT_SIZE=28
font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',FONT_SIZE)
small=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',8)
# Each row is the game's existing 256x48 match heading. Tag teams use surnames.
rows={
5:[None,('TSURUTA & BABA','HANSEN & BRODY',None,None),('JUMBO TSURUTA','STAN HANSEN',None,None),('MITSUHARU MISAWA','JUMBO TSURUTA',None,None),('MITSUHARU MISAWA','STAN HANSEN','Challenger','Champion')],
6:[('MISAWA & KOBASHI','KAWADA & TAUE',None,None),('TOSHIAKI KAWADA','MITSUHARU MISAWA','Challenger','Champion'),('MITSUHARU MISAWA','VADER','Challenger','Champion'),('JUN AKIYAMA','TAKAO OMORI',None,None),('KOBASHI & AKIYAMA','OMORI & TAKAYAMA','Champions','Challengers')],
7:[('JUN AKIYAMA','MITSUHARU MISAWA',None,None),('KENTA KOBASHI','VADER','Challenger','Champion')]}
archive=(G/'TEX.AFS').read_bytes();entry=4046848
sample=decode(archive[entry+5*SIZE:entry+6*SIZE]);vs=sample.crop((112,12,136,44));vs=vs.crop(vs.getbbox())
report=[];patches=[];preview=Image.new('RGBA',(256,12*48),(25,25,50,255));index=0

def lettering(text):
 box=font.getbbox(text);w=box[2]-box[0];h=box[3]-box[1]
 width=160 if w<=148 else w+32;strip=Image.new('RGBA',(width,32));d=ImageDraw.Draw(strip)
 left=(width-w-2)//2-box[0];top=(32-h-2)//2-box[1]
 d.text((left+2,top+2),text,font=font,fill=(255,180,0,255),stroke_width=2,stroke_fill='black')
 d.text((left,top),text,font=font,fill='black',stroke_width=1,stroke_fill='black')
 ink=Image.new('L',strip.size);ImageDraw.Draw(ink).text((left,top),text,font=font,fill=255)
 pixels=np.zeros((32,width,4),dtype=np.uint8)
 for row in range(32):
  t=max(0,min(1,(row-top-box[1])/max(h-1,1)));pixels[row,:,:3]=np.array([255,250,255])*(1-t)+np.array([102,95,126])*t;pixels[row,:,3]=255
 gradient=Image.fromarray(pixels);gradient.putalpha(ink);strip.alpha_composite(gradient)
 assert h==22 and strip.getbbox()[0]>0 and strip.getbbox()[2]<width
 # Only width changes to fit; font size and the 22-pixel capital height never change.
 return strip.resize((120,32),Image.Resampling.LANCZOS)

for tile,matches in rows.items():
 start=entry+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);target=old.copy();mask=np.zeros((256,256),bool)
 for row,match in enumerate(matches):
  y=row*48
  if match:
   left,right,lc,rc=match;target.paste((0,0,0,0),(0,y,256,y+48));mask[y:y+48,:]=True
   a,b=lettering(left),lettering(right);target.paste(a,(0,y+12));target.paste(b,(136,y+12))
   center=(a.getbbox()[2]+136+b.getbbox()[0])/2;vx=round(center-vs.width/2);vy=y+12+(32-vs.height)//2
   assert vx>=a.getbbox()[2] and vx+vs.width<=136+b.getbbox()[0], (left,right,a.getbbox(),b.getbbox(),vs.size,vx)
   target.paste(vs,(vx,vy))
   d=ImageDraw.Draw(target)
   for x,label in [(0,lc),(136,rc)]:
    if label:
     box=small.getbbox(label);d.text((x+2-box[0],y+4-box[1]),label,font=small,fill=(255,255,0,255),stroke_width=0)
   report.append({'tile':tile,'row':row,'left':left,'right':right,'font_size':FONT_SIZE,'capital_height':22,'small_labels':[lc,rc]})
  index+=1
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
 for yy,xx in zip(*np.nonzero(touched)):
  p=2048+spread(int(yy))+(spread(int(xx))<<1);block[p]=encoded[p]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),'Unrelated pixels changed'
 if tile==5:assert np.array_equal(np.asarray(sample)[:48],np.asarray(final)[:48]),'Approved sample changed'
 name=f'history-names-{tile}.bin';(R/name).write_bytes(block);patches.append([start,name])
 for row in range(len(matches)):
  outrow=(0 if tile==5 else 5 if tile==6 else 10)+row;preview.alpha_composite(final.crop((0,row*48,256,row*48+48)),(0,outrow*48))
assert len(report)==11 and sum(bool(x) for r in report for x in r['small_labels'])==10
(R/'history-texture-patches.json').write_text(json.dumps(patches))
(R/'history-names-report.json').write_text(json.dumps({'remaining_matches':report,'approved_sample_preserved':True,'additional_emulator_tests':0,'label_font':'Arial Bold Italic','label_font_size':8},indent=2))
preview.resize((768,1728),Image.Resampling.NEAREST).save(R/'history-all-names-preview.png')
print('All 12 match headings complete; approved sample preserved. 22 remaining name/team labels and 10 small role labels translated. Uniform size 28; no emulator tests.')
