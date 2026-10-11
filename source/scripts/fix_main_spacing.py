"""Restore the exact prior menu rows; replace only History and CAW lettering."""
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image
from extract_main_menu import ROOT, SIZE, OFFSET, decode, spread
from patch_options import adapt_codebook
from patch_english_menu import encode
from restore_main_style import clean
NAMES=['ARCADE','HISTORY MODE','VS','CREATE-A-WRESTLER','PRACTICE','SPECTATOR','BACKUP','OPTIONS']

OUT=ROOT/'English_Main_Menu_Final'

def main():
    base=(ROOT/'English_Menu_Corrected/TEX.AFS').read_bytes()
    source=(ROOT/'English_Menu_Corrected/TEX/spr_tit.bin').read_bytes()
    prior=(ROOT/'English_Wrestler_Names/TEX/spr_tit.bin').read_bytes()
    entries=[struct.unpack_from('<II',base,8+i*8) for i in range(struct.unpack_from('<I',base,4)[0])]
    entry=next(o for o,n in entries if n==len(source) and base[o:o+n]==source)
    original=source[OFFSET:OFFSET+SIZE]
    old=decode(original);reference=decode(prior[OFFSET:OFFSET+SIZE])
    target=old.copy();target.paste(reference.crop((0,64,256,256)),(0,64))
    records=[]
    for row,path in [(1,ROOT/'English_Menu_Corrected/history_source.png'),(3,OUT/'caw_source.png')]:
        art=clean(Image.open(path));art=art.crop(art.getbbox())
        height=20;width=min(248,round(art.width*height/art.height))
        art=art.resize((width,height),Image.Resampling.LANCZOS)
        y=66+24*row;x=(256-width)//2
        target.paste((0,0,0,0),(0,64+24*row,256,88+24*row))
        target.alpha_composite(art,(x,y))
        records.append({'text':NAMES[row],'position':[x,y],'size':[width,height]})
    # Reuse the earlier menu's codebook/index data for the six untouched labels.
    priorblock=prior[OFFSET:OFFSET+SIZE]
    touched=np.zeros((128,128),dtype=bool)
    for row in [1,3]:
        lo,hi=64+row*24,88+row*24;touched[(256-hi)//2:(256-lo)//2]=True
    adapted=adapt_codebook(target,priorblock,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
    final=decode(block)
    for row in [0,2,4,5,6,7]:
        rect=(0,64+row*24,256,88+row*24)
        assert final.crop(rect).tobytes()==reference.crop(rect).tobytes()
    assert final.crop((0,0,256,64)).tobytes()==old.crop((0,0,256,64)).tobytes()
    archive=bytearray(base);start=entry+OFFSET;archive[start:start+SIZE]=block
    assert archive[:start]==base[:start] and archive[start+SIZE:]==base[start+SIZE:]
    assert len(archive)==len(base)
    sprite=bytearray(source);sprite[OFFSET:OFFSET+SIZE]=block
    assert archive[entry:entry+len(sprite)]==sprite
    shutil.copytree(ROOT/'English_Menu_Corrected/TEX',OUT/'TEX',dirs_exist_ok=True)
    (OUT/'TEX/spr_tit.bin').write_bytes(sprite);(OUT/'TEX.AFS').write_bytes(archive)
    final.save(OUT/'main_menu.png')
    bg=Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final)
    bg.crop((0,64,256,256)).resize((768,576),Image.Resampling.NEAREST).save(OUT/'preview.png')
    report={'base':'English_Menu_Corrected/TEX.AFS','row_pitch':24,'restored_text_height':20,'six_original_menu_rows_pixel_identical':True,'only_main_menu_block_changed':True,'other_fixes_preserved':True,'in_game_tested':False,'sha256':hashlib.sha256(archive).hexdigest(),'new_labels':records}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
