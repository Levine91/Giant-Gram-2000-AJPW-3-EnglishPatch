"""Remove original Japanese glyph overhangs above all 36 controller labels."""
import hashlib
import json
import struct
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT,SIZE,decode,spread
from patch_english_menu import encode
from patch_options import adapt_codebook

base=(ROOT/'English_Options/TEX/spr_tit.bin').read_bytes()
sprite=bytearray(base)
for tile in range(24,30):
    block=base[tile*SIZE:(tile+1)*SIZE]
    old=decode(block,'565');target=old.copy()
    touched=np.zeros((128,128),dtype=bool)
    rows=[8,32,68,92,116,140] if tile<27 else [8,32,56,92,116,140]
    for y in rows:
        target.paste((0,0,24,255),(162,y-4,200,y))
        touched[128-y//2:128-(y-4)//2,81:100]=True
    adapted=adapt_codebook(target,block,touched,'565')
    encoded=encode(target,adapted,'565');clean=bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        pos=2048+spread(int(y))+(spread(int(x))<<1)
        clean[pos]=encoded[pos]
    final=decode(clean,'565')
    outside=~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
    assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
    for y in rows:
        assert np.asarray(final.crop((162,y-4,200,y)))[:,:,:3].max()<=64,(tile,y)
    sprite[tile*SIZE:(tile+1)*SIZE]=clean
    final.save(ROOT/f'English_Options/tile_{tile}_english.png')
for folder in ['English_Options','English_Pause']:
    out=ROOT/folder
    before=(out/'TEX.AFS').read_bytes();after=bytearray(before)
    off,size=struct.unpack_from('<II',before,8+3*8)
    assert before[off:off+size]==base
    after[off:off+size]=sprite
    assert after[:off+24*SIZE]==before[:off+24*SIZE]
    assert after[off+30*SIZE:]==before[off+30*SIZE:]
    assert len(after)==len(before)
    (out/'TEX.AFS').write_bytes(after)
    (out/'TEX/spr_tit.bin').write_bytes(sprite)
    report=json.loads((out/'verification.json').read_text())
    report['sha256']=hashlib.sha256(after).hexdigest()
    report['glyph_cleanup']={'controller_labels':36,'cleared_top_margin_pixels':4,
        'no_bright_pixels_in_cleared_strips':True,'all_pixels_outside_cleanup_strips_unchanged':True}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'README.txt').open('a',encoding='utf-8') as f:
        f.write('\nGlyph cleanup: removed original Japanese overhangs above all 36 controller\n'
                'labels. Cleared strips checked for bright remnants; connector lines,\n'
                'English labels, icons and every other decoded pixel preserved.\n')
sheet=Image.new('RGB',(768,512),'black')
for i,tile in enumerate(range(24,30)):
    im=decode(sprite[tile*SIZE:(tile+1)*SIZE],'565').convert('RGB')
    sheet.paste(im,(i%3*256,i//3*256))
sheet.resize((1536,1024),Image.Resampling.NEAREST).save(ROOT/'English_Pause/controllers_run_preview.png')
tiles=[22,23,24,25,26,27,28,29,35,36,37]
sheet=Image.new('RGB',(768,1120),(35,35,35));d=ImageDraw.Draw(sheet)
for i,tile in enumerate(tiles):
    im=Image.open(ROOT/f'English_Options/tile_{tile}_english.png')
    bg=Image.new('RGBA',im.size,'black');bg.alpha_composite(im)
    x,y=i%3*256,i//3*280;sheet.paste(bg,(x,y));d.text((x+4,y+258),f'Texture {tile}',fill='white')
sheet.resize((1536,2240),Image.Resampling.NEAREST).save(ROOT/'English_Options/options_preview.png')
print('All 36 label margins cleared; no bright remnants; all other pixels unchanged.')
