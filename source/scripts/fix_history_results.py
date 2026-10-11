"""Translate the pin objective and repair complete result-label strips."""
from pathlib import Path
import json,sys,shutil,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
R=Path(__file__).resolve().parent;G=R.parent
backup=R/'before-history-results';backup.mkdir(exist_ok=True)
for p in [G/'1ST_READ.BIN',G/'TEX.AFS',G/'English_Names_Verified/README.txt']:
 if not (backup/p.name).exists():shutil.copy2(p,backup/p.name)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
pairs=read(G/'English_Runtime_Fixed/runtime_verification.json')['font_pairs']
pairs.update({k[5:]:v['code'] for k,v in read(R/'catchphrase-update-report.json')['new_glyphs'].items() if k.startswith('pair:')})
text='Pin for a 3 count!';encoded=b''.join(bytes.fromhex(pairs[text[i:i+2].ljust(2)]) for i in range(0,len(text),2))+b'\0'
b=(R/'disc-original.bin').read_bytes();off=0xffa04;end=b.index(0,off)+1
assert b[off:end-1].decode('cp932')=='フォールして３カウントを奪え！' and len(encoded)<=end-off
font=(R/'moves-font.bin').read_bytes();ink=Image.new('1',(len(encoded)//2*24,24))
for j in range(0,len(encoded)-1,2):
 lead,trail=encoded[j:j+2];index=((lead-129)*2+(trail>=159))*96+trail-(126 if trail>=159 else 32 if trail>=128 else 31)-32
 ink.paste(Image.frombytes('1',(24,24),font[index*72:(index+1)*72]),(j//2*24,0))
box=ink.getbbox();x=320-(box[0]+box[2])//2
assert struct.unpack_from('<H',b,0x83342)[0]==140
(R/'results-program-patches.json').write_text(json.dumps([[off,(encoded+bytes(end-off-len(encoded))).hex()],[0x83342,struct.pack('<H',x).hex()]]))
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
a=(backup/'TEX.AFS').read_bytes();entries=read(R/'game-entries.json');patches=[]
face=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',16)
def label(target,word,x,y):
 cap=face.getbbox('H')[1]
 ImageDraw.Draw(target).text((x,y-cap),word,font=face,fill='white',stroke_width=1,stroke_fill='black')
def save(file,tile,paint):
 off=entries[file][0]+tile*SIZE;original=a[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 paint(im,mask,old)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=encoded[p]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
 name=f'results-{file}-{tile}.bin';(R/name).write_bytes(out);final.save(R/(name+'.png'));patches.append([off,name])
def results(im,mask,old,word):
 # The result row is three joined source strips. Redraw the full strips,
 # including their shared underline, rather than erasing around each word.
 for rect in [(0,220,256,256),(176,188,256,220),(176,156,240,188)]:
  im.paste((0,0,0,0),rect);x0,y0,x1,y1=rect;mask[y0:y1,x0:x1]=True
 for x0,x1,y in [(8,256,246),(176,256,214),(176,240,182)]:
  d=ImageDraw.Draw(im)
  for dy,color in [(-1,(0,0,0,210)),(0,'white'),(1,(255,102,0,255)),(2,(204,0,0,255)),(3,(0,0,0,187))]:d.line((x0,y+dy,x1-1,y+dy),fill=color)
 label(im,'Attendance',12,226)
 strip=Image.new('RGBA',(96,24));label(strip,word,4,2)
 # Place all label ink above the underline, at the same cap height/baseline.
 im.alpha_composite(strip.crop((0,0,40,24)),(216,224))
 im.alpha_composite(strip.crop((40,0,96,24)),(176,192))
 # Keep the original percentage sign while removing its closing parenthesis.
 im.alpha_composite(old.crop((204,156,228,181)),(204,156))
def stone(im,mask,old):
 rect=(0,0,256,128);im.paste((0,0,0,0),rect);mask[:128,:]=True
 ink=Image.new('L',(256,128));d=ImageDraw.Draw(ink);f=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',44)
 for word,y in [('RECREATION',10),('FAILED...',65)]:
  box=f.getbbox(word);d.text(((256-(box[2]-box[0]))//2-box[0],y-box[1]),word,font=f,fill=255)
 edge=ink.filter(ImageFilter.MaxFilter(5));shadow=Image.new('L',ink.size);shadow.paste(edge,(4,5))
 art=Image.new('RGBA',ink.size,'black');art.putalpha(ImageChops.lighter(edge,shadow))
 rng=np.random.default_rng(2000);noise=np.clip(rng.normal(145,27,(128,256)),75,210).astype('uint8');gray=Image.fromarray(noise).convert('RGBA');gray.putalpha(ink);art.alpha_composite(gray)
 shifted=Image.new('L',ink.size);shifted.paste(ink,(2,2));highlight=ImageChops.subtract(ink,shifted);white=Image.new('RGBA',ink.size,(230,235,229,255));white.putalpha(highlight);art.alpha_composite(white)
 shifted=Image.new('L',ink.size);shifted.paste(ink,(-2,-2));shade=ImageChops.subtract(ink,shifted);dark=Image.new('RGBA',ink.size,(65,72,64,255));dark.putalpha(shade);art.alpha_composite(dark)
 im.alpha_composite(art,(0,0))
for file,tile in [('spr_gam',19),('spr_gam5',19),('spr_gam4',2)]:
 save(file,tile,lambda im,mask,old:results(im,mask,old,'Accuracy' if file=='spr_gam5' else 'Popularity'))
save('spr_gam5',18,stone)
(R/'results-texture-patches.json').write_text(json.dumps(patches))
print('Verified pin objective and four result textures; adjacent artwork unchanged.')
