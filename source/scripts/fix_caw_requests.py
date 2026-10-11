from pathlib import Path
import sys,struct,json,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import decode,SIZE,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
base=(G/'TEX.AFS').read_bytes();edits=[]
def tile(entry,n,paint):
 off=entry+n*SIZE;original=base[off:off+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
 def label(rect,text,size=17,outline=0):
  x0,y0,x1,y1=rect;im.paste((0,0,0,0),rect);mask[y0:y1,x0:x1]=True
  if not text:return
  f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size);d=ImageDraw.Draw(im);box=d.textbbox((0,0),text,font=f,stroke_width=outline)
  assert box[2]-box[0]<=x1-x0,(text,rect,box)
  d.text((x0+(x1-x0-box[2]+box[0])//2-box[0],y0+(y1-y0-box[3]+box[1])//2-box[1]),text,font=f,fill='white',stroke_width=outline,stroke_fill='black')
 paint(im,mask,label)
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,original,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
 for y,x in zip(*np.nonzero(touched)):
  pos=2048+spread(int(y))+(spread(int(x))<<1);out[pos]=encoded[pos]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
 file=f'caw-{entry}-{n}.bin';(R/file).write_bytes(out);edits.append([off,file]);final.save(R/f'caw-{entry}-{n}.png')
def menu(im,mask,label):
 for rect,text in [((8,48,144,88),'Resume Practice'),((0,96,152,136),'Main Menu'),((40,144,112,184),'Join'),((160,144,256,184),'Rejoin')]:label(rect,text,16)
tile(8312832,0,menu)
def confirmation(im,mask,label):
 # Both adjacent sprite fragments form one 432-pixel sentence.
 strip=Image.new('RGBA',(432,32));d=ImageDraw.Draw(strip);f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',18);text='Are you sure you want to load this wrestler?';b=d.textbbox((0,0),text,font=f)
 assert b[2]<=420
 d.text(((432-b[2])//2, (32-(b[3]-b[1]))//2-b[1]),text,font=f,fill='white')
 label((0,64,256,128),'')
 im.paste(strip.crop((0,0,256,32)),(0,64));im.paste(strip.crop((256,0,432,32)),(0,96))
tile(8312832,6,confirmation)
def vmu0(im,mask,label):
 for y,w,text in [(176,176,'Loading VMU data...'),(192,176,'VMU data loaded'),(208,232,'Could not load VMU data')]:label((0,y,w,y+16),text,11,1)
def vmu2(im,mask,label):
 for y,w,text in [(140,176,'Loading VMU file...'),(156,160,'VMU file loaded'),(172,232,'Could not load VMU file')]:label((0,y,w,y+16),text,11,1)
# Pixel rows follow the actual text bounds, verified in the original atlas.
tile(978944,0,vmu0);tile(978944,2,vmu2)
(R/'caw-texture-patches.json').write_text(json.dumps(edits))
r=json.loads((G/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'));pairs=r['font_pairs'];program=(R/'disc-original.bin').read_bytes()
font=bytearray((R/'moves-font.bin').read_bytes())
def pair_code(pair):
 if pair in pairs:return bytes.fromhex(pairs[pair])
 for index in range(600,len(font)//72):
  row=index//96+33;col=index%96+32
  if not 33<=col<=126:continue
  lead=(row-33)//2+129;trail=col+(31 if row%2 else 126)
  if row%2 and trail>=127:trail+=1
  code=bytes([lead,trail])
  if code in program or code.hex() in pairs.values():continue
  glyph=Image.new('1',(24,24));face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',24)
  for j,ch in enumerate(pair):
   cell=Image.new('L',(16,24));ImageDraw.Draw(cell).text((0,-3),ch,font=face,fill=255);cell=cell.resize((10,24),Image.Resampling.LANCZOS).point(lambda v:255 if v>=100 else 0).convert('1');glyph.paste(cell,(j*12+1,0))
  font[index*72:(index+1)*72]=glyph.tobytes();pairs[pair]=code.hex();return code
 raise AssertionError('No free glyph')
def pack(s):
 out=b''
 for run in re.findall(r'[ -~]+|[^ -~]',s):
  if run.isascii() and ord(run[0])>=32:
   out+=b''.join(pair_code(run[i:i+2].ljust(2)) for i in range(0,len(run),2))
  else:out+=run.encode('cp932')
 return out
patches=[]
for off,cap,text in [(0xedbc0,30,'Choose a move to delete.'),(989250,49,'Choose a tag move while gripping (\x07Β\r).'),(989188,61,'Choose a tag move: opponent down (\x07Β\r).')]:
 data=pack(text);assert len(data)<=cap,(text,len(data),cap);assert b'\n' not in data;patches.append([off,(data+bytes(cap+1-len(data))).hex()])
for ref in [132896,133704]:
 pos=ref-0x52;assert program[pos:pos+4]==bytes.fromhex('64e614e5');patches.append([pos,'6ae65ce5'])
(R/'caw-program-patches.json').write_text(json.dumps(patches))
(R/'moves-font.bin').write_bytes(font)
print('Prepared 4 texture blocks and 3 one-line prompts')
