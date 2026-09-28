"""Polish letters of font `f_uni` ("Visitor TT2 BRK", 5×7 pixels).

The font has entries for every Polish letter, but their atlas cells are empty: GameMaker
rendered a char range the face didn't contain. Letters are composed from the game's own
letters: the acute is the accent from "Ó" (two diagonal pixels in rows 0–1), the dot is one
pixel in row 1, the ogonek is a hook in rows 7–8 under the letter's right side, like the
cedilla of "Ç", which also reaches two rows below the line (glyph height 9 instead of 7).

The font's lower-case letters are capitals, but not always the same ones ("n" differs from
"N"), so each Polish letter is built from its own base of the same case.

All 16 letters get new cells in the empty band at the bottom of the texture page (from row
1424; page content ends at 1418). Glyph coordinates count from the font rect's origin but
may point anywhere on the same page. So only the end of the PNG changes and the patch
carries no game pixels (pngsplice.py). Glyph structures change in place: x, y and height.
"""
from __future__ import annotations

from PIL import Image

from hld import Font

FONT = 'f_uni'
WHITE = (255, 255, 255, 255)

ACUTE = [(3, 0), (2, 1)]
DOT = [(2, 1)]
OGONEK = [(3, 7), (4, 8)]
# Ł: stem moved to column 1, diagonal stroke across it (0,4)–(2,3).
L_STROKE = {
    2: '.#...',
    3: '.##..',
    4: '##...',
    5: '.#...',
    6: '.####',
}

DESIGN = {
    'Ą': ('A', OGONEK), 'ą': ('a', OGONEK),
    'Ć': ('C', ACUTE), 'ć': ('c', ACUTE),
    'Ę': ('E', OGONEK), 'ę': ('e', OGONEK),
    'Ł': ('L', None), 'ł': ('l', None),
    'Ń': ('N', ACUTE), 'ń': ('n', ACUTE),
    'Ś': ('S', ACUTE), 'ś': ('s', ACUTE),
    'Ź': ('Z', ACUTE), 'ź': ('z', ACUTE),
    'Ż': ('Z', DOT), 'ż': ('z', DOT),
}
POLISH = ''.join(DESIGN)
PAGE_ROW = 1424     # first row of the letter band on the texture page


def cell(page: Image.Image, font: Font, char: str) -> Image.Image:
    g = font.glyphs[char]
    ax, ay = font.atlas[:2]
    return page.crop((ax + g.x, ay + g.y, ax + g.x + g.w, ay + g.y + g.h))


def pixels(img: Image.Image) -> set[tuple[int, int]]:
    return {(x, y) for x in range(img.width) for y in range(img.height) if img.getpixel((x, y))[3]}


def design(page: Image.Image, font: Font) -> dict[str, Image.Image]:
    """5×7 or 5×9 images of the Polish letters."""
    # Accent from the game itself: "Ó" minus "O", so the acute matches the font exactly.
    acute = pixels(cell(page, font, 'Ó')) - pixels(cell(page, font, 'O'))
    assert acute == set(ACUTE), acute
    cedilla = pixels(cell(page, font, 'Ç')) - pixels(cell(page, font, 'C'))
    assert {y for _, y in cedilla} == {7, 8}, cedilla   # ogonek in the same rows
    out = {}
    for char, (base, mark) in DESIGN.items():
        b = cell(page, font, base)
        assert b.size == (5, 7), (base, b.size)
        if mark is None:
            assert pixels(b) == {(0, y) for y in range(2, 7)} | {(x, 6) for x in range(5)}, base
            points = {(x, y) for y, row in L_STROKE.items() for x, c in enumerate(row) if c == '#'}
        else:
            points = pixels(b) | set(mark)
        h = 9 if mark is OGONEK else 7
        img = Image.new('RGBA', (5, h), (0, 0, 0, 0))
        for p in points:
            img.putpixel(p, WHITE)
        out[char] = img
    return out


def placement(font: Font) -> dict[str, tuple[int, int]]:
    """New glyph (x, y), relative to the font rect's origin."""
    ax, ay = font.atlas[:2]
    return {c: (2 + 7 * i - ax, PAGE_ROW - ay) for i, c in enumerate(DESIGN)}
