"""Polish glyphs composed locally from each of the game's own sprite fonts.

The game maps bytes 32..255 to sprite cells (Windows-1252 glyphs). Polish
letters go to CP1250 positions where those are unused by the game's French,
German, Italian and Spanish texts; five CP1250 positions hold letters those
languages need (Œ £ Ñ Ê ¿), so Ś Ł Ń Ę ż move to free cells instead. Every
other byte stays Windows-1252. No font or game images are stored in this repo.
"""
from PIL import Image, ImageDraw

POLISH = {
    'Ą': 0xA5, 'Ć': 0xC6, 'Ę': 0xCB, 'Ł': 0xA4, 'Ń': 0xD0, 'Ó': 0xD3, 'Ś': 0x8A, 'Ź': 0x8F, 'Ż': 0xAF,
    'ą': 0xB9, 'ć': 0xE6, 'ę': 0xEA, 'ł': 0xB3, 'ń': 0xF1, 'ó': 0xF3, 'ś': 0x9C, 'ź': 0x9F, 'ż': 0xBE,
}
# Ó/ó keep the Windows-1252 glyph, which is the same letter.
KEEP = {'Ó', 'ó'}


def encode(text: str) -> bytes:
    """Game bytes for text: Polish letters per POLISH, the rest Windows-1252."""
    return b''.join(bytes([POLISH[c]]) if c in POLISH else c.encode('cp1252') for c in text)

# IDs and cell sizes read from constructors referencing the 224-character map.
# ID 789 uses a different layout and is excluded pending a relevant in-game case.
FONT_CELLS = {
    2088: (7, 9), 3017: (8, 12), 272: (14, 24), 2744: (11, 14),
    3025: (25, 30), 3037: (12, 19), 3424: (8, 12), 3844: (11, 14),
    5334: (9, 11), 5386: (11, 14), 5829: (8, 12), 5863: (22, 32),
    5866: (7, 13), 5867: (18, 26), 5872: (18, 26), 6183: (18, 26),
    950: (11, 12), 13919: (12, 22), 14546: (22, 35),
    # Found by atlas shape, not by constructor: the in-game dialogue box font.
    5392: (9, 11), 5873: (8, 11),
}


def box(code: int, cw: int, ch: int):
    n = code - 32
    return (n % 32 * cw, n // 32 * ch, (n % 32 + 1) * cw, (n // 32 + 1) * ch)


def polish_font(source: Image.Image, cw: int, ch: int) -> Image.Image:
    result = source.copy()
    for pl, base in zip('ĄĆĘŁŃÓŚŹŻąćęłńóśźż', 'ACELNOSZZacelnoszz'):
        # Ó/ó already occupy the same positions in Western and Polish encodings.
        if pl in KEEP:
            continue
        glyph = source.crop(box(ord(base), cw, ch))
        bounds = glyph.getchannel('A').getbbox()
        assert bounds, (pl, cw, ch)
        x0, y0, x1, y1 = bounds
        color = max(glyph.get_flattened_data(), key=lambda rgba: rgba[3] * sum(rgba[:3]))
        thickness = max(1, cw // 9)
        mark = max(2, ch // 7)
        kind = pl.upper()
        if kind in 'ĆŃŚŹŻ':
            # Reserve the existing top margin; shift a tightly packed glyph down
            # if needed, without changing the cell dimensions or advance.
            if y0 < mark:
                shifted = Image.new('RGBA', glyph.size)
                shifted.paste(glyph, (0, mark - y0))
                glyph = shifted
            d = ImageDraw.Draw(glyph)
            center = (x0 + x1) // 2
            if kind == 'Ż':
                d.rectangle((center, 0, min(cw - 1, center + thickness - 1), thickness - 1), fill=color)
            else:
                d.line((center, mark - 1, min(cw - 2, center + mark - 1), 0), fill=color, width=thickness)
        elif kind in 'ĄĘ':
            # Put the ogonek below the right stem. A tight cell gets two spare
            # baseline rows by nearest-neighbour compression of the base glyph.
            tail = max(2, ch // 7)
            if y1 + tail > ch:
                body = glyph.crop((0, y0, cw, y1))
                body = body.resize((cw, ch - y0 - tail), Image.Resampling.NEAREST)
                glyph = Image.new('RGBA', (cw, ch))
                glyph.paste(body, (0, y0))
                y1 = ch - tail
            d = ImageDraw.Draw(glyph)
            x = max(1, x1 - 2)
            d.line((x, y1 - 1, max(0, x - 1), y1 + tail - 2, x, y1 + tail - 1), fill=color, width=thickness)
        elif kind == 'Ł':
            d = ImageDraw.Draw(glyph)
            y = (y0 + y1) // 2
            d.line((max(0, x0 - 1), y + 1, min(cw - 2, x0 + max(3, cw // 2)), y - 1), fill=color, width=thickness)
        result.paste(glyph, box(POLISH[pl], cw, ch)[:2])
    for code in range(32, 127):
        assert result.crop(box(code, cw, ch)).tobytes() == source.crop(box(code, cw, ch)).tobytes()
    return result


def render(text: str, atlas: Image.Image, cw: int, ch: int, color=(255, 255, 255, 255), advance=None):
    advance = cw if advance is None else advance
    result = Image.new('RGBA', (max(1, (len(text) - 1) * advance + cw), ch))
    for i, code in enumerate(encode(text)):
        glyph = atlas.crop(box(code, cw, ch))
        tinted = Image.new('RGBA', glyph.size, color)
        tinted.putalpha(glyph.getchannel('A').point(lambda a: a * color[3] // 255))
        result.alpha_composite(tinted, (i * advance, 0))
    return result
