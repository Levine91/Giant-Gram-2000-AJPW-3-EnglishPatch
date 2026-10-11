"""Translate History matches 5-12 with the established single-letter font."""
from pathlib import Path
import json, shutil, struct, textwrap
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parent; G=R.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
backup=R/'before-history-remaining'; backup.mkdir(exist_ok=True)
for name,path in [('1ST_READ.BIN',G/'1ST_READ.BIN'),('moves-font.bin',R/'moves-font.bin')]:
    if not (backup/name).exists(): shutil.copy2(path,backup/name)
b=(backup/'1ST_READ.BIN').read_bytes()
font=bytearray((backup/'moves-font.bin').read_bytes()); before=bytes(font)
paragraphs=[
["Misawa had a serious left shoulder injury. With Tsuruta also sidelined, he had no choice but to compete on the tour.",
 "Under these circumstances, he challenged for the Triple Crown. His injured shoulder became the focus of a relentless attack.",
 "Enduring excruciating pain, Misawa summoned his last reserves and delivered an elbow with all his might. At last, he stood at the pinnacle of All Japan."],
["A third straight World's Strongest Tag League victory was at stake. The final brought together the Four Pillars with an unprecedented record on the line.",
 "Misawa and Kobashi had lost the World Tag Team titles to Kawada and Taue, then lost to them again in league competition. In this match, they avenged those defeats and achieved their historic third consecutive tournament victory."],
["After losing to Kawada at the previous year's Dome show, Misawa named him as his Triple Crown challenger, seeking to settle the score.",
 "During the match, Kawada injured his right arm throwing a backfist. As he drove Misawa into the mat, he heard his own arm break.",
 "His determination to win brought him the championship, but the price was far too high."],
["The Tokyo Dome hosted a show commemorating Giant Baba's \"retirement.\" But it was Vader who held the Triple Crown.",
 "Determined to repay his mentor, Misawa could not afford to lose. Through sheer resolve, he reclaimed all three belts.",
 "With the titles in his hands, Misawa pledged to Baba that he would carry All Japan into the future."],
["The new All Japan tried a fresh approach: five major singles matches, with fans voting to decide the match order. The main event chosen was Akiyama versus Omori, who had debuted in the same year.",
 "The bout signaled a new era following the reign of the Four Pillars. Afterward, the two made a promise:",
 "\"One more time, right here.\""],
["Omori and Takayama, known as No Fear, were All Japan's breakout stars of 1999.",
 "They forced their way into a World Tag Team title match and kept provoking Kobashi and Akiyama outside the ring. The champions would not take it quietly.",
 "The match began in an atmosphere of hostility. And Kobashi was clearly not his usual self..."],
["Kobashi challenged Vader to usher in a new era. Akiyama had promised to face Kobashi for the Triple Crown, but first he had to overcome Misawa.",
 "Just as Misawa had once challenged Jumbo Tsuruta, the day had come for Akiyama to challenge Misawa.",
 "After a fierce exchange of move after move, Akiyama finally surpassed his great rival."],
["Kobashi had failed to beat Vader in their three previous singles meetings. Stripped of the World Tag Team titles and injured in the ribs, he challenged Vader with his back against the wall.",
 "He had kept growing his beard, vowing not to shave until he won. He could not afford another defeat!",
 "The time had come for Kobashi's new era to begin."]
]
stories=[[line for p in ps for line in textwrap.wrap(p,63)] for ps in paragraphs]
assert len(stories)==8 and all(len(s)<=8 and max(map(len,s))<=63 for s in stories), [len(s) for s in stories]
report=read(R/'history4-report.json'); mapping=report['alphabet'].copy()
cells={}
for name in ['history-story-report.json','history-match3-report.json']:
    cells.update({v['index']:v['code'] for v in read(R/name)['glyphs'].values()})
cells.update({v['index']:v['code'] for k,v in read(R/'catchphrase-update-report.json')['new_glyphs'].items() if k.startswith('story:')})
free=iter((i,c) for i,c in sorted(cells.items()) if c not in mapping.values())
face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',18)
changed=set()
for ch in sorted(set(''.join(''.join(s) for s in stories))-mapping.keys()):
    index,code=next(free)
    ink=Image.new('L',(11,24)); ImageDraw.Draw(ink).text((0,1),ch,font=face,fill=255)
    letter=ink.resize((6,24),Image.Resampling.LANCZOS).point(lambda p:255 if p>=100 else 0).convert('1')
    cell=Image.new('1',(24,24)); cell.paste(letter,(0,0))
    font[index*72:(index+1)*72]=cell.tobytes(); mapping[ch]=code; changed.add(index)
assert all(font[i:i+72]==before[i:i+72] for i in range(0,len(font),72) if i//72 not in changed)
# Reuse the now-obsolete Japanese descriptions and unused translation pools.
pools=[[0xf0998,0xf1200],[0x11dd68,0x11ea01],[0x104cf6,0x105c00]]
assert not any(b[0xf0998:0xf1200]) and not any(b[0x104cf6:0x105c00])
program=bytearray(b); starts=[]; reverse={bytes.fromhex(v):k for k,v in mapping.items()}
for lines in stories:
    data=b'\0'.join(b''.join(bytes.fromhex(mapping[c]) for c in line) for line in lines)+b'\0\0'
    assert [''.join(reverse[line[i:i+2]] for i in range(0,len(line),2)) for line in data[:-2].split(b'\0')]==lines
    pool=next(p for p in pools if p[1]-p[0]>=len(data))
    start=pool[0]; program[start:start+len(data)]=data; pool[0]+=len(data)+(len(data)%2)
    starts.append(start+0x8c010000)
patches=[[lo,program[lo:hi].hex()] for lo,hi in [(0xf0000,0xf1200),(0x11dd68,0x11ea01),(0x104a00,0x105c00)]]
patches += [[0x11f4c4+4*(i+4),struct.pack('<I',ptr).hex()] for i,ptr in enumerate(starts)]
# All twelve descriptions now use the already-tested English line renderer.
hook=bytearray(b[0xf1288:0xf12c8])
hook[:12]=struct.pack('<4HI',0xd001,0x402b,0x0009,0x0009,0x8c114900)
patches.append([0xf1288,hook.hex()])
(R/'history-remaining-program-patches.json').write_text(json.dumps(patches),encoding='utf-8')
(R/'moves-font.bin').write_bytes(font)
(R/'history-remaining-report.json').write_text(json.dumps({'paragraphs':paragraphs,'stories':stories,'starts':starts,'alphabet':mapping},indent=2),encoding='utf-8')
# Preview actual packed font cells at the renderer's seven-pixel advance.
def glyph_index(code):
    return next(i for i,c in cells.items() if c==code)
for n,lines in enumerate(stories,5):
    im=Image.new('RGB',(480,200),(45,45,28))
    for y,line in enumerate(lines):
        for x,ch in enumerate(line):
            i=glyph_index(mapping[ch])
            cell=Image.frombytes('1',(24,24),bytes(font[i*72:(i+1)*72]))
            im.paste('white',(12+x*7,y*21),cell)
    im.resize((960,400)).save(R/f'history-{n:02}-translated.png')
print('Eight descriptions encoded and round-trip verified; line counts:',[len(s) for s in stories])
