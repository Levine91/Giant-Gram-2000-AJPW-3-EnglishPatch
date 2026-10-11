from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent;sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
a=(R/'before-gameplay-revision/TEX.AFS').read_bytes();b=(R/'before-gameplay-revision/1ST_READ.BIN').read_bytes();edits=[]
face=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);cap=face.getbbox('H')
for n,clear,rows in [(8,[(32,104,256,128),(0,128,256,152),(0,152,192,248)],[(32,104,'Damage Focus'),(0,128,'Submission Focus'),(0,152,'Power Throws'),(0,176,'Big Moves'),(0,200,'Strikes'),(0,224,'Technical Throws')]),(9,[(0,208,184,256)],[(0,208,'Submission'),(0,232,'Standing Focus')])]:
 off=8312832+n*SIZE;olddata=a[off:off+SIZE];old=decode(olddata);im=old.copy();mask=np.zeros((256,256),bool)
 for rect in clear:
  im.paste((0,0,0,0),rect);x,y,z,w=rect;mask[y:w,x:z]=True
 d=ImageDraw.Draw(im)
 for x,y,text in rows:
  box=face.getbbox(text);assert box[2]-box[0]<=180,(text,box)
  d.text((x+2-box[0],y+4-cap[1]),text,font=face,fill='white')
 touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];ad=adapt_codebook(im,olddata,touched,'4444');encoded=encode(im,ad);out=bytearray(ad)
 for y,x in zip(*np.nonzero(touched)):
  p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=encoded[p]
 final=decode(out);assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
 name=f'wide-caw-{n}.bin';(R/name).write_bytes(out);final.resize((768,768)).save(R/(name+'.png'));edits.append([off,name])
patches=[]
def put(at,data):patches.append([at,data.hex()])
for at in [0x27bc0,0x27bfc,0x27c38]:
 assert b[at:at+2]==struct.pack('<H',0x9700+(0x27c6e-at-4)//2)
 put(at,struct.pack('<H',0x9700+(0x27c72-at-4)//2))
# Standing Focus uses the otherwise empty second row of the Submission sprite.
cave=0x1103ec;assert not any(b[cave:cave+40])
ops=[0xe01a,0x3400,0x8b09,0xe080,0x600c,0x3500,0x8b05,0xe41b,0xe500,0xe6e8,0x666c,0xe7b8,0x677c,0xd001,0x402b,0x0009]
put(cave,struct.pack('<16HI',*ops,0x8c013b00));put(0x27c78,struct.pack('<I',0x8c010000+cave))
assert b[0x27c50:0x27c52]==bytes.fromhex('30e1');put(0x27c50,bytes.fromhex('18e1'))
(R/'wide-caw-program-patches.json').write_text(json.dumps(patches));(R/'wide-caw-texture-patches.json').write_text(json.dumps(edits))
print('Eight labels use unsqueezed Arial 20 with matching left edges; Focus drawing widths expanded.')
