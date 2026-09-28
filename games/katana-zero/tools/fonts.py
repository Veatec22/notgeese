"""Polish letters for Katana ZERO sprite fonts, composed from the game's own letters.

The game draws text with sprite fonts: one frame per letter, and a char map (a string in
the exe) says which frame is which letter. Latin has the full Western European set, but no
Polish letter except "ó" (and xirod lacks even that).

Missing letters are composed from what the font has, to keep its face:
- acute (ć ń ś ź) = "é" minus "e" (for capitals "É" minus "E"),
- dot (ż) = the dot of "i" or one of the dots of "Ё",
- ogonek (ą ę) = the "ç" cedilla mirrored, attached to the letter's right leg,
- the "ł" stroke is drawn diagonally across the stem in the font's stroke width.
Fonts without the needed model (xirod has no "é" or "ç") get marks drawn in the same
geometry. Check with `--preview` and fix here, not in the graphics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops

from gmdata import DataWin

LOWER = 'ąćęłńśźżó'
UPPER = 'ĄĆĘŁŃŚŹŻÓ'
PAIRS = dict(zip(LOWER, UPPER))


def alpha(img):
    return img.getchannel('A')


def diff(a: Image.Image, b: Image.Image) -> Image.Image:
    """Pixels present in a and absent in b."""
    mask = ImageChops.subtract(alpha(a), alpha(b))
    out = Image.new('RGBA', a.size, (0, 0, 0, 0))
    out.paste(a, (0, 0), mask)
    return out


def shifted(img: Image.Image, dx: int, dy: int) -> Image.Image:
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(img, (dx, dy), img)
    return out


def over(base: Image.Image, mark: Image.Image) -> Image.Image:
    out = base.copy()
    out.alpha_composite(mark)
    return out


def bbox(img):
    return alpha(img).point(lambda v: 255 if v > 96 else 0).getbbox()


def components(img: Image.Image) -> list[Image.Image]:
    """Splits a mark into connected pieces (e.g. the two dots of "Ё")."""
    a = alpha(img)
    w, h = img.size
    px = a.load()
    seen = set()
    parts = []
    for y in range(h):
        for x in range(w):
            if px[x, y] and (x, y) not in seen:
                stack, pts = [(x, y)], []
                seen.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    pts.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                part = Image.new('RGBA', img.size, (0, 0, 0, 0))
                src = img.load()
                dst = part.load()
                for p in pts:
                    dst[p] = src[p]
                parts.append(part)
    parts.sort(key=lambda p: bbox(p)[0])
    return parts


def center_x(img):
    b = bbox(img)
    return (b[0] + b[2]) / 2


def place_over(letter: Image.Image, mark: Image.Image, ref: Image.Image | None = None) -> Image.Image:
    """Places a diacritic over a letter, centered as in the model."""
    offset = 0.0
    if ref is not None:
        offset = center_x(mark) - center_x(ref)
    dx = round(center_x(letter) + offset - center_x(mark))
    return over(letter, shifted(mark, dx, 0))


def stroke_width(letter: Image.Image) -> int:
    """Vertical stroke width: shortest horizontal run in the middle row."""
    a = alpha(letter).load()
    b = bbox(letter)
    y = (b[1] + b[3]) // 2
    runs, run = [], 0
    for x in range(letter.width):
        if a[x, y] > 96:
            run += 1
        elif run:
            runs.append(run)
            run = 0
    if run:
        runs.append(run)
    return min(runs) if runs else 1


def ogonek(letter: Image.Image, cedilla: Image.Image) -> Image.Image:
    """Cedilla mirrored horizontally, attached under the letter's right leg."""
    mark = cedilla.transpose(Image.FLIP_LEFT_RIGHT)
    mb = bbox(mark)
    lb = bbox(letter)
    dx = lb[2] - mb[2]
    return over(letter, shifted(mark, dx, 0))


def draw_ogonek(letter: Image.Image, w: int, below: int) -> Image.Image:
    """Ogonek for fonts without a cedilla: a hook in stroke width, under the right leg."""
    lb = bbox(letter)
    mark = Image.new('RGBA', letter.size, (0, 0, 0, 0))
    x_right = lb[2]
    y0 = lb[3]
    cells = [(x_right - w, y0), (x_right - 2 * w, y0 + w), (x_right - w, y0 + 2 * w)]
    for i, (cx, cy) in enumerate(cells[:max(1, below // w + 1)]):
        for yy in range(cy, min(cy + w, letter.height)):
            for xx in range(cx, cx + w):
                if 0 <= xx < letter.width:
                    mark.putpixel((xx, yy), (255, 255, 255, 255))
    return over(letter, mark)


def slash(letter: Image.Image, w: int, stem_x: tuple[int, int], y_mid: int) -> Image.Image:
    """Diagonal "ł" stroke across the stem: bottom-left to top-right."""
    mark = Image.new('RGBA', letter.size, (0, 0, 0, 0))
    x0, x1 = stem_x
    # stroke width: one pixel in pixel fonts, half the stem in bold ones
    t = 1 if w <= 2 else max(2, w // 2)
    reach = t
    cells = []
    if w <= 2:
        # classic pixel "ł": one step lower on the left, one higher on the right
        if x0 == 0:
            b = bbox(letter)
            if b[2] < letter.width:
                # stem at the left edge: shift the letter one pixel so the stroke fits
                return slash(shifted(letter, 1, 0), w, (x0 + 1, x1 + 1), y_mid)
            cells = [(x1, y_mid), (x1 + 1, y_mid - 1)]
        else:
            cells = [(x0 - 1, y_mid + 1), (x1, y_mid - 1)]
        for x, y in cells:
            if 0 <= x < letter.width and 0 <= y < letter.height:
                mark.putpixel((x, y), (255, 255, 255, 255))
        return over(letter, mark)
    left, right = x0 - reach, x1 + reach
    xc = (left + right) / 2
    for x in range(left, right):
        yc = y_mid + (xc - x - 0.5) * 0.6
        for yy in range(round(yc - t / 2), round(yc + t / 2)):
            if 0 <= x < letter.width and 0 <= yy < letter.height:
                mark.putpixel((x, yy), (255, 255, 255, 255))
    return over(letter, mark)


def stem_columns(letter: Image.Image, y: int) -> tuple[int, int]:
    """Left vertical stem in a given row: columns [from, to)."""
    a = alpha(letter).load()
    x = 0
    while x < letter.width and a[x, y] <= 96:
        x += 1
    x1 = x
    while x1 < letter.width and a[x1, y] > 96:
        x1 += 1
    return x, x1


def glyphs_for(dw: DataWin, sprite, charmap: str) -> dict[str, Image.Image]:
    """Polish letters missing in a font, in LOWER+UPPER order."""
    def g(c):
        return dw.frame_image(sprite.frames[charmap.index(c)]) if c in charmap else None

    have = set(charmap)
    out: dict[str, Image.Image] = {}
    w = stroke_width(g('l') or g('L'))

    acute_lo = diff(g('é'), g('e')) if g('é') and g('e') else None
    acute_up = diff(g('É'), g('E')) if g('É') and g('E') else None
    ced_lo = diff(g('ç'), g('c')) if g('ç') and g('c') else None
    ced_up = diff(g('Ç'), g('C')) if g('Ç') and g('C') else None
    dot_lo = None
    if g('i') is not None:
        parts = components(g('i'))
        if len(parts) > 1:
            dot_lo = min(parts, key=lambda p: bbox(p)[1])
    dot_up = None
    if g('Ё') is not None and g('Е') is not None:
        dots = components(diff(g('Ё'), g('Е')))
        if dots:
            dot_up = dots[0]
            # the two dots are symmetric; for "Ż" take one, centered
    if acute_up is None and dot_up is not None:
        acute_up = synth_acute(dot_up, w)
    if acute_lo is None:
        acute_lo = acute_up
    if dot_lo is None:
        dot_lo = dot_up
    if dot_up is None and dot_lo is not None and acute_up is not None:
        # dot over a capital at the height of the "É" acute
        dy = bbox(acute_up)[3] - bbox(dot_lo)[3]
        dot_up = shifted(dot_lo, 0, dy)
    if ced_up is None:
        ced_up = ced_lo
    if ced_lo is None:
        ced_lo = ced_up

    ref_lo = g('e')
    ref_up = g('E')

    def build(ch: str) -> Image.Image | None:
        upper = ch in UPPER
        base_ch = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ś': 's', 'ź': 'z', 'ż': 'z', 'ó': 'o',
                   'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z', 'Ó': 'O'}[ch]
        base = g(base_ch)
        if base is None:
            return None
        acute = acute_up if upper else acute_lo
        dot = dot_up if upper else dot_lo
        ced = ced_up if upper else ced_lo
        ref = ref_up if upper else ref_lo
        if ch in 'ćńśźóĆŃŚŹÓ':
            return place_over(base, acute, None) if acute is not None else None
        if ch in 'żŻ':
            return place_over(base, dot, None) if dot is not None else None
        if ch in 'ąęĄĘ':
            if ced is not None:
                return ogonek(base, ced)
            return draw_ogonek(base, w, sprite.height - bbox(base)[3])
        if ch in 'łŁ':
            b = bbox(base)
            y_mid = b[1] + (b[3] - b[1]) * 11 // 20
            return slash(base, w, stem_columns(base, y_mid), y_mid)
        return None

    for ch in LOWER + UPPER:
        if ch in have:
            continue
        img = build(ch)
        if img is not None:
            out[ch] = img
    return out


def synth_acute(dot: Image.Image, w: int) -> Image.Image:
    """Acute from a dot: the same dot repeated diagonally up-right."""
    b = bbox(dot)
    step = max(1, (b[2] - b[0]) // 2)
    mark = Image.new('RGBA', dot.size, (0, 0, 0, 0))
    for k in range(3):
        mark.alpha_composite(shifted(dot, k * step - step, -k * step + step))
    return mark


FONT_SPRITES = ['spr_textbox_font', 'spr_vcr_font', 'spr_vcr_font_tiny', 'spr_vhs_font',
                'spr_xirod_font_rus', 'spr_big_font']


def preview(dw: DataWin, maps: dict[str, str], out: Path):
    sprites = dw.sprites()
    rows = []
    for name in FONT_SPRITES:
        s = sprites[name]
        m = maps[name]
        new = glyphs_for(dw, s, m)
        sample = [dw.frame_image(s.frames[m.index(c)]) for c in 'acelnoszACELNOSZ' if c in m]
        cells = sample + list(new.values())
        scale = max(1, 96 // s.height)
        row = Image.new('RGBA', ((s.width + 2) * len(cells) * scale, s.height * scale), (30, 30, 70, 255))
        for i, c in enumerate(cells):
            row.alpha_composite(c.resize((s.width * scale, s.height * scale), Image.NEAREST),
                                (i * (s.width + 2) * scale, 0))
        rows.append(row)
    sheet = Image.new('RGBA', (max(r.width for r in rows), sum(r.height + 8 for r in rows)), (10, 10, 20, 255))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height + 8
    sheet.save(out)
    print(f'preview: {out}')


if __name__ == '__main__':
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-win', required=True)
    ap.add_argument('--maps', required=True, help='JSON: sprite -> char map (from extract.py)')
    ap.add_argument('--preview', required=True)
    a = ap.parse_args()
    preview(DataWin(Path(a.data_win)), json.loads(Path(a.maps).read_text(encoding='utf-8')), Path(a.preview))
