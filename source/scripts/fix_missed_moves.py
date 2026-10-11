"""Fill missed move tables by reusing the game's existing translated strings."""
from pathlib import Path
import json,struct
from PIL import Image
R=Path(__file__).resolve().parent;G=R.parent
b=(G/'1ST_READ.BIN').read_bytes();rep=json.loads((G/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'));lookup={x['jp']:x for x in rep['labels']};pairs=rep['font_pairs'].copy()
font=bytearray((R/'moves-font.bin').read_bytes())
def index(code):
 a,z=code;return ((a-129)*2+(z>=159))*96+z-(126 if z>=159 else 32 if z>=128 else 31)-32
# Only one new pair is needed; copy its two letter cells from the verified font.
if 'Ed' not in pairs:
 cells=[]
 for ch in 'Ed':
  pair=next(p for p in pairs if ch in p);j=pair.index(ch);at=index(bytes.fromhex(pairs[pair]))*72
  cells.append(Image.frombytes('1',(24,24),bytes(font[at:at+72])).crop((j*12,0,j*12+12,24)))
 for i in range(600,len(font)//72):
  row=i//96+33;col=i%96+32
  if not 33<=col<=126:continue
  lead=(row-33)//2+129;trail=col+(31 if row%2 else 126)
  if row%2 and trail>=127:trail+=1
  code=bytes([lead,trail])
  if code in b or code.hex() in pairs.values():continue
  glyph=Image.new('1',(24,24));glyph.paste(cells[0],(0,0));glyph.paste(cells[1],(12,0));font[i*72:i*72+72]=glyph.tobytes();pairs['Ed']=code.hex();break
 else:raise AssertionError('No free font cell')
def pack(s):return b''.join(bytes.fromhex(pairs[s[i:i+2].ljust(2)]) for i in range(0,len(s),2))+b'\0'
patches=[];rows=[]
# The 39-entry fusion-name table was outside the previous localization scan.
for pos in range(0x11b878,0x11b914,4):
 old=struct.unpack_from('<I',b,pos)[0]-0x8c010000;end=b.index(0,old);jp=b[old:end].decode('cp932')
 if jp=='ビルドアップドッキング':
  en='Build-Up Docking';new=old;data=pack(en);assert len(data)<=end-old+1;patches.append([old,(data+bytes(end-old+1-len(data))).hex()])
 else:
  entry=lookup[jp];en=entry['en'];new=entry['new_offset'];assert b[new:new+len(pack(en))]==pack(en)
 refs=[i for i in range(0,len(b)-3,4) if struct.unpack_from('<I',b,i)[0]==old+0x8c010000]
 assert pos in refs
 for ref in refs:patches.append([ref,struct.pack('<I',new+0x8c010000).hex()])
 rows.append({'japanese':jp,'english':en,'old_offset':old,'new_offset':new,'refs':refs})
# The first primary move sits 16 bytes before the old scan's lower bound.
old=0x100380;new=0x11b56a;data=pack('Knife-Edge Chop')
assert b[old:b.index(0,old)].decode('cp932')=='水平チョップ'
assert all(not new<=row['new_offset']<new+len(data) for row in rows)
patches.append([new,data.hex()]);refs=[]
for i in range(0,len(b)-3,4):
 if struct.unpack_from('<I',b,i)[0]==old+0x8c010000:patches.append([i,struct.pack('<I',new+0x8c010000).hex()]);refs.append(i)
assert len(refs)>=3
rows.append({'japanese':'水平チョップ','english':'Knife-Edge Chop','old_offset':old,'new_offset':new,'refs':refs})
result=bytearray(b)
for off,h in patches:result[off:off+len(bytes.fromhex(h))]=bytes.fromhex(h)
for row in rows:
 raw=pack(row['english']);off=row['new_offset'];assert result[off:off+len(raw)]==raw
 for ref in row['refs']:assert struct.unpack_from('<I',result,ref)[0]==off+0x8c010000
(R/'missed-move-patches.json').write_text(json.dumps(patches))
(R/'missed-move-report.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'moves-font.bin').write_bytes(font)
print('Verified',len(rows),'missed move labels and all their pointers; one font pair added.')
