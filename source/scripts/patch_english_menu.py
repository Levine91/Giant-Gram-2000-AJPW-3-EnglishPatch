"""Pack generated English labels into the existing Dreamcast VQ texture.

Requires Pillow and NumPy. Originals are read-only; outputs go to English_Menu.
Usage: python patch_english_menu.py labels.png y0,y1,...,y8
The nine pixel coordinates delimit the eight generated label rows.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

import numpy as np
from PIL import Image

from extract_main_menu import ROOT, OFFSET, SIZE, decode, spread


def encode(image, original, pixel_format='4444'):
    # Reuse the original codebook: the untouched Start prompt stays exact.
    words = np.frombuffer(original[:2048], dtype='<u2').reshape(256, 4)
    if pixel_format == '4444':
        colors = np.stack([((words >> 8) & 15)*17, ((words >> 4) & 15)*17,
                           (words & 15)*17, (words >> 12)*17], axis=-1)
    elif pixel_format == '1555':
        colors = np.stack([((words >> 10) & 31)*255//31, ((words >> 5) & 31)*255//31,
                           (words & 31)*255//31, (words >> 15)*255], axis=-1)
    elif pixel_format == '565':
        colors = np.stack([((words >> 11) & 31)*255//31, ((words >> 5) & 63)*255//63,
                           (words & 31)*255//31, np.full_like(words, 255)], axis=-1)
    else:
        raise ValueError('Unsupported pixel format')
    colors = colors.astype(np.float32)
    colors[:, :, :3] *= colors[:, :, 3:4] / 255
    colors[:, :, 3] *= 2
    codebook = colors.reshape(256, 16)
    pixels = np.asarray(image, dtype=np.float32)[::-1]
    pixels[:, :, :3] *= pixels[:, :, 3:4] / 255
    pixels[:, :, 3] *= 2
    vectors = pixels.reshape(128, 2, 128, 2, 4).transpose(0, 2, 3, 1, 4).reshape(-1, 16)
    indices = np.empty(16384, dtype=np.uint8)
    for start in range(0, len(vectors), 256):
        distances = ((vectors[start:start+256, None] - codebook[None])**2).sum(axis=2)
        indices[start:start+256] = distances.argmin(axis=1)
    twiddled = bytearray(16384)
    for y in range(128):
        for x in range(128):
            twiddled[spread(y) | (spread(x) << 1)] = int(indices[y*128+x])
    return original[:2048] + twiddled


def main():
    art = Image.open(sys.argv[1]).convert('RGBA')
    rows = [int(value) for value in sys.argv[2].split(',')]
    if len(rows) != 9 or any(a >= b for a, b in zip(rows, rows[1:])):
        raise ValueError('Supply nine increasing row boundaries')
    if rows[0] < 0 or rows[-1] > art.height:
        raise ValueError('Row boundaries exceed the artwork')
    source = (ROOT / 'TEX' / 'spr_tit.bin').read_bytes()
    original = source[OFFSET:OFFSET+SIZE]
    old_image = decode(original)
    # A full source round trip checks VQ order, orientation, alpha and colors.
    assert decode(encode(old_image, original)).tobytes() == old_image.tobytes()
    target = old_image.copy()
    target.paste((0, 0, 0, 0), (0, 64, 256, 256))
    labels = ['Arcade', 'Classic Match Recreation', 'VS', 'Create-A-Wrestler',
              'Practice', 'Spectator', 'Backup', 'Options']
    for i, (top, bottom) in enumerate(zip(rows, rows[1:])):
        sprite = art.crop((0, top, art.width, bottom))
        # Ignore nearly transparent generation noise when finding the bounds.
        bbox = sprite.getchannel('A').point(lambda a: 255 if a >= 64 else 0).getbbox()
        if bbox is None:
            raise ValueError(f'Missing label: {labels[i]}')
        sprite = sprite.crop(bbox)
        max_width = 228 if i < 2 else (156 if i < 6 else 188)
        width = min(max_width, round(sprite.width * 20 / sprite.height))
        sprite = sprite.resize((width, 20), Image.Resampling.LANCZOS)
        target.paste(sprite, ((256-width)//2, 66+24*i))
    block = bytearray(encode(target, original))
    # Keep every original VQ index above the menu byte-for-byte unchanged.
    for y in range(96, 128):
        for x in range(128):
            address = 2048 + spread(y) + (spread(x) << 1)
            block[address] = original[address]
    assert len(block) == SIZE
    decoded = decode(block)
    assert decoded.crop((0, 0, 256, 64)).tobytes() == old_image.crop((0, 0, 256, 64)).tobytes()
    edited = source[:OFFSET] + block + source[OFFSET+SIZE:]
    archive = (ROOT / 'TEX.AFS').read_bytes()
    assert archive[:4] == b'AFS\0'
    matches = []
    for index in range(struct.unpack_from('<I', archive, 4)[0]):
        start, size = struct.unpack_from('<II', archive, 8+8*index)
        if size == len(source) and archive[start:start+size] == source:
            matches.append(start)
    if len(matches) != 1:
        raise ValueError('Expected exactly one matching original sprite entry')
    entry = matches[0]
    absolute = entry + OFFSET
    patched = archive[:absolute] + block + archive[absolute+SIZE:]
    assert len(patched) == len(archive)
    assert patched[:absolute] == archive[:absolute]
    assert patched[absolute+SIZE:] == archive[absolute+SIZE:]
    assert patched[entry:entry+len(edited)] == edited
    output = ROOT / 'English_Menu'
    (output / 'TEX').mkdir(parents=True, exist_ok=True)
    (output / 'TEX' / 'spr_tit.bin').write_bytes(edited)
    (output / 'TEX.AFS').write_bytes(patched)
    target.save(output / 'menu_before_compression.png')
    decoded.save(output / 'main_menu_english.png')
    preview = Image.new('RGBA', decoded.size, (0, 0, 0, 255))
    preview.alpha_composite(decoded)
    preview.convert('RGB').resize((768, 768), Image.Resampling.NEAREST).save(output / 'preview.png')
    report = {'labels': labels, 'sprite_offset': hex(OFFSET), 'archive_offset': hex(absolute),
              'block_size': SIZE, 'archive_size': len(patched),
              'original_sha256': hashlib.sha256(archive).hexdigest(),
              'patched_sha256': hashlib.sha256(patched).hexdigest(),
              'checks': ['source VQ round trip exact', 'Start prompt unchanged',
                         'archive size unchanged', 'all bytes outside menu block unchanged',
                         'patched archive entry matches patched sprite'],
              'in_game_tested': False}
    (output / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
