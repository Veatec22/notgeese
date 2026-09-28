"""Polish letters for BPM's fonts: ąćęłńśźż and capitals.

Neither MotorBlock nor RunyTunes has them. Each new letter is a TrueType composite:
a reference to the font's own base letter plus a diacritic mark drawn here from a few
points - acute, dot, ogonek, stroke. The added glyph data is therefore entirely ours;
nothing of the original outlines is copied, only referenced by glyph index.

    python fonts_pl.py <font.ufont> <style> <out.ufont>

`style` picks the mark geometry: motorblock or runytunes.
"""
import copy
import sys

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

# letter -> (base, mark)
LETTERS = {
    'ą': ('a', 'ogonek'), 'ć': ('c', 'acute'), 'ę': ('e', 'ogonek'), 'ł': ('l', 'stroke'),
    'ń': ('n', 'acute'), 'ś': ('s', 'acute'), 'ź': ('z', 'acute'), 'ż': ('z', 'dot'),
    'Ą': ('A', 'ogonek'), 'Ć': ('C', 'acute'), 'Ę': ('E', 'ogonek'), 'Ł': ('L', 'stroke'),
    'Ń': ('N', 'acute'), 'Ś': ('S', 'acute'), 'Ź': ('Z', 'acute'), 'Ż': ('Z', 'dot'),
}


def motorblock(case, base_box):
    """Blocky marks: parallelograms and squares at the font's stem widths."""
    x0, y0, x1, y1 = base_box
    stem = 160 if case == 'lower' else 200
    top = y1
    cx = (x0 + x1) / 2
    if case == 'lower':
        acute = [(cx - 117, top + 60), (cx - 35, top + 230), (cx + 116, top + 230), (cx + 35, top + 60)]
        dot = [(cx - 80, top + 60), (cx - 80, top + 220), (cx + 80, top + 220), (cx + 80, top + 60)]
    else:
        acute = [(cx - 117, top + 86), (cx - 35, top + 256), (cx + 116, top + 256), (cx + 35, top + 86)]
        dot = [(cx - 100, top + 76), (cx - 100, top + 256), (cx + 100, top + 256), (cx + 100, top + 76)]
    # Ogonek: a block hanging from the right half of the baseline, cut on the diagonal
    # like the font's own terminals, ending in a foot that points right.
    d = stem
    if y0 < -d * 0.5:
        # a/A already end in a spike below the baseline: the ogonek is a foot turning
        # left from its tip.
        ogonek = [(x1, y0 + d * 0.3), (x1, y0 - d * 0.75), (x1 - d * 1.3, y0 - d * 0.75),
                  (x1 - d * 1.3, y0 - d * 0.3), (x1 - d * 0.5, y0 - d * 0.3), (x1 - d * 0.5, y0 + d * 0.3)]
    else:
        ogonek = [(x1 - d * 1.5, 0), (x1 - d * 1.5, -d * 1.1), (x1 - d * 0.5, -d * 1.1),
                  (x1 - d * 0.5, -d * 0.55), (x1 - d * 0.9, -d * 0.55), (x1 - d * 0.9, 0)]
    # Stroke: a slanted bar through the stem at half height.
    mid = (y1 - y0) / 2
    t = stem * 0.55
    stroke = [(x0 - stem * 0.35, mid - stem * 0.6), (x0 - stem * 0.35, mid - stem * 0.6 + t),
              (x0 + stem * 1.45, mid + stem * 0.35 + t), (x0 + stem * 1.45, mid + stem * 0.35)]
    return dict(acute=acute, dot=dot, ogonek=ogonek, stroke=stroke)


def runytunes(case, base_box):
    """Thin marks for the narrow art-deco capitals (both cases share glyphs)."""
    x0, y0, x1, y1 = base_box
    cx = (x0 + x1) / 2
    acute = [(cx - 99, 854), (cx - 73, 914), (cx + 99, 988), (cx + 125, 928)]
    dot = [(cx - 42, 872), (cx - 42, 956), (cx + 42, 956), (cx + 42, 872)]
    # Ogonek: a thin hook curling left under the right foot of the letter.
    ogonek = [(x1 - 84, 0), (x1 - 84, -70), (x1 - 110, -110), (x1 - 150, -140), (x1 - 150, -170),
              (x1 - 100, -150), (x1 - 50, -110), (x1 - 30, -60), (x1 - 30, 0)]
    stem, mid = 84, (y1 - y0) / 2
    stroke = [(x0 - 40, mid - 40), (x0 - 40, mid + 10), (x0 + 150, mid + 110), (x0 + 150, mid + 60)]
    return dict(acute=acute, dot=dot, ogonek=ogonek, stroke=stroke)


STYLES = {'motorblock': motorblock, 'runytunes': runytunes}


def polygon_glyph(points):
    pen = TTGlyphPen(None)
    pen.moveTo(points[0])
    for p in points[1:]:
        pen.lineTo(p)
    pen.closePath()
    return pen.glyph()


def ensure_clockwise(points):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
    # TrueType outer contours run clockwise (negative area in y-up coordinates).
    return points if area < 0 else points[::-1]


def open_font(path):
    """No bounding-box recalculation on save: it would decode and re-encode every glyph
    of the font. The glyphs we add get their bounds and maxp limits set by `extend`."""
    return TTFont(path, recalcBBoxes=False)


def extend(font, style):
    glyf, hmtx, cmap = font['glyf'], font['hmtx'], font.getBestCmap()
    added = []
    for letter, (base_char, mark) in LETTERS.items():
        if ord(letter) in cmap:
            continue
        base = cmap[ord(base_char)]
        # Measure a copy: expanding the font's own glyph would make fontTools re-encode it,
        # and the rebuilt font would no longer carry the original bytes unchanged.
        g = copy.deepcopy(glyf[base])
        g.expand(glyf)
        g.recalcBounds(glyf)
        box = (g.xMin, g.yMin, g.xMax, g.yMax)
        case = 'lower' if letter.islower() else 'upper'
        points = STYLES[style](case, box)[mark]
        points = ensure_clockwise([(round(x), round(y)) for x, y in points])
        mark_name = f'pl.{mark}.{base}'
        mark_glyph = polygon_glyph(points)
        mark_glyph.recalcBounds(glyf)
        glyf[mark_name] = mark_glyph
        hmtx[mark_name] = (0, min(p[0] for p in points))

        composite = Glyph()
        composite.numberOfContours = -1
        composite.components = []
        for name in (base, mark_name):
            c = GlyphComponent()
            c.glyphName, c.x, c.y, c.flags = name, 0, 0, 0x4  # ROUND_XY_TO_GRID
            composite.components.append(c)
        composite.components[0].flags |= 0x200  # USE_MY_METRICS
        name = f'uni{ord(letter):04X}'
        glyf[name] = composite
        # Bounds from the measured copy and the mark, not recalcBounds: that would expand
        # the font's own base glyph in place.
        composite.xMin, composite.yMin = min(g.xMin, mark_glyph.xMin), min(g.yMin, mark_glyph.yMin)
        composite.xMax, composite.yMax = max(g.xMax, mark_glyph.xMax), max(g.yMax, mark_glyph.yMax)
        points = len(g.coordinates) + len(mark_glyph.coordinates)
        contours = g.numberOfContours + mark_glyph.numberOfContours
        maxp = font['maxp']
        maxp.maxComponentElements = max(maxp.maxComponentElements, 2)
        maxp.maxComponentDepth = max(maxp.maxComponentDepth, 1)
        maxp.maxCompositePoints = max(maxp.maxCompositePoints, points)
        maxp.maxCompositeContours = max(maxp.maxCompositeContours, contours)
        hmtx[name] = hmtx[base]
        added.append((letter, name))

    font.setGlyphOrder(glyf.glyphOrder)
    for table in font['cmap'].tables:
        if table.isUnicode():
            for letter, name in added:
                table.cmap[ord(letter)] = name
    post = font['post']
    if post.formatType == 2.0:
        post.extraNames = []
        post.mapping = {}
    return added


def main():
    source, style, out = sys.argv[1:4]
    font = open_font(source)
    added = extend(font, style)
    font.save(out)
    check = TTFont(out).getBestCmap()
    missing = [letter for letter in LETTERS if ord(letter) not in check]
    assert not missing, missing
    print(f'{out}: +{len(added)} letters')


if __name__ == '__main__':
    main()
