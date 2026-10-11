"""Replace the complete interview bank without changing its selectors or unrelated text."""
from pathlib import Path
import json,struct,textwrap,shutil
from PIL import Image
R=Path(__file__).resolve().parent;G=R.parent;B=R/'before-all-interviews';B.mkdir(exist_ok=True)
for name,src in [('1ST_READ.BIN',G/'1ST_READ.BIN'),('font.bin',R/'moves-font.bin')]:
 if not (B/name).exists():shutil.copy2(src,B/name)
b=(B/'1ST_READ.BIN').read_bytes();original=(R/'disc-original.bin').read_bytes()
font=bytearray((B/'font.bin').read_bytes());font_before=bytes(font)
sources=json.loads((R/'all-interviews-source.json').read_text(encoding='utf-8'))
sources={x['offset']:x for x in sources if not x['ja'].isascii()}
english={}
for row in (R/'interviews-english.txt').read_text(encoding='utf-8').splitlines():
 key,value=row.split('|',1);key=int(key,16);assert key not in english;english[key]=value
assert set(english)==set(sources),(set(sources)-set(english),set(english)-set(sources))
pairs=json.loads((R/'alignment-report.json').read_text())['font_pairs'].copy()
def index(code):
 a,t=bytes.fromhex(code);return ((a-129)*2+(t>=159))*96+t-(126 if t>=159 else 32 if t>=128 else 31)-32
letters={}
for pair,code in pairs.items():
 cell=Image.frombytes('1',(24,24),bytes(font[index(code)*72:(index(code)+1)*72]))
 for j,ch in enumerate(pair):letters.setdefault(ch,cell.crop((j*12,0,j*12+12,24)))
# Japanese glyphs used only by the interview bank can be reclaimed because
# every reference to that bank is replaced. Preserve all other original and
# current text, as well as every previously allocated English pair.
used={tuple(bytes.fromhex(v)) for v in pairs.values()}
for source in (b,original):
 remaining=bytearray(source)
 for lo,hi in [(0xf4b58,0xf56ac),(0xf573c,0xfc450)]:remaining[lo:hi]=bytes(hi-lo)
 used.update(zip(remaining,remaining[1:]))
free=[]
for i in range(600,len(font)//72):
 row=i//96+33;col=i%96+32
 if not 33<=col<=126:continue
 a=(row-33)//2+129;t=col+(31 if row%2 else 126)
 if row%2 and t>=127:t+=1
 if (a,t) not in used:free.append((i,bytes([a,t])))
free=iter(free);new={}
def encode(lines):
 result=[]
 for line in lines:
  chunks=[]
  for j in range(0,len(line),2):
   pair=line[j:j+2].ljust(2)
   if pair not in pairs:
    i,code=next(free);cell=Image.new('1',(24,24))
    for k,ch in enumerate(pair):cell.paste(letters[ch],(k*12,0))
    font[i*72:(i+1)*72]=cell.tobytes();pairs[pair]=code.hex();new[pair]={'index':i,'code':code.hex()}
   chunks.append(bytes.fromhex(pairs[pair]))
  result.append(b''.join(chunks))
 return b'\n'.join(result)+b'\0'
records=[]
for at,text in sorted(english.items()):
 lines=text.split('~') if '~' in text else textwrap.wrap(text,44,break_long_words=False,break_on_hyphens=False)
 assert 1<=len(lines)<=3 and max(map(len,lines))<=44,(hex(at),lines)
 records.append({'old_offset':at,'japanese':sources[at]['ja'],'english':lines,'refs':sources[at]['refs'],'data':encode(lines)})
# Reuse only the old dialogue storage. The twelve movie filenames between
# these two regions must remain at their original offsets.
regions=[(0xf4b58,0xf56ac),(0xf573c,0xfc450)];pools=[list(x) for x in regions]
program=bytearray(b)
for lo,hi in regions:program[lo:hi]=bytes(hi-lo)
for rec in sorted(records,key=lambda x:len(x['data']),reverse=True):
 data=rec['data'];size=(len(data)+1)&~1
 fitting=[p for p in pools if p[1]-p[0]>=size];assert fitting,('Interview storage full',len(data),pools)
 pool=min(fitting,key=lambda p:p[1]-p[0]);at=pool[0];pool[0]+=size
 program[at:at+len(data)]=data;rec['new_offset']=at
 for ref in rec['refs']:
  assert struct.unpack_from('<I',b,ref)[0]==0x8c010000+rec['old_offset'],hex(ref)
  struct.pack_into('<I',program,ref,0x8c010000+at)
patches=[[lo,program[lo:hi].hex()] for lo,hi in regions]
patches += [[ref,program[ref:ref+4].hex()] for rec in records for ref in rec['refs']]
reverse={bytes.fromhex(v):k for k,v in pairs.items()}
for rec in records:
 raw=bytes(program[rec['new_offset']:]).split(b'\0',1)[0]
 decoded=[''.join(reverse[line[j:j+2]] for j in range(0,len(line),2)).rstrip() for line in raw.split(b'\n')]
 assert decoded==rec['english'],rec
 for ref in rec['refs']:assert struct.unpack_from('<I',program,ref)[0]==rec['new_offset']+0x8c010000
 del rec['data']
allowed={x['index'] for x in new.values()}
assert all(font[i:i+72]==font_before[i:i+72] for i in range(0,len(font),72) if i//72 not in allowed)
assert program[0xf56ac:0xf573c]==b[0xf56ac:0xf573c]
(R/'all-interview-program-patches.json').write_text(json.dumps(patches))
(R/'all-interview-report.json').write_text(json.dumps({'entry_count':len(records),'newly_translated':len(records)-1,'reference_count':sum(len(x['refs']) for x in records),'line_width':44,'max_lines':3,'remaining_bytes':sum(hi-lo for lo,hi in pools),'new_pairs':new,'font_pairs':pairs,'entries':records},ensure_ascii=False,indent=2),encoding='utf-8')
(R/'moves-font.bin').write_bytes(font)
p=R/'build_verified.py';s=p.read_text()
if "'all-interview-program-patches.json'" not in s:
 s=s.replace("'champion-tag-program-patches.json']","'champion-tag-program-patches.json','all-interview-program-patches.json']")
 p.write_text(s)
out=G/'English_Names_Verified/All_Interview_Translations.txt'
out.write_text('GIANT GRAM 2000 - COMPLETE INTERVIEW TRANSLATION\n569 entries: 568 newly translated; existing Honda quote preserved.\nIncludes matchup, tag, championship, unused-character and interviewer text.\n\n'+''.join(f"Entry {i+1:03d} - original offset 0x{x['old_offset']:06X}\n"+'\n'.join(x['english'])+'\n\n' for i,x in enumerate(records)),encoding='utf-8')
print(f"Prepared {len(records)} entries, {sum(len(x['refs']) for x in records)} references, {len(new)} new font pairs; {sum(hi-lo for lo,hi in pools)} storage bytes remain.")
