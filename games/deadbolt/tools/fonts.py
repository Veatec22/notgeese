"""Polish letters in DEADBOLT's three fonts: design and preview.

Each letter is a recipe: the game's base letter (e.g. "a"), its offset in a new cell,
cell size, advance width and our mark pixels (acute, dot, ogonek, stroke). The plugin
composes letters in memory from game pixels and our marks, so the package carries not a
single pixel of the game atlas, only the recipe (`notgeese/fonts.txt`).

fontMedium is effectively fontSmall scaled ×2 (same shapes, 2×2 pixels), so its marks are
fontSmall's at scale 2. Its existing "Ó" has no acute (rasterization dropped it); the
recipe replaces it.

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\fonts.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"

writes work/font-preview.png (composed from the game atlas; for viewing only, never packaged).
"""
from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

# Marks in font units: (x, y) from the top-left of the base letter cell.
TINY_ACUTE = [(2, 3), (3, 2)]          # over a lower-case letter (x-height from row 5)
TINY_DOT = [(2, 3)]
TINY_ACUTE_CAP = [(2, 1), (3, 0)]      # over a capital (from row 3)
TINY_DOT_CAP = [(2, 1)]

SMALL_ACUTE = [(3, 2), (4, 2), (2, 3), (3, 3)]      # x-height from row 5
SMALL_DOT = [(2, 2), (3, 2), (2, 3), (3, 3)]
SMALL_ACUTE_CAP = [(3, 0), (4, 0)]                  # capitals from row 2, one row of gap
SMALL_DOT_CAP = [(2, 0), (3, 0)]


def ogonek(x: int, thick: bool) -> list[tuple[int, int]]:
    """Ogonek below the baseline (row 10), anchored at column x, going down and right."""
    if thick:
        return [(x, 11), (x + 1, 11), (x + 1, 12), (x + 2, 12)]
    return [(x, 11), (x + 1, 12)]


# letter -> (base, dx, extra width, mark, new height or None, extra advance)
TINY = {
    'ą': ('a', 0, 0, ogonek(4, False), 13, 0),
    'ć': ('c', 0, 0, TINY_ACUTE, None, 0),
    'ę': ('e', 0, 0, ogonek(3, False), 13, 0),
    'ł': ('l', 1, 2, [(0, 7), (2, 5)], None, 2),
    'ń': ('n', 0, 0, TINY_ACUTE, None, 0),
    'ó': ('o', 0, 0, TINY_ACUTE, None, 0),
    'ś': ('s', 0, 0, TINY_ACUTE, None, 0),
    'ź': ('z', 0, 0, TINY_ACUTE, None, 0),
    'ż': ('z', 0, 0, TINY_DOT, None, 0),
    'Ą': ('A', 0, 0, ogonek(3, False), 13, 0),
    'Ć': ('C', 0, 0, TINY_ACUTE_CAP, None, 0),
    'Ę': ('E', 0, 0, ogonek(3, False), 13, 0),
    'Ł': ('L', 1, 1, [(0, 8), (2, 6)], None, 1),
    'Ń': ('N', 0, 0, TINY_ACUTE_CAP, None, 0),
    'Ó': ('O', 0, 0, TINY_ACUTE_CAP, None, 0),
    'Ś': ('S', 0, 0, TINY_ACUTE_CAP, None, 0),
    'Ź': ('Z', 0, 0, TINY_ACUTE_CAP, None, 0),
    'Ż': ('Z', 0, 0, TINY_DOT_CAP, None, 0),
}

SMALL = {
    'ą': ('a', 0, 0, ogonek(4, True), 13, 0),
    'ć': ('c', 0, 0, SMALL_ACUTE, None, 0),
    'ę': ('e', 0, 0, ogonek(3, True), 13, 0),
    'ł': ('l', 0, 0, [(0, 7), (1, 7), (1, 6), (4, 6), (4, 5), (5, 5)], None, 0),
    'ń': ('n', 0, 0, SMALL_ACUTE, None, 0),
    'ó': ('o', 0, 0, SMALL_ACUTE, None, 0),
    'ś': ('s', 0, 0, SMALL_ACUTE, None, 0),
    'ź': ('z', 0, 0, SMALL_ACUTE, None, 0),
    'ż': ('z', 0, 0, SMALL_DOT, None, 0),
    'Ą': ('A', 0, 0, ogonek(3, True), 13, 0),
    'Ć': ('C', 0, 0, SMALL_ACUTE_CAP, None, 0),
    'Ę': ('E', 0, 0, ogonek(4, True), 13, 0),
    'Ł': ('L', 1, 1, [(0, 7), (1, 7), (1, 6), (4, 6), (4, 5), (5, 5)], None, 1),
    'Ń': ('N', 0, 0, SMALL_ACUTE_CAP, None, 0),
    'Ó': ('O', 0, 0, SMALL_ACUTE_CAP, None, 0),
    'Ś': ('S', 0, 0, SMALL_ACUTE_CAP, None, 0),
    'Ź': ('Z', 0, 0, SMALL_ACUTE_CAP, None, 0),
    'Ż': ('Z', 0, 0, SMALL_DOT_CAP, None, 0),
}

FONTS = {'fontTiny': (TINY, 1), 'fontSmall': (SMALL, 1), 'fontMedium': (SMALL, 2)}


def medium_acute(width: int):
    """Slanted acute over a fontMedium capital: rows 0–2, row 3 gap (capitals from 4)."""
    x = width // 2 - 1
    return [(x, 2), (x + 1, 2), (x + 1, 1), (x + 2, 1), (x + 2, 0), (x + 3, 0)]


# fontMedium has 4 free pixel rows above capitals, not 2 units ×2, so the acute can be
# slanted. Pixels already at scale 1 (widths: C, N, O 14 px; S, Z 12 px).
MEDIUM_PIXELS = {
    'Ć': medium_acute(14), 'Ń': medium_acute(14), 'Ó': medium_acute(14),
    'Ś': medium_acute(12), 'Ź': medium_acute(12),
    'Ż': [(5, 1), (6, 1), (5, 2), (6, 2)],
}


def recipes():
    """List (font, letter, base, dx, +width, +advance, new height or None, pixels) in pixels."""
    out = []
    for font, (design, scale) in FONTS.items():
        for letter, (base, dx, extra_w, marks, height, extra_shift) in design.items():
            if font == 'fontMedium' and letter in MEDIUM_PIXELS:
                px = MEDIUM_PIXELS[letter]
                out.append((font, letter, base, dx * scale, extra_w * scale, extra_shift * scale,
                            height * scale if height else None, px))
                continue
            px = sorted({(x * scale + i, y * scale + j) for x, y in marks
                         for i in range(scale) for j in range(scale)})
            out.append((font, letter, base, dx * scale, extra_w * scale, extra_shift * scale,
                        height * scale if height else None, px))
    return out


def write_recipes(path: Path):
    lines = []
    for font, letter, base, dx, extra_w, extra_shift, height, px in recipes():
        marks = ' '.join(f'{x},{y}' for x, y in px)
        lines.append(f'{font}\t{ord(letter)}\t{ord(base)}\t{dx}\t{extra_w}\t{extra_shift}\t{height or 0}\t{marks}\n')
    path.write_text(''.join(lines), encoding='ascii', newline='\n')
    return len(lines)


# --- preview from the game atlas (work/ only) ---

def load_fonts(game: Path):
    d = (game / 'data.win').read_bytes()
    u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    cstr = lambda p: d[p:d.index(b'\0', p)].decode()
    chunks, o = {}, 8
    while o < len(d):
        chunks[d[o:o + 4].decode()] = o + 8
        o += 8 + u32(o + 4)
    plist = lambda c: [u32(chunks[c] + 4 + 4 * i) for i in range(u32(chunks[c]))]
    pages = []
    for p in plist('TXTR'):
        png = u32(p + 4)
        pages.append(Image.open(io.BytesIO(d[png:d.index(b'IEND', png) + 8])).convert('RGBA'))
    fonts = {}
    for f in plist('FONT'):
        sx, sy, *_, tex = struct.unpack_from('<11H', d, u32(f + 28))
        glyphs = {}
        for i in range(u32(f + 40)):
            c, x, y, w, h, shift, off = struct.unpack_from('<6Hh', d, u32(f + 44 + 4 * i))
            glyphs[chr(c)] = (pages[tex].crop((sx + x, sy + y, sx + x + w, sy + y + h)), shift, off)
        fonts[cstr(u32(f))] = glyphs
    return fonts


def compose(glyphs, letter, base, dx, extra_w, extra_shift, height, px):
    img, shift, off = glyphs[base]
    w, h = img.width + extra_w, height or img.height
    cell = Image.new('RGBA', (w, h))
    cell.paste(img, (dx, 0))
    for x, y in px:
        cell.putpixel((x, y), (255, 255, 255, 255))
    return cell, shift + extra_shift, off


def preview(game: Path, out: Path):
    fonts = load_fonts(game)
    for font, letter, *rest in recipes():
        fonts[font][letter] = compose(fonts[font], letter, *rest)
    samples = ['Zażółć gęślą jaźń. ZAŻÓŁĆ GĘŚLĄ JAŹŃ.',
               'Łódź, źdźbło, ćma, Ńa? Śnieg, Ęą. Żniwiarz!',
               "'E': OTWÓRZ DRZWI  Nieźle, żniwiarzu."]
    rows = []
    for font in FONTS:
        for text in samples:
            glyphs = fonts[font]
            width = sum(glyphs[c][1] if c in glyphs else 8 for c in text) + 8
            height = max(g[0].height for g in glyphs.values()) + 4
            row = Image.new('RGBA', (width, height), (20, 20, 24, 255))
            x = 4
            for c in text:
                img, shift, off = glyphs.get(c, glyphs['?'])
                row.alpha_composite(img, (x + off, 2))
                x += shift
            rows.append(row)
    W = max(r.width for r in rows)
    sheet = Image.new('RGBA', (W, sum(r.height for r in rows)), (20, 20, 24, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
    out.parent.mkdir(exist_ok=True)
    sheet.save(out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    print(preview(args.game, ROOT / 'work/font-preview.png'))
