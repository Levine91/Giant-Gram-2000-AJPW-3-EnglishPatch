"""Translate the twelve alternate-perspective Historic Match descriptions."""
from pathlib import Path
import json, shutil, struct, textwrap
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parent; G=R.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
backup=R/'before-history-13-24'; backup.mkdir(exist_ok=True)
for name,path in [('1ST_READ.BIN',G/'1ST_READ.BIN'),('moves-font.bin',R/'moves-font.bin')]:
    if not (backup/name).exists(): shutil.copy2(path,backup/name)
b=(backup/'1ST_READ.BIN').read_bytes()
font=bytearray((backup/'moves-font.bin').read_bytes()); before=bytes(font)
paragraphs=[
["Armed with his neck-breaking Western Lariat, Stan Hansen suddenly arrived in All Japan. His first title opponent was the world-famous Giant Baba.",
 "Baba may have been past his prime, but his devastating 16-Mon Kick could not be ignored. Defeat the champion and take his belt!"],
["The Unsinkable Battleship, Stan Hansen, and the Beast, Bruiser Brody: the strongest foreign tag team challenged Baba and Tsuruta for the International Tag Team titles.",
 "This was also the match in which Hansen and Brody unleashed their devastating double-team move."],
["Tsuruta held the International Heavyweight title; Hansen held the PWF and UN Heavyweight titles. These three prestigious belts had produced countless classic matches. Now the day had come to unite them.",
 "Who would become the first Triple Crown Heavyweight Champion, the mark of a true champion?"],
["The wrestler exodus was an inescapable chapter in All Japan's history. It also deeply shocked those who stayed.",
 "With the promotion's survival at stake, Tsuruta had to carry it forward as its ace. In that role, he accepted Misawa's challenge."],
["Three years after losing the unification match to Tsuruta, Hansen once again held the Triple Crown. He had won all nine matches in that year's Champion Carnival.",
 "His challenger was an injured Misawa. But anyone who showed mercy had no right to wear those belts. Hansen attacked Misawa's left shoulder relentlessly."],
["Misawa and Kobashi of the Super Generation Army faced Kawada and Taue of the Holy Demon Army. The Four Pillars had clashed many times, producing classic after classic.",
 "With Misawa and Kobashi chasing a third straight World's Strongest Tag League victory, Kawada and Taue stood in their way, determined to stop them at any cost."],
["Mitsuharu Misawa and Toshiaki Kawada had been rivals since before they joined All Japan, a fact everyone recognized.",
 "Misawa himself named Kawada as his Triple Crown challenger. Of all the matches they had fought, this became one of their most brutal encounters."],
["This Triple Crown match headlined the show commemorating the \"retirement\" of the great world champion, Giant Baba.",
 "The heir to King's Road faced the holder of the Triple Crown. Now their pride and determination would collide."],
["In a new experiment, fans voted to decide the order of five major singles matches. The chosen main event featured none of the Four Pillars.",
 "Omori and Akiyama had joined All Japan in the same year. Their rivalry was sure to become a marquee attraction in years to come. This match was its opening chapter."],
["No Fear were making headlines inside and outside the ring. Their endless taunts finally pushed Kobashi past his limit.",
 "Defeating Burning, said to be All Japan's strongest team, would make No Fear number one. Their greatest opportunity had arrived."],
["Misawa once challenged the formidable Tsuruta to build a new era. Now another new era was approaching, but Misawa would not let the next generation take over so easily.",
 "Seeing his younger self in Akiyama, Misawa stepped into the ring."],
["Holding both the Triple Crown and World Tag Team titles, Vader dominated All Japan's championships. His challenger was Kobashi, whose ribs had been injured in their World Tag Team match.",
 "Vader tore away Kobashi's protective tape and struck without mercy. Kobashi's cries of agony echoed through the arena."]
]
stories=[[line for p in ps for line in textwrap.wrap(p,63)] for ps in paragraphs]
assert len(stories)==12 and all(len(s)<=8 and max(map(len,s))<=63 for s in stories)
prior=read(R/'history-remaining-report.json'); mapping=prior['alphabet'].copy()
cells={}
for name in ['history-story-report.json','history-match3-report.json']:
    cells.update({v['index']:v['code'] for v in read(R/name)['glyphs'].values()})
cells.update({v['index']:v['code'] for k,v in read(R/'catchphrase-update-report.json')['new_glyphs'].items() if k.startswith('story:')})
free=iter((i,c) for i,c in sorted(cells.items()) if c not in mapping.values())
face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',18); changed=set()
for ch in sorted(set(''.join(''.join(s) for s in stories))-mapping.keys()):
    index,code=next(free)
    ink=Image.new('L',(11,24)); ImageDraw.Draw(ink).text((0,1),ch,font=face,fill=255)
    letter=ink.resize((6,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1')
    cell=Image.new('1',(24,24));cell.paste(letter,(0,0))
    font[index*72:(index+1)*72]=cell.tobytes();mapping[ch]=code;changed.add(index)
assert all(font[i:i+72]==before[i:i+72] for i in range(0,len(font),72) if i//72 not in changed)
def encode(lines):
    return b'\0'.join(b''.join(bytes.fromhex(mapping[c]) for c in line) for line in lines)+b'\0\0'
ends=[ptr-0x8c010000+len(encode(lines)) for ptr,lines in zip(prior['starts'],prior['stories']) if 0x11dd68<=ptr-0x8c010000<0x11ea01]
reclaimed=(max(ends)+1)&~1
pools=[[0xf0fa0,0xf1200],[0x10522a,0x105c00],[reclaimed,0x11f4c4],[0x10f4a6,0x10f8ec],[0x10b9d4,0x10bc20]]
for lo,hi in pools:
    if lo!=reclaimed: assert not any(b[lo:hi]),hex(lo)
program=bytearray(b);starts=[None]*12
encoded=[encode(s) for s in stories]
for index in sorted(range(12),key=lambda i:len(encoded[i]),reverse=True):
    data=encoded[index]
    fitting=[p for p in pools if p[1]-p[0]>=len(data)]
    assert fitting, ('Insufficient reserved text space',index,[p[1]-p[0] for p in pools])
    pool=min(fitting,key=lambda p:p[1]-p[0])
    start=pool[0];program[start:start+len(data)]=data;pool[0]+=len(data)+(len(data)%2)
    starts[index]=start+0x8c010000
patches=[[lo,program[lo:hi].hex()] for lo,hi in [(0xf0000,0xf1200),(0x104a00,0x105c00),(0x11dd68,0x11f4c4),(0x10f4a6,0x10f8ec),(0x10b9d4,0x10bc20)]]
patches += [[0x11f4c4+4*(i+12),struct.pack('<I',ptr).hex()] for i,ptr in enumerate(starts)]
reverse={bytes.fromhex(v):k for k,v in mapping.items()}
for data,lines in zip(encoded,stories):
    assert [''.join(reverse[line[i:i+2]] for i in range(0,len(line),2)) for line in data[:-2].split(b'\0')]==lines
(R/'history-13-24-program-patches.json').write_text(json.dumps(patches),encoding='utf-8')
(R/'moves-font.bin').write_bytes(font)
(R/'history-13-24-report.json').write_text(json.dumps({'paragraphs':paragraphs,'stories':stories,'starts':starts,'alphabet':mapping},indent=2),encoding='utf-8')
indexes={code:i for i,code in cells.items()}
sheet=Image.new('RGB',(960,1320),(0,0,0));draw=ImageDraw.Draw(sheet)
for j,lines in enumerate(stories):
    im=Image.new('RGB',(480,200),(45,45,28))
    for y,line in enumerate(lines):
        for x,ch in enumerate(line):
            i=indexes[mapping[ch]]
            cell=Image.frombytes('1',(24,24),bytes(font[i*72:(i+1)*72]))
            im.paste('white',(12+x*7,y*21),cell)
    im.resize((960,400)).save(R/f'history-{j+13:02}-translated.png')
    x=j%2*480;y=j//2*220;sheet.paste(im,(x,y+20));draw.text((x+8,y+3),f'Match {j+13}',fill='white')
sheet.save(R/'history-13-24-review.png')
print('Verified 12 translations; line counts:',[len(s) for s in stories],'; new font cells:',len(changed))
