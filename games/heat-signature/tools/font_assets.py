"""Rasterize independently licensed Xolonium; never reads game textures."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CHARS = ''.join(chr(i) for i in range(32, 127)) + 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ–—…„“”’'
VARIANTS = [(8, 0, 0), (8, 1, 0), (10, 0, 0), (10, 1, 0),
            (12, 0, 0), (12, 0, 1), (15, 0, 0), (16, 0, 0),
            (24, 0, 0), (24, 1, 0), (48, 0, 0), (48, 1, 0), (64, 1, 0)]


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    files, report = [], []
    for size, bold, italic in VARIANTS:
        font = ImageFont.truetype(str(ROOT / 'fonts' / f'Xolonium-{"Bold" if bold else "Regular"}.ttf'), round(size * 4 / 3))
        boxes = [font.getbbox(c, anchor='ls') for c in CHARS if c != ' ']
        top, bottom = min(b[1] for b in boxes), max(b[3] for b in boxes)
        height = bottom - top + 2
        width = max(b[2] - min(0, b[0]) for b in boxes) + 4 + (math.ceil(height * .18) if italic else 0)
        strip = Image.new('RGBA', (width * len(CHARS), height))
        metrics = []
        for index, char in enumerate(CHARS):
            glyph = Image.new('RGBA', (width, height))
            draw = ImageDraw.Draw(glyph)
            if char == ' ':
                # Near-transparent endpoints give the proportional sprite font a
                # real space advance. No visible white rectangle in the UI.
                draw.point((1, height - 1), fill=(255, 255, 255, 1))
                draw.point((max(2, round(font.getlength(' '))), height - 1), fill=(255, 255, 255, 1))
            else:
                left = font.getbbox(char, anchor='ls')[0]
                draw.text((1 - min(0, left), 1 - top), char, font=font, anchor='ls', fill='white', stroke_width=0)
                if italic:
                    glyph = glyph.transform(glyph.size, Image.Transform.AFFINE,
                                            (1, .18, -.18 * height, 0, 1, 0), Image.Resampling.BICUBIC)
                assert glyph.getchannel('A').getbbox(), (size, char)
            strip.paste(glyph, (index * width, 0))
            bbox = glyph.getchannel('A').getbbox()
            advance = max(round(font.getlength(char)), bbox[2] - bbox[0] + max(1, size // 12))
            metrics.append(f'{ord(char)} {index} {advance} {-bbox[0]} {height}\n')
        name = f'font-{size}-{bold}-{italic}.png'
        strip.save(out / name, optimize=True)
        files.append(name)
        metric_name = name.replace('.png', '.metrics')
        (out / metric_name).write_text(''.join(metrics), encoding='ascii')
        files.append(metric_name)
        report.append(dict(file=name, frames=len(CHARS), width=strip.width, height=height, cell_width=width))
    (out / 'charmap.txt').write_text(CHARS, encoding='utf-8')
    (ROOT / 'work/font-assets.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return files + ['charmap.txt']


if __name__ == '__main__':
    print(build(ROOT / 'dist/notgeese/fonts'))
