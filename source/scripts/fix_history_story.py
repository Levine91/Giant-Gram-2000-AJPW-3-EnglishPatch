"""Install the user-approved first History Mode passage in its original text slot."""
from pathlib import Path
import json,textwrap
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;G=R.parent
paragraphs=['PWF Heavyweight Championship Match','Giant Baba was 44 years old when he faced Hansen. There was speculation that he had reached his physical limits, and some even considered a successful title defense hopeless.','But Baba met Hansen head-on and spectacularly defended his championship.','Named Match of the Year, this bout marked the beginning of Baba\u2019s miraculous resurgence.']
lines=[line for p in paragraphs for line in textwrap.wrap(p,63)]
assert len(lines)==8
program=(G/'1ST_READ.BIN').read_bytes();font=bytearray((R/'moves-font.bin').read_bytes());before=bytes(font)
program_codes=set(zip(program,program[1:]))
used=set(json.loads((G/'English_Runtime_Fixed/runtime_verification.json').read_text(encoding='utf-8'))['font_pairs'].values())
chunks={};face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',18);allowed=set()
prior=R/'history-story-report.json'
reuse=json.loads(prior.read_text())['glyphs'] if prior.exists() else {}
def glyph(text):
 if text in chunks:return bytes.fromhex(chunks[text])
 choices=[]
 if text in reuse:choices=[(reuse[text]['index'],bytes.fromhex(reuse[text]['code']))]
 else:
  for i in range(600,len(font)//72):
   row=i//96+33;col=i%96+32
   if not 33<=col<=126:continue
   lead=(row-33)//2+129;trail=col+(31 if row%2 else 126)
   if row%2 and trail>=127:trail+=1
   code=bytes([lead,trail])
   if tuple(code) in program_codes or code.hex() in used or i in allowed:continue
   choices=[(i,code)];break
 assert choices,'No free font cell'
 i,code=choices[0];cell=Image.new('1',(24,24))
 for j,ch in enumerate(text):
  ink=Image.new('L',(11,24));ImageDraw.Draw(ink).text((0,1),ch,font=face,fill=255)
  ink=ink.resize((6,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1');cell.paste(ink,(j*7,0))
 assert cell.crop((20,0,24,24)).getbbox() is None, 'Glyph exceeds sampled width'
 font[i*72:(i+1)*72]=cell.tobytes();allowed.add(i);chunks[text]=code.hex();reuse[text]={'index':i,'code':code.hex()};return code
encoded=b'\n'.join(b''.join(glyph(line[i:i+3].ljust(3)) for i in range(0,len(line),3)) for line in lines)+b'\0'
original=(R/'disc-original.bin').read_bytes();offset=0x11dd68;end=original.index(0,offset);capacity=end-offset+1
assert len(encoded)<=capacity,(len(encoded),capacity)
assert original[offset:end].decode('cp932').startswith('\uff30\uff37\uff26')
assert all(font[i:i+72]==before[i:i+72] for i in range(0,len(font),72) if i//72 not in allowed)
reverse={v:k for k,v in chunks.items()}
assert [''.join(reverse[line[i:i+2].hex()] for i in range(0,len(line),2)).rstrip() for line in encoded[:-1].split(b'\n')]==lines
(R/'history-story-patches.json').write_text(json.dumps([[offset,(encoded+bytes(capacity-len(encoded))).hex()]]))
(R/'moves-font.bin').write_bytes(font)
(R/'history-story-report.json').write_text(json.dumps({'paragraphs':paragraphs,'lines':lines,'glyphs':{k:reuse[k] for k in chunks},'offset':offset,'capacity':capacity,'encoded_bytes':len(encoded),'other_glyphs_unchanged':True},indent=2))
preview=Image.new('RGB',(544,276),(48,48,35))
for y,line in enumerate(lines):
 for x in range(0,len(line),3):
  key=line[x:x+3].ljust(3);i=reuse[key]['index'];im=Image.frombytes('1',(24,24),bytes(font[i*72:(i+1)*72]));preview.paste('white',(12+x//3*24,8+y*32),im)
preview.save(R/'history-story-preview.png')
print('Verified exact approved wording in 8 lines;',len(encoded),'bytes in',capacity,'byte original slot;',len(chunks),'dedicated glyphs. Other text unchanged.')
