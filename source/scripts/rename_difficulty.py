"""Replace only the options Level label in the corrected cumulative archive."""
import hashlib
import json
import shutil
import struct
import sys
import numpy as np
from PIL import Image
from extract_main_menu import SIZE, decode, spread
from patch_options import adapt_codebook, read_labels
from patch_english_menu import encode
from fix_options_layout import OUT, sized

shutil.copyfile(sys.argv[1],OUT/'difficulty_source.png')
alpha=np.asarray(Image.open(sys.argv[1]).convert('RGBA'))[:,:,3].copy()
alpha[alpha<20]=0
Image.fromarray(np.repeat(alpha[:,:,None],3,2)).save(OUT/'difficulty_mask.png')
art=read_labels(OUT/'difficulty_mask.png',[['Difficulty']])['Difficulty']
report=json.loads((OUT/'verification.json').read_text())
art,top=sized(art,report['label_cap_height'])
assert art.width<=176 and art.height<=15
before=(OUT/'TEX.AFS').read_bytes();archive=bytearray(before)
entry,size=struct.unpack_from('<II',archive,32);offset=entry+22*SIZE
original=bytes(archive[offset:offset+SIZE]);old=decode(original);target=old.copy()
target.paste((0,0,0,0),(0,0,184,16))
ink=Image.new('RGBA',art.size,'white');ink.putalpha(art.getchannel('A'))
target.alpha_composite(ink,(4,1-top))
touched=np.zeros((128,128),bool);touched[120:128,0:92]=True
adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):
    pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
final=decode(block)
outside=~np.repeat(np.repeat(touched[::-1],2,0),2,1)
assert np.array_equal(np.asarray(old)[outside],np.asarray(final)[outside])
archive[offset:offset+SIZE]=block
assert archive[:offset]==before[:offset] and archive[offset+SIZE:]==before[offset+SIZE:]
assert len(archive)==len(before)
(OUT/'TEX.AFS').write_bytes(archive)
(OUT/'TEX/spr_tit.bin').write_bytes(archive[entry:entry+size])
final.save(OUT/'tile_22.png')
layout=Image.open(OUT/'options_layout_preview.png').convert('RGBA')
layout.paste((0,0,32,255),(90,64,458,96))
layout.alpha_composite(final.crop((0,0,184,16)).resize((368,32),Image.Resampling.NEAREST),(90,64))
layout.save(OUT/'options_layout_preview.png')
sheet=Image.open(OUT/'texture_preview.png').convert('RGBA')
bg=Image.new('RGBA',(256,256),'#000020');bg.alpha_composite(final)
sheet.paste(bg.resize((512,512),Image.Resampling.NEAREST),(0,0));sheet.save(OUT/'texture_preview.png')
report['sha256']=hashlib.sha256(archive).hexdigest()
report['difficulty_rename']={'previous_sha256':hashlib.sha256(before).hexdigest(),'all_other_pixels_identical':True,'position':[4,1-top],'size':art.size}
report['changes'][0]['labels'][0].update(text='Difficulty',position=[4,1-top],size=art.size)
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Difficulty patched; all other pixels and archive blocks unchanged.')
