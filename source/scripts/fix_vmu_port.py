from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parent;G=R.parent
sys.path.insert(0,str(G/'scripts'))
from extract_main_menu import SIZE,decode,spread
from patch_options import adapt_codebook
from patch_english_menu import encode
off=8312832+46*SIZE
backup=R/'port-before.bin'
if not backup.exists():backup.write_bytes((G/'TEX.AFS').read_bytes()[off:off+SIZE])
block=backup.read_bytes();old=decode(block);im=old.copy()
rect=(20,8,88,34);x0,y0,x1,y1=rect
# The untouched top band contains the same column-wise orange highlight.
for x in range(x0,x1):
 im.paste(old.getpixel((x,4)),(x,y0,x+1,y1))
face=old.crop(rect).getchannel('B').point(lambda b:round(max(0,b-17)*255/238))
edge=face.filter(ImageFilter.MaxFilter(3))
ink=Image.new('RGBA',face.size,'black');ink.putalpha(edge);im.alpha_composite(ink,(x0,y0))
ink=Image.new('RGBA',face.size,'white');ink.putalpha(face);im.alpha_composite(ink,(x0,y0))
mask=np.zeros((256,256),bool);mask[y0:y1,x0:x1]=True
touched=mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
adapted=adapt_codebook(im,block,touched,'4444');encoded=encode(im,adapted);out=bytearray(adapted)
for y,x in zip(*np.nonzero(touched)):
 p=2048+spread(int(y))+(spread(int(x))<<1);out[p]=encoded[p]
final=decode(out)
assert np.array_equal(np.asarray(final)[~mask],np.asarray(old)[~mask])
(R/'vmu-port-fixed.bin').write_bytes(out)
(R/'vmu-port-texture-patches.json').write_text(json.dumps([[off,'vmu-port-fixed.bin']]))
final.crop((0,0,140,38)).resize((840,228),Image.Resampling.NEAREST).save(R/'vmu-port-fixed.png')
print('Port background and outline repaired; all pixels outside the label preserved.')
