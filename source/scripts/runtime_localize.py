"""Localize existing two-byte text using unused font cells, without code hooks."""
import json,re,struct,unicodedata,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from extract_main_menu import ROOT
from patch_expanded import RUNTIME_NAMES

OUT=ROOT/'English_Runtime_Fixed'
OUT.mkdir(exist_ok=True)
ORIGINAL=(ROOT/'1ST_READ.BIN').read_bytes()
TERMS={}
for file in ['move_terms.txt','runtime_extra.txt']:
    p=Path(__file__).with_name(file)
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#'):
                a,b=line.split('=',1);TERMS[a]=b.strip()
ORDER=sorted(TERMS,key=len,reverse=True)

def translate(s):
    if s=='ショップに新しいコスチュームが\n追加されました！':return 'New costumes added\nto the shop!'
    if s=='合成結果と同じコマンドの技をすでに\n覚えているので、この組み合わせでは\n合成できません。':return 'Cannot fuse these moves.\nYou already know a move\nwith the resulting command.'
    if s.startswith('〔掴み状態でタッチ中'):return 'Choose a move for tagging\nwhile gripping (\x07Β\r).'
    if s.startswith('〔敵ダウン時タッチ中'):return 'Choose a move for tagging\nwhile the opponent is down (\x07Β\r).'
    out=[];i=0
    while i<len(s):
        term=next((t for t in ORDER if s.startswith(t,i)),None)
        if term:out.append(' '+TERMS[term]+' ');i+=len(term)
        else:out.append(unicodedata.normalize('NFKC',s[i]));i+=1
    result=''.join(out)
    # ASCII runs in the original (DDT, model codes, numbers) remain contiguous.
    result=re.sub(r' *([+&()/]) *',r'\1',result)
    result=re.sub(r' +([.,!?])',r'\1',result)
    result=re.sub(r' +', ' ',result).strip(' ')
    return result

def rows(lo,hi):
    for m in re.finditer(rb'[^\x00]+',ORIGINAL[lo:hi]):
        raw=m.group()
        try:s=raw.decode('cp932')
        except UnicodeDecodeError:continue
        if s and all(ord(c)>=32 or c in '\r\n\t\x07\x08' for c in s):
            yield lo+m.start(),raw,s

def catalog():
    out=[]
    for lo,hi,kind in [(0x100390,0x105c78,'move'),(0xf160c,0xf261c,'command'),(0x125df0,0x126831,'hint'),(0xf261c,0xf2f28,'costume')]:
        for offset,raw,s in rows(lo,hi):
            if not any('\u3040'<=c<='\u9fff' or '\uff01'<=c<='\uff5e' for c in s):continue
            en=translate(s)
            out.append({'offset':offset,'jp':s,'en':en,'kind':kind,'capacity':len(raw)})
    for offset in [0xec9b4,0xecc7c,0xeccac,0xecccc,0xeccf0,0xecd10,0xedbe0,0xedc04,0xedc2c,0xedc5c,0xedc8c,0xedcc0,0xedcf4,0xedd20,0xedd44,0xedd6c,0xedd94,0xeddbc,0xedddc,0xeddfc,0xede20,0xede78,0xedec4]:
        raw=ORIGINAL[offset:ORIGINAL.index(0,offset)];s=raw.decode('cp932')
        out.append({'offset':offset,'jp':s,'en':translate(s),'kind':'caw_prompt','capacity':len(raw)})
    return out

def runs(s):
    return re.findall(r'[ -~]+|[^ -~]',s)

def encoded_length(s):
    return sum(((len(r)+1)//2)*2 if r.isascii() and ord(r[0])>=32 else len(r.encode('cp932')) for r in runs(s))

def code(index):
    row=index//96+33;col=index%96+32
    if not 33<=col<=126:return None
    lead=(row-33)//2+0x81;trail=col+(31 if row%2 else 126)
    if row%2 and trail>=127:trail+=1
    return bytes([lead,trail])

def glyph_index(c):
    a,b=c
    row=(a-0x81)*2+0x21
    if b>=0x9f:row+=1;col=b-0x7e
    else:col=b-(0x20 if b>=0x80 else 0x1f)
    return (row-0x21)*96+col-0x20

def build():
    items=catalog()
    assert not any(re.search('[\u3041-\u309f\u30a1-\u30fa\u3400-\u9fff]',r['en']) for r in items)
    for i,name in enumerate(RUNTIME_NAMES):
        items.append({'offset':0x1209e0+i*26,'jp':ORIGINAL[0x1209e0+i*26:0x1209e0+(i+1)*26].split(b'\0')[0].decode('cp932'),'en':name,'kind':'name','capacity':25})
    font_original=(ROOT/'TEX/zi.bin').read_bytes();font=bytearray(font_original)
    pairs=sorted({r[i:i+2].ljust(2) for item in items for r in runs(item['en']) if r.isascii() and ord(r[0])>=32 for i in range(0,len(r),2)})
    free=[i for i in range(600,len(font)//72) if code(i) and code(i) not in ORIGINAL]
    # No original executable/data string contains any of these two-byte codes.
    # Preserve the font's size, lookup formula, and every other bitmap.
    free.sort(key=lambda i:(any(font_original[i*72:(i+1)*72]),i))
    assert len(pairs)<=len(free),(len(pairs),len(free))
    pair_codes={p:code(i) for p,i in zip(pairs,free)}
    latin={}
    for ch in set(''.join(pairs)):
        if ch==' ':latin[ch]=Image.new('L',(12,24));continue
        full={'\"':'”',"'":'’'}.get(ch,chr(ord(ch)+0xfee0))
        try:c=full.encode('cp932')
        except UnicodeEncodeError:
            c={'-':'－','~':'～','"':'”',"'":'’','\\':'＼'}.get(ch,full).encode('cp932')
        index=glyph_index(c)
        glyph=np.unpackbits(np.frombuffer(font_original[index*72:(index+1)*72],dtype='uint8')).reshape(24,24)*255
        src=Image.fromarray(glyph);box=src.getbbox();assert box,ch
        src=src.crop((box[0],0,box[2],24))
        if src.width>10:src=src.resize((10,24),Image.Resampling.BOX)
        src=src.point(lambda v:255 if v>=96 else 0)
        latin[ch]=Image.new('L',(12,24));latin[ch].paste(src,((12-src.width)//2,0))
    for pair,index in zip(pairs,free):
        glyph=Image.new('L',(24,24));glyph.paste(latin[pair[0]],(0,0));glyph.paste(latin[pair[1]],(12,0))
        font[index*72:(index+1)*72]=np.packbits(np.asarray(glyph)>0).tobytes()
        assert glyph_index(pair_codes[pair])==index
    def pack(s):
        result=bytearray()
        for r in runs(s):
            if r.isascii() and ord(r[0])>=32:
                for i in range(0,len(r),2):result+=pair_codes[r[i:i+2].ljust(2)]
            else:result+=r.encode('cp932')
        return bytes(result)
    baseline=(ROOT/'English_Expanded/1ST_READ.BIN').read_bytes();program=bytearray(baseline)
    allowed=np.zeros(len(program),dtype=bool);pointers={};spare=[];pending=[]
    words=np.frombuffer(ORIGINAL[:len(ORIGINAL)//4*4],dtype='<u4')
    # Keep strings at their original addresses when they fit. Larger strings
    # use only freed tails of translated strings, with all pointers redirected.
    for item in items:
        off=item['offset'];cap=item['capacity'];encoded=pack(item['en'])
        item['bytes']=len(encoded);item['refs']=(np.flatnonzero(words==0x8c010000+off)*4).tolist()
        interior=words[(words>0x8c010000+off)&(words<=0x8c010000+off+cap)]
        assert not len(interior),(hex(off),'interior pointer',interior.tolist())
        allowed[off:off+cap+1]=True
        if item['kind']=='name' or not item['refs']:
            assert len(encoded)<=cap,item
            program[off:off+cap+1]=encoded+b'\0'*(cap+1-len(encoded))
            item['new_offset']=off
            if item['kind']!='name' and cap-len(encoded)>=4:spare.append([off+len(encoded)+1,off+cap+1])
        else:
            assert item['refs'],item
            end=off+cap+1
            while end%4 and end<len(ORIGINAL) and ORIGINAL[end]==0:end+=1
            allowed[off:end]=True
            program[off:end]=b'\0'*(end-off);spare.append([off,end]);pending.append((item,encoded))
    # Coalesce only immediately adjacent vacated bytes.
    spaces=[]
    for lo,hi in sorted(spare):
        if spaces and lo==spaces[-1][1]:spaces[-1][1]=hi
        else:spaces.append([lo,hi])
    for item,encoded in sorted(pending,key=lambda p:len(p[1]),reverse=True):
        need=len(encoded)+1
        fits=[(hi-lo,j) for j,(lo,hi) in enumerate(spaces) if hi-lo>=need]
        assert fits,('No reclaimed space',item)
        _,j=min(fits);off=spaces[j][0];spaces[j][0]+=need
        program[off:off+need]=encoded+b'\0';item['new_offset']=off
        for pos in item['refs']:
            assert not allowed[pos:pos+4].any(),('pointer overlaps string',pos)
            allowed[pos:pos+4]=True;struct.pack_into('<I',program,pos,off+0x8c010000)
    for item in items:
        off=item['new_offset'];expected=pack(item['en'])
        assert program[off:off+len(expected)+1]==expected+b'\0'
        for pos in item['refs']:
            # Name pointers in the cumulative baseline deliberately point into
            # the fixed name table, whose slots remain at their original offsets.
            assert struct.unpack_from('<I',program,pos)[0]==off+0x8c010000
    changed=np.frombuffer(baseline,dtype='uint8')!=np.frombuffer(program,dtype='uint8')
    assert not np.any(changed&~allowed)
    archive=bytearray((ROOT/'English_Expanded/TEX.AFS').read_bytes())
    entries=[struct.unpack_from('<II',archive,8+i*8) for i in range(struct.unpack_from('<I',archive,4)[0])]
    entry=next(off for off,n in entries if n==len(font_original) and archive[off:off+n]==font_original)
    archive[entry:entry+len(font)]=font
    shutil.copytree(ROOT/'English_Expanded/TEX',OUT/'TEX',dirs_exist_ok=True)
    (OUT/'TEX/zi.bin').write_bytes(font);(OUT/'TEX.AFS').write_bytes(archive);(OUT/'1ST_READ.BIN').write_bytes(program)
    report={'labels':items,'font_pairs':{p:c.hex() for p,c in pair_codes.items()},'font_indices':free[:len(pairs)],'font_offset':entry,'program_changed_bytes':int(changed.sum()),'font_size_unchanged':True,'program_size_unchanged':True,'code_instructions_unchanged':True,'in_game_tested':False}
    (OUT/'runtime_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    samples=RUNTIME_NAMES+['Back Drop','Rear','Jumping Knee Strike','Double Brainbuster','Throat Slash','Arms Out Taunt','Front Kick','Rear Grip','Vader Hammer','Golden Left','Figure-4 Leglock']
    preview=Image.new('RGB',(768,((len(samples)+1)//2)*38),'#182638');d=ImageDraw.Draw(preview)
    for n,s in enumerate(samples):
        encoded=pack(s);x=(n%2)*384+8;y=(n//2)*38+4
        for j in range(0,len(encoded),2):
            k=glyph_index(encoded[j:j+2]);a=np.unpackbits(np.frombuffer(font[k*72:(k+1)*72],dtype='uint8')).reshape(24,24)*255
            glyph=Image.fromarray(a);preview.paste('white',(x+j//2*24,y),glyph)
    preview.save(OUT/'runtime_names_preview.png')
    print('Built',len(items),'labels,',len(pairs),'font pairs;',len(pending),'strings relocated into reclaimed text space.')

if __name__=='__main__':
    import sys
    if '--build' in sys.argv:build();sys.exit()
    items=catalog()
    (OUT/'catalog.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
    missing=[r for r in items if re.search('[\u3040-\u9fff]',r['en'])]
    print('Catalog',len(items),'untranslated',len(missing))
    for r in missing:print(hex(r['offset']),r['jp'],'=>',r['en'])
