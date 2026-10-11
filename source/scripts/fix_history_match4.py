"""Use a reusable History alphabet and align the History pause choices."""
from pathlib import Path
import json, struct, shutil, textwrap, sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
R=Path(__file__).resolve().parent; G=R.parent
backup=R/'before-history-match4'; backup.mkdir(exist_ok=True)
for p in [G/'1ST_READ.BIN',G/'TEX.AFS',R/'moves-font.bin',G/'English_Names_Verified/README.txt']:
 if not (backup/p.name).exists(): shutil.copy2(p,backup/p.name)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
b=(backup/'1ST_READ.BIN').read_bytes(); font=bytearray((backup/'moves-font.bin').read_bytes())
one=read(R/'history-story-report.json'); three=read(R/'history-match3-report.json')
two=read(R/'catchphrase-update-report.json')
four=['All Japan Pro Wrestling faced an unprecedented crisis as wrestlers left in droves. To save the promotion and forge a new path, Misawa challenged Tsuruta.', '"I will beat Tsuruta!"', 'Despite the crushing pressure, Misawa fought with all his strength and achieved the miracle of overcoming Tsuruta. Tears welled up in his eyes.']
stories=[one['lines'],[l for p in ['A best-of-three-falls match for the International Tag Team Championship held by Baba and Tsuruta.','It brought together the finest competitors of the era.','Although the challengers lost by disqualification, the action was fierce from start to finish.'] for l in textwrap.wrap(p,63)],three['lines'],[l for p in four for l in textwrap.wrap(p,63)]]
assert all(len(s)<=8 and max(map(len,s))<=63 for s in stories)
# Recycle only cells already dedicated to these History descriptions. This
# avoids consuming Japanese or Create-A-Wrestler character cells.
cells={v['index']:v['code'] for v in one['glyphs'].values()}
cells.update({v['index']:v['code'] for k,v in two['new_glyphs'].items() if k.startswith('story:')})
cells.update({v['index']:v['code'] for v in three['glyphs'].values()})
alphabet=sorted(set(''.join(''.join(s) for s in stories)))
assert len(alphabet)<=len(cells)
face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',18); mapping={}
for ch,(index,code) in zip(alphabet,sorted(cells.items())):
 ink=Image.new('L',(11,24));ImageDraw.Draw(ink).text((0,1),ch,font=face,fill=255)
 letter=ink.resize((6,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1')
 cell=Image.new('1',(24,24));cell.paste(letter,(0,0));font[index*72:(index+1)*72]=cell.tobytes();mapping[ch]=code
patches=[];cursor=0xf0000;starts=[]
assert not any(b[cursor:0xf1200]),'History storage must be unused'
reverse={bytes.fromhex(v):k for k,v in mapping.items()}
for lines in stories:
 data=b'\0'.join(b''.join(bytes.fromhex(mapping[c]) for c in line) for line in lines)+b'\0\0'
 assert [''.join(reverse[line[i:i+2]] for i in range(0,len(line),2)) for line in data[:-2].split(b'\0')]==lines
 starts.append(cursor+0x8c010000);patches.append([cursor,data.hex()]);cursor+=len(data)+(len(data)%2)
assert cursor<=0xf1200
pool=bytearray(0x1200)
for off,data in patches:
 raw=bytes.fromhex(data);pool[off-0xf0000:off-0xf0000+len(raw)]=raw
patches=[[0xf0000,pool.hex()]]
for i,ptr in enumerate(starts):patches.append([0x11f4c4+i*4,struct.pack('<I',ptr).hex()])
# Same existing renderer and font size, now one English character per cell.
# Four pointer checks leave all untranslated descriptions at their original pitch.
ops=[0xe718]
for j in range(4):ops += [0,0x3400,0]
ops += [0xd007,0x402b,0x0009,0xd006,0x402b,0x0009,0x0009]
for j in range(4):
 at=2+6*j;lit=40+4*j;ops[at//2]=0xd000+(lit-((at+4)&~3))//4
 at+=4;ops[at//2]=0x8900+(32-at-4)//2
code=struct.pack('<20H6I',*ops,*starts,0x8c015144,0x8c114900)
assert len(code)==64 and 0xf1288+len(code)<=0xf1300
for j in range(4):
 at=2+6*j;assert ((at+4)&~3)+(ops[at//2]&255)*4==40+4*j
 at+=4;assert at+4+(ops[at//2]&255)*2==32
patches.append([0xf1288,code.hex()])
# Render individual lines so the native 256-glyph cap stays intact, while
# preserving the established 21-pixel line spacing independently of pitch.
lineops=[0x4f22,0x2f86,0x2f96,0x2fa6,0x6843,0x6953,0x6a63,
 0x6483,0x6593,0x66a3,0xe707,0xd009,0x400b,0x0009,
 0x6084,0x2008,0x8bfc,0x6080,0x2008,0x8902,0x7a15,0xaff0,0x0009,
 0x6af6,0x69f6,0x68f6,0x4f26,0x000b,0x0009,0x0009]
assert not any(b[0x104900:0x104940])
patches.append([0x104900,struct.pack('<30HI',*lineops,0x8c015144).hex()])
(R/'history4-program-patches.json').write_text(json.dumps(patches))
(R/'moves-font.bin').write_bytes(font)
(R/'history4-report.json').write_text(json.dumps({'paragraphs':four,'stories':stories,'alphabet':mapping,'starts':starts,'storage_end':cursor},indent=2))
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
archive=(backup/'TEX.AFS').read_bytes();entry=read(R/'game-entries.json')['spr_gam5'][0];at=entry+9*SIZE
original=archive[at:at+SIZE];old=decode(original);im=old.copy();mask=np.zeros((256,256),bool)
face=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
for y,label in [(0,'Resume Match'),(200,'Match Select'),(224,'Main Menu')]:
 im.paste((0,0,0,0),(0,y,128,y+24));mask[y:y+24,:128]=True
 box=face.getbbox(label,stroke_width=1);w=box[2]-box[0];h=box[3]-box[1]
 assert w<=128 and h<=24
 # Native sprite origins differ; compensate so visible ink centers at x=320.
 center={'Resume Match':66,'Match Select':70,'Main Menu':88}[label]
 art=Image.new('RGBA',(w,h));ImageDraw.Draw(art).text((-box[0],-box[1]),label,font=face,fill=(255,221,68,255),stroke_width=1,stroke_fill='black')
 art=art.resize((round(w*.94),h),Image.Resampling.LANCZOS)
 im.alpha_composite(art,(center-art.width//2,y+(24-h)//2))
touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1];adapted=adapt_codebook(im,original,touched,'4444');packed=encode(im,adapted);out=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):
 p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=packed[p]
assert np.array_equal(np.asarray(old)[~mask],np.asarray(decode(out))[~mask])
(R/'history4-pause.bin').write_bytes(out);decode(out).save(R/'history4-pause-atlas.png')
(R/'history4-texture-patches.json').write_text(json.dumps([[at,'history4-pause.bin']]))
print('Verified four passages, reusable alphabet, and unchanged surrounding pause artwork.',len(alphabet),'letters;',len(stories[3]),'new lines.')
