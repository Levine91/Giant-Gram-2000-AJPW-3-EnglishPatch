"""Build a separate GDI; preserve originals and verify Mode 1 checksums."""
from pathlib import Path
import json, struct, shutil, hashlib
ROOT=Path(__file__).resolve().parent
GAME=ROOT.parent
OUT=GAME/'English_Names_Verified'
OUT.mkdir(exist_ok=True)
fwd=[];back=[0]*256;crc=[]
for i in range(256):
 j=(i<<1)^(0x11d if i&128 else 0);fwd.append(j);back[i^j]=i
 v=i
 for _ in range(8):v=(v>>1)^(0xd8018001 if v&1 else 0)
 crc.append(v)
def ecc(src,major,minor,mult,inc):
 out=bytearray(major*2);size=major*minor
 for m in range(major):
  index=(m>>1)*mult+(m&1);a=b=0
  for _ in range(minor):
   v=src[index];index=(index+inc)%size;a^=v;b^=v;a=fwd[a]
  a=back[fwd[a]^b];out[m]=a;out[m+major]=a^b
 return out
def checksums(s):
 assert len(s)==2352 and s[15]==1
 s=bytearray(s);v=0
 for x in s[:2064]:v=(v>>8)^crc[(v^x)&255]
 struct.pack_into('<I',s,2064,v);s[2068:2076]=bytes(8)
 s[2076:2248]=ecc(s[12:2076],86,24,2,86)
 s[2248:2352]=ecc(s[12:2248],52,43,86,88)
 return s
source=GAME.parent/'track03.bin'
with source.open('rb') as f:
 f.seek(16*2352);sample=f.read(2352)
 assert checksums(sample)==sample,'Sector checksum self-check failed'
program=bytearray((ROOT/'disc-original.bin').read_bytes())
patches=json.loads((ROOT/'spacing_patches.json').read_text())
if (ROOT/'caw-program-patches.json').exists():patches+=json.loads((ROOT/'caw-program-patches.json').read_text())
if (ROOT/'missed-move-patches.json').exists():patches+=json.loads((ROOT/'missed-move-patches.json').read_text())
if (ROOT/'history-story-patches.json').exists():patches+=json.loads((ROOT/'history-story-patches.json').read_text())
if (ROOT/'caw-polish-program-patches.json').exists():patches+=json.loads((ROOT/'caw-polish-program-patches.json').read_text())
if (ROOT/'catchphrase-program-patches.json').exists():patches+=json.loads((ROOT/'catchphrase-program-patches.json').read_text())
if (ROOT/'history4-program-patches.json').exists():patches+=json.loads((ROOT/'history4-program-patches.json').read_text())
if (ROOT/'results-program-patches.json').exists():patches+=json.loads((ROOT/'results-program-patches.json').read_text())
if (ROOT/'remaining-program-patches.json').exists():patches+=json.loads((ROOT/'remaining-program-patches.json').read_text())
if (ROOT/'history-remaining-program-patches.json').exists():patches+=json.loads((ROOT/'history-remaining-program-patches.json').read_text())
if (ROOT/'history-13-24-program-patches.json').exists():patches+=json.loads((ROOT/'history-13-24-program-patches.json').read_text())
if (ROOT/'vs-default-program-patches.json').exists():patches+=json.loads((ROOT/'vs-default-program-patches.json').read_text())
if (ROOT/'october-program-patches.json').exists():patches+=json.loads((ROOT/'october-program-patches.json').read_text())
if (ROOT/'alignment-program-patches.json').exists():patches+=json.loads((ROOT/'alignment-program-patches.json').read_text())
for layer in ['grab-program-patches.json','wide-caw-program-patches.json','ring-exit-program-patches.json','champion-tag-program-patches.json','all-interview-program-patches.json']:
 patches+=json.loads((ROOT/layer).read_text())
patches+=json.loads((ROOT/'tournament-program-patches.json').read_text())
for off,data in patches:program[off:off+len(bytes.fromhex(data))]=bytes.fromhex(data)
meta=json.loads((ROOT/'prompt_patch.json').read_text())
# Use the final merged bytes when newer patches reuse an older text pool.
changes=[(546682,off,bytes(program[off:off+len(bytes.fromhex(data))])) for off,data in patches]
changes.append((317680,meta['archive_offset'],(ROOT/'prompt-fixed.bin').read_bytes()))
if (ROOT/'moves-font.bin').exists():
 fontmeta=json.loads((ROOT/'moves-font-meta.json').read_text());changes.append((317680,fontmeta['archive_offset'],(ROOT/'moves-font.bin').read_bytes()))
if (ROOT/'caw-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'caw-texture-patches.json').read_text()))
if (ROOT/'arcade_patch.json').exists():
 m=json.loads((ROOT/'arcade_patch.json').read_text());changes.append((317680,m['archive_offset'],(ROOT/'arcade-fixed.bin').read_bytes()))
if (ROOT/'match-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'match-texture-patches.json').read_text()))
if (ROOT/'intro-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'intro-texture-patches.json').read_text()))
if (ROOT/'history-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'history-texture-patches.json').read_text()))
if (ROOT/'history-ui-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'history-ui-texture-patches.json').read_text()))
if (ROOT/'history-polish-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'history-polish-texture-patches.json').read_text()))
if (ROOT/'caw-polish-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'caw-polish-texture-patches.json').read_text()))
if (ROOT/'catchphrase-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'catchphrase-texture-patches.json').read_text()))
if (ROOT/'history4-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'history4-texture-patches.json').read_text()))
if (ROOT/'results-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'results-texture-patches.json').read_text()))
if (ROOT/'remaining-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'remaining-texture-patches.json').read_text()))
if (ROOT/'venue-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'venue-texture-patches.json').read_text()))
if (ROOT/'october-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'october-texture-patches.json').read_text()))
if (ROOT/'interview-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'interview-texture-patches.json').read_text()))
if (ROOT/'credits-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'credits-texture-patches.json').read_text()))
if (ROOT/'alignment-texture-patches.json').exists():
 changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'alignment-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'wide-caw-texture-patches.json').read_text()))
changes.extend((167878,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'original-model-restores.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'champion-panels-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'tutorial-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'tit4-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'main-vs-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'history-weight-credit-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'tournament-texture-patches.json').read_text()))
changes.extend((317680,o,(ROOT/f).read_bytes()) for o,f in json.loads((ROOT/'vmu-port-texture-patches.json').read_text()))
for name in ['track01.bin','track02.raw','track03.bin','Giant Gram 2000.gdi']:
 target=OUT/name
 if not target.exists():shutil.copyfile(GAME.parent/name,target)
# Later revisions replace earlier versions of the same texture block.
changes=[(extent,offset,data) for (extent,offset),data in {(e,o):d for e,o,d in changes}.items()]
sectors={}
with (OUT/'track03.bin').open('r+b') as f:
 for extent,offset,data in changes:
  while data:
   sector=(extent-45000)+offset//2048;inside=offset%2048;n=min(len(data),2048-inside)
   if sector not in sectors:f.seek(sector*2352);sectors[sector]=bytearray(f.read(2352))
   sectors[sector][16+inside:16+inside+n]=data[:n];offset+=n;data=data[n:]
 for index,sector in sectors.items():f.seek(index*2352);f.write(checksums(sector))
 # Verify every patched byte from the completed disc.
 for extent,offset,data in changes:
  read=bytearray();remaining=len(data)
  while remaining:
   inside=offset%2048;n=min(remaining,2048-inside)
   f.seek(((extent-45000)+offset//2048)*2352+16+inside);read+=f.read(n);remaining-=n;offset+=n
  assert read==data
(ROOT/'verified-program.bin').write_bytes(program)
print('Verified patched sectors:',len(sectors),flush=True)
print('Disc:',OUT/'Giant Gram 2000.gdi',flush=True)
