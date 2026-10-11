"""Localize selection-screen name rows, preserving the cumulative VS patch."""
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT, SIZE, decode, spread
from patch_options import read_labels, adapt_codebook
from patch_english_menu import encode

OUT = ROOT / 'English_Wrestler_Names'
ROWS = {
    34: ['Giant Baba','Mitsuharu Misawa','Toshiaki Kawada','Akira Taue','Kenta Kobashi','Jun Akiyama','Stan Hansen','Vader'],
    35: ['Gary Albright','Johnny Ace','Hiroshi Hase','Wolf Hawkfield','Grace','Hyper','Diablo','Tiger'],
    36: ['Rikidozan','Steve Williams','Bruno Sammartino','Gene Kiniski','Don Leo Jonathan','Giant Crusher','Bruiser Brody','The Crusher'],
    38: ['The Destroyer','Dick the Bruiser','Crusher Lisowski','Fritz Von Erich','Bobo Brazil'],
    40: ['Takao Omori','Yoshihiro Takayama','Mike Barton','Yoshinari Ogawa','Tamon Honda','Masahito Kakihara','Kentaro Shiga'],
    41: ['Johnny Smith','Maunakea Mossman','Jumbo Tsuruta',None,'Ogami Kongo','Sky High Edge','Super Tigre Dos Mil','Young Giant Baba'],
    42: ['The Master A.M.','Mangler D.H.','Cyclops E.C.','The Killer B.I.'],
}
NAMES = [n for row in ROWS.values() for n in row if n] + ['Comical King','Kyohei Wada','VM-1']

def main():
    labels = {}
    for sheet, names in enumerate([NAMES[:26],NAMES[26:]]):
        im = Image.open(OUT/f'labels_{sheet}.png').convert('RGBA')
        a = np.asarray(im)
        alpha = a[:,:,3].copy() if a[:,:,3].min()<20 else a[:,:,:3].max(2)
        alpha[alpha<30] = 0
        maskpath = OUT/f'labels_mask_{sheet}.png'
        Image.fromarray(np.repeat(alpha[:,:,None],3,2)).save(maskpath)
        labels.update(read_labels(maskpath,[names[:len(names)//2],names[len(names)//2:]]))
    baseline = (ROOT/'English_VS/TEX.AFS').read_bytes()
    source = (ROOT/'English_VS/TEX/spr_sel3.bin').read_bytes()
    entries = [struct.unpack_from('<II',baseline,8+i*8) for i in range(struct.unpack_from('<I',baseline,4)[0])]
    entry = next(o for o,n in entries if n==len(source) and baseline[o:o+n]==source)
    archive, sprite = bytearray(baseline), bytearray(source)
    changes, previews = [], []
    rows = dict(ROWS)
    rows[37] = ['Comical King'] + [None]*6 + ['Kyohei Wada']
    for tile, names in sorted(rows.items()):
        block = source[tile*SIZE:(tile+1)*SIZE]
        old = decode(block)
        target = old.copy()
        mask = np.zeros((256,256),dtype=bool)
        for row,name in enumerate(names):
            if name is None:
                continue
            y,y1 = row*32,(row+1)*32
            if tile==40:
                y,y1 = row*36,(row+1)*36
            elif tile==41 and row<3:
                y,y1 = [(0,40),(40,76),(76,112)][row]
            bounds = old.crop((0,y,256,y1)).getbbox()
            assert bounds is not None
            target.paste((0,0,0,0),(0,y,256,y1))
            mask[y:y1,:] = True
            art = labels[name]
            h = 22
            w = min(232,round(art.width*h/art.height))
            ink = Image.new('RGBA',(w,h),'white')
            ink.putalpha(art.getchannel('A').resize((w,h),Image.Resampling.LANCZOS))
            target.alpha_composite(ink,((240-w)//2,y+bounds[1]+(bounds[3]-bounds[1]-h)//2))
            changes.append({'tile':tile,'row':row,'name':name})
        touched = mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
        adapted = adapt_codebook(target,block,touched,'4444')
        candidate = encode(target,adapted)
        packed = bytearray(adapted)
        for y,x in zip(*np.nonzero(touched)):
            pos = 2048+spread(int(y))+(spread(int(x))<<1)
            packed[pos] = candidate[pos]
        final = decode(packed)
        assert np.array_equal(np.asarray(old)[~mask],np.asarray(final)[~mask])
        # Every edited row was fully cleared; verify its empty margins remain empty.
        expected = np.asarray(target)[:,:,3]
        actual = np.asarray(final)[:,:,3]
        assert not np.any(actual[mask & (expected==0)]>85), f'Stray pixels in tile {tile}'
        sprite[tile*SIZE:(tile+1)*SIZE] = packed
        archive[entry+tile*SIZE:entry+(tile+1)*SIZE] = packed
        final.save(OUT/f'names_{tile}.png')
        bg = Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final)
        previews.append((tile,bg.convert('RGB')))
    cursor = 0
    for tile in sorted(rows):
        start = entry+tile*SIZE
        assert archive[cursor:start]==baseline[cursor:start]
        cursor = start+SIZE
    assert archive[cursor:]==baseline[cursor:] and len(archive)==len(baseline)
    assert archive[entry:entry+len(source)]==sprite
    shutil.copytree(ROOT/'English_VS/TEX',OUT/'TEX',dirs_exist_ok=True)
    (OUT/'TEX/spr_sel3.bin').write_bytes(sprite)
    (OUT/'TEX.AFS').write_bytes(archive)
    for pg in range(2):
        sheet = Image.new('RGB',(1024,280),'#222222');d = ImageDraw.Draw(sheet)
        for col,(tile,im) in enumerate(previews[pg*4:(pg+1)*4]):
            sheet.paste(im,(col*256,0));d.text((col*256+4,260),f'Name sheet {tile}',fill='white')
        sheet.resize((2048,560),Image.Resampling.NEAREST).save(OUT/f'preview_{pg+1}.png')
    report = {'base':'English_VS/TEX.AFS','translated_labels':len(changes),'sha256':hashlib.sha256(archive).hexdigest(),'previous_patches_preserved':True,'unmodified_pixels_identical':True,'archive_size_unchanged':True,'in_game_tested':False,'names':changes}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Translated {len(changes)} labels in {len(rows)} name sheets. All preservation checks passed.')

if __name__=='__main__':
    main()
