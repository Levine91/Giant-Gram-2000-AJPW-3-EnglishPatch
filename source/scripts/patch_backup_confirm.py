import json,struct
import numpy as np
from PIL import Image
from extract_main_menu import ROOT,SIZE,decode,spread
from patch_options import read_labels,adapt_codebook
from patch_english_menu import encode
from polish_menus import generated,sized
from patch_expanded import WHITE

OUT=ROOT/'English_Runtime_Fixed'
def main():
    batches=json.loads((ROOT/'English_CAW/label_batches.json').read_text());labels={}
    for i,batch in enumerate(batches):
        labels.update(read_labels(ROOT/f'English_CAW/labels_{i}_mask.png',[batch[:20],batch[20:]] if len(batch)>20 else [batch]))
    labels.update(generated(ROOT/'English_Expanded/labels_1.png',WHITE,2))
    sprite=bytearray((OUT/'TEX/spr_tit.bin').read_bytes());old_sprite=bytes(sprite)
    original=bytes(sprite[31*SIZE:32*SIZE]);target=decode(original);mask=np.zeros((256,256),dtype=bool)
    def clear(rect):
        x,y,x1,y1=rect;target.paste((0,0,0,0),rect);mask[y:y1,x:x1]=True
    a,at=sized(labels['Overwrite this slot?'],17);b,bt=sized(labels['Are you sure?'],17)
    strip=Image.new('RGBA',(416,32));w=a.width+b.width+10;x=(416-w)//2
    strip.alpha_composite(a,(x,7-at));strip.alpha_composite(b,(x+a.width+10,7-bt))
    clear((0,96,256,164))
    target.paste(strip.crop((0,0,256,32)),(0,100));target.paste(strip.crop((256,0,416,32)),(0,132))
    for rect,text in [((8,224,72,256),'Yes'),((72,224,160,256),'No')]:
        clear(rect);art,top=sized(labels[text],20);x,y,x1,y1=rect
        target.alpha_composite(art,(x+(x1-x-art.width)//2,y+5-top))
    touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
    adapted=adapt_codebook(target,original,touched,'4444');candidate=encode(target,adapted);block=bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        pos=2048+spread(int(y))+(spread(int(x))<<1);block[pos]=candidate[pos]
    final=decode(block);outside=~np.repeat(np.repeat(touched[::-1],2,0),2,1)
    assert np.array_equal(np.asarray(final)[outside],np.asarray(decode(original))[outside])
    sprite[31*SIZE:32*SIZE]=block
    archive=bytearray((OUT/'TEX.AFS').read_bytes())
    entries=[struct.unpack_from('<II',archive,8+i*8) for i in range(struct.unpack_from('<I',archive,4)[0])]
    entry=next(o for o,n in entries if n==len(sprite) and archive[o:o+n]==old_sprite)
    archive[entry:entry+len(sprite)]=sprite
    (OUT/'TEX.AFS').write_bytes(archive);(OUT/'TEX/spr_tit.bin').write_bytes(sprite)
    bg=Image.new('RGBA',(416,80),'#142030')
    bg.alpha_composite(final.crop((0,100,256,132)),(0,0));bg.alpha_composite(final.crop((0,132,160,164)),(256,0))
    bg.alpha_composite(final.crop((8,224,160,256)),(132,44))
    bg.resize((1248,240),Image.Resampling.NEAREST).save(OUT/'backup_confirm_preview.png')
    print('Backup overwrite confirmation and Yes/No packed; untouched pixels preserved.')
if __name__=='__main__':main()
