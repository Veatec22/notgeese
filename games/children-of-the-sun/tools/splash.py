"""Render the Polish splash logos: warning, publisher, author.

The game's Unity splash screen shows three 1024x1024 logo textures with baked English text
(globalgamemanagers.assets: logowarning, logodevolver, agameby_logo): a yellow blackletter
headline and white serif text below. We draw our own from scratch with OFL fonts, same layout;
nothing is taken from the game's images. The plugin loads them into the logo textures.

Fonts (OFL, from github.com/google/fonts, kept in work/fonts, not shipped):
UnifrakturMaguntia-Book.ttf (headline; no "ż", composed from "z" and its dot) and
Vollkorn[wght].ttf (body, the same face as the original warning text).

    .venv\\Scripts\\python.exe games\\children-of-the-sun\\tools\\splash.py [--preview]
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import polish_by_key  # noqa: E402

FONTS = ROOT / 'work' / 'fonts'
FONT_URLS = {
    'UnifrakturMaguntia-Book.ttf': 'ofl/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf',
    'Vollkorn[wght].ttf': 'ofl/vollkorn/Vollkorn%5Bwght%5D.ttf',
}
OUT = ROOT / 'work' / 'splash'
SIZE = 1024
YELLOW = (255, 255, 0, 255)
WHITE = (255, 255, 255, 255)

# Texture name -> (headline, lines below, body style). Headline/body of the warning come from
# the translation file (photowarning_head/_body); the names stay as in the original.
PUBLISHER = 'wydawca'
AUTHOR = 'gra autorstwa'


def font(name: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    if not path.exists():
        FONTS.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve('https://raw.githubusercontent.com/google/fonts/main/' + FONT_URLS[name], path)
    f = ImageFont.truetype(str(path), size)
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f


def headline(draw: ImageDraw.ImageDraw, text: str, baseline: int, pitch: int) -> None:
    """Letter-spaced blackletter, like the original: each letter on a fixed pitch."""
    f = font('UnifrakturMaguntia-Book.ttf', 64)
    x = SIZE / 2 - pitch * (len(text) - 1) / 2
    for ch in text:
        if ch == ' ':
            x += pitch
            continue
        base = 'z' if ch == 'ż' else ch
        draw.text((x, baseline), base, font=f, fill=YELLOW, anchor='ms')
        if ch == 'ż':
            # Dot above, the same diamond the font uses on "i".
            dot_h = 9
            top = draw.textbbox((x, baseline), 'z', font=f, anchor='ms')[1]
            cx, cy = x, top - dot_h - 3
            draw.polygon([(cx, cy - dot_h / 2 - 1), (cx + dot_h / 2, cy), (cx, cy + dot_h / 2 + 1), (cx - dot_h / 2, cy)], fill=YELLOW)
        x += pitch


def spaced(draw: ImageDraw.ImageDraw, text: str, baseline: int, size: int, tracking: int) -> None:
    """White capitals with letter spacing, centred."""
    f = font('Vollkorn[wght].ttf', size, 400)
    widths = [draw.textlength(c, font=f) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (SIZE - total) / 2
    for c, w in zip(text, widths):
        draw.text((x, baseline), c, font=f, fill=WHITE, anchor='ls')
        x += w + tracking


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ''
    for word in text.split():
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def body(draw: ImageDraw.ImageDraw, text: str, top: int) -> int:
    f = font('Vollkorn[wght].ttf', 37, 400)
    lines = wrap(draw, text, f, 1000)
    # Balance two lines like the original instead of a long first and short second.
    if len(lines) == 2:
        words = text.split()
        best = min(range(1, len(words)), key=lambda i: max(
            draw.textlength(' '.join(words[:i]), font=f), draw.textlength(' '.join(words[i:]), font=f)))
        lines = [' '.join(words[:best]), ' '.join(words[best:])]
    for i, line in enumerate(lines):
        draw.text((SIZE / 2, top + i * 60), line, font=f, fill=WHITE, anchor='mt')
    return len(lines)


def render() -> dict:
    pl = polish_by_key(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    made = {}

    def canvas():
        image = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 0))
        return image, ImageDraw.Draw(image)

    image, draw = canvas()
    headline(draw, pl['photowarning_head'], 515, 41)
    lines = body(draw, pl['photowarning_body'], 550)
    image.save(OUT / 'logowarning.png')
    made['logowarning'] = {'headline': pl['photowarning_head'], 'body_lines': lines}

    image, draw = canvas()
    headline(draw, PUBLISHER, 515, 43)
    spaced(draw, 'DEVOLVER DIGITAL', 588, 70, 17)
    image.save(OUT / 'logodevolver.png')
    made['logodevolver'] = {'headline': PUBLISHER}

    image, draw = canvas()
    headline(draw, AUTHOR, 512, 40)
    spaced(draw, 'RENÉ ROTHER', 588, 70, 17)
    image.save(OUT / 'agameby_logo.png')
    made['agameby_logo'] = {'headline': AUTHOR}
    return made


def preview() -> Path:
    sheet = Image.new('RGBA', (SIZE, 3 * 260), (40, 20, 60, 255))
    for i, name in enumerate(['logowarning', 'logodevolver', 'agameby_logo']):
        sheet.alpha_composite(Image.open(OUT / f'{name}.png').crop((0, 430, SIZE, 690)), (0, i * 260))
    path = ROOT / 'work' / 'splash_preview.png'
    sheet.convert('RGB').save(path)
    return path


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--preview', action='store_true', help='also write work/splash_preview.png')
    args = parser.parse_args()
    made = render()
    if args.preview:
        made['preview'] = str(preview())
    print(json.dumps(made, ensure_ascii=False))


if __name__ == '__main__':
    main()
