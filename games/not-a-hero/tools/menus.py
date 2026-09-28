"""Menu graphics beyond the main menu: level list, election progress, character
cards, controller notices and the final boss prompt.

Positions, fonts and spacing were measured on the English originals
(tools/locate.py and pixel bands); see docs/technical.md. Text comes from en-pl-review.json.
`{...}` in a line marks the highlight colour (red percentage, white key names).
"""
import re

import numpy as np
from PIL import Image, ImageDraw

from fonts import render

SMALL = 3424  # 8x12 cells, the menu font
BOLD = 3037   # 12x19 cells, cap height 14


def segments(line):
    """Split 'A {B} C' into [(text, highlighted)]."""
    return [(part, i % 2 == 1) for i, part in enumerate(re.split(r'[{}]', line)) if part]


def draw_line(image, line, fonts, x, y, colors, font=SMALL, cell=(8, 12), advance=7, scale=1, center=False):
    """Draw a line whose glyph cells start at (x, y); `center` makes x the midpoint."""
    plain = line.replace('{', '').replace('}', '')
    width = ((len(plain) - 1) * advance + cell[0]) * scale
    left = x - width // 2 if center else x
    pos = 0
    for text, highlight in segments(line):
        label = render(text, fonts[font], *cell, colors[1 if highlight else 0], advance)
        if scale != 1:
            label = label.resize((label.width * scale, label.height * scale), Image.Resampling.NEAREST)
        image.alpha_composite(label, (left + pos * advance * scale, y))
        pos += len(text)
    assert 0 <= left and left + width <= image.width, (line, left, width, image.width)
    return left, width


def brightest(pixels):
    return max(pixels, key=lambda c: sum(c[:3]) * c[3])


def level_list(assets, mapping, fonts, pl):
    """DAY n / SECRET n entries in three states (selected, normal, locked)."""
    # Entries sit 14 px apart: DAY 1..21, then SECRET 1..3. The game draws digits
    # without their left bearing, so only the word is matched pixel-exactly.
    words = {w: np.asarray(render(w, fonts[SMALL], 8, 12, advance=7))[..., 3] > 0 for w in ('DAY', 'SECRET')}
    result = {}
    for index in sorted({mapping[i] for i in range(88, 277)}):
        im = assets.image(index)
        arr = np.asarray(im)
        visible = (arr[..., 3] > 0) & (arr[..., :3].max(axis=2) > 25)
        rows = np.nonzero(visible[:, 126:].any(axis=1))[0]
        y = rows.min() - 3  # cap top sits 3 px into the cell
        slot = (rows.min() - 66) // 14 + 1
        assert (rows.min() - 66) % 14 == 0, index
        word = 'DAY' if slot <= 21 else 'SECRET'
        number = slot if slot <= 21 else slot - 21
        template = words[word]
        assert (visible[y:y + template.shape[0], 128:128 + template.shape[1]] == template).all(), (index, word)
        color = brightest(im.crop((128, y, im.width, y + 12)).get_flattened_data())
        background = im.getpixel((im.width - 1, y + 6))
        ImageDraw.Draw(im).rectangle((127, y, im.width - 1, y + 11), fill=background)
        polish = pl['menu|' + ('day' if word == 'DAY' else 'secret')] + f' {number}'
        draw_line(im, polish, fonts, 128, y, (color, color))
        result[index] = im
    return result


def election(assets, mapping, fonts, pl):
    """Progress checklist (mayor → global megalord) and the ELECTION DAY caption."""
    rows = [(0, 'megalord'), (12, 'king'), (24, 'minister'), (36, 'mayor')]
    result = {}
    for index in sorted({mapping[i] for i in range(346, 355)}):
        im = assets.image(index)
        background = im.getpixel((126, 47))
        draw = ImageDraw.Draw(im)
        for top, term in rows:
            color = brightest(im.crop((12, top, 127, top + 8)).get_flattened_data())
            draw.rectangle((12, top, 126, top + 7), fill=background)
            # The top row starts at the image edge; 2 px lower keeps accents visible.
            draw_line(im, pl['menu|' + term], fonts, 12, top - 3 + (2 if top == 0 else 0), (color, color))
        # ELECTION DAY spans the full width, from x=0.
        color = brightest(im.crop((0, 51, 127, 65)).get_flattened_data())
        draw.rectangle((0, 51, 126, 64), fill=background)
        draw_line(im, pl['menu|election'], fonts, 63, 51 - 5, (color, color), BOLD, (12, 19), 10, center=True)
        result[index] = im
    return result


def election_day(assets, fonts, pl):
    """Big DAY 22 / ELECTION DAY caption with its underline (image 786)."""
    im = assets.image(786)
    background = im.getpixel((5, 5))
    white = brightest(im.crop((164, 114, 413, 138)).get_flattened_data())
    ImageDraw.Draw(im).rectangle((100, 70, im.width - 100, 150), fill=background)
    # 5 px higher than the original, so accents of the big line below stay clear.
    draw_line(im, pl['menu|day'] + ' 22', fonts, 289, 91 - 6 - 5, (white, white), scale=2, center=True)
    left, width = draw_line(im, pl['menu|election_day'], fonts, 289, 114 - 9, (white, white), scale=3, center=True)
    ImageDraw.Draw(im).rectangle((left, 145, left + width - 3, 147), fill=white)
    return {786: im}


def cards(assets, fonts, pl, ids):
    """Character select cards: the description under the name, font 3424, pitch 9."""
    result = {}
    for index in ids:
        im = assets.image(index)
        arr = np.asarray(im).astype(int)
        text = ((arr[..., :3].min(axis=2) > 225) | ((arr[..., 0] > 180) & (arr[..., 1] < 110))) & (arr[..., 3] > 0)
        rows = np.nonzero(text[60:].any(axis=1))[0] + 60
        white = brightest(im.crop((0, rows.min(), im.width, rows.max() + 1)).get_flattened_data())
        red = (255, 38, 38, 255)
        if ((arr[60:, :, 0] > 180) & (arr[60:, :, 1] < 110) & (arr[60:, :, 3] > 0)).any():
            reds = arr[60:][(arr[60:, :, 0] > 180) & (arr[60:, :, 1] < 110) & (arr[60:, :, 3] > 0)]
            red = tuple(int(v) for v in reds[0])
        ImageDraw.Draw(im).rectangle((0, 66, im.width - 1, im.height - 1), fill=im.getpixel((2, im.height - 2)))
        lines = pl[f'card|{index}'].split('\n')
        assert 71 + 13 * (len(lines) - 1) + 8 <= im.height, index
        for row, line in enumerate(lines):
            draw_line(im, line, fonts, im.width // 2, 71 + 13 * row - 3, (white, red), advance=9, center=True)
        result[index] = im
    return result


def controller(assets, fonts, pl):
    """Controller detected / press start notices; the pad icon stays."""
    result = {}
    # (image, term, first cell top, number of lines); line pitch is 10 px.
    for index, term, top, count in [(1892, 'controller_detected', 3, 4), (149, 'press_start', 8, 2)]:
        im = assets.image(index)
        arr = np.asarray(im)
        # Grey text is white with partial alpha, so weigh colour by alpha.
        visible = lambda y0, y1: [tuple(int(v) for v in p) for p in arr[y0:y1, 3:141].reshape(-1, 4)
                                  if p[3] > 40 and max(p[:3]) > 60]
        strength = lambda c: sum(c[:3]) * c[3]
        bright = max(visible(top + 1, top + 9), key=strength)
        dim = min(visible(top + 11, top + 10 * count) or [bright], key=strength)
        fill = tuple(int(v) for v in arr[5, 5])  # box interior, (nearly) transparent
        ImageDraw.Draw(im).rectangle((2, top, im.width - 3, top + 10 * count + 1), fill=fill)
        for row, line in enumerate(pl['menu|' + term].split('\n')):
            # 1892: white heading, grey lines with white key names; 149: one red colour.
            colors = (bright, bright) if row == 0 or index == 149 else (dim, bright)
            draw_line(im, line, fonts, im.width // 2, top + 10 * row, colors, center=True)
        result[index] = im
    return result


def shoot_her(assets, mapping, fonts, pl):
    """Boss prompt: two black lines inside a white box whose position varies."""
    first, second = pl['menu|shoot_her'].split('\n')
    result = {}
    for index in sorted({mapping[i] for i in range(446, 478)}):
        im = assets.image(index)
        arr = np.asarray(im).astype(int)
        dark = (arr[..., :3].max(axis=2) < 60) & (arr[..., 3] > 200)
        ys, xs = np.nonzero(dark[:, 8:70])
        x0, x1 = xs.min() + 8, xs.max() + 8
        ImageDraw.Draw(im).rectangle((x0, ys.min(), x1, ys.max()), fill=(255, 255, 255, 255))
        black = tuple(arr[ys[0], xs[0] + 8])
        middle = (x0 + x1 + 1) // 2
        draw_line(im, first, fonts, middle, ys.min() - 5, (black, black), BOLD, (12, 19), 11, center=True)
        draw_line(im, second, fonts, middle, ys.min() + 16 - 5, (black, black), BOLD, (12, 19), 11, center=True)
        result[index] = im
    return result


def reset_confirm(assets, mapping, fonts, pl):
    """Reset progress warning (red, three lines) and the NO / YES choice."""
    warning = pl['menu|reset_warning'].split('\n')
    result = {}
    for index in sorted({mapping[i] for i in range(336, 346)}):
        im = assets.image(index)
        red = brightest(im.crop((221, 122, 340, 130)).get_flattened_data())
        choices = [(175, pl['menu|no']), (189, pl['menu|yes'])]
        colors = [brightest(im.crop((221, y + 3, 260, y + 11)).get_flattened_data()) for y, _ in choices]
        ImageDraw.Draw(im).rectangle((220, 118, im.width - 1, 202), fill=im.getpixel((im.width - 1, 150)))
        for y, line in zip((119, 133, 161), warning):
            draw_line(im, line, fonts, 221, y, (red, red))
        for (y, line), color in zip(choices, colors):
            draw_line(im, line, fonts, 221, y, (color, color))
        result[index] = im
    return result


def polish_flag(assets):
    """Language select: the English flag (6170) becomes the Polish one.

    Frame pixels are those shared by the French and Spanish flags; the field
    between them gets the white and red of the game's own French flag.
    """
    french = np.asarray(assets.image(6174)).astype(int)
    spanish = np.asarray(assets.image(6172)).astype(int)
    field = (french != spanish).any(axis=2)
    ys, xs = np.nonzero(field)
    top, bottom, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    white = tuple(int(v) for v in french[(top + bottom) // 2, (left + right) // 2])
    red = tuple(int(v) for v in french[(top + bottom) // 2, right - 2])
    flag = french.copy()
    middle = (top + bottom + 1) // 2
    flag[top:middle, left:right + 1] = white
    flag[middle:bottom + 1, left:right + 1] = red
    assert assets.image(6170).size == assets.image(6174).size
    return {6170: Image.fromarray(flag.astype(np.uint8), 'RGBA')}
