"""Apply the approved introduction lettering without any further emulator runs."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode

NAMES={
21:['Rikidozan','Steve Williams'],22:['Bruno Sammartino','Cyclops E.C.'],
23:['Gene Kiniski','Mangler D.H.'],24:['Don Leo Jonathan','The Killer B.I.'],
25:['Tiger Jeet Singh'],26:['Giant Crusher','Bruiser Brody'],
27:['The Crusher','The Destroyer'],28:['Dick the Bruiser','Crusher Lisowski'],
29:['Fritz Von Erich','Bobo Brazil'],30:['Technical King'],31:['Comical King'],
40:['Giant Baba','Takao Omori'],41:['Mitsuharu Misawa','Yoshihiro Takayama'],
42:['Toshiaki Kawada','Mike Barton'],43:['Akira Taue','Yoshinari Ogawa'],
44:['Kenta Kobashi','Tamon Honda'],45:['Jun Akiyama','Masahito Kakihara'],
46:['Stan Hansen','Kentaro Shiga'],47:['Vader','Johnny Smith'],
48:['Gary Albright','Maunakea Mossman'],49:['Johnny Ace','Jumbo Tsuruta'],
50:['Hiroshi Hase','Ogami Kongo'],51:['Wolf Hawkfield','Sky High Edge'],
52:['Grace','Super Tigre Dos Mil'],53:['Hyper','Young Giant Baba'],
54:['Diablo','The Master A.M.']}
FONT_SIZE=48
font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',FONT_SIZE)
archive=(G/'TEX.AFS').read_bytes();entry=5779456;patches=[];report=[]
approved={(41,0),(44,128)}

def lettering(name):
 text=name.upper();strip=Image.new('RGBA',(416,64));d=ImageDraw.Draw(strip);box=d.textbbox((0,0),text,font=font)
 w=box[2]-box[0];h=box[3]-box[1];tracking=min(0,(402-w)/(len(text)-1));w+=tracking*(len(text)-1)
 assert w+10<=416 and h+10<=64 and tracking>=-1
 x=(416-w-4)//2-box[0];top=(64-h-4)//2-box[1]
 def draw(drawer,dx,dy,**kwargs):
  if tracking==0:drawer.text((x+dx,top+dy),text,font=font,**kwargs)
  else:
   for i,ch in enumerate(text):drawer.text((x+dx+font.getlength(text[:i])+i*tracking,top+dy),ch,font=font,**kwargs)
 draw(d,4,4,fill=(255,180,0,255),stroke_width=3,stroke_fill='black')
 draw(d,0,0,fill='black',stroke_width=2,stroke_fill='black')
 ink=Image.new('L',strip.size);draw(ImageDraw.Draw(ink),0,0,fill=255)
 pixels=np.zeros((64,416,4),dtype=np.uint8)
 for row in range(64):
  t=max(0,min(1,(row-(top+box[1]))/max(h-1,1)));c=np.array([255,250,255])*(1-t)+np.array([102,95,126])*t
  if row%3==0:c=np.minimum(255,c+18)
  pixels[row,:,:3]=c;pixels[row,:,3]=255
 gradient=Image.fromarray(pixels);gradient.putalpha(ink);strip.alpha_composite(gradient)
 bounds=strip.getbbox();assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<416 and bounds[3]<64,(name,bounds)
 return strip,tracking

for tile,names in NAMES.items():
 start=entry+tile*SIZE;original=archive[start:start+SIZE];old=decode(original);target=old.copy();mask=np.zeros((256,256),bool)
 for row,name in enumerate(names):
  y=row*128;strip,tracking=lettering(name)
  if (tile,y) not in approved:
   target.paste((0,0,0,0),(0,y,256,y+128))
   target.paste(strip.crop((0,0,256,64)),(0,y));target.paste(strip.crop((256,0,416,64)),(0,y+64));mask[y:y+128,:]=True
  report.append({'name':name,'tile':tile,'y':y,'font':'Impact','font_size':FONT_SIZE,'tracking':tracking,'approved_sample_preserved':(tile,y) in approved})
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
 for yy,xx in zip(*np.nonzero(touched)):
  at=2048+spread(int(yy))+(spread(int(xx))<<1);block[at]=encoded[at]
 final=decode(block);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),(tile,'Unrelated art or approved sample changed')
 name=f'intro-names-{tile}.bin';(R/name).write_bytes(block);patches.append([start,name])
assert len(report)==49 and {r['font_size'] for r in report}=={48}
(R/'intro-texture-patches.json').write_text(json.dumps(patches))
(R/'intro-names-report.json').write_text(json.dumps({'names':report,'emulator_tests_after_approval':0,'approved_sample_pixels_preserved':True},indent=2))
print('Prepared 49 introduction labels at size 48; approved samples and unrelated pixels preserved.')
