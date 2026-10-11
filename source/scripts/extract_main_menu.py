from pathlib import Path
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OFFSET = 0xDC800
SIZE = 0x4800

def spread(value):
    return sum(((value >> bit) & 1) << (2 * bit) for bit in range(7))

def decode(block, pixel_format='4444'):
    if len(block) != SIZE:
        raise ValueError("Expected one 256x256 VQ block (18432 bytes)")
    palette = struct.unpack("<1024H", block[:2048])
    indices = block[2048:]
    image = Image.new("RGBA", (256, 256))
    pixels = image.load()
    for y in range(256):
        for x in range(256):
            index = indices[spread(y // 2) | (spread(x // 2) << 1)]
            value = palette[index * 4 + (x % 2) * 2 + y % 2]
            if pixel_format == '4444':
                color = (((value >> 8) & 15)*17, ((value >> 4) & 15)*17,
                         (value & 15)*17, ((value >> 12) & 15)*17)
            elif pixel_format == '1555':
                color = (((value >> 10) & 31)*255//31, ((value >> 5) & 31)*255//31,
                         (value & 31)*255//31, 255 if value & 32768 else 0)
            elif pixel_format == '565':
                color = (((value >> 11) & 31)*255//31, ((value >> 5) & 63)*255//63,
                         (value & 31)*255//31, 255)
            else:
                raise ValueError('Unsupported pixel format')
            pixels[x, 255-y] = color
    return image

if __name__ == "__main__":
    assert [spread(i) for i in range(4)] == [0, 1, 4, 5]
    test = decode(struct.pack("<1024H", *([0xF123]*1024)) + bytes(16384))
    assert test.getpixel((0, 0)) == (17, 34, 51, 255)
    source = (ROOT / "TEX" / "spr_tit.bin").read_bytes()
    image = decode(source[OFFSET:OFFSET+SIZE])
    image.save(Path(__file__).with_name("main_menu.png"))
    background = Image.new("RGBA", image.size, (0, 0, 0, 255))
    background.alpha_composite(image)
    background.convert("RGB").resize((768,768), Image.Resampling.NEAREST).save(
        Path(__file__).with_name("main_menu_preview.png"))
    print("Verified decoder; exported main menu. Original game files unchanged.")
