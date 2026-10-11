"""Restore rule brackets and the original warm gradient, gold rim and shadow."""
from pathlib import Path
import json,shutil,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-rules-lettering';B.mkdir(exist_ok=True)
for name in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/name).exists():shutil.copy2(G/name,B/name)
a=(B/'TEX.AFS').read_bytes();off=5779456+39*SIZE;old=a[off:off+SIZE];original=decode(old);im=original.copy();mask=np.zeros((256,256),bool)
def art(text,width,left=False,right=False):
 font=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',40)
 bb=font.getbbox(text);ink=Image.new('L',(bb[2]-bb[0]+4,34));ImageDraw.Draw(ink).text((2-bb[0],-bb[1]),text,font=font,fill=255,stroke_width=1)
 ink=ink.crop(ink.getbbox());target=width-12-(18 if left or right else 0)
 ink=ink.resize((min(target,ink.width),30),Image.Resampling.LANCZOS)
 shape=Image.new('L',(width,46));x=23 if left else 5;shape.paste(ink,(x,6))
 draw=ImageDraw.Draw(shape)
 if left:draw.line([(15,5),(5,20),(13,36)],fill=255,width=5)
 if right:
  x+=ink.width+7;draw.line([(x,5),(x+9,20),(x+1,36)],fill=255,width=5)
 # Gold backplate is visible above/left; the dark extrusion falls below/right.
 edge=shape.filter(ImageFilter.MaxFilter(5));result=Image.new('RGBA',shape.size)
 for dx,dy,color,alpha in [(1,4,(51,34,34,255),edge),(-1,-2,(255,221,85,255),edge),(0,0,(34,17,17,255),edge)]:
  layer=Image.new('RGBA',shape.size,color);layer.putalpha(alpha);result.alpha_composite(layer,(dx,dy))
 fill=Image.new('RGBA',shape.size);d=ImageDraw.Draw(fill)
 for y in range(46):
  t=max(0,min(1,(y-6)/29));c=tuple(round(a*(1-t)+b*t) for a,b in zip((255,68,34),(255,255,221)));d.line((0,y,width,y),fill=(*c,255))
 fill.putalpha(shape);result.alpha_composite(fill);return result
rows=[(0,256,'NO TIME LIMIT',True,False),(48,176,'ONE FALL',False,True),(96,144,'30 MIN',True,False),(144,144,'60 MIN',True,False),(192,184,'BEST OF 3',False,True)]
for y,w,text,left,right in rows:
 im.paste((0,0,0,0),(0,y,w,y+48));mask[y:y+48,:w]=True;im.alpha_composite(art(text,w,left,right),(0,y))
touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,old,touched,'4444');enc=encode(im,adapted);out=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=enc[p]
final=decode(out);assert np.array_equal(np.asarray(original)[~mask],np.asarray(final)[~mask]),'Unrelated artwork changed'
# Update the existing layer so the established build/install sequence picks it up.
name='history-polish-spr_gam2-39.bin';assert [off,name] in json.loads((R/'history-polish-texture-patches.json').read_text())
if not (B/name).exists():shutil.copy2(R/name,B/name)
(R/name).write_bytes(out);final.save(R/(name+'.png'))
preview=Image.new('RGB',(768,768),(32,32,32));large=final.resize((768,768),Image.Resampling.NEAREST);preview.paste(large,(0,0),large);preview.save(R/'rules-corrected-preview.png')
print('Rule brackets and gold-backed lettering prepared; VS and unrelated pixels preserved.')
