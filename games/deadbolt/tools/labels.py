"""Polish labels on DEADBOLT graphics (main menu, tutorial, mission select): design and preview.

The plugin receives no game pixels. For each label the recipe (`notgeese/labels.txt`) says:
  erase: in the frame rect, paint pixels in the label's text colors with the background
         color (label texture, stains and dirt, stays because it has other colors);
  fill:  fill a rect with a color (the "SPACE" key with letters cut out);
  mask:  draw our mask (Polish text) in the given color; AA=00 means transparent.
Coordinates from the top-left of the frame's source rect (TPAG) on the texture page.
Masks are rendered 1-bit from faces of similar character (Courier New Bold, Ink Free,
Bahnschrift, Georgia Bold, Lucida Console) and processed (bold, shadow, worn ink).
The package carries only these masks of specific labels, no font files.

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\labels.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"

writes previews work/labels-preview-*.png (composed from game graphics; for viewing only).
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
FONTS = Path(r'C:\Windows\Fonts')

TYPEWRITER = dict(font='courbd.ttf')
MARKER = dict(font='Inkfree.ttf', bold=1)
STENCIL = dict(font='bahnschrift.ttf')
CHALK = dict(font='Inkfree.ttf')
HAND = dict(font='Inkfree.ttf')
SERIF = dict(font='georgiab.ttf')
MONO = dict(font='lucon.ttf')
PIXEL = dict(font=None)   # own face, see PIXEL_GLYPHS


def rgba(h: str):
    """RRGGBB or RRGGBBAA (AA=00: transparent)."""
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + ((int(h[6:8], 16),) if len(h) == 8 else (255,))


# Each label: sprite, frame, rect to clean (x0, y0, x1, y1 inclusive) with background and text colors
# (or `fill`), the area the new text may occupy, PL text, style, cap height,
# text center (or `left`), letter spacing, color.
LABELS = [
    # Main menu: one 960×540 image, every button in a different style.
    dict(sprite='sMain', frame=0, rect=(146, 108, 277, 125), bg='dcd2b4', inks=['5b4444', '9e7c7c', 'baa69e'],
         area=(120, 106, 298, 127), text='NOWA GRA', style=TYPEWRITER, cap=12, center=(211, 116.5), spacing=5,
         color='5b4444', mottle='9e7c7c'),
    dict(sprite='sMain', frame=0, rect=(142, 164, 279, 181), bg='dcd2b4', inks=['5b4444', '9e7c7c', 'baa69e'],
         area=(120, 162, 298, 184), text='WCZYTAJ GRĘ', style=TYPEWRITER, cap=12, center=(210, 172.5), spacing=2,
         color='5b4444', mottle='9e7c7c'),
    dict(sprite='sMain', frame=0, rect=(145, 219, 276, 239), bg='cccb95', inks=['201d1c', 'baa985'],
         area=(131, 217, 298, 241), text='WŁASNE MAPY', style=MARKER, cap=15, center=(213, 229), spacing=1,
         color='201d1c'),
    dict(sprite='sMain', frame=0, rect=(143, 276, 277, 296), bg='201d1c', inks=['e1e1d7', '777573', '101014', '222626'],
         area=(120, 274, 298, 298), text='OPCJE', style=STENCIL, cap=15, center=(210, 285.5), spacing=10,
         color='e1e1d7', shadow=[('101014', 1, 2), ('777573', 0, 1)]),
    dict(sprite='sMain', frame=0, rect=(147, 330, 273, 355), bg='222626', inks=['777573', '33302f'],
         area=(120, 329, 298, 356), text='TWÓRCY', style=CHALK, cap=19, center=(211, 344), spacing=7,
         color='777573'),
    dict(sprite='sMain', frame=0, rect=(150, 381, 282, 411), bg='e1e1d7', inks=['201d1c', '33302f', '777573'],
         area=(131, 381, 285, 411), text='WYJDŹ', style=MARKER, cap=22, center=(210, 398), spacing=6,
         color='201d1c', bold=1),
    # Tutorial: yellow handwritten labels on transparent background; "SPACE" cut into a yellow key.
    dict(sprite='sTutorial', frame=4, rect=(21, 0, 54, 15), bg='00000000', inks=['e2ed5c'],
         area=(21, 0, 54, 41), text='KLIK', style=PIXEL, cap=9, center=(38, 7.5), spacing=1, color='e2ed5c'),
    dict(sprite='sTutorial', frame=5, rect=(0, 12, 34, 30), bg='00000000', inks=['e2ed5c'],
         area=(0, 2, 35, 38), text='TRZYMAJ', style=PIXEL, cap=9, center=(17.5, 21), spacing=1, color='e2ed5c'),
    dict(sprite='sTutorial', frame=5, rect=(57, 12, 89, 30), bg='00000000', inks=['e2ed5c'],
         area=(57, 2, 90, 38), text='POTEM', style=PIXEL, cap=9, center=(73.5, 21), spacing=2, color='e2ed5c'),
    dict(sprite='sTutorial', frame=6, rect=(24, 11, 45, 25), bg='00000000', inks=['e2ed5c'],
         area=(22, 4, 46, 32), text='LUB', style=PIXEL, cap=9, center=(34, 18), spacing=1, color='e2ed5c'),
    dict(sprite='sTutorial', frame=6, fill=(55, 15, 96, 24), fillcolor='e2ed5c',
         area=(52, 13, 99, 26), text='SPACJA', style=PIXEL, cap=9, center=(76, 19.5), spacing=2, color='00000000'),
    # Mission select: the "Back" button (frame 1 highlighted) and the folder.
    dict(sprite='sMissionBack', frame=0, rect=(3, 3, 36, 14), bg='9a8a74', inks=['635845'],
         area=(3, 2, 68, 16), text='Wstecz', style=SERIF, cap=9, left=4, center=(0, 8.5), spacing=0, color='635845'),
    dict(sprite='sMissionBack', frame=1, rect=(3, 3, 36, 14), bg='9a8a74', inks=['ffffff'],
         area=(3, 2, 70, 16), text='Wstecz', style=SERIF, cap=9, left=4, center=(0, 8.5), spacing=0, color='ffffff'),
    dict(sprite='sMissionFolder', frame=0, rect=(13, 10, 41, 20), bg='9a8a74', inks=['635845'],
         area=(13, 9, 90, 20), text='Nazwa:', style=MONO, cap=8, left=14, center=(0, 15), spacing=0, color='635845'),
    dict(sprite='sMissionFolder', frame=0, rect=(13, 25, 48, 35), bg='9a8a74', inks=['635845'],
         area=(13, 24, 62, 35), text='Nr akt:', style=MONO, cap=8, left=14, center=(0, 30), spacing=0, color='635845'),
]


# Own pixel face for the tutorial (1 px stroke, 7-row capitals stretched to 9).
PIXEL_GLYPHS = {
    'A': ['.##.', '#..#', '#..#', '####', '#..#', '#..#', '#..#'],
    'B': ['###.', '#..#', '#..#', '###.', '#..#', '#..#', '###.'],
    'C': ['.###', '#...', '#...', '#...', '#...', '#...', '.###'],
    'E': ['####', '#...', '#...', '###.', '#...', '#...', '####'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
    'J': ['.###', '...#', '...#', '...#', '...#', '#..#', '.##.'],
    'K': ['#..#', '#.#.', '##..', '##..', '#.#.', '#..#', '#..#'],
    'L': ['#...', '#...', '#...', '#...', '#...', '#...', '####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'O': ['.##.', '#..#', '#..#', '#..#', '#..#', '#..#', '.##.'],
    'P': ['###.', '#..#', '#..#', '###.', '#...', '#...', '#...'],
    'R': ['###.', '#..#', '#..#', '###.', '#.#.', '#..#', '#..#'],
    'S': ['.###', '#...', '#...', '.##.', '...#', '...#', '###.'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#..#', '#..#', '#..#', '#..#', '#..#', '#..#', '.##.'],
    'Y': ['#.#', '#.#', '#.#', '.#.', '.#.', '.#.', '.#.'],
    'Z': ['####', '...#', '...#', '..#.', '.#..', '#...', '####'],
}


def render_pixel(text, spacing=1, seed=3):
    """Mask from the own face: rows 1 and 5 doubled (9 px), letters bounce ±1 px like handwriting."""
    rnd = random.Random(seed)
    glyphs = [PIXEL_GLYPHS[c] for c in text]
    width = sum(len(g[0]) for g in glyphs) + spacing * (len(glyphs) - 1)
    img = Image.new('L', (width, 11), 0)
    x = 0
    for g in glyphs:
        rows = g[:2] + g[1:2] + g[2:6] + g[5:6] + g[6:]
        dy = 1 + rnd.choice((-1, 0, 0, 1))
        for y, row in enumerate(rows):
            for xx, ch in enumerate(row):
                if ch == '#':
                    img.putpixel((x + xx, y + dy), 255)
        x += len(g[0]) + spacing
    return img.crop(img.getbbox())


def render(text, style, cap, spacing, bold=None):
    """Text mask (Image 'L', 0/255) with cap height `cap`."""
    if style is PIXEL:
        return render_pixel(text, spacing)
    path = str(FONTS / style['font'])
    size = cap
    for _ in range(60):   # size search: height of "H"
        font = ImageFont.truetype(path, size)
        box = font.getbbox('H')
        if box[3] - box[1] >= cap:
            break
        size += 1
    top = font.getbbox('H')[1]
    widths = [font.getlength(c) for c in text]
    img = Image.new('L', (int(sum(widths) + spacing * len(text) + cap * 2), cap * 3), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = '1'
    x = cap // 2
    for c, w in zip(text, widths):
        d.text((x, cap - top), c, font=font, fill=255)
        x += w + spacing
    thick = bold if bold is not None else style.get('bold', 0)
    for _ in range(thick):
        img = img.filter(ImageFilter.MaxFilter(3)) if thick > 1 else _thicken(img)
    return img.crop(img.getbbox())


def _thicken(img):
    """1 px bold to the right and down (like a marker), no sideways swelling."""
    out = img.copy()
    out.paste(255, mask=img.transform(img.size, Image.AFFINE, (1, 0, -1, 0, 1, 0)))
    out.paste(255, mask=img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, -1)))
    return out


def build():
    """Operations for the plugin, in execution order."""
    ops = []
    rnd = random.Random(7)
    for lab in LABELS:
        s, f = lab['sprite'], lab['frame']
        if 'fill' in lab:
            ops.append(('fill', s, f, *lab['fill'], lab['fillcolor']))
        else:
            ops.append(('erase', s, f, *lab['rect'], lab['bg'], lab['inks'], 12))
        mask = render(lab['text'], lab['style'], lab['cap'], lab['spacing'], lab.get('bold'))
        cx, cy = lab['center']
        mx, my = round(cx - mask.width / 2), round(cy - mask.height / 2)
        if 'left' in lab:
            mx = lab['left']
        ax0, ay0, ax1, ay1 = lab['area']   # label interior where the new text may go
        if mx < ax0 or my < ay0 or mx + mask.width - 1 > ax1 or my + mask.height - 1 > ay1:
            raise SystemExit(f"{lab['text']}: mask {mask.size} at ({mx}, {my}) does not fit in {lab['area']}")
        for color, dx, dy in lab.get('shadow', []):
            ops.append(('mask', s, f, mx + dx, my + dy, mask, color))
        ops.append(('mask', s, f, mx, my, mask, lab['color']))
        if lab.get('mottle'):   # worn ink as in the original
            mot = Image.new('L', mask.size, 0)
            src, dst = mask.load(), mot.load()
            for y in range(mask.height):
                for x in range(mask.width):
                    if src[x, y] and (x + 2 * y) % 5 == 0 and rnd.random() < 0.8:
                        dst[x, y] = 255
            ops.append(('mask', s, f, mx, my, mot, lab['mottle']))
    return ops


def count(img: Image.Image, op) -> int:
    """How many old-text pixels erase paints / how many transparent ones fill fills, like the plugin."""
    px = img.load()
    kind, _, _, x0, y0, x1, y1 = op[:7]
    n = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = px[x, y]
            if kind == 'fill':
                n += p[3] == 0
            elif p[3] and any(sum(abs(a - b) for a, b in zip(p[:3], rgba(i)[:3])) <= op[9] for i in op[8]):
                n += 1
    return n


def write_recipe(path: Path, game: Path) -> int:
    """labels.txt for the plugin; expected pixel counts from game graphics (the plugin compares ±10%)."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from inspect_game import DataWin
    ops = build()
    frames = {(n, k): img.copy() for n, k, img in DataWin(game / 'data.win').sprite_frames({lab['sprite'] for lab in LABELS})}
    lines = []
    for op in ops:
        kind, sprite, frame = op[:3]
        work = frames[(sprite, frame)]
        if kind == 'erase':
            x0, y0, x1, y1, bg, inks, tol = op[3:]
            lines.append(f'erase\t{sprite}\t{frame}\t{x0}\t{y0}\t{x1}\t{y1}\t{bg}\t{",".join(inks)}\t{tol}\t{count(work, op)}\n')
            apply(work, [op], sprite, frame)
        elif kind == 'fill':
            x0, y0, x1, y1, color = op[3:]
            lines.append(f'fill\t{sprite}\t{frame}\t{x0}\t{y0}\t{x1}\t{y1}\t{color}\t{count(work, op)}\n')
            apply(work, [op], sprite, frame)
        else:
            x, y, mask, color = op[3:]
            rows = ['' .join('1' if mask.getpixel((xx, yy)) else '0' for xx in range(mask.width))
                    for yy in range(mask.height)]
            lines.append(f'mask\t{sprite}\t{frame}\t{x}\t{y}\t{mask.width}\t{mask.height}\t{color}\t{"/".join(rows)}\n')
            apply(work, [op], sprite, frame)
    path.write_text(''.join(lines), encoding='ascii', newline='\n')
    return len(lines)


def apply(img: Image.Image, ops, sprite, frame):
    """What the plugin will do, on a copy of the frame (preview)."""
    px = img.load()
    for op in ops:
        kind, s, f = op[:3]
        if (s, f) != (sprite, frame):
            continue
        if kind == 'erase':
            x0, y0, x1, y1, bg, inks, tol = op[3:]
            inks = [rgba(i) for i in inks]
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    p = px[x, y]
                    if p[3] and any(sum(abs(a - b) for a, b in zip(p[:3], ink[:3])) <= tol for ink in inks):
                        px[x, y] = rgba(bg)
        elif kind == 'fill':
            x0, y0, x1, y1, color = op[3:]
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    px[x, y] = rgba(color)
        else:
            x, y, mask, color = op[3:]
            c = rgba(color)
            for yy in range(mask.height):
                for xx in range(mask.width):
                    if mask.getpixel((xx, yy)):
                        px[x + xx, y + yy] = c
    return img


def preview(game: Path):
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from inspect_game import DataWin
    ops = build()
    dw = DataWin(game / 'data.win')
    frames = {(n, k): img for n, k, img in dw.sprite_frames({lab['sprite'] for lab in LABELS})}
    out = []
    for (name, k), img in frames.items():
        if not any(op[1] == name and op[2] == k for op in ops):
            continue
        after = apply(img.copy(), ops, name, k)
        if name == 'sMain':
            img, after = img.crop((100, 90, 320, 420)), after.crop((100, 90, 320, 420))
        if name == 'sMissionFolder':
            img, after = img.crop((0, 0, 100, 45)), after.crop((0, 0, 100, 45))
        pair = Image.new('RGBA', (img.width * 2 + 8, img.height), (40, 40, 40, 255))
        pair.alpha_composite(img, (0, 0))
        pair.alpha_composite(after, (img.width + 8, 0))
        scale = 3 if name == 'sMain' else 6
        out.append((f'{name}-{k}', pair.resize((pair.width * scale, pair.height * scale), Image.NEAREST)))
    for name, im in out:
        im.save(ROOT / f'work/labels-preview-{name}.png')
    return [n for n, _ in out]


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    print(preview(ap.parse_args().game))
