"""Translate the requested injury, result, system and Honda interview labels."""
from pathlib import Path
import ast,json,shutil,struct,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
R=Path(__file__).resolve().parent;G=R.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
backup=R/'before-october-labels';backup.mkdir(exist_ok=True)
for name,p in [('1ST_READ.BIN',G/'1ST_READ.BIN'),('TEX.AFS',G/'TEX.AFS'),('moves-font.bin',R/'moves-font.bin')]:
 if not (backup/name).exists():shutil.copy2(p,backup/name)
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
# Reuse the established deterministic lettering and texture encoder, without
# executing the earlier patch script or reinstalling its obsolete data.
tree=ast.parse((R/'fix_remaining_ui.py').read_text(encoding='utf-8'))
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['gold_text','center','clear']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'existing-lettering','exec'))
a=(backup/'TEX.AFS').read_bytes();entries=read(R/'game-entries.json');entries['spr_sys']=[978944,110592]
textures=[];review=[]
def save(file,tile,items):
 off=entries[file][0]+tile*SIZE;original=a[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 for word,rect,style in items:
  clear(im,mask,rect)
  w=rect[2]-rect[0];h=rect[3]-rect[1]
  if style in ['gold','success']:art=gold_text(word,72 if style=='success' else 32,1)
  else:
   face=ImageFont.truetype('C:/Windows/Fonts/arialbi.ttf' if style=='cream' else 'C:/Windows/Fonts/arialbd.ttf',18 if style=='cream' else 20)
   bb=face.getbbox(word,stroke_width=1);art=Image.new('RGBA',(bb[2]-bb[0]+4,bb[3]-bb[1]+4))
   ImageDraw.Draw(art).text((2-bb[0],2-bb[1]),word,font=face,fill=(255,238,153,255) if style=='cream' else ('yellow' if style=='yellow' else 'white'),stroke_width=1,stroke_fill='black')
  art=art.crop(art.getbbox());scale=min(1,(w-4)/art.width,(h-4)/art.height)
  if scale<1:art=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
  center(im,art,rect)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
 adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=encoded[p]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask]),(file,tile)
 name=f'october-{file}-{tile}.bin';(R/name).write_bytes(out);final.save(R/(name+'.png'));textures.append([off,name]);review.append((file,tile,final))
for file in ['spr_gam','spr_gam5']:
 for tile,words in [(2,['Face']),(3,['Neck']),(4,['Right Elbow','Left Elbow']),(5,['Right Wrist','Left Wrist']),(6,['Right Knee','Left Knee']),(7,['Right Ankle','Left Ankle']),(8,['Lower Back'])]:
  save(file,tile,[(word,(i*128,128,i*128+(128 if len(words)==2 else 96),192),'gold') for i,word in enumerate(words)])
save('spr_gam5',14,[('RECREATION',(0,8,256,88),'success'),('SUCCESS!!',(0,88,256,176),'success')])
save('spr_sys',0,[('Controller disconnected',(0,104,256,128),'yellow'),('or',(0,128,256,152),'yellow'),('checking memory card.',(0,152,256,176),'yellow')])
save('spr_gam2',34,[('Match Results',(0,104,112,136),'white')])
save('spr_gam3',1,[("Winner Interview",(16,0,180,20),'cream')])
save('spr_gam3',2,[('Honda',(0,40,48,60),'cream'),('Comments',(128,60,240,80),'cream')])
# Honda's two-line quote occupies its original string slot; no pointer changes.
b=(backup/'1ST_READ.BIN').read_bytes();original=(R/'disc-original.bin').read_bytes();off=1017544;end=original.index(0,off)+1
assert original[off:end-1].decode('cp932')=='甘く見ないで欲しい、\n五輪の星は伊達じゃない！'
quote="Don't underrate me!\nI'm an Olympic star!"
font=bytearray((backup/'moves-font.bin').read_bytes());pairs=read(G/'English_Runtime_Fixed/runtime_verification.json')['font_pairs']
pairs.update({k[5:]:v['code'] for k,v in read(R/'catchphrase-update-report.json')['new_glyphs'].items() if k.startswith('pair:')})
def index(code):
 x,y=bytes.fromhex(code);return ((x-129)*2+(y>=159))*96+y-(126 if y>=159 else 32 if y>=128 else 31)-32
letters={}
for pair,code in pairs.items():
 i=index(code);cell=Image.frombytes('1',(24,24),bytes(font[i*72:(i+1)*72]));letters.setdefault(pair[0],cell.crop((0,0,12,24)));letters.setdefault(pair[1],cell.crop((12,0,24,24)))
used=set(zip(b,b[1:]))|set(zip(original,original[1:]));new={}
def pair_code(pair):
 if pair not in pairs:
  cell=Image.new('1',(24,24))
  for j,ch in enumerate(pair):cell.paste(letters[ch],(j*12,0))
  for i in range(600,len(font)//72):
   row=i//96+33;col=i%96+32
   if not 33<=col<=126:continue
   lead=(row-33)//2+129;trail=col+(31 if row%2 else 126)
   if row%2 and trail>=127:trail+=1
   code=bytes([lead,trail])
   if tuple(code) in used:continue
   used.add(tuple(code));font[i*72:(i+1)*72]=cell.tobytes();pairs[pair]=code.hex();new[pair]={'index':i,'code':code.hex()};break
  else:raise AssertionError('No free glyph')
 return bytes.fromhex(pairs[pair])
encoded=b'\n'.join(b''.join(pair_code(line[i:i+2].ljust(2)) for i in range(0,len(line),2)) for line in quote.split('\n'))+b'\0'
assert len(encoded)<=end-off,(len(encoded),end-off)
patches=[[off,(encoded+bytes(end-off-len(encoded))).hex()]]
allowed={v['index'] for v in new.values()};before=(backup/'moves-font.bin').read_bytes()
assert all(font[i:i+72]==before[i:i+72] for i in range(0,len(font),72) if i//72 not in allowed)
(R/'moves-font.bin').write_bytes(font)
(R/'october-program-patches.json').write_text(json.dumps(patches))
(R/'october-texture-patches.json').write_text(json.dumps(textures))
(R/'october-labels-report.json').write_text(json.dumps({'quote':quote,'new_pairs':new,'textures':len(textures),'unrelated_pixels_unchanged':True},indent=2))
sheet=Image.new('RGB',(1024,280*((len(review)+3)//4)),(40,40,40));d=ImageDraw.Draw(sheet)
for j,(file,tile,im) in enumerate(review):
 x=j%4*256;y=j//4*280;sheet.paste(im,(x,y+24),im);d.text((x,y),f'{file} {tile}',fill='white')
sheet.save(R/'october-labels-review.png')
preview=Image.new('RGB',(600,100),(30,30,30))
for y,line in enumerate(quote.split('\n')):
 for x in range(0,len(line),2):
  i=index(pairs[line[x:x+2].ljust(2)]);cell=Image.frombytes('1',(24,24),bytes(font[i*72:(i+1)*72]));preview.paste('white',(20+x*12,12+y*32),cell)
preview.save(R/'october-honda-review.png')
print('Prepared',len(textures),'texture patches and Honda quote. Other pixels and font cells unchanged.')
