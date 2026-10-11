"""Fit generated English headings into the three existing venue-card textures."""
from pathlib import Path
import json, shutil, sys
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parent
G = R.parent
sys.path.insert(0, str(G/'scripts'))
from extract_main_menu import decode, spread, SIZE
from patch_options import adapt_codebook
from patch_english_menu import encode

backup = R / 'before-venue-cards'
backup.mkdir(exist_ok=True)
source = G / 'TEX/spr_sel3.bin'
if not (backup / source.name).exists():
    shutil.copy2(source, backup / source.name)
original = (backup / source.name).read_bytes()
sheet = R / 'venue-labels-source.png'
if not sheet.exists():
    shutil.copy2(Path('private_inputs/venue-labels-input.png'), sheet)
art = Image.open(sheet).convert('RGBA')
labels = [art.crop(box) for box in [(417,60,1357,281), (505,347,1253,572), (28,626,1196,831), (1200,626,1741,831)]]
# The two italic words meet along a diagonal in the source sheet. A vertical
# crop clips the A and carries its left outline into the end of UNDERGROUND.
bottom = np.array(art.crop((0,610,art.width,850)))
yy,xx = np.indices(bottom.shape[:2])
split = 1205 - 0.30 * (yy + 610 - 626)
for index,keep in [(2,xx < split),(3,xx >= split)]:
    pixels = bottom.copy()
    pixels[:,:,3] = np.where(keep & (pixels[:,:,3] >= 128),pixels[:,:,3],0)
    if index == 3:
        # Follow the A's own outer edge; the adjacent D's outline crosses the
        # old separator lower down. Preserve the A's pale outline in full.
        excess = xx < (1214 - 0.35 * (yy + 610 - 650))
        pixels[excess,3] = 0
        assert not pixels[excess,3].any()
    label = Image.fromarray(pixels)
    labels[index] = label.crop(label.getbbox())
preview = Image.new('RGBA', (194*3,256), (24,20,34,255))
patches = []
for row, tile in enumerate((18,19,20)):
    block = original[tile*SIZE:(tile+1)*SIZE]
    old = decode(block)
    target = old.copy()
    # Preserve the side rails and all venue photography below the heading.
    target.paste((0,0,0,0), (0,0,194,24))
    target.paste((0,0,0,255), (16,24,180,66))
    # Reuse the original frame's pixel rows, including its four-pixel inner
    # highlight at y=34..37; the earlier reconstruction was two pixels high.
    frame = decode(original[18*SIZE:19*SIZE])
    for y in range(24,31):
        target.paste(old.getpixel((12,y)), (16,y,180,y+1))
    for y in range(31,40):
        target.paste(frame.getpixel((22,y)), (20,y,174,y+1))
    target.paste(frame.crop((16,31,20,42)), (16,31))
    target.paste(frame.crop((174,31,180,42)), (174,31))
    if row == 2:
        # The original right corner contains title cutouts. Mirror the intact
        # left frame before compositing the English heading to close both gaps.
        corner = target.crop((0,24,24,48)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        target.paste(corner, (170,24))
    assert target.getpixel((40,36)) == frame.getpixel((22,36))
    assert target.getpixel((40,34)) == frame.getpixel((22,34))
    if row < 2:
        label = labels[row].resize((166,48), Image.Resampling.LANCZOS)
        target.alpha_composite(label, (14,6))
    else:
        # Two lines keep the longer translation readable at native resolution.
        target.alpha_composite(labels[2].resize((174,25),Image.Resampling.LANCZOS),(10,3))
        target.alpha_composite(labels[3].resize((80,25),Image.Resampling.LANCZOS),(57,29))
        # Remove the generated label's stray right-edge pixels beside the D.
        # These overlay the repaired frame, so clean them after compositing.
        target.paste((136,238,221,255), (180,24,184,28))
    mask = np.zeros((256,256),bool)
    mask[:66,:194] = True
    touched = mask.reshape(128,2,128,2).any(axis=(1,3))[::-1]
    adapted = adapt_codebook(target,block,touched,'4444')
    encoded = encode(target,adapted)
    result = bytearray(adapted)
    for y,x in zip(*np.nonzero(touched)):
        address = 2048 + spread(int(y)) + (spread(int(x)) << 1)
        result[address] = encoded[address]
    final = decode(result)
    if row == 2:
        repaired = np.asarray(final)[24:28,180:184]
        assert (repaired[:,:,1] >= 200).all() and (repaired[:,:,3] == 255).all(), 'Teal gap remains'
    assert np.array_equal(np.asarray(final)[~mask],np.asarray(old)[~mask]), 'Unrelated artwork changed'
    assert len(result) == SIZE
    name = f'venue-spr_sel3-{tile}.bin'
    (R/name).write_bytes(result)
    final.save(R/f'venue-card-{tile}.png')
    preview.alpha_composite(final.crop((0,0,194,256)),(row*194,0))
    patches.append([4046848+tile*SIZE,name])
(R/'venue-texture-patches.json').write_text(json.dumps(patches),encoding='utf-8')
preview.resize((1164,512),Image.Resampling.NEAREST).save(R/'venue-cards-preview.png')
print('Prepared three venue cards; all pixels outside header regions are unchanged.')
