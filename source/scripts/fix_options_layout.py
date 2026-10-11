"""Repair options typography and missing setting labels on the cumulative archive."""
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

OUT=ROOT/'English_Options_Fixed'
NAMES=['Level','Stamina','Stamina Gauge','Reversal Points','Time Limit','Screen',
       'Sound','Controls','Giant Channel','Restore Defaults','Exit','Download',
       'Easy','Normal','Hard','Vibration','Off','On','All Japan Mode','Best of Three']

def cap_bounds(art):
    a=np.asarray(art.getchannel('A'))>100
    occupied=a.any(axis=0)
    first=int(np.flatnonzero(occupied)[0])
    end=first+1
    while end<len(occupied) and occupied[end]:end+=1
    rows=np.flatnonzero(a[:,first:end].any(axis=1))
    return int(rows[0]),int(rows[-1]+1)

def sized(art,cap):
    top,bottom=cap_bounds(art)
    scale=cap/(bottom-top)
    result=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
    return result,cap_bounds(result)[0]

def main():
    OUT.mkdir(exist_ok=True)
    source=OUT/'labels_source.png'
    if len(sys.argv)>1:shutil.copyfile(sys.argv[1],source)
    # Use the supplied transparency; RGB beneath transparent pixels is irrelevant.
    alpha=np.asarray(Image.open(source).convert('RGBA'))[:,:,3].copy()
    alpha[alpha<20]=0
    maskpath=OUT/'labels_mask.png'
    Image.fromarray(np.repeat(alpha[:,:,None],3,axis=2)).save(maskpath)
    labels=read_labels(maskpath,[NAMES])
    if (OUT/'difficulty_mask.png').exists():
        labels.update(read_labels(OUT/'difficulty_mask.png',[['Difficulty']]))
    # One cap size and baseline for main labels, a second shared size for choices.
    label_cap=12
    while any(sized(labels[n],label_cap)[0].width>120 for n in NAMES[:12]+NAMES[15:16]+NAMES[18:]):label_cap-=1
    choice_cap=12
    while any(sized(labels[n],choice_cap)[0].width>w for n,w in [('Easy',72),('Normal',44),('Hard',72),('Off',40),('On',40)]):choice_cap-=1
    assert label_cap>=9 and choice_cap>=9
    baseline=(ROOT/'TEX.AFS').read_bytes()
    archive=bytearray(baseline)
    off,size=struct.unpack_from('<II',baseline,8+3*8)
    assert size==50*SIZE
    sprite=bytearray(baseline[off:off+size])
    records=[];previews=[]
    for tile,fmt in [(22,'4444'),(33,'4444'),(37,'1555')]:
        original=bytes(sprite[tile*SIZE:(tile+1)*SIZE]);old=decode(original,fmt)
        target=old.copy();mask=Image.new('1',(256,256));md=ImageDraw.Draw(mask);edits=[]
        def put(rect,name,choice=False,align='left',left=4):
            x0,y0,x1,y1=rect
            target.paste((0,0,0,0),rect)
            art,cap_top=sized(labels[name],choice_cap if choice else label_cap)
            assert art.width<=x1-x0-2 and art.height<=y1-y0,(name,art.size,rect)
            x=x0+(x1-x0-art.width)//2 if align=='center' else x0+left
            # Match capital tops, retaining descenders at their natural depth.
            y=y0+1-cap_top
            assert x>=x0 and x+art.width<=x1 and y>=y0 and y+art.height<=y1,(name,x,y,art.size)
            ink=Image.new('RGBA',art.size,'white');ink.putalpha(art.getchannel('A'))
            target.alpha_composite(ink,(x,y))
            md.rectangle((x0,y0,x1-1,y1-1),fill=1)
            edits.append({'text':name,'clear':rect,'position':[x,y],'size':art.size,'cap_height':choice_cap if choice else label_cap,'alignment':align})
        if tile==22:
            for i,name in enumerate(NAMES[:10]):
                put((0,i*16,184,(i+1)*16),'Difficulty' if i==0 and 'Difficulty' in labels else name)
            # Exit's displayed span is 40 pixels. Download must begin after it.
            put((0,160,40,176),'Exit')
            put((40,160,136,176),'Download')
            for name,x0,x1 in [('Easy',0,80),('Normal',96,144),('Hard',160,240)]:
                put((x0,176,x1,192),name,True,'center')
        elif tile==33:
            for y,name in [(192,'All Japan Mode'),(208,'Best of Three'),(224,'Vibration')]:put((0,y,184,y+16),name)
            put((16,240,64,256),'On',True,'center')
            put((96,240,144,256),'Off',True,'center')
        else:put((0,96,128,112),'Restore Defaults')
        touched=np.asarray(mask).reshape(128,2,128,2).any(axis=(1,3))[::-1]
        adapted=adapt_codebook(target,original,touched,fmt)
        candidate=encode(target,adapted,fmt);block=bytearray(adapted)
        for y,x in zip(*np.nonzero(touched)):
            pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
        final=decode(block,fmt)
        outside=~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
        assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
        # No ink is allowed in Exit's boundary after the word; this catches ExitD.
        if tile==22:
            assert np.asarray(final)[160:176,34:40,3].max()==0
        sprite[tile*SIZE:(tile+1)*SIZE]=block
        start=off+tile*SIZE;archive[start:start+SIZE]=block
        final.save(OUT/f'tile_{tile}.png')
        bg=Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final);previews.append((tile,bg.convert('RGB')))
        records.append({'tile':tile,'offset':start,'labels':edits})
    cursor=0
    for r in sorted(records,key=lambda r:r['offset']):
        assert archive[cursor:r['offset']]==baseline[cursor:r['offset']]
        cursor=r['offset']+SIZE
    assert archive[cursor:]==baseline[cursor:] and len(archive)==len(baseline)
    shutil.copytree(ROOT/'English_CAW/TEX',OUT/'TEX',dirs_exist_ok=True)
    (OUT/'TEX/spr_tit.bin').write_bytes(sprite)
    (OUT/'TEX.AFS').write_bytes(archive)
    sheet=Image.new('RGB',(768,280),'#222222');d=ImageDraw.Draw(sheet)
    for i,(tile,im) in enumerate(previews):sheet.paste(im,(i*256,0));d.text((i*256+4,260),f'Texture {tile}',fill='white')
    sheet.resize((1536,560),Image.Resampling.NEAREST).save(OUT/'texture_preview.png')
    # A readable layout preview uses the decoded game sprites, not the source art.
    tiles={t:Image.open(OUT/f'tile_{t}.png') for t in [22,33,37]}
    screen=Image.new('RGBA',(640,480),'#000020');draw=ImageDraw.Draw(screen)
    layout=[(22,0),(22,16),(33,192),(33,208),(22,32),(22,48),(22,64),(22,80),(33,224),(22,96),(22,112),(37,96),(22,160)]
    for i,(tile,y) in enumerate(layout):
        h=16;rect=(0,y,128 if tile==37 else (40 if y==160 else 184),y+h)
        art=tiles[tile].crop(rect);dest=(45,32+i*31);screen.alpha_composite(art,dest);draw.rectangle((30,dest[1]+5,35,dest[1]+10),fill='white')
    for x,rect in zip([320,410,500],[(0,176,80,192),(96,176,144,192),(160,176,240,192)]):
        art=tiles[22].crop(rect);screen.alpha_composite(art,(x-art.width//2,32))
    for x,rect in [(320,(96,240,144,256)),(500,(16,240,64,256))]:
        art=tiles[33].crop(rect);screen.alpha_composite(art,(x-art.width//2,32+8*31))
    screen.resize((1280,960),Image.Resampling.NEAREST).save(OUT/'options_layout_preview.png')
    report={'base_sha256':hashlib.sha256(baseline).hexdigest(),'sha256':hashlib.sha256(archive).hexdigest(),'archive_size_unchanged':True,'other_translations_preserved':True,'untouched_pixels_identical':True,'exit_boundary_clear':True,'label_cap_height':label_cap,'choice_cap_height':choice_cap,'in_game_tested':False,'changes':records}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))

if __name__=='__main__':main()
