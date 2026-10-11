"""Translate CAW texture labels, retaining earlier patches and untouched pixels."""
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from extract_main_menu import ROOT, SIZE, decode, spread
from patch_english_menu import encode
from patch_options import adapt_codebook, read_labels

OUT = ROOT/'English_CAW'
SPECS = {}

def add(file, tile, rect, text, style='white', height=20):
    SPECS.setdefault((file,tile),[]).append((rect,text,style,height))

def rows(file,tile,x0,x1,y,step,names,style='white',height=20):
    for i,name in enumerate(names):
        add(file,tile,(x0,y+i*step,x1,y+(i+1)*step),name,style,height)

a,b='spr_cmk.bin','spr_cmk2.bin'
rows(a,6,0,100,0,32,['Move Fusion','Delete Moves','Quotes','Taunt','Tag Moves','Signature Name','Double Team'])
rows(a,6,100,192,0,32,['Tactics','Name','Body Type','Catchphrase','Height','Weight'])
rows(a,9,0,224,0,64,['Rename Move','Double Team','Taunt','Tag Moves'],'outline',42)
rows(a,10,0,184,0,32,['Title Wins','Champion Carnival','World Tag League','One-Night Tournament'],'outline',20)
rows(a,10,0,72,128,36,['Early','Middle','Late'],'outline',26)
rows(a,14,0,150,0,40,['Aggressive','Normal','Defensive'],'blue',24)
for rect,text in [((184,0,256,20),'Free space'),((136,20,256,40),'Saving needs 14'),((168,40,256,64),'blocks on a'),((0,64,104,84),'is insufficient.'),((0,84,168,104),'free blocks on a'),((0,104,152,124),'memory card.'),((94,128,256,148),'A VMU game already'),((36,148,256,168),'Overwrite erases all VMU'),((180,168,256,192),'Overwrite'),((0,192,128,212),'exists.'),((0,212,184,232),'game data.'),((0,232,56,256),'it?')]:
    add(a,16,rect,text,height=14)
for rect,text in [((0,0,52,32),'Yes'),((52,0,128,32),'No'),((0,32,44,56),'Yes'),((44,32,112,56),'No'),((0,64,256,88),'Saving needs 14 free blocks.'),((0,96,96,120),''),((0,128,208,152),''),((0,168,256,192),'Accessing memory card...'),((0,192,256,216),'Do not turn off power.'),((0,224,256,248),'Downloading...')]:
    add(a,17,rect,text)
for rect,text in [((0,48,144,80),'Resume Practice'),((0,96,144,128),'Title Menu'),((32,144,104,176),'Join'),((152,144,232,176),'Rejoin')]:
    add(b,0,rect,text)
for rect,text in [((128,40,256,64),'Not enough free space.'),((0,68,256,92),'Saving needs 14 free blocks.'),((0,96,112,120),''),((0,124,208,148),''),((64,164,256,188),'Accessing memory card...'),((0,196,120,220),'')]:
    add(b,1,rect,text)
add(b,2,(156,6,228,30),'Height','panel-yellow')
add(b,2,(156,40,228,64),'Weight','panel-yellow')
add(b,3,(8,4,72,32),'Port','orange',20)
for rect,text in [((0,0,256,24),'WARNING: Delete wrestler'),((0,24,256,48),'and exit Create-A-Wrestler?'),((0,48,152,72),'from the VMU'),((0,72,232,96),'Are you sure?'),((0,128,256,152),'Exit Create-A-Wrestler?'),((0,160,192,184),'Are you sure?'),((0,192,48,216),'Yes'),((64,192,136,216),'No'),((0,224,256,240),'(Remember to save'),((0,240,96,256),'your data.)')]:
    add(b,5,rect,text,'yellow' if rect[1]>=224 else 'white',14 if rect[1]>=224 else 18)
rows(b,6,0,256,0,32,['Overwrite this slot?','Are you sure?','Load this wrestler?','Are you sure?','Retire this wrestler?','Are you sure?','Save in this slot?'],height=18)
add(b,8,(0,64,48,88),'Traits','yellow',16)
add(b,8,(48,64,216,88),'Easily Learned Moves','yellow',16)
rows(b,8,0,256,88,24,['Choose an appearance.','Damage Focus'])
add(b,8,(0,136,128,160),'Submission Focus')
add(b,8,(128,136,256,160),'Standing Focus')
rows(b,8,0,256,160,24,['Power Throws','Big Moves','Strikes','Technical Throws'])
rows(b,10,0,256,0,32,['Are you sure?','No created-wrestler file.','Choose again.'],height=18)
add(b,10,(52,120,112,148),'Select','yellow',16)
add(b,10,(144,120,224,148),'Confirm','yellow',16)
add(b,10,(0,160,60,188),'Back','yellow',16)
add(b,11,(0,0,180,58),'Shop','outline',38)
add(b,11,(8,204,60,230),'Level','gray',14)
for rect,text in [((60,0,128,32),'Mask'),((136,0,208,32),'Chest'),((76,32,112,64),'Elbow'),((136,32,208,64),'Wrist'),((76,64,112,96),'Waist'),((148,64,184,96),'Knee'),((76,96,112,128),'Feet')]:
    add(b,13,rect,text,'yellow',18)
add(b,15,(0,48,64,72),'Exit',height=18)
rows(b,16,0,256,48,24,['Enter a surname.','Enter a first name.'],height=18)
add(b,18,(0,192,224,256),'Move Fusion','outline',40)
rows(b,19,96,240,0,32,['Unique Counters','Outside Moves','Tag Moves','Double Team','Taunt','Knuckle Lock'],'yellow')
add(b,19,(0,192,208,256),'Delete Moves','outline',38)
rows(b,20,0,80,144,24,['ABC / Other'],height=14)
add(b,20,(80,144,160,168),'Cancel',height=14)
add(b,20,(160,144,256,168),'Confirm',height=14)
add(b,21,(10,8,256,30),'Choose a catchphrase.','panel',18)
add(b,21,(0,54,28,78),'','panel')
add(b,22,(0,168,200,232),'Body Type','outline',40)
rows(b,23,0,192,0,24,["Add 'no'","Omit 'no'"],height=18)
add(b,23,(0,48,192,104),'Status','outline',38)
add(b,23,(0,202,56,232),'Move List','yellow',14)
add(b,23,(110,202,202,232),'Scroll','yellow',16)
add(b,24,(8,14,72,42),'Signature','panel-yellow',14)
add(b,24,(48,144,256,208),'Locker Room','outline',38)
add(b,25,(6,4,240,30),'Total Training Time','panel-yellow',18)
for y,left,right in [(68,'Level','Spirit'),(98,'Popularity','Friendship'),(128,'Power','Type'),(154,'Stamina','Progress')]:
    add(b,25,(8,y,84,y+26),left,'yellow')
    add(b,25,(88,y,168,y+26),right,'yellow')
for i,name in enumerate(['STR','THR','SUB','CTR']): add(b,25,(i*32,184,(i+1)*32,218),name,'yellow',14)
rows(b,26,0,128,0,24,['Striker','Suplex'],height=18)
rows(b,26,128,256,0,24,['Technician','Comedy'],height=18)
add(b,26,(0,152,192,216),'Move List','outline',38)
rows(b,28,0,112,80,32,['Strikes','Front Moves','Side Moves','Rear Moves','Setups'],'yellow')
add(b,28,(128,228,256,256),'Burning Moves','yellow',18)
rows(b,29,0,136,0,32,['Hammer Throw','Ground Moves','Apron Moves','Outside Dives'],'yellow')
add(b,29,(0,216,96,248),'Scroll','yellow')
rows(b,29,136,256,0,32,['Signature 1','Signature 2','Locker Room'],'yellow',18)
for rect,text in [((136,96,256,128),'Burning Start'),((136,128,256,156),'Status'),((136,156,256,184),'Move List'),((128,188,256,216),'Winner Interview'),((128,216,256,248),'Intro Comment')]:add(b,29,rect,text,'yellow',18)
add(b,30,(0,0,256,62),'Training Match','outline',38)
add(b,30,(8,70,256,94),'Choose an opponent.','panel',18)
add(b,30,(0,116,16,144),'','panel')
add(b,30,(96,184,256,248),'Tactics','outline',38)
add(b,33,(12,8,256,30),'Use this wrestler?','panel',18)
add(b,33,(0,54,80,78),'','panel')
add(b,33,(0,96,52,120),'Yes')
add(b,33,(60,96,136,122),'No')
add(b,33,(0,120,120,144),'')
add(b,33,(144,152,256,184),'Retired.')
add(b,33,(0,184,40,216),'')
for tile,items in {
34:[((72,0,256,24),'Not enough free blocks.'),((0,32,256,56),'Saving needs ?? free blocks.'),((0,56,120,80),''),((0,88,208,112),''),((28,120,256,144),'No data available to load.'),((0,152,144,176),''),((48,184,256,208),'Load failed.'),((0,216,144,240),'')],
35:[((48,0,256,24),'Save failed.'),((0,32,144,56),''),((48,64,256,88),'Load failed.'),((0,96,144,120),''),((56,128,256,152),'Retire failed.'),((0,160,144,184),''),((32,208,224,240),'Loaded.')],
36:[((0,0,256,24),'No wrestler to retire.'),((0,32,200,56),''),((0,64,256,88),'No created wrestler to load.'),((0,96,208,120),''),((0,128,256,152),'Memory card not recognized.'),((0,160,176,184),''),((32,208,224,240),'Saved.')],
37:[((0,184,256,208),'Choose a face type.'),((0,208,72,232),'')],
38:[((100,120,256,144),'Giant Channel'),((24,144,256,168),'could not be loaded.'),((0,176,144,200),''),((0,200,232,224),'')],
40:[((0,120,256,144),'Choose a save slot.'),((0,144,120,168),''),((0,168,256,192),'Choose a wrestler to load.'),((0,192,120,216),''),((0,216,256,240),'Choose a wrestler to retire.')],
45:[((0,0,256,24),'This name contains words'),((0,24,256,48),'that cannot display correctly'),((0,48,96,72),'Continue?'),((160,80,216,104),'Yes'),((248,80,256,104),''),((0,112,256,136),'in the arcade version.'),((0,136,256,160),'Continue anyway?'),((0,184,72,208),'No')]
}.items():
    for rect,text in items:add(b,tile,rect,text,height=18)
rows(b,39,0,160,0,64,['Save','Load','Retire'],'outline',42)
add(b,39,(40,194,144,216),'Total Training Time','orange',14)
rows(b,41,16,96,48,32,['Training','Save','Retire'])
rows(b,41,104,208,48,32,['Shop','Load','Suspend'])
add(b,41,(0,160,120,184),'')
add(b,43,(0,170,192,240),'Quotes','outline',40)
add(b,46,(20,8,88,34),'Port','orange',20)

# Texture rows are packed tightly and several messages wrap to a later row.
# Use measured ink bounds, not a uniform grid, for these fragments.
def bounds(file,tile,rects):
    assert len(rects)==len(SPECS[file,tile])
    SPECS[file,tile]=[(rect,*record[1:]) for rect,record in zip(rects,SPECS[file,tile])]

bounds(a,16,[(184,2,256,22),(136,24,256,42),(168,44,256,62),(0,68,104,86),(0,88,168,106),(0,108,152,126),(92,130,256,150),(34,150,256,170),(172,170,256,192),(0,194,128,214),(0,214,184,234),(0,236,56,254)])
# The second warning is one sentence over four atlas fragments.
r=SPECS[a,16]
r[1]=(r[1][0],'Saving needs 14',*r[1][2:])
r[2]=(r[2][0],'memory card.',*r[2][2:])
r[4]=(r[4][0],'free blocks on a',*r[4][2:])
r[5]=(r[5][0],'',*r[5][2:])
bounds(a,17,[(0,0,52,28),(52,0,132,28),(0,32,44,56),(44,32,112,56),(0,66,256,94),(0,96,96,122),(0,124,208,152),(0,166,256,192),(0,194,256,220),(0,222,256,248)])
bounds(b,0,[(8,52,140,86),(0,100,150,134),(40,148,108,180),(156,148,256,180)])
bounds(b,1,[(128,38,256,66),(0,68,256,94),(0,96,112,122),(0,124,208,152),(56,160,256,190),(0,194,148,222)])
bounds(b,5,[(0,2,256,28),(0,28,256,54),(0,58,152,84),(0,86,232,110),(0,130,256,158),(0,162,192,190),(0,194,52,220),(56,194,136,220),(0,222,256,240),(0,240,96,256)])
bounds(b,8,[(0,54,48,80),(48,54,208,80),(32,80,256,104),(32,104,164,128),(0,128,128,152),(128,128,240,152),(0,152,176,176),(0,174,56,198),(0,200,72,224),(0,222,192,246)])
bounds(b,34,[(72,0,256,26),(0,28,256,56),(0,56,136,82),(0,84,212,114),(28,116,256,144),(0,148,152,176),(48,180,256,208),(0,212,148,240)])
bounds(b,35,[(48,2,256,30),(0,34,144,62),(48,66,256,94),(0,98,144,126),(52,130,256,158),(0,162,144,190),(32,212,224,242)])
bounds(b,36,[(0,0,256,30),(0,32,200,62),(0,64,256,94),(0,96,208,126),(40,128,256,158),(0,160,176,190),(32,212,224,242)])
bounds(b,37,[(0,166,256,190),(0,192,72,214)])
bounds(b,38,[(96,112,256,140),(20,140,256,168),(0,168,144,196),(0,196,232,224)])
bounds(b,45,[(0,4,256,28),(0,28,256,50),(0,50,96,72),(160,76,216,100),(248,76,256,100),(0,108,256,132),(0,132,256,156),(0,180,72,204)])
bounds(b,39,[(0,0,170,64),(0,64,170,128),(0,128,170,190),(40,194,146,218)])
r=SPECS[b,45]
r[1]=(r[1][0],'in the arcade version.',*r[1][2:])
r[2]=(r[2][0],'',*r[2][2:])
r[5]=(r[5][0],'that cannot display correctly',*r[5][2:])
# Keep the two numeric placeholders at their original locations for runtime digits.
r=SPECS[b,34]
r[1]=((0,28,156,56),'Saving needs','white',18)
r.insert(2,((196,28,256,56),'free blocks.','white',18))

def main():
    OUT.mkdir(exist_ok=True)
    names=list(dict.fromkeys(r[1] for rs in SPECS.values() for r in rs if r[1]))
    if len(sys.argv)==1:
        batches=[names[i:i+40] for i in range(0,len(names),40)]
        (OUT/'label_batches.json').write_text(json.dumps(batches,indent=2))
        print(json.dumps(batches));return
    batches=json.loads((OUT/'label_batches.json').read_text())
    labels={}
    for i,batch in enumerate(batches):
        # Extract the white letter interiors; generated sheets have a gray backdrop.
        rgb=np.asarray(Image.open(OUT/f'labels_{i}.png').convert('RGB'))
        alpha=np.clip((rgb.min(axis=2).astype(float)-220)*255/25,0,255).astype('uint8')
        clean=OUT/f'labels_{i}_mask.png'
        Image.fromarray(np.repeat(alpha[:,:,None],3,axis=2)).save(clean)
        labels.update(read_labels(clean,[batch[:20],batch[20:]] if len(batch)>20 else [batch]))
    for name,source,from_end in [('Saving needs','Saving needs 14',1),('free blocks.','Saving needs ?? free blocks.',2)]:
        art=labels[source];empty=np.flatnonzero(np.asarray(art.getchannel('A')).max(0)==0)
        gaps=[g for g in np.split(empty,np.where(np.diff(empty)>1)[0]+1) if len(g)>=9 and g[0]>0 and g[-1]<art.width-1]
        boundary=int(gaps[-from_end][0])
        labels[name]=art.crop((0,0,boundary,art.height)) if name=='Saving needs' else art.crop((int(gaps[-from_end][-1])+1,0,art.width,art.height))
    shutil.copytree(ROOT/'English_Pause/TEX',OUT/'TEX',dirs_exist_ok=True)
    baseline=(ROOT/'English_Pause/TEX.AFS').read_bytes()
    archive=bytearray(baseline)
    entries=[struct.unpack_from('<II',baseline,8+i*8) for i in range(struct.unpack_from('<I',baseline,4)[0])]
    changes=[];previews=[]
    for file in [a,b]:
        source=(ROOT/'TEX'/file).read_bytes(); edited=bytearray(source)
        start=next(off for off,size in entries if size==len(source) and baseline[off:off+size]==source)
        for (filename,tile),records in SPECS.items():
            if filename!=file:continue
            original=source[tile*SIZE:(tile+1)*SIZE]
            old=decode(original);target=old.copy();mask=Image.new('1',(256,256));md=ImageDraw.Draw(mask)
            for rect,name,style,height in records:
                x0,y0,x1,y1=rect
                bg=(0,0,0,0)
                if style in ('orange','gray','panel','panel-yellow'):
                    pixels=np.asarray(old.crop(rect));colors,counts=np.unique(pixels.reshape(-1,4),axis=0,return_counts=True)
                    bg=tuple(int(v) for v in colors[counts.argmax()])
                    if style=='orange':bg=old.getpixel((10,200) if tile==39 else (10,12))
                target.paste(bg,rect)
                if name:
                    art=labels[name]
                    px=np.asarray(old.crop(rect))
                    foreground=(px[:,:,3]>100)&((px[:,:,:3].min(2)>170) if style=='orange' else (px[:,:,:3].max(2)>160))
                    yy,xx=np.nonzero(foreground)
                    bx,by,ex,ey=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1) if len(xx) else (2,2,x1-x0-2,y1-y0-2)
                    h=min(height,ey-by);w=min(ex-bx,max(1,round(art.width*h/art.height)))
                    alpha=art.getchannel('A').resize((w,h),Image.Resampling.LANCZOS)
                    ink=Image.new('RGBA',(w,h),(255,255,0,255) if style in ('yellow','outline','panel-yellow') else (255,255,255,255));ink.putalpha(alpha)
                    pos=(x0+bx+(ex-bx-w)//2,y0+by+(ey-by-h)//2)
                    target.alpha_composite(ink,pos)
                md.rectangle((x0,y0,x1-1,y1-1),fill=1)
            touched=np.asarray(mask).reshape(128,2,128,2).any(axis=(1,3))[::-1]
            adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted)
            block=bytearray(adapted)
            for y,x in zip(*np.nonzero(touched)):
                pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
            final=decode(block)
            outside=~np.repeat(np.repeat(touched[::-1],2,axis=0),2,axis=1)
            assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
            if file==b and tile==34:
                assert np.array_equal(np.asarray(old)[28:56,156:196],np.asarray(final)[28:56,156:196])
            edited[tile*SIZE:(tile+1)*SIZE]=block
            archive[start+tile*SIZE:start+(tile+1)*SIZE]=block
            final.save(OUT/f'{Path(file).stem}_{tile}.png')
            target.save(OUT/f'{Path(file).stem}_{tile}_target.png')
            preview=Image.new('RGBA',(256,256),'black');preview.alpha_composite(final)
            previews.append((f'{file} / {tile}',preview.convert('RGB')))
            changes.append({'file':file,'tile':tile,'offset':start+tile*SIZE,'labels':records})
        (OUT/'TEX'/file).write_bytes(edited)
    cursor=0
    for c in sorted(changes,key=lambda c:c['offset']):
        assert archive[cursor:c['offset']]==baseline[cursor:c['offset']]
        cursor=c['offset']+SIZE
    assert archive[cursor:]==baseline[cursor:] and len(archive)==len(baseline)
    (OUT/'TEX.AFS').write_bytes(archive)
    for page in range((len(previews)+7)//8):
        group=previews[page*8:(page+1)*8];sheet=Image.new('RGB',(768,((len(group)+2)//3)*280),(30,30,30));d=ImageDraw.Draw(sheet)
        for i,(name,im) in enumerate(group):
            x,y=i%3*256,i//3*280;sheet.paste(im,(x,y));d.text((x+4,y+260),name,fill='white')
        sheet.resize((1536,sheet.height*2),Image.Resampling.NEAREST).save(OUT/f'preview_{page+1}.png')
    report={'base':'English_Pause/TEX.AFS','earlier_patches_preserved':True,'unmodified_cells_identical':True,'archive_size_unchanged':True,'in_game_tested':False,'sha256':hashlib.sha256(archive).hexdigest(),'changes':changes}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Patched {len(changes)} texture blocks with {len(names)} unique labels.')

if __name__=='__main__':main()
