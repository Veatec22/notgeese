"""Nexus images for the Ultrawide mod: header 1300x372 and gallery 1920x1080.

The key art is brought back to the game's native 320x180 (DEADBOLT renders 960x540 = 3x) and
scaled by whole numbers only, so pixels stay square. "ULTRAWIDE" is set in the game's own
fontSmall, read from data.win. Output in dist/ (key art and game font are the publisher's, never
committed or packaged).

    .venv\\Scripts\\python.exe games\\deadbolt\\mods\\ultrawide\\tools\\art.py --art <key art 16:9>
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
GAME = MOD.parents[1]
sys.path.insert(0, str(GAME / 'tools'))
import fonts  # noqa: E402

NATIVE = (320, 180)
BONE = (236, 228, 196, 255)     # skull highlight
SHADOW = (122, 78, 18, 255)     # shirt shadow


def word(glyphs, text, scale):
    """Text in game font pixels with a one-pixel drop shadow, scaled by a whole number."""
    width = sum(glyphs[c][1] for c in text) + 1
    height = max(glyphs[c][0].height for c in text) + 1
    layers = []
    for colour, dx in ((SHADOW, 1), (BONE, 0)):
        layer = Image.new('RGBA', (width, height))
        x = 0
        for c in text:
            img, shift, off = glyphs[c]
            tint = Image.new('RGBA', img.size, colour)
            tint.putalpha(img.getchannel('A'))
            layer.alpha_composite(tint, (x + off + dx, dx))
            x += shift
        layers.append(layer)
    out = layers[0]
    out.alpha_composite(layers[1])
    bbox = out.getbbox()
    out = out.crop(bbox)
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def circle_span(art):
    """Left and right edge of the peephole: columns with anything brighter than the black frame."""
    a = np.asarray(art.convert('L'))
    cols = np.where((a > 24).sum(axis=0) > 3)[0]
    return int(cols.min()), int(cols.max())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--art', type=Path, required=True)
    ap.add_argument('--game', type=Path, default=Path(r'C:\SteamLibrary\steamapps\common\DEADBOLT'))
    args = ap.parse_args()
    src = Image.open(args.art).convert('RGB')
    assert abs(src.width / src.height - 16 / 9) < 0.01, src.size
    art = src.resize(NATIVE, Image.BOX).convert('RGBA')
    glyphs = fonts.load_fonts(args.game)['fontSmall']
    left, right = circle_span(art)
    bg = art.getpixel((2, 2))
    out = GAME / 'dist'

    # Gallery 1920x1080 = 384x216 x5: scene on top, the word under it.
    canvas = Image.new('RGBA', (384, 216), bg)
    canvas.alpha_composite(art, (32, 0))
    text = word(glyphs, 'ULTRAWIDE', 2)
    canvas.alpha_composite(text, ((384 - text.width) // 2, 216 - text.height - 9))
    canvas.resize((1920, 1080), Image.NEAREST).convert('RGB').save(out / 'ultrawide-gallery.png')

    # Header 1300x372 = 650x186 x2: ULTRA (peephole) WIDE.
    canvas = Image.new('RGBA', (650, 186), bg)
    x0 = (650 - NATIVE[0]) // 2
    canvas.alpha_composite(art, (x0, 3))
    ultra, wide = word(glyphs, 'ULTRA', 3), word(glyphs, 'WIDE', 3)
    y = (186 - ultra.height) // 2
    gap = 14
    canvas.alpha_composite(ultra, (x0 + left - gap - ultra.width, y))
    canvas.alpha_composite(wide, (x0 + right + gap, y))
    canvas.resize((1300, 372), Image.NEAREST).convert('RGB').save(out / 'ultrawide-header.png')
    print(f'Wrote {out / "ultrawide-gallery.png"} and {out / "ultrawide-header.png"}; peephole x {left}-{right}')


if __name__ == '__main__':
    main()
