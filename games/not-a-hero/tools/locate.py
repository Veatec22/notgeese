"""Find where and in which sprite font a known English line is drawn in an image.

Used while mapping menu graphics: renders the line in every atlas and spacing,
then looks for a pixel-exact match of the glyph mask. Not used by the build.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from fonts import FONT_CELLS, render


def mask(image, threshold=60, dark=False):
    a = np.asarray(image.convert('RGBA'), dtype=np.int32)
    if dark:
        return (a[..., 3] > 0) & (a[..., :3].max(axis=2) < threshold)
    return (a[..., 3] > 0) & (a[..., :3].max(axis=2) > threshold)


def locate(image, text, atlases, threshold=60, dark=False):
    """Return [(font_id, advance, x, y)] for exact matches of `text` in `image`."""
    target = mask(image, threshold, dark)
    found = []
    for font, (cw, ch) in FONT_CELLS.items():
        for advance in range(max(1, cw - 4), cw + 5):
            glyphs = np.asarray(render(text, atlases[font], cw, ch, advance=advance))[..., 3] > 0
            rows, cols = np.nonzero(glyphs)
            if not len(rows):
                continue
            template = glyphs[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
            if template.shape[0] > target.shape[0] or template.shape[1] > target.shape[1]:
                continue
            windows = sliding_window_view(target, template.shape)
            hits = np.argwhere((windows == template).all(axis=(2, 3)))
            for y, x in hits:
                found.append((font, advance, int(x - cols.min()), int(y - rows.min())))
    return found
