"""Translate the complete CAW word bank and History Match 2; align Weight."""
from pathlib import Path
import json,struct,sys,textwrap,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
backup=R/'before-catchphrase-update';backup.mkdir(exist_ok=True)
for path in [G/'1ST_READ.BIN',G/'TEX.AFS',R/'moves-font.bin',G/'English_Names_Verified/README.txt']:
 if not (backup/path.name).exists():shutil.copy2(path,backup/path.name)
original=(R/'disc-original.bin').read_bytes();program=(backup/'1ST_READ.BIN').read_bytes();font=bytearray((backup/'moves-font.bin').read_bytes());before=bytes(font)
rows=json.loads((R/'catchphrase-source.json').read_text(encoding='utf-8'))
en=[v.strip() for line in (R/'catchphrase-english.txt').read_text(encoding='utf-8-sig').splitlines() for v in line.split('|')]
assert len(rows)==len(en)==560 and all(0<len(s)<=14 for s in en)
pairs=json.loads((G/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'))['font_pairs']
def index(code):
 a,b=code;return ((a-129)*2+(b>=159))*96+b-(126 if b>=159 else 32 if b>=128 else 31)-32
letters={}
for pair,code in pairs.items():
 im=Image.frombytes('1',(24,24),bytes(font[index(bytes.fromhex(code))*72:(index(bytes.fromhex(code))+1)*72]))
 letters.setdefault(pair[0],im.crop((0,0,12,24)))
used=set(zip(original,original[1:]))|set(zip(program,program[1:]));allocated=set();newglyphs={}
def allocate(key,im):
 for i in range(600,len(font)//72):
  row=i//96+33;col=i%96+32
  if not 33<=col<=126 or i in allocated:continue
  lead=(row-33)//2+129;trail=col+(31 if row%2 else 126)
  if row%2 and trail>=127:trail+=1
  code=bytes([lead,trail])
  if tuple(code) in used:continue
  font[i*72:(i+1)*72]=im.tobytes();allocated.add(i);used.add(tuple(code));newglyphs[key]={'index':i,'code':code.hex()};return code
 raise AssertionError('No unused font cell')
def pair_code(s):
 if s in pairs:return bytes.fromhex(pairs[s])
 im=Image.new('1',(24,24))
 for j,ch in enumerate(s):
  if ch not in letters:
   cell=Image.new('L',(16,24));ImageDraw.Draw(cell).text((0,-3),ch,font=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',24),fill=255)
   letter=Image.new('1',(12,24));letter.paste(cell.resize((10,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1'),(1,0));letters[ch]=letter
  im.paste(letters[ch],(j*12,0))
 code=allocate('pair:'+s,im);pairs[s]=code.hex();return code
patches=[];start=0x10e2f0;end=0x10f8dc;pool=bytearray();offsets={};translations=[]
for row,text in zip(rows,en):
 if text not in offsets:
  offsets[text]=start+len(pool)
  data=(row['jp'].encode('cp932') if text=='*' else b''.join(pair_code(text[i:i+2].ljust(2)) for i in range(0,len(text),2)))
  assert len(data)<=16
  pool+=data+b'\0'
 patches.append([row['pointer'],struct.pack('<I',0x8c010000+offsets[text]).hex()])
 translations.append(dict(row,en=text,new_offset=offsets[text]))
assert len(pool)<=end-start
# The table is the sole pointer owner of these original strings.
refs={row['pointer'] for row in rows};oldoffs={row['offset'] for row in rows}
for p in range(0,len(original)-3,4):
 if struct.unpack_from('<I',original,p)[0]-0x8c010000 in oldoffs:assert p in refs,hex(p)
patches.append([start,(pool+bytes(end-start-len(pool))).hex()])
paragraphs=['A best-of-three-falls match for the International Tag Team Championship held by Baba and Tsuruta.','It brought together the finest competitors of the era.','Although the challengers lost by disqualification, the action was fierce from start to finish.']
lines=[l for p in paragraphs for l in textwrap.wrap(p,63)];triples={};face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',18)
for line in lines:
 for k in range(0,len(line),3):
  s=line[k:k+3].ljust(3)
  if s in triples:continue
  im=Image.new('1',(24,24))
  for j,ch in enumerate(s):
   ink=Image.new('L',(11,24));ImageDraw.Draw(ink).text((0,1),ch,font=face,fill=255)
   im.paste(ink.resize((6,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1'),(j*7,0))
  assert im.crop((20,0,24,24)).getbbox() is None
  triples[s]=allocate('story:'+s,im)
encoded=b'\n'.join(b''.join(triples[l[i:i+3].ljust(3)] for i in range(0,len(l),3)) for l in lines)+b'\0'
off=0x11de6e;capacity=original.index(0,off)-off+1;assert len(encoded)<=capacity
patches.append([off,(encoded+bytes(capacity-len(encoded))).hex()])
reverse={v:k for k,v in triples.items()};assert [''.join(reverse[l[i:i+2]] for i in range(0,len(l),2)).rstrip() for l in encoded[:-1].split(b'\n')]==lines
assert all(font[p:p+72]==before[p:p+72] for p in range(0,len(font),72) if p//72 not in allocated)
# Weight's independent source cell is used by the Body Type dialog.
archive=(backup/'TEX.AFS').read_bytes();entry=json.loads((R/'caw-entries.json').read_text())['spr_cmk'][0];at=entry+6*SIZE;block=archive[at:at+SIZE];old=decode(block);target=old.copy();rect=(100,160,192,192);target.paste((0,0,0,0),rect)
f=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',29);box=f.getbbox('Weight');cap=f.getbbox('H');ink=Image.new('L',(box[2]-box[0],box[3]-cap[1]));ImageDraw.Draw(ink).text((-box[0],-cap[1]),'Weight',font=f,fill=255)
ink=ink.resize((76,23),Image.Resampling.LANCZOS);art=Image.new('RGBA',ink.size,'white');art.putalpha(ink);target.alpha_composite(art,(108,170))
mask=np.zeros((256,256),bool);mask[160:192,100:192]=True;touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
adapted=adapt_codebook(target,block,touched,'4444');packed=encode(target,adapted);out=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):
 p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=packed[p]
assert np.array_equal(np.asarray(old)[~mask],np.asarray(decode(out))[~mask])
(R/'catchphrase-weight.bin').write_bytes(out)
texture_patches=[[at,'catchphrase-weight.bin']]
# Localize the optional Japanese joining particle and its two choices.
at2=json.loads((R/'caw-entries.json').read_text())['spr_cmk2'][0]+23*SIZE
block2=archive[at2:at2+SIZE];old2=decode(block2);target2=old2.copy();target2.paste((0,0,0,0),(0,0,192,48))
f2=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',24);f2.set_variation_by_axes([400,75])
for y,text in [(0,"Add 'of'"),(24,"Omit 'of'")]:
 box=f2.getbbox(text);w=box[2]-box[0];h=box[3]-box[1]
 ImageDraw.Draw(target2).text(((160-w)//2-box[0],y+(24-h)//2-box[1]),text,font=f2,fill='white')
m=np.zeros((256,256),bool);m[:48,:192]=True;t=m.reshape(128,2,128,2).any(axis=(1,3))[::-1]
ad=adapt_codebook(target2,block2,t,'4444');pa=encode(target2,ad);out2=bytearray(ad)
for y,x in zip(*np.nonzero(t)):
 pos=2048+spread(int(y))+(spread(int(x))<<1);out2[pos]=pa[pos]
assert np.array_equal(np.asarray(old2)[~m],np.asarray(decode(out2))[~m])
(R/'catchphrase-joiner.bin').write_bytes(out2);texture_patches.append([at2,'catchphrase-joiner.bin'])
(R/'catchphrase-texture-patches.json').write_text(json.dumps(texture_patches))

# Catchphrase rows use a thinner highlight; center their English cap height.
cave=0xf1320
assert not any(program[cave:cave+24])
code=struct.pack('<10HI',0x6040,0x600c,0xe184,0x611c,0x3012,0x8b00,0x7605,0xd001,0x402b,0x0009,0x8c0155a0)
patches.append([cave,code.hex()])
for at in [0x29098,0x291b8]:
 assert struct.unpack_from('<I',original,at)[0]==0x8c0155a0
 patches.append([at,struct.pack('<I',0x8c010000+cave).hex()])
# A visible space before the second word, and around the optional 'of'.
assert original[0xede94:0xede97]=='の'.encode('cp932')+b'\0'
patches.append([0xede94,(pair_code('of')+b'\0').hex()])
assert original[0x272da:0x272dc]==bytes.fromhex('1870')
patches.append([0x272da,'2470'])
assert not any(program[0xf1340:0xf1364])
first=struct.pack('<8HII',0xd104,0x3410,0x8b00,0x750c,0xd001,0x402b,0x0009,0x0009,0x8c101320,0x8c0fde94)
second=struct.pack('<4HI',0x750c,0xd001,0x402b,0x0009,0x8c101320)
patches.extend([[0xf1340,first.hex()],[0xf1358,second.hex()],[0x272f4,struct.pack('<I',0x8c101340).hex()],[0x2732c,struct.pack('<I',0x8c101358).hex()]])
assert max(((len(s)+1)//2)*24 for s in en)*2+48<=420
(R/'catchphrase-program-patches.json').write_text(json.dumps(patches))
(R/'moves-font.bin').write_bytes(font)
(R/'catchphrase-update-report.json').write_text(json.dumps({'choices':translations,'new_glyphs':newglyphs,'story_paragraphs':paragraphs,'story_lines':lines,'story_offset':off,'story_capacity':capacity,'story_bytes':len(encoded),'pool_bytes':len(pool),'other_font_cells_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Verified',len(rows),'choices,',len(allocated),'new glyphs,',len(lines),'story lines, isolated Weight texture edit.')
