"""Translate pause textures on top of English_Options; requires NumPy/Pillow.
Usage: python patch_pause.py pause-labels.png variant-labels.png
"""
from pathlib import Path
import hashlib
import json
import shutil
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

from extract_main_menu import ROOT, SIZE, decode, spread
from patch_english_menu import encode
from patch_options import read_labels, adapt_codebook

LEFT = ['Resume Match','Wrestler Select','Style Select','Title Menu','No Change',
        'Ring Center','Near Ropes','Near Corner','Outside Ring','Ring Apron','Standing']
RIGHT = ['Face Up','Face Down','2 vs 1','1 vs 2','2 vs 2','Opponent Position',
         'Opponent State','Restore Stamina','Boost Spirit','Resume Practice','End Practice']


def main():
    labels = read_labels(sys.argv[1],[LEFT,RIGHT])
    labels.update(read_labels(sys.argv[2],[['Match Select','Match Settings','Player Select']]))
    prompts = read_labels(ROOT/'English_Options/labels_source.png')
    labels.update({name:prompts[name] for name in ['Back','Select','Confirm']})
    output = ROOT/'English_Pause'
    (output/'TEX').mkdir(parents=True,exist_ok=True)
    for src,name in [(sys.argv[1],'labels_source.png'),(sys.argv[2],'variant_labels_source.png')]:
        if Path(src).resolve() != (output/name).resolve():
            shutil.copyfile(src,output/name)
    baseline = (ROOT/'English_Options/TEX.AFS').read_bytes()
    archive = bytearray(baseline)
    changes,previews = [],[]
    for filename,tiles in [('spr_gam.bin',[9,11,12,13]),
                           ('spr_gam5.bin',[9,11,12,13]),('spr_gam2.bin',[38])]:
        source = (ROOT/'TEX'/filename).read_bytes()
        matches=[]
        for i in range(struct.unpack_from('<I',baseline,4)[0]):
            off,size=struct.unpack_from('<II',baseline,8+8*i)
            if size==len(source) and baseline[off:off+size]==source:
                matches.append(off)
        if len(matches)!=1:
            raise ValueError(f'Expected one matching archive entry for {filename}')
        entry=matches[0]
        edited=bytearray(source)
        for tile in tiles:
            original=source[tile*SIZE:(tile+1)*SIZE]
            old=decode(original)
            target=old.copy()
            mask=Image.new('1',(256,256));md=ImageDraw.Draw(mask)
            records=[]

            def put(rect,name,yellow=True,height=18):
                x0,y0,x1,y1=rect
                box=old.crop(rect).getbbox()
                if box is None:
                    raise ValueError(f'Empty label: {filename} tile {tile} {name}')
                bx,by,ex,ey=box
                h=min(height,ey-by)
                art=labels[name]
                w=min(ex-bx,max(1,round(art.width*h/art.height)))
                art=art.resize((w,h),Image.Resampling.LANCZOS)
                tint=Image.new('RGBA',art.size,(255,255,0,255) if yellow else (255,255,255,255))
                tint.putalpha(art.getchannel('A'))
                target.paste((0,0,0,0),rect)
                target.alpha_composite(tint,(x0+bx+(ex-bx-w)//2,y0+by+(ey-by-h)//2))
                md.rectangle((x0,y0,x1-1,y1-1),fill=1)
                records.append({'label':name,'rectangle':rect})

            if tile==9:
                put((0,0,120,24),'Resume Match')
                put((0,176,176,200),'Wrestler Select')
                put((0,200,176,224),'Match Select' if filename=='spr_gam5.bin' else 'Style Select')
                put((0,224,176,248),'Title Menu')
            elif tile==11:
                for row,name in enumerate(['No Change','Ring Center','Near Ropes','Near Corner',
                    'Outside Ring','Ring Apron','Standing','Face Up','Face Down','2 vs 1']):
                    put((0,row*24,144,(row+1)*24),name,False)
            elif tile==12:
                put((0,0,144,24),'1 vs 2',False)
                put((0,24,144,48),'2 vs 2',False)
                put((0,48,176,72),'Opponent Position')
                put((0,72,176,96),'Opponent State')
                put((24,100,148,124),'Restore Stamina')
                put((30,132,114,156),'Boost Spirit')
                put((148,132,208,156),'Back')
                put((28,164,88,188),'Select')
                put((120,164,200,188),'Confirm')
                put((32,192,144,216),'Resume Match')
            elif tile==13:
                put((0,0,176,24),'Resume Practice')
                put((0,24,176,48),'End Practice')
            else:
                for row,name in enumerate(['Resume Match','Match Settings','Player Select','Title Menu']):
                    put((0,136+32*row,144,152+32*row),name,False,14)
            touched=np.asarray(mask).reshape(128,2,128,2).any(axis=(1,3))[::-1]
            adapted=adapt_codebook(target,original,touched,'4444')
            encoded=encode(target,adapted)
            block=bytearray(adapted)
            for y,x in zip(*np.nonzero(touched)):
                pos=2048+spread(int(y))+(spread(int(x))<<1)
                block[pos]=encoded[pos]
            final=decode(block)
            outside=~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
            assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
            offset=entry+tile*SIZE
            archive[offset:offset+SIZE]=block
            edited[tile*SIZE:(tile+1)*SIZE]=block
            final.save(output/f'{Path(filename).stem}_{tile}.png')
            changes.append({'file':filename,'tile':tile,'archive_offset':offset,'labels':records})
            if filename!='spr_gam5.bin' or tile==9:
                bg=Image.new('RGBA',final.size,'black');bg.alpha_composite(final)
                previews.append((f'{filename} / {tile}',bg.convert('RGB')))
        assert archive[entry:entry+len(edited)]==edited
        (output/'TEX'/filename).write_bytes(edited)
    assert len(archive)==len(baseline)
    cursor=0
    for record in sorted(changes,key=lambda c:c['archive_offset']):
        start=record['archive_offset']
        assert archive[cursor:start]==baseline[cursor:start]
        cursor=start+SIZE
    assert archive[cursor:]==baseline[cursor:]
    # This entire entry contains both earlier menu translations.
    title_off,title_size=struct.unpack_from('<II',baseline,8+3*8)
    assert archive[title_off:title_off+title_size]==baseline[title_off:title_off+title_size]
    (output/'TEX/spr_tit.bin').write_bytes(archive[title_off:title_off+title_size])
    (output/'TEX.AFS').write_bytes(archive)
    sheet=Image.new('RGB',(768,280*((len(previews)+2)//3)),(35,35,35));d=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(previews):
        x,y=i%3*256,i//3*280
        sheet.paste(im,(x,y));d.text((x+3,y+258),name,fill='white')
    sheet.resize((1536,sheet.height*2),Image.Resampling.NEAREST).save(output/'pause_preview.png')
    report={'base':'English_Options/TEX.AFS','main_and_options_preserved':True,
        'outside_edited_texture_cells_unchanged':True,'archive_length_unchanged':True,
        'sha256':hashlib.sha256(archive).hexdigest(),'in_game_tested':False,'changes':changes}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Patched {len(changes)} pause texture blocks; previous translations preserved.')


if __name__=='__main__':
    main()
