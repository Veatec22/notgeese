"""Render a line of text from a TrueType font to PNG, for checking glyphs by eye.

    python render.py <font> <out.png> <text> [size]
"""
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw


def parts(font, name):
    """Contour groups: one per component of a composite, filled independently."""
    glyph = font['glyf'][name]
    if glyph.isComposite():
        out = []
        for c in glyph.components:
            for group in parts(font, c.glyphName):
                out.append([[(x + c.x, y + c.y) for x, y in contour] for contour in group])
        return out
    return [contours(font, name)]


def contours(font, name):
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    out, current, last = [], [], None
    for op, args in pen.value:
        if op == 'moveTo':
            current = [args[0]]; last = args[0]
        elif op == 'lineTo':
            current.append(args[0]); last = args[0]
        elif op == 'qCurveTo':
            points = list(args)
            if points[-1] is None:
                points = points[:-1]
                start = points[-1]
                points = points + [start]
            on = last
            for i in range(len(points) - 1):
                c = points[i]
                end = points[i + 1] if i == len(points) - 2 else (
                    ((points[i][0] + points[i + 1][0]) / 2, (points[i][1] + points[i + 1][1]) / 2))
                for t in range(1, 9):
                    t /= 8
                    current.append(((1 - t) ** 2 * on[0] + 2 * (1 - t) * t * c[0] + t * t * end[0],
                                    (1 - t) ** 2 * on[1] + 2 * (1 - t) * t * c[1] + t * t * end[1]))
                on = end
            last = on
        elif op == 'curveTo':
            p0 = last
            c1, c2, p3 = args
            for t in range(1, 13):
                t /= 12
                current.append(tuple((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * c1[k]
                                     + 3 * (1 - t) * t * t * c2[k] + t ** 3 * p3[k] for k in range(2)))
            last = p3
        elif op in ('closePath', 'endPath'):
            if current:
                out.append(current)
            current = []
    return out


def render(font, text, size=96, margin=20):
    upm = font['head'].unitsPerEm
    scale = size / upm
    cmap = font.getBestCmap()
    hmtx = font['hmtx']
    asc, desc = font['hhea'].ascent, font['hhea'].descent
    width = sum(hmtx[cmap.get(ord(c), '.notdef')][0] for c in text) * scale + 2 * margin
    height = (asc - desc) * scale + 2 * margin
    image = Image.new('L', (int(width) + 1, int(height) + 1), 0)
    x = margin
    for ch in text:
        name = cmap.get(ord(ch), '.notdef')
        for group in parts(font, name):
            filled = Image.new('1', image.size, 0)
            for contour in group:
                mask = Image.new('L', image.size, 0)
                pts = [(x + px * scale, margin + (asc - py) * scale) for px, py in contour]
                if len(pts) > 2:
                    ImageDraw.Draw(mask).polygon(pts, fill=255)
                filled = ImageChops.logical_xor(filled, mask.convert('1'))
            image = ImageChops.logical_or(image.convert('1'), filled).convert('L')
        x += hmtx[name][0] * scale
    return ImageChops.invert(image)


if __name__ == '__main__':
    font = TTFont(sys.argv[1])
    render(font, sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 96).save(sys.argv[2])
