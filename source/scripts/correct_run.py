"""Correct only the six Move labels in the existing options and pause patches."""
import hashlib
import json
import struct
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT, SIZE, decode, spread
from patch_english_menu import encode
from patch_options import read_labels, adapt_codebook

art=read_labels(ROOT/'English_Options/run_label.png',[['Run']])['Run']
art=art.resize((round(art.width*12/art.height),12),Image.Resampling.LANCZOS)
white=Image.new('RGBA',art.size,'white');white.putalpha(art.getchannel('A'))
rows={24:68,25:116,26:140,27:32,28:140,29:8}
base=(ROOT/'English_Options/TEX/spr_tit.bin').read_bytes()
sprite=bytearray(base)
for tile,y0 in rows.items():
    original=base[tile*SIZE:(tile+1)*SIZE]
    old=decode(original,'565');target=old.copy()
    target.paste((0,0,24,255),(162,y0-4,200,y0+16))
    target.alpha_composite(white,(162,y0+2))
    touched=np.zeros((128,128),dtype=bool)
    touched[128-(y0+16)//2:128-(y0-4)//2,81:100]=True
    adapted=adapt_codebook(target,original,touched,'565')
    encoded=encode(target,adapted,'565');block=bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        pos=2048+spread(int(y))+(spread(int(x))<<1)
        block[pos]=encoded[pos]
    final=decode(block,'565')
    outside=~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
    assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
    sprite[tile*SIZE:(tile+1)*SIZE]=block
    final.save(ROOT/f'English_Options/tile_{tile}_english.png')
for folder in ['English_Options','English_Pause']:
    output=ROOT/folder
    before=(output/'TEX.AFS').read_bytes();archive=bytearray(before)
    entry,size=struct.unpack_from('<II',before,8+3*8)
    assert before[entry:entry+size]==base
    archive[entry:entry+size]=sprite
    cursor=0
    for tile in rows:
        start=entry+tile*SIZE
        assert archive[cursor:start]==before[cursor:start]
        cursor=start+SIZE
    assert archive[cursor:]==before[cursor:]
    assert len(archive)==len(before)
    (output/'TEX.AFS').write_bytes(archive)
    (output/'TEX/spr_tit.bin').write_bytes(sprite)
    report=json.loads((output/'verification.json').read_text())
    report['sha256']=hashlib.sha256(archive).hexdigest()
    report['controller_correction']={'from':'Move','to':'Run','occurrences':6,
        'all_other_decoded_pixels_unchanged':True}
    for change in report['changes']:
        for label in change['labels']:
            if label['label']=='Move':label['label']='Run'
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    readme=output/'README.txt'
    text=readme.read_text(encoding='utf-8')
    if 'Controller correction:' not in text:
        readme.write_text(text+'\nController correction: all six Move labels now read Run. All other\n'
            'decoded pixels and earlier translations are unchanged.\n',encoding='utf-8')
    print(folder,report['sha256'])
sheet=Image.new('RGB',(768,512),'black')
for i,tile in enumerate(rows):
    im=decode(sprite[tile*SIZE:(tile+1)*SIZE],'565').convert('RGB')
    sheet.paste(im,(i%3*256,i//3*256))
sheet.resize((1536,1024),Image.Resampling.NEAREST).save(ROOT/'English_Pause/controllers_run_preview.png')
# Refresh the older options overview as well, so no published preview stays stale.
tiles=[22,23,24,25,26,27,28,29,35,36,37]
sheet=Image.new('RGB',(768,1120),(35,35,35));d=ImageDraw.Draw(sheet)
for i,tile in enumerate(tiles):
    im=Image.open(ROOT/f'English_Options/tile_{tile}_english.png')
    bg=Image.new('RGBA',im.size,'black');bg.alpha_composite(im)
    x,y=i%3*256,i//3*280
    sheet.paste(bg,(x,y));d.text((x+4,y+258),f'Texture {tile}',fill='white')
sheet.resize((1536,2240),Image.Resampling.NEAREST).save(ROOT/'English_Options/options_preview.png')
