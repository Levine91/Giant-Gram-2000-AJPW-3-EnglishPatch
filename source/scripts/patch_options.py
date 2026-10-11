"""Pack options translations into the existing textures; keep the main-menu patch.
Run with NumPy and Pillow: python patch_options.py source-label-sheet.png extra-labels.png
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

LEFT = ['Difficulty','Stamina','Stamina Gauge','Reversal Points','Time Limit',
        'Screen','Sound','Controls','Giant Channel','Restore Defaults','Exit',
        'Download','Easy','Normal','Hard','Show','Hide','30 min','60 min',
        'Unlimited','Burning','Double Team','OR','(A: Confirm)']
RIGHT = ['Audio','Sound Test','Volume','Done','Stereo','Mono','Crowd','Commentary',
         'min','Taunt','Move','Throw','Grapple','Strike','Tag','Normal','Wide',
         'Confirm-yellow','Select-yellow','Back-yellow','OPTIONS-yellow',
         'Confirm','Select','Back']


def read_labels(path, columns=None):
    if columns is None:
        columns = [LEFT, RIGHT]
    rgb = np.asarray(Image.open(path).convert('RGB'))
    labels = {}
    for col, names in enumerate(columns):
        pixels = rgb[:, col*rgb.shape[1]//len(columns):(col+1)*rgb.shape[1]//len(columns)]
        rows = np.flatnonzero((pixels.max(axis=2) > 100).sum(axis=1) > 8)
        groups = np.split(rows, np.where(np.diff(rows) > 4)[0]+1)
        if len(groups) != len(names):
            raise ValueError(f'Expected {len(names)} separated labels in column {col}, got {len(groups)}')
        for name, group in zip(names, groups):
            part = pixels[max(0, group[0]-2):group[-1]+3].copy()
            alpha = part.max(axis=2)
            alpha[alpha < 45] = 0
            # Black-backed generation is converted to RGBA for texture packing.
            color = np.minimum(255, part.astype(float)*255/np.maximum(alpha[:,:,None],1)).astype('uint8')
            sprite = Image.fromarray(np.dstack([color, alpha]))
            labels[name] = sprite.crop(sprite.getbbox())
    return labels


def adapt_codebook(image, original, touched, fmt):
    """Use only palette entries unreferenced by preserved texture cells."""
    indices = np.frombuffer(original[2048:],dtype='uint8')
    keep = {int(indices[spread(y)+(spread(x)<<1)])
            for y in range(128) for x in range(128) if not touched[y,x]}
    free = sorted(set(range(256))-keep)
    if not free:
        return original
    rgba = np.asarray(image)[::-1].astype(np.uint16)
    if fmt == '4444':
        q = (rgba+8)//17
        words = (q[:,:,3]<<12)|(q[:,:,0]<<8)|(q[:,:,1]<<4)|q[:,:,2]
    elif fmt == '1555':
        words = ((rgba[:,:,3]>=128).astype('uint16')<<15)|(((rgba[:,:,0]*31+127)//255)<<10)|(((rgba[:,:,1]*31+127)//255)<<5)|((rgba[:,:,2]*31+127)//255)
    else:
        words = (((rgba[:,:,0]*31+127)//255)<<11)|(((rgba[:,:,1]*63+127)//255)<<5)|((rgba[:,:,2]*31+127)//255)
    vectors = words.reshape(128,2,128,2).transpose(0,2,3,1).reshape(128,128,4)[touched]
    unique,counts = np.unique(vectors,axis=0,return_counts=True)
    palette = np.frombuffer(original[:2048],dtype='<u2').reshape(256,4).copy()

    def features(w):
        if fmt == '4444':
            c = np.stack([((w>>8)&15)/15,((w>>4)&15)/15,(w&15)/15,(w>>12)/15],axis=-1)
        elif fmt == '1555':
            c = np.stack([((w>>10)&31)/31,((w>>5)&31)/31,(w&31)/31,w>>15],axis=-1)
        else:
            c = np.stack([((w>>11)&31)/31,((w>>5)&63)/63,(w&31)/31,np.ones_like(w)],axis=-1)
        c[:,:,:3] *= c[:,:,3:4]
        c[:,:,3] *= 2
        return c.reshape(-1,16).astype('float32')

    desired = features(unique)
    nearest = np.full(len(unique),np.inf)
    for fixed in features(palette[sorted(keep)]):
        nearest = np.minimum(nearest,((desired-fixed)**2).sum(axis=1))
    # Greedy weighted VQ representatives; small text textures need no new library.
    for slot in free:
        choice = int(np.argmax(nearest*counts))
        palette[slot] = unique[choice]
        nearest = np.minimum(nearest,((desired-desired[choice])**2).sum(axis=1))
    assert np.array_equal(palette[sorted(keep)],np.frombuffer(original[:2048],dtype='<u2').reshape(256,4)[sorted(keep)])
    return palette.astype('<u2').tobytes()+original[2048:]


def main():
    labels = read_labels(sys.argv[1])
    labels.update(read_labels(sys.argv[2],[['Level','Comm.','min','Download complete',
        'Save complete','Load complete','Burning','Double Team']]))
    labels.update(read_labels(ROOT/'English_Options/run_label.png',[['Run']]))
    output = ROOT/'English_Options'
    (output/'TEX').mkdir(parents=True, exist_ok=True)
    for source_path,name in [(sys.argv[1],'labels_source.png'),(sys.argv[2],'extra_labels_source.png')]:
        if Path(source_path).resolve() != (output/name).resolve():
            shutil.copyfile(source_path,output/name)
    source = (ROOT/'TEX/spr_tit.bin').read_bytes()
    baseline = (ROOT/'English_Menu/TEX.AFS').read_bytes()
    base_sprite = (ROOT/'English_Menu/TEX/spr_tit.bin').read_bytes()
    entry, size = struct.unpack_from('<II', baseline, 8+3*8)
    assert size == len(source) and baseline[entry:entry+size] == base_sprite
    assert base_sprite[:49*SIZE] == source[:49*SIZE]
    archive, sprite_file = bytearray(baseline), bytearray(base_sprite)
    changes, previews = [], []
    for tile in [22,23,24,25,26,27,28,29,35,36,37]:
        fmt = '565' if 24 <= tile <= 29 else ('1555' if tile == 37 else '4444')
        original = source[tile*SIZE:(tile+1)*SIZE]
        old = decode(original, fmt)
        target = old.copy()
        mask = Image.new('1', (256,256))
        md = ImageDraw.Draw(mask)
        records = []

        def put(rect, name, height=14, ink=True, background=(0,0,0,0), yellow=False):
            x0,y0,x1,y1 = rect
            bounds = old.crop(rect).getbbox() if ink else (0,0,x1-x0,y1-y0)
            if bounds is None:
                raise ValueError(f'No original label at tile {tile}: {rect}')
            bx,by,ex,ey = bounds
            clear_rect = (x0,y0-4,x1,y1) if 24 <= tile <= 29 else rect
            target.paste(background, clear_rect)
            if name:
                art = labels[name]
                h = min(height, ey-by)
                w = min(ex-bx, max(1, round(art.width*h/art.height)))
                art = art.resize((w,h), Image.Resampling.LANCZOS)
                if yellow:
                    colored = Image.new('RGBA',art.size,(255,255,0,255))
                    colored.putalpha(art.getchannel('A'))
                    art = colored
                # Opaque diagrams retain a dark backing under the translated label.
                target.alpha_composite(art,(x0+bx,y0+by+(ey-by-h)//2))
            cx0,cy0,cx1,cy1 = clear_rect
            md.rectangle((cx0,cy0,cx1-1,cy1-1),fill=1)
            records.append({'label':name,'rectangle':rect})

        if tile == 22:
            for row,name in enumerate(LEFT[:10]):
                if row == 0:
                    name = 'Level'
                put((0,row*16,184,(row+1)*16),name)
            put((0,160,32,176),'Exit')
            put((32,160,136,176),'Download')
            for rect,name in [((0,176,80,192),'Easy'),((96,176,144,192),'Normal'),
                ((160,176,240,192),'Hard'),((0,192,80,208),'Show'),
                ((80,192,160,208),'Hide'),((0,208,80,224),'30 min'),
                ((96,208,160,224),'60 min'),((176,208,240,224),'Unlimited'),
                ((0,224,80,240),'Normal'),((96,224,160,240),'Wide'),
                ((0,240,112,256),'(A: Confirm)')]:
                put(rect,name)
        elif tile == 23:
            put((0,0,224,40),'OPTIONS-yellow',32)
            put((28,40,88,72),'Select-yellow',24)
            put((120,40,200,72),'Confirm-yellow',24)
            put((28,72,88,100),'Back-yellow',24)
            for row,name in enumerate(['Audio','Sound Test','Volume','Done']):
                put((0,104+16*row,136,120+16*row),name)
            put((0,168,72,184),'Stereo')
            put((72,168,144,184),'Mono')
            put((140,120,176,136),'Crowd')
            put((140,136,176,152),'Comm.')
            put((0,200,136,216),'Done')
        elif 24 <= tile <= 29:
            mapping = {
                24:['Taunt','Taunt','Run','Throw','Grapple','Strike'],
                25:['Throw','Taunt','Grapple','Taunt','Run','Strike'],
                26:['Taunt','Throw','Taunt','Grapple','Strike','Run'],
                27:['Strike','Run','Taunt','Taunt','Throw','Grapple'],
                28:['Strike','Grapple','Throw','Taunt','Taunt','Run'],
                29:['Run','Taunt','Taunt','Throw','Grapple','Strike']}
            ys = [8,32,68,92,116,140] if tile < 27 else [8,32,56,92,116,140]
            for y,name in zip(ys,mapping[tile]):
                put((162,y,200,y+16),name,12,False,(0,0,24,255))
        elif tile in [35,36]:
            for y in ([8,120] if tile == 35 else [8]):
                put((38,y,120,y+16),'Burning',12,False,(0,0,24,255),True)
                put((38,y+18,120,y+34),'Double Team',12,False,(0,0,24,255),True)
            if tile == 35:
                put((230,8,256,24),'OR',12,False,(0,0,24,255))
                put((0,64,16,80),None,ink=False,background=(0,0,24,255))
                put((206,120,248,136),'OR',12,False,(0,0,24,255))
            else:
                put((206,8,248,24),'OR',12,False,(0,0,24,255))
                put((64,112,256,144),'Download complete',26)
                put((0,144,128,176),None)
                put((0,176,256,208),'Save complete',26)
                put((0,208,256,240),'Load complete',26)
        else:
            for rect,name in [((0,96,128,112),'Restore Defaults'),
                ((0,112,16,128),'min'),((0,128,48,144),'Unlimited'),
                ((0,160,32,176),'Crowd'),((0,176,32,192),'Comm.')]:
                put(rect,name)

        # Copy only complete edited 2x2 VQ cells; preserve every other index.
        touched = np.asarray(mask).reshape(128,2,128,2).any(axis=(1,3))[::-1]
        adapted = adapt_codebook(target,original,touched,fmt)
        candidate = encode(target, adapted, fmt)
        block = bytearray(adapted)
        for y,x in zip(*np.nonzero(touched)):
            address = 2048+spread(int(y))+(spread(int(x))<<1)
            block[address] = candidate[address]
        final = decode(block, fmt)
        outside = ~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
        assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
        start = entry+tile*SIZE
        archive[start:start+SIZE] = block
        sprite_file[tile*SIZE:(tile+1)*SIZE] = block
        final.save(output/f'tile_{tile}_english.png')
        bg = Image.new('RGBA',(256,256),'black');bg.alpha_composite(final)
        previews.append((tile,bg.convert('RGB')))
        changes.append({'tile':tile,'format':fmt,'archive_offset':hex(start),'labels':records})
    assert len(archive) == len(baseline)
    assert archive[entry+49*SIZE:entry+50*SIZE] == baseline[entry+49*SIZE:entry+50*SIZE]
    assert archive[entry:entry+size] == sprite_file
    allowed = [(entry+c['tile']*SIZE,entry+(c['tile']+1)*SIZE) for c in changes]
    cursor = 0
    for start,end in sorted(allowed):
        assert archive[cursor:start] == baseline[cursor:start]
        cursor = end
    assert archive[cursor:] == baseline[cursor:]
    (output/'TEX.AFS').write_bytes(archive)
    (output/'TEX/spr_tit.bin').write_bytes(sprite_file)
    sheet = Image.new('RGB',(768,280*((len(previews)+2)//3)),(35,35,35))
    draw = ImageDraw.Draw(sheet)
    for i,(tile,im) in enumerate(previews):
        x,y=(i%3)*256,(i//3)*280
        sheet.paste(im,(x,y));draw.text((x+4,y+258),f'Texture {tile}',fill='white')
    sheet.resize((1536,sheet.height*2),Image.Resampling.NEAREST).save(output/'options_preview.png')
    report = {'base':'English_Menu/TEX.AFS','originals_preserved':True,
        'main_menu_preserved':True,'outside_edited_VQ_cells_unchanged':True,
        'archive_size':len(archive),'sha256':hashlib.sha256(archive).hexdigest(),
        'in_game_tested':False,'changes':changes}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Patched {len(changes)} textures; main menu and all unrelated bytes preserved.')


if __name__ == '__main__':
    main()
