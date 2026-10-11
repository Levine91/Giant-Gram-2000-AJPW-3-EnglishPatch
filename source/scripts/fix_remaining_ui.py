"""Remaining tournament labels and command prefixes; isolate the ring prompt sprite."""
from pathlib import Path
import json, struct, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
R=Path(__file__).resolve().parent; G=R.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
backup=R/'before-remaining-ui'; backup.mkdir(exist_ok=True)
for p in [G/'1ST_READ.BIN',G/'TEX.AFS',G/'English_Names_Verified/README.txt']:
 if not (backup/p.name).exists(): shutil.copy2(p,backup/p.name)
b=(backup/'1ST_READ.BIN').read_bytes(); a=(backup/'TEX.AFS').read_bytes()
pairs=read(G/'English_Runtime_Fixed/runtime_verification.json')['font_pairs']
pairs.update({k[5:]:v['code'] for k,v in read(R/'catchphrase-update-report.json')['new_glyphs'].items() if k.startswith('pair:')})
def text_bytes(s):
 return b'\n'.join(b''.join(bytes.fromhex(pairs[line[i:i+2].ljust(2)]) for i in range(0,len(line),2)) for line in s.split('\n'))
patches=[]
def patch(off,data): patches.append([off,data.hex()])
# Crop the unused top 16 pixels of the Y prompt's rectangle. Its screen
# origin advances by the same amount, leaving the actual icon in place.
assert b[0x584d0:0x584d2]==bytes.fromhex('40e2') and b[0x584d6:0x584d8]==bytes.fromhex('60e6')
assert struct.unpack_from('<H',b,0x58588)[0]==231
patch(0x584d0,bytes.fromhex('30e2')); patch(0x584d6,bytes.fromhex('70e6')); patch(0x58588,struct.pack('<H',247))
off=0xf3810; end=b.index(0,off)+1
assert b[off:end-1].decode('cp932')=='同点者多数のため\n決勝戦進出者を選抜中です。'
message='Multiple ties.\nSelecting finalists.'; data=text_bytes(message)+b'\0'
assert len(data)<=end-off; patch(off,data+bytes(end-off-len(data)))
cursor=0x104a00; counts={}
for prefix,word in [(bytes.fromhex('84408441'),'Near Corner'),(bytes.fromhex('84428443'),'Near Ropes')]:
 i=0; count=0
 while (i:=b.find(prefix,i))>=0:
  start=b.rfind(b'\0',0,i)+1; end=b.index(0,i); raw=b[start:end]
  refs=[j for j in range(0,len(b)-3,4) if b[j:j+4]==struct.pack('<I',start+0x8c010000)]
  assert refs,hex(start)
  data=raw.replace(prefix,text_bytes(word))+b'\0'
  assert cursor+len(data)<0x105c00 and not any(b[cursor:cursor+len(data)])
  patch(cursor,data)
  for ref in refs: patch(ref,struct.pack('<I',cursor+0x8c010000))
  cursor+=len(data); count+=1; i=end
 assert count>0; counts[word]=count
# Explicitly own the whole reserved pool so subsequent revisions erase stale bytes.
pool=bytearray(0x1200)
for off,h in patches:
 if 0x104a00<=off<0x105c00: pool[off-0x104a00:off-0x104a00+len(bytes.fromhex(h))]=bytes.fromhex(h)
patches=[p for p in patches if not 0x104a00<=p[0]<0x105c00]
patch(0x104a00,pool)
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
entries=read(R/'game-entries.json'); textures=[]
def save(file,tile,paint):
 off=entries[file][0]+tile*SIZE; original=a[off:off+SIZE]; old=decode(original); im=old.copy(); mask=np.zeros((256,256),bool)
 paint(im,mask,old)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,original,touched,'4444'); encoded=encode(im,adapted); out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1); out[p]=encoded[p]
 assert np.array_equal(np.asarray(old)[~mask],np.asarray(decode(out))[~mask])
 name=f'remaining-{file}-{tile}.bin'; (R/name).write_bytes(out); textures.append([off,name])
def clear(im,mask,rect,color=(0,0,0,0)):
 im.paste(color,rect); x0,y0,x1,y1=rect; mask[y0:y1,x0:x1]=True
def white(word,size,sx=1):
 f=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf',size); box=f.getbbox(word,stroke_width=1)
 im=Image.new('RGBA',(box[2]-box[0]+2,box[3]-box[1]+2))
 ImageDraw.Draw(im).text((1-box[0],1-box[1]),word,font=f,fill='white',stroke_width=1,stroke_fill='black')
 return im.resize((round(im.width*sx),im.height),Image.Resampling.LANCZOS)
def center(im,art,rect):
 x0,y0,x1,y1=rect; assert art.width<=x1-x0 and art.height<=y1-y0
 im.alpha_composite(art,(x0+(x1-x0-art.width)//2,y0+(y1-y0-art.height)//2))
def badges(im,mask,old):
 # Recover the repeated gold emblem from all three copies, excluding white
 # title ink; the copies have identical geometry and different occlusions.
 copies=np.stack([np.asarray(old.crop((0,y,176,y+72))).copy() for y in (0,72,144)])
 rgb=copies[:,:,:,:3].astype(int)
 gold=(rgb[:,:,:,0]>75)&(rgb[:,:,:,1]>30)&(rgb[:,:,:,2]*1.5<rgb[:,:,:,1])
 score=np.where(gold,copies[:,:,:,3],-1); pick=np.argmax(score,axis=0)
 yy,xx=np.indices((72,176)); clean=copies[pick,yy,xx].copy(); clean[~gold.any(axis=0)]=0
 for y,word in zip((0,72,144),('One Night Tournament','Champion Carnival',"World’s Strongest Tag League")):
  clear(im,mask,(0,y+24,176,y+48))
  im.alpha_composite(Image.fromarray(clean).crop((0,24,176,48)),(0,y+24))
  center(im,white(word,14,.75),(0,y+24,176,y+48))
def dialog(im,mask,old):
 bg=(17,0,51,170)
 clear(im,mask,(128,12,256,36),bg); clear(im,mask,(0,68,120,92),bg)
 strip=Image.new('RGBA',(248,24)); center(strip,white('View results only?',22),(0,0,248,24))
 im.alpha_composite(strip.crop((0,0,128,24)),(128,12)); im.alpha_composite(strip.crop((128,0,248,24)),(0,68))
 for word,rect in [('Yes',(16,136,88,168)),('No',(96,136,176,168))]:
  clear(im,mask,rect,old.getpixel((20,138))); center(im,white(word,26),rect)
def gold_text(word,size,sx):
 f=ImageFont.truetype('C:/Windows/Fonts/impact.ttf',size); box=f.getbbox(word)
 ink=Image.new('L',(box[2]-box[0]+12,box[3]-box[1]+12)); ImageDraw.Draw(ink).text((5-box[0],4-box[1]),word,font=f,fill=255)
 ink=ink.resize((round(ink.width*sx),ink.height),Image.Resampling.LANCZOS)
 edge=ink.filter(ImageFilter.MaxFilter(5)); art=Image.new('RGBA',ink.size)
 for dy in (5,4,3):
  sh=Image.new('RGBA',ink.size,(25+dy*5,25+dy*5,25+dy*5,255)); sh.putalpha(edge); art.alpha_composite(sh,(2,dy))
 outline=Image.new('RGBA',ink.size,(225,30,0,255)); outline.putalpha(edge); art.alpha_composite(outline)
 grad=np.zeros((ink.height,ink.width,4),dtype='uint8'); grad[:,:,0]=255; grad[:,:,3]=255
 for y in range(ink.height): grad[y,:,1]=int(150+105*np.sin(np.pi*y/max(1,ink.height-1)))
 fill=Image.fromarray(grad); fill.putalpha(ink); art.alpha_composite(fill); return art
def injury(im,mask,old,word,rect):
 clear(im,mask,rect); center(im,gold_text(word,44,.65),rect)
def champion(im,mask,old):
 rect=(0,144,192,232); clear(im,mask,rect); center(im,gold_text('CHAMPION',80,.48),rect)
save('spr_gam2',36,badges); save('spr_gam2',35,dialog); save('spr_gam2',34,champion)
for file in ('spr_gam','spr_gam5'):
 save(file,3,lambda im,m,o:injury(im,m,o,'Neck',(0,128,96,184)))
 save(file,6,lambda im,m,o:injury(im,m,o,'Left Knee',(128,128,256,184)))
(R/'remaining-program-patches.json').write_text(json.dumps(patches))
(R/'remaining-texture-patches.json').write_text(json.dumps(textures))
(R/'remaining-report.json').write_text(json.dumps({'commands':counts,'tie_message':message,'texture_blocks':len(textures),'ring_prompt_crop':[136,112,256,160]},indent=2))
print('Prepared patches:',counts,'and',len(textures),'texture blocks. Bounds and untouched artwork verified.')
