"""Translate VS selection textures without changing earlier menu patches."""
import hashlib
import json
import shutil
import struct
import sys
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT,SIZE,decode,spread
from patch_options import read_labels,adapt_codebook
from patch_english_menu import encode

OUT=ROOT/'English_VS'
NAMES=['Single Match','Tag Match','Choose a match type.','Choose type and players.',
 '4 Entries','6 Entries','8 Entries','Choose entry count.','No Time Limit','One Fall',
 '30 min','60 min','Best of Three Falls','No Limit / One Fall','60 min / One Fall',
 '60 min / Best of Three','Choose the wrestlers.','Move Cursor','Select Wrestler',
 'Change Player','Start: Confirm','Use these settings?','Yes','No','Select','Confirm',
 'Cancel','Next Screen','Challenge the World Tag Champions!','Win to claim the titles!',
 'Enjoy a special one-off match.','Win seven singles','Win seven tag matches','in a row!',
 'Challenge the Triple Crown champion!','Win to claim the title!']

def source_labels():
    im=Image.open(OUT/'labels_source.png').convert('RGBA');a=np.asarray(im)
    alpha=a[:,:,3] if a[:,:,3].min()<20 else a[:,:,:3].max(2)
    alpha=alpha.copy();alpha[alpha<30]=0
    Image.fromarray(np.repeat(alpha[:,:,None],3,2)).save(OUT/'labels_mask.png')
    return read_labels(OUT/'labels_mask.png',[NAMES[:18],NAMES[18:]])

def main():
    labels=source_labels()
    badges={}
    for t in [0,1,6,7,9]:
        im=Image.open(OUT/f'badge_{t}.png').convert('RGBA')
        a=np.asarray(im.getchannel('A')).copy();a[a<20]=0;im.putalpha(Image.fromarray(a))
        badges[t]=im.crop(im.getbbox())
    baseline=(ROOT/'English_Options_Fixed/TEX.AFS').read_bytes();archive=bytearray(baseline)
    entries=[struct.unpack_from('<II',baseline,8+i*8) for i in range(struct.unpack_from('<I',baseline,4)[0])]
    OUT.joinpath('TEX').mkdir(exist_ok=True)
    shutil.copytree(ROOT/'English_Options_Fixed/TEX',OUT/'TEX',dirs_exist_ok=True)
    changes=[];previews=[]
    for filename,tiles in [('spr_sel.bin',[0,1,2,3,4,6,7,8,9,'rules']),('spr_sel3.bin',[7,8,9,10,28,29,37])]:
        source=(ROOT/'TEX'/filename).read_bytes()
        entry=next(o for o,n in entries if n==len(source) and baseline[o:o+n]==source)
        edited=bytearray(source)
        for tile in tiles:
            # Four uncompressed portrait pages sit before spr_sel's final VQ block.
            offset=len(source)-SIZE if tile=='rules' else tile*SIZE
            original=source[offset:offset+SIZE];old=decode(original);target=old.copy()
            mask=Image.new('1',(256,256));md=ImageDraw.Draw(mask);records=[]
            def clear(rect,panel=False):
                target.paste((17,0,51,170) if panel else (0,0,0,0),rect)
                x0,y0,x1,y1=rect;md.rectangle((x0,y0,x1-1,y1-1),fill=1)
            def put(rect,name,height=18,color=(255,255,0),panel=False):
                clear(rect,panel)
                if name:
                    x0,y0,x1,y1=rect;art=labels[name]
                    h=min(height,y1-y0-4);w=min(x1-x0-4,max(1,round(art.width*h/art.height)))
                    ink=Image.new('RGBA',(w,h),(*color,255));ink.putalpha(art.getchannel('A').resize((w,h),Image.Resampling.LANCZOS))
                    target.alpha_composite(ink,(x0+(x1-x0-w)//2,y0+(y1-y0-h)//2))
                records.append({'text':name,'rectangle':rect})
            def badge(rect,number,gray=False):
                clear(rect);x0,y0,x1,y1=rect
                art=badges[number].resize((x1-x0,y1-y0),Image.Resampling.LANCZOS)
                if gray:
                    muted=art.convert('L').point(lambda v:round(v*0.4)).convert('RGBA');muted.putalpha(art.getchannel('A'));art=muted
                target.alpha_composite(art,(x0,y0));records.append({'badge':number,'rectangle':rect,'disabled':gray})
            if filename=='spr_sel.bin':
                if tile in [0,1,2,3,6,7,9]:
                    bounds=old.getbbox();clear((0,0,256,256))
                    badge(bounds, tile-2 if tile in [2,3] else tile,tile in [2,3])
                elif tile==4:
                    put((0,0,256,32),'Choose a match type.')
                    put((0,32,256,64),'Choose type and players.')
                    put((0,64,136,96),'')
                elif tile==8:
                    for i,name in enumerate(['4 Entries','6 Entries','8 Entries']):put((i*56,0,(i+1)*56,32),name,12,(255,255,255))
                    put((112,32,256,64),'Choose entry count.',16)
                    put((0,64,116,96),'')
                else:
                    put((0,0,256,48),'No Time Limit',30,(255,153,119))
                    put((0,48,184,96),'One Fall',30,(255,153,119))
                    put((0,96,144,144),'30 min',30,(255,153,119))
                    put((0,144,144,192),'60 min',30,(255,153,119))
                    put((0,192,184,248),'Best of Three Falls',28,(255,153,119))
            elif tile==7:
                for y,name in [(96,'No Limit / One Fall'),(120,'60 min / One Fall'),(144,'60 min / Best of Three')]:put((0,y,256,y+24),name,18,(255,255,255))
            elif tile==8:
                clear((0,0,256,256))
                for y,n in [(0,6),(80,7),(168,9)]:badge((0,y,176,y+72),n)
            elif tile==9:
                put((0,8,56,36),'',panel=True)
                put((88,12,256,36),'Use these settings?',16,(255,255,255),True)
                put((68,68,232,94),'',panel=True)
                put((0,98,10,128),'',panel=True)
                put((0,140,56,160),'',panel=True)
                put((24,174,76,202),'Yes',20,(255,255,255))
                put((88,174,168,202),'No',20,(255,255,255))
            elif tile==10:
                put((18,8,256,34),'Choose the wrestlers.',18,(255,255,255),True)
                put((68,42,208,68),'Move Cursor',18,panel=True)
                put((68,70,208,96),'Select Wrestler',18,panel=True)
                put((68,98,256,128),'Change Player',18,panel=True)
                put((144,138,256,160),'Start: Confirm',14,(255,102,51),True)
            elif tile==28:
                put((48,8,256,32),'Challenge the World Tag Champions!',16)
                put((60,32,256,56),'Enjoy a special one-off match.',16)
                put((0,72,212,96),'Win to claim the titles!',16)
                put((0,96,196,120),'')
            elif tile==29:
                for rect,name,height in [((68,0,256,32),'Win seven singles',20),((0,32,196,64),'in a row!',20),((68,64,256,96),'Win seven tag matches',20),((0,96,196,128),'in a row!',20),((80,136,256,160),'Challenge the Triple Crown champion!',16),((60,160,256,184),'Enjoy a special one-off match.',16),((0,200,176,224),'Win to claim the title!',16),((0,224,196,248),'',16)]:put(rect,name,height)
            elif tile==37:
                put((34,128,88,160),'Select',16)
                put((178,128,232,160),'Confirm',16)
                put((32,160,152,192),'Cancel',18)
                put((32,192,132,224),'Next Screen',18)
            touched=np.asarray(mask).reshape(128,2,128,2).any(axis=(1,3))[::-1]
            adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
            for y,x in zip(*np.nonzero(touched)):
                pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
            final=decode(block);outside=~np.repeat(np.repeat(touched[::-1],2,0),2,1)
            assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
            edited[offset:offset+SIZE]=block;archive[entry+offset:entry+offset+SIZE]=block
            final.save(OUT/f'{filename[:-4]}_{tile}.png');target.save(OUT/f'{filename[:-4]}_{tile}_target.png')
            bg=Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final)
            previews.append((f'{filename} / {tile}',bg.convert('RGB')))
            changes.append({'file':filename,'tile':tile,'offset':entry+offset,'labels':records})
        assert archive[entry:entry+len(source)]==edited
        (OUT/'TEX'/filename).write_bytes(edited)
    cursor=0
    for c in sorted(changes,key=lambda c:c['offset']):
        assert archive[cursor:c['offset']]==baseline[cursor:c['offset']];cursor=c['offset']+SIZE
    assert archive[cursor:]==baseline[cursor:] and len(archive)==len(baseline)
    (OUT/'TEX.AFS').write_bytes(archive)
    for pg in range((len(previews)+5)//6):
        sheet=Image.new('RGB',(768,560),'#222222');d=ImageDraw.Draw(sheet)
        for i,(name,im) in enumerate(previews[pg*6:(pg+1)*6]):
            x=i%3*256;y=i//3*280;sheet.paste(im,(x,y));d.text((x+4,y+258),name,fill='white')
        sheet.resize((1536,1120),Image.Resampling.NEAREST).save(OUT/f'preview_{pg+1}.png')
    report={'base':'English_Options_Fixed/TEX.AFS','base_sha256':hashlib.sha256(baseline).hexdigest(),'sha256':hashlib.sha256(archive).hexdigest(),'earlier_translations_preserved':True,'outside_edited_cells_identical':True,'archive_size_unchanged':True,'in_game_tested':False,'changes':changes}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Patched {len(changes)} VS texture blocks. Earlier translations preserved.')

if __name__=='__main__':main()
