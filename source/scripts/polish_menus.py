"""Consistent cap heights, centered pause labels, and outlined VS descriptions."""
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT, SIZE, OFFSET, decode, spread
from patch_options import read_labels, adapt_codebook
from patch_english_menu import encode

from patch_wrestler_names import ROWS, NAMES

OUT = ROOT/'English_Menu_Polish'
MAIN = ['Arcade','History Mode','VS','Create-A-Wrestler','Practice','Spectator','Backup','Options']
PAUSE = ['Resume Match','Wrestler Select','Style Select','Title Menu','No Change','Ring Center','Near Ropes','Near Corner','Outside Ring','Ring Apron','Standing','Face Up','Face Down','2 vs 1','1 vs 2','2 vs 2','Opponent Position','Opponent State','Restore Stamina','Boost Spirit','Resume Practice','End Practice','Match Select','Match Settings','Player Select','Back','Select','Confirm']
VS = ['Choose a match type.','Choose type and players.','Choose entry count.','Challenge the tag champs!','Win to claim the titles!','Enjoy a special match.','Win seven singles','matches in a row!','Win seven tag matches','in a row!','Challenge the Triple Crown','Win to claim the title!']

def generated(path, names, columns):
    im=Image.open(path).convert('RGBA')
    alpha=np.asarray(im.getchannel('A')).copy();alpha[alpha<30]=0
    im.putalpha(Image.fromarray(alpha))
    result={}
    for col in range(columns):
        x0=col*im.width//columns;x1=(col+1)*im.width//columns
        a=alpha[:,x0:x1]
        rows=np.flatnonzero((a>100).sum(1)>8)
        groups=np.split(rows,np.where(np.diff(rows)>4)[0]+1)
        ns=names[col*len(names)//columns:(col+1)*len(names)//columns]
        assert len(groups)==len(ns),(path,len(groups),len(ns))
        for name,g in zip(ns,groups):
            art=im.crop((x0,max(0,int(g[0])-2),x1,min(im.height,int(g[-1])+3)))
            result[name]=art.crop(art.getbbox())
    return result

def sized(art,cap):
    # Measure the first capital's fill, excluding outlines and descenders.
    def bounds(im):
        a=np.asarray(im)
        ink=(a[:,:,0]>180)&(a[:,:,1]>150)&(a[:,:,3]>150)
        columns=np.flatnonzero(ink.sum(0)>=max(2,im.height//20));first=int(columns[0]);end=first+1
        while end<im.width and ink[:,end].any():end+=1
        rows=np.flatnonzero(ink[:,first:end].any(1))
        return int(rows[0]),int(rows[-1])+1
    top,bottom=bounds(art);scale=cap/(bottom-top)
    result=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.LANCZOS)
    return result,bounds(result)[0]


def main():
    labels={}
    for i,(names,cols) in enumerate([(MAIN,1),(PAUSE,2),(VS,2)]):
        labels.update(generated(OUT/f'labels_{i}.png',names,cols))
    for i,ns in enumerate([NAMES[:26],NAMES[26:]]):
        labels.update(read_labels(ROOT/f'English_Wrestler_Names/labels_mask_{i}.png',[ns[:len(ns)//2],ns[len(ns)//2:]]))
    from fix_options_layout import NAMES as OPTIONS
    options=read_labels(ROOT/'English_Options_Fixed/labels_mask.png',[OPTIONS])
    labels.update({n:options[n] for n in ['On','Off']})
    def render(name,cap):
        return sized(labels[name],round(cap*0.75) if name[0].islower() else cap)
    baseline=(ROOT/'English_Wrestler_Names/TEX.AFS').read_bytes()
    archive=bytearray(baseline)
    entries=[struct.unpack_from('<II',baseline,8+i*8) for i in range(struct.unpack_from('<I',baseline,4)[0])]
    jobs={}
    def add(file,tile,rect,name,family='pause',color=None,width=None):
        jobs.setdefault((file,tile),[]).append({'rectangle':rect,'text':name,'family':family,'color':color,'width':width})
    for i,n in enumerate(MAIN):
        add('spr_tit.bin',OFFSET//SIZE,(0,64+i*24,256,88+i*24),n,'main',width=156 if 2<=i<6 else 188)
    for n,x in [('On',16),('Off',96)]:add('spr_tit.bin',33,(x,240,x+48,256),n,'option')
    for f in ['spr_gam.bin','spr_gam5.bin']:
        for rect,n in [((0,0,120,24),'Resume Match'),((0,176,176,200),'Wrestler Select'),((0,200,176,224),'Match Select' if f=='spr_gam5.bin' else 'Style Select'),((0,224,176,248),'Title Menu')]:add(f,9,rect,n,color=(255,221,68))
        for row,n in enumerate(['No Change','Ring Center','Near Ropes','Near Corner','Outside Ring','Ring Apron','Standing','Face Up','Face Down','2 vs 1']):add(f,11,(0,row*24,144,(row+1)*24),n,color=(255,255,255))
        for rect,n in [((0,0,144,24),'1 vs 2'),((0,24,144,48),'2 vs 2'),((0,48,176,72),'Opponent Position'),((0,72,176,96),'Opponent State'),((24,100,148,124),'Restore Stamina'),((30,132,114,156),'Boost Spirit'),((148,132,208,156),'Back'),((28,164,88,188),'Select'),((120,164,200,188),'Confirm'),((32,192,144,216),'Resume Match')]:add(f,12,rect,n,'pause_prompt' if n in ['Restore Stamina','Boost Spirit','Back','Select','Confirm'] else 'pause',color=(255,255,255) if n in ['1 vs 2','2 vs 2'] else (255,221,68))
        for row,n in enumerate(['Resume Practice','End Practice']):add(f,13,(0,row*24,176,(row+1)*24),n,color=(255,221,68))
    for row,n in enumerate(['Resume Match','Match Settings','Player Select','Title Menu']):add('spr_gam2.bin',38,(0,136+row*32,144,152+row*32),n,'pause_small',(255,255,255))
    add('spr_sel.bin',4,(0,0,256,32),VS[0],'vs')
    add('spr_sel.bin',4,(0,32,256,64),VS[1],'vs')
    add('spr_sel.bin',8,(112,32,256,64),VS[2],'vs')
    for rect,n in [((48,8,256,32),VS[3]),((0,72,212,96),VS[4]),((60,32,256,56),VS[5])]:add('spr_sel3.bin',28,rect,n,'vs')
    for rect,n in [((68,0,256,32),VS[6]),((0,32,196,64),VS[7]),((68,64,256,96),VS[8]),((0,96,196,128),VS[9]),((80,136,256,160),VS[10]),((0,200,176,224),VS[11]),((60,160,256,184),VS[5])]:add('spr_sel3.bin',29,rect,n,'vs')
    rows=dict(ROWS);rows[37]=['Comical King']+[None]*6+['Kyohei Wada']
    for tile,ns in rows.items():
        for row,n in enumerate(ns):
            if n is None:continue
            y,y1=row*32,(row+1)*32
            if tile==40:y,y1=row*36,(row+1)*36
            elif tile==41 and row<3:y,y1=[(0,40),(40,76),(76,112)][row]
            add('spr_sel3.bin',tile,(0,y,256,y1),n,'name',(255,255,255),232)
    caps={'main':18,'pause':14,'pause_small':10,'pause_prompt':10,'option':12,'vs':15,'name':18}
    for fam in caps:
        relevant=[r for rs in jobs.values() for r in rs if r['family']==fam]
        while any(render(r['text'],caps[fam])[0].width>(r['width'] or r['rectangle'][2]-r['rectangle'][0]-8) or render(r['text'],caps[fam])[0].height>r['rectangle'][3]-r['rectangle'][1]-2 for r in relevant):caps[fam]-=1
        assert caps[fam]>=8,(fam,caps[fam])
    changes=[];previews=[];sprites={}
    for (file,tile),records in jobs.items():
        if file not in sprites:
            source=(ROOT/'English_Wrestler_Names/TEX'/file).read_bytes()
            entry=next(o for o,n in entries if n==len(source) and baseline[o:o+n]==source)
            sprites[file]=(entry,bytearray(source))
        entry,sprite=sprites[file]
        original=bytes(sprite[tile*SIZE:(tile+1)*SIZE]);old=decode(original)
        target=old.copy();mask=np.zeros((256,256),dtype=bool)
        if file=='spr_sel3.bin' and tile in [28,29]:
            target.paste((0,0,0,0),(0,0,256,256));mask[:]=True
        for r in records:
            x0,y0,x1,y1=r['rectangle'];fam=r['family'];n=r['text']
            target.paste((0,0,0,0),(x0,y0,x1,y1));mask[y0:y1,x0:x1]=True
            art,top=render(n,caps[fam])
            if r['color']:
                ink=Image.new('RGBA',art.size,(*r['color'],255));ink.putalpha(art.getchannel('A'));art=ink
            span=240 if fam=='name' else x1-x0
            x=x0+(span-art.width)//2
            # Same capital top and baseline, regardless of descenders in a name.
            y=y0+(y1-y0-caps[fam])//2-top
            if n[0].islower():y+=caps[fam]-round(caps[fam]*0.75)
            if y+art.height>y1:y=y1-art.height
            assert x>=x0 and y>=y0 and x+art.width<=x1 and y+art.height<=y1,(n,art.size,(x,y),r)
            target.alpha_composite(art,(x,y))
            r.update(cap_height=caps[fam],position=(x,y),size=art.size)
        touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
        adapted=adapt_codebook(target,original,touched,'4444');encoded=encode(target,adapted);block=bytearray(adapted)
        for y,x in zip(*np.nonzero(touched)):
            pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=encoded[pos]
        final=decode(block)
        outside=~np.repeat(np.repeat(touched[::-1],2,0),2,1)
        assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
        sprite[tile*SIZE:(tile+1)*SIZE]=block
        start=entry+tile*SIZE;archive[start:start+SIZE]=block
        final.save(OUT/f'{file[:-4]}_{tile}.png')
        target.save(OUT/f'{file[:-4]}_{tile}_target.png')
        bg=Image.new('RGBA',(256,256),'#283848');bg.alpha_composite(final)
        previews.append((f'{file} / {tile}',bg.convert('RGB')))
        changes.append({'file':file,'tile':tile,'offset':start,'labels':records})
    cursor=0
    for c in sorted(changes,key=lambda c:c['offset']):
        assert archive[cursor:c['offset']]==baseline[cursor:c['offset']];cursor=c['offset']+SIZE
    assert archive[cursor:]==baseline[cursor:] and len(archive)==len(baseline)
    shutil.copytree(ROOT/'English_Wrestler_Names/TEX',OUT/'TEX',dirs_exist_ok=True)
    for f,(entry,sprite) in sprites.items():
        assert archive[entry:entry+len(sprite)]==sprite
        (OUT/'TEX'/f).write_bytes(sprite)
    (OUT/'TEX.AFS').write_bytes(archive)
    for pg in range((len(previews)+5)//6):
        sheet=Image.new('RGB',(768,560),'#222222');d=ImageDraw.Draw(sheet)
        for i,(name,im) in enumerate(previews[pg*6:(pg+1)*6]):
            x=i%3*256;y=i//3*280;sheet.paste(im,(x,y));d.text((x+2,y+258),name,fill='white')
        sheet.resize((1536,1120),Image.Resampling.NEAREST).save(OUT/f'preview_{pg+1}.png')
    report={'base':'English_Wrestler_Names/TEX.AFS','caps':caps,'sha256':hashlib.sha256(archive).hexdigest(),'unmodified_pixels_identical':True,'unmodified_archive_bytes_identical':True,'archive_size_unchanged':True,'in_game_tested':False,'changes':changes}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'caps':caps,'patched_blocks':len(changes),'preservation_checks':'passed'}))

if __name__=='__main__':main()
