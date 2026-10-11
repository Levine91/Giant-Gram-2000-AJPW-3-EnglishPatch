from pathlib import Path
import json,re,struct
from PIL import Image,ImageFont,ImageDraw
ROOT=Path(__file__).resolve().parent;GAME=ROOT.parent
report=json.loads((GAME/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'))
program=(GAME/'1ST_READ.BIN').read_bytes();archive=(GAME/'TEX.AFS').read_bytes();offset,size=struct.unpack_from('<II',archive,8)
font=bytearray(archive[offset:offset+size]);before=bytes(font)
def idx(code):
 a,b=code;return ((a-129)*2+(b>=159))*96+b-(126 if b>=159 else 32 if b>=128 else 31)-32
pairs=report['font_pairs']
def pack(s):
 result=b''
 for run in re.findall(r'[ -~]+|[^ -~]',s):
  if run.isascii() and ord(run[0])>=32:
   result+=b''.join(bytes.fromhex(pairs[run[i:i+2].ljust(2)]) for i in range(0,len(run),2))
  else:result+=run.encode('cp932')
 return result
for row in report['labels']:
 data=pack(row['en']);at=row['new_offset']
 assert program[at:at+len(data)]==data,(row['en'],hex(at))
face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',24);letters={}
for ch in set(''.join(pairs)):
 im=Image.new('L',(16,24));ImageDraw.Draw(im).text((0,-3),ch,font=face,fill=255)
 im=im.resize((10,24),Image.Resampling.LANCZOS).point(lambda v:255 if v>=100 else 0).convert('1')
 cell=Image.new('1',(12,24));cell.paste(im,(1,0));letters[ch]=cell
changed=[]
for pair,code in pairs.items():
 im=Image.new('1',(24,24));im.paste(letters[pair[0]],(0,0));im.paste(letters[pair[1]],(12,0))
 at=idx(bytes.fromhex(code))*72;data=im.tobytes()
 if font[at:at+72]!=data:changed.append(pair)
 font[at:at+72]=data
# Every translation uses the same fixed cells and baseline; icons remain untouched.
allowed={idx(bytes.fromhex(c)) for c in pairs.values()}
assert all(font[i:i+72]==before[i:i+72] for i in range(0,len(font),72) if i//72 not in allowed)
(ROOT/'moves-font.bin').write_bytes(font)
(ROOT/'moves-font-meta.json').write_text(json.dumps({'archive_offset':offset,'length':size,'changed_pairs':len(changed)}))
print('Verified',len(report['labels']),'encoded labels;',len(changed),'of',len(pairs),'pairs needed font normalization')
print('Name pair changes:',[p for p in changed if p in [n[i:i+2].ljust(2) for n in ['Mitsuharu Misawa','Toshiaki Kawada'] for i in range(0,len(n),2)]])
