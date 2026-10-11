"""Match the shared history-button lettering to its digits; add translation credit."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import decode,SIZE,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-history-weight-credit';B.mkdir(exist_ok=True)
for n in ['TEX.AFS','1ST_READ.BIN']:
 if not (B/n).exists():shutil.copy2(G/n,B/n)
a=(B/'TEX.AFS').read_bytes();patches=[]
def save(off,im,mask,name):
 old=a[off:off+SIZE];touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,old,touched,'4444');enc=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=enc[p]
 final=decode(out);assert np.array_equal(np.asarray(decode(old))[~mask],np.asarray(final)[~mask]),name
 (R/name).write_bytes(out);patches.append([off,name]);return final
def text(s,font,fill='white',stroke=(68,17,34,255)):
 bb=font.getbbox(s,stroke_width=1);im=Image.new('RGBA',(bb[2]-bb[0]+4,bb[3]-bb[1]+4));ImageDraw.Draw(im).text((2-bb[0],2-bb[1]),s,font=font,fill=fill,stroke_width=1,stroke_fill=stroke);return im.crop(im.getbbox())
off=4046848+3*SIZE;im=decode(a[off:off+SIZE]);mask=np.zeros((256,256),bool);bg=im.getpixel((60,14))
# One shared button sprite is used for both match-selection pages.
for rect,s in [((10,8,38,36),'No.'),((72,8,124,36),'MATCH')]:
 x,y,x1,y1=rect;im.paste(bg,rect);mask[y:y1,x:x1]=True;art=text(s,ImageFont.truetype('C:/Windows/Fonts/impact.ttf',27),stroke=(34,17,68,255));art=art.resize((min(x1-x-2,art.width),21),Image.Resampling.LANCZOS);im.alpha_composite(art,(x+(x1-x-art.width)//2,y+(y1-y-21)//2))
final=save(off,im,mask,'history-weight-button.bin');final.resize((768,768),Image.Resampling.NEAREST).save(R/'history-weight-button-preview.png')
entry=6793216;old=Image.new('RGBA',(512,256))
for j in range(2):o=entry+(23+j)*SIZE;old.paste(decode(a[o:o+SIZE]),(j*256,0))
im=old.copy();im.paste((0,0,0,0),(0,40,512,208));im.paste(old.crop((0,112,512,176)),(0,48))
for s,rect,size,stroke in [('ENGLISH TRANSLATION BY',(0,136,512,160),18,(170,68,0,255)),('Levine91',(0,159,512,195),24,(68,17,34,255))]:
 fill=(255,255,221,255) if size==18 else 'white'
 art=text(s,ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size),fill=fill,stroke=stroke);im.alpha_composite(art,((512-art.width)//2,rect[1]+(rect[3]-rect[1]-art.height)//2))
heading='ENGLISH TRANSLATION BY'
# Keep native glyphs on the original two-pixel compression grid. Moving them
# onto odd grid positions previously created new VQ blocks and visible seams.
glyphs={};reference=im.copy()
motion=Image.new('RGBA',(512,256))
for j in range(2):o=entry+(17+j)*SIZE;motion.paste(decode(a[o:o+SIZE]),(j*256,0))
spans=[('E',225,233),('N',291,300),('G',312,322),('L',253,260),('I',263,264),('S',303,312),('H',153,163),('T',213,222),('R',236,245),('A',165,176),('O',212,223),('B',344,353),('Y',355,364)]
for ch,left,right in spans:
 source=motion if ch in 'GO' else reference;y=58 if ch in 'GO' else 54
 x0=(left-1)//2*2;x1=(right+3)//2*2
 cell=source.crop((x0,y,x1,y+16))
 # Remove only possible neighboring glyph fringe outside this glyph's rim.
 for xx in range(cell.width):
  if not left-1<=xx+x0<=right+1:cell.paste((0,0,0,0),(xx,0,xx+1,16))
 glyphs[ch]=cell
# Remove neighboring-letter fragments, not the native rim of each letter.
repairs={'E':[(10,4,11,12)],'T':[(0,5,3,16),(10,5,12,16)],
 'A':[(12,0,14,9),(13,9,14,16),(0,0,1,7)],
 'H':[(12,13,13,14)],
 'O':[(1,0,2,16),(14,0,15,5)],
 'B':[(11,0,14,2)],'Y':[(0,6,2,16)]}
for ch,rects in repairs.items():
 for rect in rects:glyphs[ch].paste((0,0,0,0),rect)
for ch in 'GO':
 cell=glyphs[ch];aligned=Image.new('RGBA',cell.size)
 aligned.paste(cell.crop((0,1,cell.width,16)),(0,0));glyphs[ch]=aligned
width=sum(6 if ch==' ' else glyphs[ch].width for ch in heading)
native_art=Image.new('RGBA',(width,16));x=0
for ch in heading:
 if ch==' ':x+=6
 else:cell=glyphs[ch];native_art.paste(cell,(x,0));x+=cell.width
im.paste((0,0,0,0),(0,136,512,160));im.paste(native_art,(((512-width)//4)*2,138))
# Clean only the letter faces and cool-colored contamination. Warm outline
# pixels are protected byte-for-byte, so this cannot recolor or move the rim.
clean=np.asarray(native_art).copy();before=clean.copy()
warm=(clean[:,:,0]>clean[:,:,2]+20)&(clean[:,:,0]>60)&(clean[:,:,1]<220)
face=(clean[:,:,0]>=220)&(clean[:,:,1]>=220)&(clean[:,:,2]>=150)&(clean[:,:,3]>=170)
cool=(clean[:,:,2]>clean[:,:,0])&~warm
clean[cool]=0
clean[face]=(255,255,221,255)
# Heal isolated compression pinholes inside strokes, without touching counters
# or any part of the protected outline.
for yy in range(1,15):
 for xx in range(1,width-1):
  if warm[yy,xx] or face[yy,xx]:continue
  if sum(bool(face[y,x]) for y,x in [(yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)])>=3:
   clean[yy,xx]=(255,255,221,255)
assert np.array_equal(clean[warm],before[warm]),'Outline changed'
native_art=Image.fromarray(clean)
im.paste(native_art,(((512-width)//4)*2,138))
final=Image.new('RGBA',(512,256))
for j in range(2):
 mask=np.zeros((256,256),bool);mask[40:208]=True;part=save(entry+(23+j)*SIZE,im.crop((j*256,0,(j+1)*256,256)),mask,f'translation-credit-{23+j}.bin');final.paste(part,(j*256,0))
final.resize((1024,512),Image.Resampling.NEAREST).save(R/'credits-translated-23.png')
(R/'history-weight-credit-texture-patches.json').write_text(json.dumps(patches));print('Shared history button and translation credit prepared; unrelated pixels preserved.')
