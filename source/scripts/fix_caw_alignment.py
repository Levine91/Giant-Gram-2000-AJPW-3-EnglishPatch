from pathlib import Path
import json,struct,sys,re,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
B=R/'before-caw-alignment';B.mkdir(exist_ok=True)
for name,src in [('program.bin',G/'1ST_READ.BIN'),('textures.bin',G/'TEX.AFS'),('font.bin',R/'moves-font.bin')]:
 if not (B/name).exists():shutil.copyfile(src,B/name)
program=(B/'program.bin').read_bytes();archive=(B/'textures.bin').read_bytes();font=bytearray((B/'font.bin').read_bytes());patches=[];textures=[]
report=json.loads((G/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'));pairs=report['font_pairs'].copy()
for key,value in json.loads((R/'catchphrase-update-report.json').read_text(encoding='utf-8'))['new_glyphs'].items():
 if key.startswith('pair:'):pairs[key[5:]]=value['code']
for key,value in json.loads((R/'october-labels-report.json').read_text())['new_pairs'].items():pairs[key]=value['code']
def idx(code):
 a,b=code;return ((a-129)*2+(b>=159))*96+b-(126 if b>=159 else 32 if b>=128 else 31)-32
def pair_code(pair):
 if pair not in pairs:
  for i in range(600,len(font)//72):
   row=i//96+33;col=i%96+32
   if not 33<=col<=126:continue
   a=(row-33)//2+129;b=col+(31 if row%2 else 126)
   if row%2 and b>=127:b+=1
   code=bytes([a,b])
   if code in program or code.hex() in pairs.values() or code in (R/'disc-original.bin').read_bytes():continue
   face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',24);glyph=Image.new('1',(24,24))
   for j,ch in enumerate(pair):
    cell=Image.new('L',(16,24));ImageDraw.Draw(cell).text((0,-3),ch,font=face,fill=255);cell=cell.resize((10,24),Image.Resampling.LANCZOS).point(lambda v:255 if v>=100 else 0).convert('1');glyph.paste(cell,(j*12+1,0))
   font[i*72:(i+1)*72]=glyph.tobytes();pairs[pair]=code.hex();break
  else:raise AssertionError('No unused font cell')
 return bytes.fromhex(pairs[pair])
def pack(s):
 out=b''
 for run in re.findall(r'[ -~]+|[^ -~]',s):
  if run.isascii() and ord(run[0])>=32:out+=b''.join(pair_code(run[i:i+2].ljust(2)) for i in range(0,len(run),2))
  else:out+=run.encode('cp932')
 return out
def put(off,data):patches.append([off,data.hex()])
# A dedicated, checked empty pool keeps longer words clear of neighboring strings.
pool=0x105b24
assert not any(program[pool:pool+340])
changed=[]
for row in report['labels']:
 if 'gripping' not in row['en'].lower():continue
 text=row['en'].replace('Gripping','Grappling').replace('gripping','grappling')
 if row['kind']=='caw_prompt':text='Choose a tag move while grappling (\x07Β\r).'
 data=pack(text)+b'\0';at=pool;pool+=len(data)+(len(data)%2)
 put(at,data)
 for ref in row['refs']:put(ref,struct.pack('<I',0x8c010000+at))
 changed.append({'old':row['new_offset'],'offset':at,'text':text,'refs':row['refs']})
# Tiny position wrappers retain the existing text renderer and all input choices.
def position_wrapper(x,y,target):return struct.pack('<6H3I',0xd502,0xd603,0xd003,0x402b,0x0009,0x0009,x,y,target)
prompt_results=[]
for row in report['labels']:
 if row['kind']!='caw_prompt' or not any(t in row['en'].lower() for t in ['choose taunt','whip attack','tagging','opponent down']):continue
 text=next((z['text'] for z in changed if z['refs']==row['refs']),row['en'])
 if row['refs']==[133704]:text='Choose a tag move: opponent down (\x07Β\r).'
 # The English font has 12-pixel letters; the button icon occupies one 24-pixel cell.
 plain=text.replace('\x07Β\r','@@');width=len(plain)*12
 x=(640-width)//2
 pool=(pool+3)&~3;at=pool;blob=position_wrapper(x,106,0x8c0155a0);put(at,blob);pool+=len(blob)
 for ref in row['refs']:
  assert struct.unpack_from('<I',program,ref+4)[0]==0x8c0155a0,(row,hex(ref+4))
  put(ref+4,struct.pack('<I',0x8c010000+at))
 prompt_results.append({'text':text,'x':x,'y':106,'wrapper':at})
# Friendship: measure the actual glyph pixels, including trailing padding,
# using the same pitch cap as the existing renderer.
pool=(pool+3)&~3;friend=pool
table=0x10f730;records=[]
assert not any(program[table:table+428])
seen=set()
for i in range(53):
 ptr=struct.unpack_from('<I',program,0x11ced4+i*4)[0]
 if ptr in seen:continue
 seen.add(ptr);at=ptr-0x8c010000
 assert 0<=at<len(program)
 raw=program[at:].split(b'\0',1)[0];assert len(raw)%2==0
 if not raw:continue
 pitch=min(24,304//len(raw));bounds=[]
 for j in range(0,len(raw),2):
  k=idx(raw[j:j+2]);assert 0<=k<len(font)//72
  box=Image.frombytes('1',(24,24),bytes(font[k*72:(k+1)*72])).getbbox()
  if box:bounds.append((j//2*pitch+box[0],j//2*pitch+box[2]))
 left=min(x[0] for x in bounds);right=max(x[1] for x in bounds)
 delta=round(79.5-(left+right)/2)
 records.append((ptr,delta))
data=b''.join(struct.pack('<Ii',p,x) for p,x in records)+bytes(8);put(table,data)
# Lookup covers every value in the game's Friendship roster, including the dash value.
ops=[0xd207,0x6022,0x2008,0x8908,0x3400,0x8902,0x7208,0xaff8,0x0009,
     0x5121,0x351c,0x7604,0xd002,0x402b,0x0009,0x0009]
# Both no-match and matching entries continue through the original renderer.
ops[3]=0x8907
put(friend,struct.pack('<16HII',*ops,0x8c010000+table,0x8c101200)+bytes(16));pool+=56
put(0x2dcf0,struct.pack('<I',0x8c010000+friend))
assert pool<0x105c78
def tile(n,rows):
 off=8312832+n*SIZE;original=archive[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 face=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',20);face.set_variation_by_axes([400,75]);cap=face.getbbox('H')
 for rect,text in rows:
  x0,y0,x1,y1=rect;im.paste((0,0,0,0),rect);mask[y0:y1,x0:x1]=True
 for rect,text in rows:
  x0,y0,x1,y1=rect;b=face.getbbox(text);art=Image.new('RGBA',(b[2]-b[0]+2,24))
  ImageDraw.Draw(art).text((1-b[0],4-cap[1]),text,font=face,fill='white')
  art=art.resize((round(art.width*.70),24),Image.Resampling.LANCZOS)
  assert art.width<=x1-x0-2,(text,art.width,x1-x0)
  im.alpha_composite(art,(x0+2,y0))
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];ad=adapt_codebook(im,original,touched,'4444');en=encode(im,ad);out=bytearray(ad)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=en[p]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
 name=f'alignment-cmk2-{n}.bin';(R/name).write_bytes(out);final.resize((768,768)).save(R/(name+'.png'));textures.append([off,name])
tile(8,[((32,104,164,128),'Damage Focus'),((0,128,128,152),'Submission Focus'),((128,128,240,152),'Standing Focus'),((0,152,176,176),'Power Throws'),((0,176,56,200),'Big Moves'),((0,200,72,224),'Strikes'),((0,224,192,248),'Technical Throws')])
tile(9,[((0,208,144,232),'Submission')])
(R/'alignment-program-patches.json').write_text(json.dumps(patches))
(R/'alignment-texture-patches.json').write_text(json.dumps(textures))
(R/'alignment-report.json').write_text(json.dumps({'wording':changed,'prompts':prompt_results,'friendship_wrapper':friend,'end':pool,'font_pairs':pairs},indent=2))
(R/'moves-font.bin').write_bytes(font)
print('Prepared',len(patches),'program edits and',len(textures),'texture blocks; unrelated pixels verified unchanged.')
