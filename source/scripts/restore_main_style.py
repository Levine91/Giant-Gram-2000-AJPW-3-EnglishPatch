"""Restore the original English artwork and case; normalize its letter size."""
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image
from extract_main_menu import ROOT, SIZE, OFFSET, decode, spread
from patch_options import adapt_codebook
from patch_english_menu import encode
from polish_menus import sized

OUT=ROOT/'English_Menu_Corrected'
NAMES=['ARCADE','HISTORY MODE','VS','Create-A-Wrestler','PRACTICE','SPECTATOR','BACKUP','OPTIONS']

def clean(im):
    im=im.convert('RGBA');a=np.asarray(im.getchannel('A')).copy();a[a<30]=0
    im.putalpha(Image.fromarray(a));return im

def main():
    im=clean(Image.open(ROOT/'English_Menu/labels_source.png'))
    a=np.asarray(im.getchannel('A'));rs=np.flatnonzero((a>100).sum(1)>8)
    groups=np.split(rs,np.where(np.diff(rs)>4)[0]+1)
    assert len(groups)==10
    labels=[]
    for g in groups[2:]:
        art=im.crop((0,int(g[0])-2,im.width,int(g[-1])+3))
        labels.append(art.crop(art.getbbox()))
    history=clean(Image.open(OUT/'history_source.png'))
    labels[1]=history.crop(history.getbbox())
    widths=[228,228,156,156,156,156,188,188]
    cap=18
    while any(sized(a,cap)[0].width>w or sized(a,cap)[0].height>22 for a,w in zip(labels,widths)):cap-=1
    assert cap>=12
    base=(ROOT/'English_Menu_Polish/TEX.AFS').read_bytes()
    source=(ROOT/'English_Menu_Polish/TEX/spr_tit.bin').read_bytes()
    entries=[struct.unpack_from('<II',base,8+i*8) for i in range(struct.unpack_from('<I',base,4)[0])]
    entry=next(o for o,n in entries if n==len(source) and base[o:o+n]==source)
    original=source[OFFSET:OFFSET+SIZE];old=decode(original);target=old.copy()
    target.paste((0,0,0,0),(0,64,256,256))
    records=[]
    for i,(name,art) in enumerate(zip(NAMES,labels)):
        art,top=sized(art,cap)
        x=(256-art.width)//2;y=64+i*24+(24-cap)//2-top
        assert y>=64+i*24 and y+art.height<=88+i*24
        target.alpha_composite(art,(x,y))
        records.append({'text':name,'cap_height':cap,'size':art.size,'position':(x,y),'reused_original_art':i!=1})
    touched=np.zeros((128,128),dtype=bool);touched[:96]=True
    adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
    final=decode(block)
    assert final.crop((0,0,256,64)).tobytes()==old.crop((0,0,256,64)).tobytes()
    archive=bytearray(base);start=entry+OFFSET;archive[start:start+SIZE]=block
    assert archive[:start]==base[:start] and archive[start+SIZE:]==base[start+SIZE:] and len(archive)==len(base)
    sprite=bytearray(source);sprite[OFFSET:OFFSET+SIZE]=block
    assert archive[entry:entry+len(sprite)]==sprite
    shutil.copytree(ROOT/'English_Menu_Polish/TEX',OUT/'TEX',dirs_exist_ok=True)
    (OUT/'TEX/spr_tit.bin').write_bytes(sprite);(OUT/'TEX.AFS').write_bytes(archive)
    final.save(OUT/'main_menu.png')
    bg=Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final)
    bg.resize((768,768),Image.Resampling.NEAREST).save(OUT/'preview.png')
    report={'base':'English_Menu_Polish/TEX.AFS','main_menu_only_changed':True,'start_prompt_preserved':True,'archive_size_unchanged':True,'all_other_fixes_preserved':True,'in_game_tested':False,'sha256':hashlib.sha256(archive).hexdigest(),'labels':records}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Restored previous artwork and capitalization. Shared cap height: {cap}. Preservation checks passed.')

if __name__=='__main__':main()
