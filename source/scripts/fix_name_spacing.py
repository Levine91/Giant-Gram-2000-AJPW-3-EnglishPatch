from pathlib import Path
import struct
from PIL import Image,ImageFont,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
NAMES='Random|Giant Baba|Mitsuharu Misawa|Toshiaki Kawada|Akira Taue|Kenta Kobashi|Jun Akiyama|Stan Hansen|Vader|Gary Albright|Johnny Ace|Hiroshi Hase|Wolf Hawkfield|Grace|Hyper|Diablo|Kyohei Wada|Wolf Hawkfield|Jeffry McWild|Kage-Maru|Tiger|Takao Omori|Yoshihiro Takayama|Mike Barton|Yoshinari Ogawa|Tamon Honda|Masahito Kakihara|Kentaro Shiga|Johnny Smith|Maunakea Mossman|Jumbo Tsuruta|Ogami Kongo|Sky High Edge|Super Tigre Dos Mil|Young Giant Baba|The Master A.M.|Mangler D.H.|Cyclops E.C.|The Killer B.I.|Rikidozan|Steve Williams|Bruno Sammartino|Gene Kiniski|Don Leo Jonathan|Giant Crusher|Bruiser Brody|The Crusher|The Destroyer|Dick the Bruiser|Crusher Lisowski|Fritz Von Erich|Bobo Brazil|Dynamite Kid'.split('|')
def index(code):
 a,b=code
 return ((a-129)*2+(b>=159))*96+b-(126 if b>=159 else 32 if b>=128 else 31)-32

def main():
 program=(ROOT/'1ST_READ.BIN').read_bytes()
 archive=bytearray((ROOT/'TEX.AFS').read_bytes())
 off,size=struct.unpack_from('<II',archive,8)
 font=bytearray(archive[off:off+size]); before=bytes(font)
 pairs={}
 for k,name in enumerate(NAMES):
  encoded=program[0x1209e0+k*26:0x1209e0+(k+1)*26].split(b'\0')[0]
  padded=name+' '*(len(name)%2)
  assert len(encoded)==len(padded),(k,name,encoded.hex())
  for j in range(0,len(encoded),2):
   code=encoded[j:j+2];pair=padded[j:j+2]
   assert code not in pairs or pairs[code]==pair,(code,pair,pairs.get(code))
   pairs[code]=pair
 face=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',24)
 letters={}
 for c in set(''.join(pairs.values())):
  im=Image.new('L',(16,24));ImageDraw.Draw(im).text((0,-3),c,font=face,fill=255)
  # One shared horizontal scale preserves letter proportions, including narrow i/l.
  im=im.resize((10,24),Image.Resampling.LANCZOS).point(lambda v:255 if v>=100 else 0).convert('1')
  cell=Image.new('1',(12,24));cell.paste(im,(1,0));letters[c]=cell
 for code,pair in pairs.items():
  im=Image.new('1',(24,24));im.paste(letters[pair[0]],(0,0));im.paste(letters[pair[1]],(12,0))
  at=index(code)*72;assert 0<=at<=len(font)-72
  font[at:at+72]=im.tobytes()
 # Verify cell edges stay empty so adjacent glyphs cannot overlap.
 for code in pairs:
  at=index(code)*72;im=Image.frombytes('1',(24,24),bytes(font[at:at+72]))
  assert not im.crop((0,0,1,24)).getbbox()
  assert not im.crop((23,0,24,24)).getbbox()
 preview=Image.new('RGB',(760,220),'#181818');d=ImageDraw.Draw(preview)
 for row,k in enumerate([2,3,1,22]):
  s=program[0x1209e0+k*26:0x1209e0+(k+1)*26].split(b'\0')[0]
  line=Image.new('1',(len(s)*12,24))
  for j in range(0,len(s),2):
   at=index(s[j:j+2])*72;line.paste(Image.frombytes('1',(24,24),bytes(font[at:at+72])),(j*12,0))
  preview.paste(line.resize((line.width*2,48),Image.Resampling.NEAREST),(8,row*54))
 preview.save(ROOT/'name_spacing_preview.png')
 backup=ROOT/'Name_Spacing_Backup';backup.mkdir(exist_ok=True)
 for name,data in [('zi.bin',before),('1ST_READ.BIN',program)]:
  dest=backup/name
  if not dest.exists():dest.write_bytes(data)
 archive[off:off+size]=font
 assert len(font)==size
 (ROOT/'TEX.AFS').write_bytes(archive)
 (ROOT/'TEX/zi.bin').write_bytes(font)
 assert (ROOT/'TEX/zi.bin').read_bytes()==(ROOT/'TEX.AFS').read_bytes()[off:off+size]
 assert (ROOT/'1ST_READ.BIN').read_bytes()==program
 print(f'Updated {len(pairs)} shared name glyphs for {len(NAMES)} roster entries; font copies match, executable unchanged.')
if __name__=='__main__':main()
