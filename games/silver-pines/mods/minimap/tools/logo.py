"""Mod logo: the Silver Pines key art with a third red title block reading MINIMAP.

The new block is stitched from the letter-free top and bottom bands of the PINES block, so the
paint texture and torn edges are the game's own; text is set in Bahnschrift Bold, close to the title's even-weight letters.
Output goes to dist/ (key art is the publisher's promotional material, not committed).

    .venv\\Scripts\\python.exe games\\silver-pines\\mods\\minimap\\tools\\logo.py --art <keyart 1920x1080>
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

GAME = Path(__file__).resolve().parents[3]
FONT = Path('C:/Windows/Fonts/bahnschrift.ttf')
# PINES block in the 1920x1080 key art: x 992-1757, y 554-782; letters sit in y 615-705.
X0, X1, Y0, Y1 = 975, 1775, 548, 790
TOP_CUT, BOTTOM_CUT = 612, 708
GAP = 34
TEXT = 'MINIMAP'


def redness(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.clip((r - np.maximum(g, b) - 40) / 90.0, 0, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--art', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=GAME/'dist/minimap-logo.png')
    args = ap.parse_args()
    art = Image.open(args.art).convert('RGB')
    assert art.size == (1920, 1080), art.size
    a = np.asarray(art).astype(np.float32)

    top = a[Y0:TOP_CUT, X0:X1]
    bottom = a[BOTTOM_CUT:Y1, X0:X1]
    feather = 12
    # Overlap the bands by `feather` rows and cross-fade, so the seam disappears in the grain.
    h = top.shape[0] + bottom.shape[0] - feather
    block = np.zeros((h, X1 - X0, 3), np.float32)
    block[:top.shape[0]] = top
    w = np.linspace(0, 1, feather)[:, None, None]
    seam = top.shape[0] - feather
    block[seam:top.shape[0]] = top[-feather:] * (1 - w) + bottom[:feather] * w
    block[top.shape[0]:] = bottom[feather:]
    alpha = redness(block)
    alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))) / 255.0

    # Lettering: dark stencil text, eroded by the paint's own grain like the title letters.
    tile = Image.new('L', (block.shape[1], block.shape[0]), 0)
    d = ImageDraw.Draw(tile)
    font = ImageFont.truetype(str(FONT), int(h * 0.56))
    font.set_variation_by_name('Bold')
    spacing = int(h * 0.30)
    widths = [d.textlength(c, font=font) for c in TEXT]
    total = sum(widths) + spacing * (len(TEXT) - 1)
    x = (block.shape[1] - total) / 2
    bbox = font.getbbox('M')
    y = (block.shape[0] - (bbox[3] - bbox[1])) / 2 - bbox[1]
    for c, cw in zip(TEXT, widths):
        d.text((x, y), c, font=font, fill=255)
        x += cw + spacing
    letters = np.asarray(tile.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255.0
    rim = np.asarray(tile.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255.0
    grain = block.mean(axis=2)
    grain = (grain - grain.min()) / max(1.0, grain.max() - grain.min())
    rng = np.random.default_rng(7)
    wear = np.clip(1.25 - rng.random(letters.shape) * 0.25 - (1 - grain) * 0.35, 0, 1)
    ink = letters * wear
    painted = block.copy()
    painted = painted * (1 - rim[..., None] * 0.55)  # ink bleed: darker paint around the letters
    painted = painted * (1 - ink[..., None]) + np.array([12, 4, 4], np.float32) * ink[..., None]

    out = a.copy()
    ty = Y1 + GAP - (Y0 - 554)  # same visual gap as SILVER/PINES
    region = out[ty:ty + h, X0:X1]
    region[:] = region * (1 - alpha[..., None]) + painted * alpha[..., None]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    logo = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    logo.save(args.out)
    print(f'Wrote {args.out} (block {X1 - X0}x{h} at y {ty})')
    header(logo, args.out.with_name('minimap-header.png'))
    header(logo, args.out.with_name('minimap-banner-1920.jpg'), size=(1920, 1080), face_rows=(0, 1080),
           title_height=640, fade=260)


def header(logo, path, size=(1300, 372), face_rows=(25, 625), title_height=None, fade=140):
    """Banner layout: face on the left, the three title blocks scaled down on the right.

    Default is the Nexus header (1300x372); the gallery version is 1920x1080."""
    w, h = size
    bg = (1, 6, 9)  # the key art's near-black right side
    canvas = Image.new('RGB', size, bg)
    # Face: head top to chin, x 0-960 of the key art (left of the title blocks).
    top, bottom = face_rows
    s = h / (bottom - top)
    face = logo.crop((0, top, 960, bottom)).resize((round(960 * s), h), Image.LANCZOS)
    mask = np.ones((h, face.width), np.float32)
    mask[:, -fade:] = np.linspace(1, 0, fade)[None, :]
    canvas.paste(face, (0, 0), Image.fromarray((mask * 255).astype(np.uint8)))
    # Title group: SILVER, PINES, MINIMAP with a little of the dark surround.
    title = logo.crop((966, 280, 1776, 972))
    th = title_height or h - 44
    title = title.resize((round(title.width * th / title.height), th), Image.LANCZOS)
    canvas.paste(title, (round(w * 0.71 - title.width / 2), (h - th) // 2))
    canvas.save(path, quality=92) if path.suffix == '.jpg' else canvas.save(path)
    print(f'Wrote {path} {size}')


if __name__ == '__main__':
    main()
