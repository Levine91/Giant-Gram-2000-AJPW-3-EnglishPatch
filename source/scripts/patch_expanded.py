"""Pause, tournament, Backup/loading localization plus runtime wrestler names."""
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageDraw
from extract_main_menu import ROOT,SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
from polish_menus import generated,sized,PAUSE

OUT=ROOT/'English_Expanded'
BASE=ROOT/'English_Main_Menu_Final'
GOLD=['Resume Match','Wrestler Select','Match Type Selection','Main Menu','Match Select','Opponent Position','Opponent State','Restore Stamina','Boost Spirit','Back','Select','Confirm','Resume Practice','End Practice','Choose match type and players','Choose amount of participants','Move Cursor','Select Wrestler','Change Player','Loading... Please wait.']
WHITE=['Confirm these participants?','Save','Load','Choose where to save.','Choose where to load.','Save in this slot?','Load this file?','Are you sure?','Not enough free space.','14 free blocks are required.','Save completed.','Load completed.','Saving failed.','Loading failed.','No file found.','Choose again.','Accessing memory card...','Do not turn off the power.','Yes','No','Port A','Port B','Port C','Port D']
RUNTIME_NAMES=['Random','Giant Baba','Mitsuharu Misawa','Toshiaki Kawada','Akira Taue','Kenta Kobashi','Jun Akiyama','Stan Hansen','Vader','Gary Albright','Johnny Ace','Hiroshi Hase','Wolf Hawkfield','Grace','Hyper','Diablo','Kyohei Wada','Wolf Hawkfield','Jeffry McWild','Kage-Maru','Tiger','Takao Omori','Yoshihiro Takayama','Mike Barton','Yoshinari Ogawa','Tamon Honda','Masahito Kakihara','Kentaro Shiga','Johnny Smith','Maunakea Mossman','Jumbo Tsuruta','Ogami Kongo','Sky High Edge','Super Tigre Dos Mil','Young Giant Baba','The Master A.M.','Mangler D.H.','Cyclops E.C.','The Killer B.I.','Rikidozan','Steve Williams','Bruno Sammartino','Gene Kiniski','Don Leo Jonathan','Giant Crusher','Bruiser Brody','The Crusher','The Destroyer','Dick the Bruiser','Crusher Lisowski','Fritz Von Erich','Bobo Brazil','Dynamite Kid','VM-1','VM-2','VM-3','VM-4','Champion 1','Champion 2','Champion 3']

def patch_program():
    original=(ROOT/'1ST_READ.BIN').read_bytes();data=bytearray(original)
    table=0x1209e0;stride=26;ptrtable=0x11ced4;records=[]
    assert len(RUNTIME_NAMES)==60
    assert original[table:table+10].decode('cp932')=='　ランダム'
    for i,name in enumerate(RUNTIME_NAMES):
        start=table+i*stride;old=original[start:start+stride]
        assert b'\0' in old
        english=name.encode('ascii')
        assert len(english)<stride
        data[start:start+stride]=english+b'\0'*(stride-len(english))
        # The HUD lookup table uses the same roster order. Point actual wrestlers
        # at the translated fixed-width strings; preserve placeholder entries.
        ptrpos=ptrtable+i*4;pointer=struct.unpack_from('<I',original,ptrpos)[0]
        redirected=False
        if i not in [0,16] and i<53:
            assert 0x8c102f28<=pointer<=0x8c1031e4
            struct.pack_into('<I',data,ptrpos,0x8c010000+start);redirected=True
        records.append({'index':i,'old':old.split(b'\0')[0].decode('cp932'),'name':name,'offset':start,'hud_pointer_redirected':redirected})
    changed=np.frombuffer(original,dtype='uint8')!=np.frombuffer(data,dtype='uint8')
    allowed=np.zeros(len(data),dtype=bool);allowed[table:table+60*stride]=True
    for i in range(1,53):
        if i!=16:allowed[ptrtable+i*4:ptrtable+i*4+4]=True
    assert not np.any(changed&~allowed) and len(data)==len(original)
    for i,name in enumerate(RUNTIME_NAMES):
        assert data[table+i*stride:table+(i+1)*stride].split(b'\0')[0].decode('ascii')==name
    (OUT/'1ST_READ.BIN').write_bytes(data)
    return {'sha256':hashlib.sha256(data).hexdigest(),'original_sha256':hashlib.sha256(original).hexdigest(),'size_unchanged':True,'only_name_data_changed':True,'records':records}

def main():
    sheet=Image.open(OUT/'labels_0.png').convert('RGBA')
    # The generated columns have unequal widths; split in their actual gutter.
    split=700;column=max(split,sheet.width-split)
    balanced=Image.new('RGBA',(column*2,sheet.height))
    balanced.paste(sheet.crop((0,0,split,sheet.height)),(0,0))
    balanced.paste(sheet.crop((split,0,sheet.width,sheet.height)),(column,0))
    balanced.save(OUT/'labels_balanced.png')
    labels=generated(OUT/'labels_balanced.png',GOLD,2)
    labels.update(generated(OUT/'labels_1.png',WHITE,2))
    old_labels=generated(ROOT/'English_Menu_Polish/labels_1.png',PAUSE,2)
    labels.update({n:old_labels[n] for n in ['Match Settings','Player Select']})
    base=(BASE/'TEX.AFS').read_bytes();archive=bytearray(base)
    entries=[struct.unpack_from('<II',base,8+i*8) for i in range(struct.unpack_from('<I',base,4)[0])]
    files={};changes=[];previews=[]
    jobs={}
    def add(file,tile,rect,name,cap=12,style='native',align='center',background=None,clear=None):
        jobs.setdefault((file,tile),[]).append({'parts':[rect],'name':name,'cap':cap,'style':style,'align':align,'background':background,'clear':clear})
    def stitch(file,tile,parts,name,cap=14,style='native',background=None):
        jobs.setdefault((file,tile),[]).append({'parts':parts,'name':name,'cap':cap,'style':style,'align':'center','background':background,'clear':None})
    # Resume's sampled UV starts after the atlas's left padding. Keep its ink
    # inside that span instead of centering it over x=0..120.
    for f in ['spr_gam.bin','spr_gam5.bin']:
        add(f,9,(12,0,120,24),'Resume Match',10,clear=(0,0,120,24))
        for y,n in [(176,'Wrestler Select'),(200,'Match Type Selection' if f=='spr_gam.bin' else 'Match Select'),(224,'Main Menu')]:add(f,9,(8,y,168,y+24),n,10,clear=(0,y,176,y+24))
        for rect,n in [((0,48,176,72),'Opponent Position'),((0,72,176,96),'Opponent State'),((24,100,148,124),'Restore Stamina'),((30,132,114,156),'Boost Spirit'),((148,132,208,156),'Back'),((28,164,88,188),'Select'),((120,164,200,188),'Confirm'),((32,192,144,216),'Resume Match')]:add(f,12,rect,n,10)
        add(f,13,(0,0,176,24),'Resume Practice',10)
        add(f,13,(0,24,176,48),'End Practice',10)
    for i,n in enumerate(['Resume Match','Match Settings','Player Select','Main Menu']):
        add('spr_gam2.bin',38,(0,136+i*32,144,152+i*32),n,10,'white',clear=(0,128+i*32,152,160+i*32))
    add('spr_cmk2.bin',0,(0,96,144,128),'Main Menu',16,'white')
    # These phrases wrap across atlas rows but appear as single screen lines.
    stitch('spr_sel.bin',4,[(0,32,256,64),(0,64,136,96)],'Choose match type and players',14)
    stitch('spr_sel.bin',8,[(112,32,256,64),(0,64,112,96)],'Choose amount of participants',14)
    panel=(17,0,51,170)
    for y,n in [(42,'Move Cursor'),(70,'Select Wrestler'),(98,'Change Player')]:
        add('spr_sel3.bin',10,(72,y,208,y+26),n,14,align='left',background=panel,clear=(68,y,256 if y==98 else 208,y+30 if y==98 else y+26))
    stitch('spr_sel3.bin',9,[(88,12,256,36),(64,68,232,92)],'Confirm these participants?',16,'native',panel)
    stitch('spr_sys.bin',5,[(0,144,256,160),(0,160,48,176)],'Loading... Please wait.',10,'white')
    # Backup menu choices, prompts, and related save/load dialogs.
    add('spr_tit.bin',40,(0,208,256,224),'Choose where to save.',11,clear=(0,208,256,240))
    add('spr_tit.bin',40,(0,240,256,256),'Choose where to load.',11)
    for tile,specs in [(41,[((16,0,256,32),'Save in this slot?'),((0,32,176,64),'Are you sure?'),((16,64,256,96),'Not enough free space.'),((16,96,256,128),'14 free blocks are required.'),((56,192,256,224),'Saving failed.')]),(42,[((0,0,256,32),'Load this file?'),((0,32,176,64),'Are you sure?'),((56,64,256,96),'Loading failed.'),((16,128,256,160),'No file found.'),((0,192,176,224),'Choose again.')])]:
        for rect,n in specs:add('spr_tit.bin',tile,rect,n,14)
    # Shared access and confirmation labels are also used by Backup.
    for rect,n in [((0,0,56,32),'Yes'),((56,0,136,32),'No'),((0,32,48,64),'Yes'),((48,32,112,64),'No'),((0,168,256,192),'Accessing memory card...'),((0,192,256,216),'Do not turn off the power.')]:add('spr_tit.bin',19,rect,n,12)
    for i,n in enumerate(['Port A','Port B','Port C','Port D']):
        x=(i%2)*96;y=48+(i//2)*24
        add('spr_tit.bin',31,(x,y,x+80,y+24),n,12,clear=(x,y,x+96,y+24))
    jobs[('spr_sel3.bin',8)]=[]
    changes=[]
    for (file,tile),specs in jobs.items():
        if file not in files:
            p=BASE/'TEX'/file
            source=p.read_bytes() if p.exists() else (ROOT/'TEX'/file).read_bytes()
            entry=next(o for o,n in entries if n==len(source) and base[o:o+n]==source)
            files[file]=(entry,bytearray(source))
        entry,sprite=files[file];original=bytes(sprite[tile*SIZE:(tile+1)*SIZE]);old=decode(original)
        target=old.copy();mask=np.zeros((256,256),dtype=bool);records=[]
        def clear(rect,bg=None):
            x0,y0,x1,y1=rect;target.paste(bg or (0,0,0,0),rect);mask[y0:y1,x0:x1]=True
        if file=='spr_tit.bin' and tile in [41,42]:clear((0,0,256,256))
        for spec in specs:
            parts=spec['parts'];n=spec['name'];cap=spec['cap']
            width=sum(r[2]-r[0] for r in parts);height=min(r[3]-r[1] for r in parts)
            art,top=sized(labels[n],cap)
            while art.width>width-6 or art.height>height-2:
                cap-=1;art,top=sized(labels[n],cap)
            assert cap>=8,(n,cap,width,height)
            if spec['style']=='white':
                a=np.asarray(art).copy();v=np.minimum(255,a[:,:,0].astype(float)*255/229).astype('uint8');a[:,:,:3]=v[:,:,None];art=Image.fromarray(a)
            strip=Image.new('RGBA',(width,height),spec['background'] or (0,0,0,0))
            x=2 if spec['align']=='left' else (width-art.width)//2
            y=max(0,(height-cap)//2-top);y=min(y,height-art.height)
            strip.alpha_composite(art,(x,y))
            if spec['clear']:clear(spec['clear'],spec['background'])
            cursor=0
            for rect in parts:
                clear(rect,spec['background']);x0,y0,x1,y1=rect;w=x1-x0
                target.paste(strip.crop((cursor,0,cursor+w,height)),(x0,y0));cursor+=w
            records.append({'text':n,'parts':parts,'cap_height':cap,'alignment':spec['align'],'logical_width':width,'ink_position':[x,y],'ink_size':art.size})
        if file=='spr_sel3.bin' and tile==8:
            clear((0,0,256,256))
            for y,number in [(0,6),(72,7),(144,9)]:
                art=Image.open(ROOT/f'English_VS/badge_{number}.png').convert('RGBA');a=np.asarray(art.getchannel('A')).copy();a[a<30]=0;art.putalpha(Image.fromarray(a));art=art.crop(art.getbbox())
                art=art.resize((176,60),Image.Resampling.LANCZOS);target.alpha_composite(art,(0,y))
                records.append({'badge':number,'rectangle':[0,y,176,y+60],'correct_atlas_pitch':72})
        if file=='spr_tit.bin' and tile==40:
            sheet=Image.open(OUT/'buttons.png').convert('RGBA')
            for row in range(2):
                for col in range(2):
                    art=sheet.crop((col*sheet.width//2,row*sheet.height//2,(col+1)*sheet.width//2,(row+1)*sheet.height//2))
                    a=np.asarray(art.getchannel('A')).copy();a[a<30]=0;art.putalpha(Image.fromarray(a));art=art.crop(art.getbbox())
                    x=col*104;y=100+row*40;clear((x,y,x+104,y+32))
                    target.alpha_composite(art.resize((100,30),Image.Resampling.LANCZOS),(x,y))
                    records.append({'button':'Save' if col==0 else 'Load','state':row,'rectangle':[x,y,x+104,y+32]})
        touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
        adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
        for y,x in zip(*np.nonzero(touched)):
            pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
        final=decode(block);outside=~np.repeat(np.repeat(touched[::-1],2,0),2,1)
        assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
        start=entry+tile*SIZE;sprite[tile*SIZE:(tile+1)*SIZE]=block;archive[start:start+SIZE]=block
        final.save(OUT/f'{file[:-4]}_{tile}.png');target.save(OUT/f'{file[:-4]}_{tile}_target.png')
        bg=Image.new('RGBA',(256,256),'#304050');bg.alpha_composite(final);previews.append((f'{file} / {tile}',bg.convert('RGB')))
        changes.append({'file':file,'tile':tile,'offset':start,'labels':records})
    cursor=0
    for c in sorted(changes,key=lambda c:c['offset']):
        assert archive[cursor:c['offset']]==base[cursor:c['offset']];cursor=c['offset']+SIZE
    assert archive[cursor:]==base[cursor:] and len(archive)==len(base)
    shutil.copytree(BASE/'TEX',OUT/'TEX',dirs_exist_ok=True)
    for f,(entry,sprite) in files.items():
        assert archive[entry:entry+len(sprite)]==sprite
        (OUT/'TEX'/f).write_bytes(sprite)
    (OUT/'TEX.AFS').write_bytes(archive)
    for pg in range((len(previews)+5)//6):
        sheet=Image.new('RGB',(768,560),'#222222');d=ImageDraw.Draw(sheet)
        for i,(n,im) in enumerate(previews[pg*6:(pg+1)*6]):
            x=i%3*256;y=i//3*280;sheet.paste(im,(x,y));d.text((x+2,y+258),n,fill='white')
        sheet.resize((1536,1120),Image.Resampling.NEAREST).save(OUT/f'preview_{pg+1}.png')
    program=patch_program()
    report={'base':'English_Main_Menu_Final','sha256':hashlib.sha256(archive).hexdigest(),'unmodified_pixels_identical':True,'unmodified_archive_bytes_identical':True,'archive_size_unchanged':True,'main_menu_preserved':True,'in_game_tested':False,'changes':changes,'program':program}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n')
    print(f'Patched {len(changes)} texture blocks and 60 runtime name slots. Preservation checks passed.')

if __name__=='__main__':main()
