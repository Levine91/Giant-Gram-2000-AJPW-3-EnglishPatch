"""Translate the six requested tutorial tiles; preserve the 512-pixel strip packing."""
from pathlib import Path
import json,shutil,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-how-to-play';B.mkdir(exist_ok=True)
for name in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/name).exists():shutil.copy2(G/name,B/name)
a=(B/'TEX.AFS').read_bytes();base=2582528
colors={'w':((255,255,255,255),(0,68,255,255)),'g':((255,238,153,255),(153,68,0,255)),'X':((255,255,0,255),(119,85,0,255)),'B':((34,170,255,255),(0,68,170,255)),'A':((255,34,17,255),(153,0,0,255)),'Y':((0,255,187,255),(0,102,85,255))}
# Each tuple keeps the original color roles: button, action, surrounding text.
rows={
2:[ [('X','X'),('w',': '),('g','Strike'),('w',' attacks')], [('g','Strikes'),('w',' can counter '),('g','throws'),('w','.')], [('B','B'),('w',': Perform a '),('g','throw')], [('g','Throws'),('w',' are strong against '),('g','grabs'),('w','.')], [('A','A'),('w',': '),('g','Grab'),('w',' your opponent')]],
3:[[('w','You can also '),('g','catch strikes'),('w','.')],[('w','After a grab, '),('g','break their balance')],[('w','for a chance to land a '),('g','big move!')],[('g','Strike > Grab > Throw'),('w',' makes a combo.')],[('w','Create your own '),('g','original combos!')]],
4:[[('w','During a brawl, '),('Y','Y'),('w',': '),('g','Enter / exit the ring')],[('w','With your opponent down, '),('B','B'),('w',': '),('g','Pin')],[('w','For some throws, '),('g','keep holding '),('B','B')],[('w','to go straight from the throw into a '),('g','pin.')]],
5:[[('w','In tag matches, '),('Y','Y'),('w',': '),('g','Tag your partner')],[('w','Partner in trouble? '),('Y','Y'),('w',': '),('g','Enter the ring!')],[('w','A brawl is your chance to '),('g','double-team!')],[('w','4-way brawl: '),('g','Press two buttons together')],[('w','3-way, one foe: '),('g','Press two buttons together')]],
6:[[('w','3-way, two foes: '),('g','Press two buttons together')],[('w','When tagging while '),('g','holding an opponent')],[('g','press two buttons together'),('w',' to double-team.')]]}
font=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',23)
def line(parts,font=font,width=512,height=24,baseline=18):
 length=sum(font.getlength(s) for _,s in parts);im=Image.new('RGBA',(int(length)+6,height));d=ImageDraw.Draw(im);x=3
 for color,s in parts:
  fill,stroke=colors[color];d.text((x,baseline),s,font=font,anchor='ls',fill=fill,stroke_width=1,stroke_fill=stroke);x+=font.getlength(s)
 if im.width>width:im=im.resize((width,height),Image.Resampling.LANCZOS)
 return im
patches=[];review=Image.new('RGB',(1024,600),(40,40,40));report=[]
for k,tile in enumerate([0,2,3,4,5,6]):
 off=base+tile*SIZE;old=a[off:off+SIZE];source=decode(old);im=source.copy();mask=np.zeros((256,256),bool)
 if tile==0:
  for j,text in enumerate(['Move','Throw','Grab','Strike']):
   y=j*32;im.paste((0,0,0,0),(20,y,64,y+32));mask[y:y+32,20:64]=True
   # Text originally overlays the right edge of each button. Restore that
   # circular edge from its intact left side before overlaying the English.
   for yy in range(y,y+32):
    for xx in range(20,32):im.putpixel((xx,yy),source.getpixel((31-xx,yy)))
   art=line([('g',text)],ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',18),44,24,17);im.alpha_composite(art,(20,y+4))
  review.paste(im,(0,0),im)
 else:
  im.paste((0,0,0,0),(0,0,256,240));mask[:240,:]=True;wide=Image.new('RGBA',(512,120))
  for j,parts in enumerate(rows[tile]):
   art=line(parts);wide.alpha_composite(art,((512-art.width)//2,j*24));report.append({'tile':tile,'line':j,'text':''.join(s for _,s in parts),'height':24,'font_size':23})
  for j in range(5):
   im.paste(wide.crop((0,j*24,256,j*24+24)),(0,j*48));im.paste(wide.crop((256,j*24,512,j*24+24)),(0,j*48+24))
  reconstructed=Image.new('RGBA',(512,120))
  for j in range(5):
   reconstructed.paste(im.crop((0,j*48,256,j*48+24)),(0,j*24));reconstructed.paste(im.crop((0,j*48+24,256,j*48+48)),(256,j*24))
  assert reconstructed.tobytes()==wide.tobytes()
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,old,touched,'4444');enc=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=enc[p]
 final=decode(out);assert np.array_equal(np.asarray(source)[~mask],np.asarray(final)[~mask])
 name=f'tutorial-{tile}.bin';(R/name).write_bytes(out);patches.append([off,name])
 if tile!=0:
  wide=Image.new('RGBA',(512,120))
  for j in range(5):wide.paste(final.crop((0,j*48,256,j*48+24)),(0,j*24));wide.paste(final.crop((0,j*48+24,256,j*48+48)),(256,j*24))
  x=512 if tile==2 else (tile-3)%2*512;y=0 if tile==2 else 280+(tile-3)//2*160;review.paste(wide,(x,y),wide)
(R/'tutorial-texture-patches.json').write_text(json.dumps(patches));(R/'tutorial-translation-report.json').write_text(json.dumps(report,indent=2));review.save(R/'tutorial-translated-review.png')
print('Translated six panels; strip joins and untouched pixels verified.')
