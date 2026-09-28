r"""Build the NOT A HERO translation into dist/build; never modifies the installation.

Usage: .venv\Scripts\python.exe games/not-a-hero/tools/build.py --game "C:\Games\Not A Hero"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

import pefile
from PIL import Image, ImageDraw

from assets import Assets
from fonts import FONT_CELLS, encode, polish_font, render
from ini import FILES, check, entries
import exe
import menus

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries, polish_by_key  # noqa: E402
VERSION = '0.1'
HASHES = {
    'Assets.dat': '25023db094a6d3dc0534953b9963116b1bb16926ae2742d2b40040aeea5c0a33',
    'Src/talk.ini': '32ab82c39bf2a4a7ae18a738e272be2fb61575018e19742fe28a6ef50e690183',
    'Src/ENDS.ini': 'ac42487d1dc370a61b45c9d7ea19b722114c3476e2990e28a2dde4846b649f71',
    'Src/chat.ini': '2e6bf9537daeda8da6c4262cd7335b580412a3221716b98162c626e484d02ad1',
    'Src/LEVELS/SETTINGS.ini': 'cc1e60be8d6c0cd6b3469936897f7cce7cac5153a94ae4e131b504723a0bbebb',
    'NOT A HERO.exe': 'b0994004562401d734f6f821c3cea88dcb11634b1c59735789ac2339edf0eebd',
}


def menu_map(exe: bytes) -> dict[int, int]:
    pe = pefile.PE(data=exe)
    mapping = {}
    for i in range(557):
        offset = exe.index(f'./menu/fre/{i}.png'.encode())
        address = pe.OPTIONAL_HEADER.ImageBase + pe.get_rva_from_offset(offset)
        refs = list(re.finditer(re.escape(struct.pack('<I', address)), exe))
        ids = set()
        for ref in refs:
            at = ref.start()
            if exe[at - 1] != 0x68:  # PUSH string address, not unrelated data
                continue
            match = re.search(rb'\x50(?:\x68(.{4})|\x6a(.))\xe8', exe[at:at + 42], re.S)
            if match:
                ids.add(int.from_bytes(match[1] or match[2], 'little'))
        assert len(ids) == 1, (i, ids)
        mapping[i] = ids.pop()
    return mapping


def rewrite_ini(raw: bytes, relative: str, pl: dict, originals: dict) -> tuple[bytes, int]:
    lines = raw.decode('cp1252').splitlines(keepends=True)
    result = [line.encode('cp1252') for line in lines]
    count = 0
    for index, term, english in entries(raw, relative):
        if term not in pl:
            continue
        assert originals[term] == english, term
        problems = check(term, english, pl[term])
        assert not problems, (term, problems)
        line = lines[index]
        key = line.split('=', 1)[0]
        ending = line[len(line.rstrip('\r\n')):]
        # Unchanged lines keep their exact bytes; changed ones use the game font encoding.
        result[index] = encode(key + '=' + pl[term] + ending)
        count += 1
    built = b''.join(result)
    expected = sum(k.startswith(relative + '|') for k in pl)
    assert count == expected, (relative, count, expected)
    assert len(raw.splitlines()) == len(built.splitlines())
    return built, count


def menu_images(assets: Assets, mapping: dict, fonts: dict, pl: dict):
    result = {}
    atlas = fonts[3017]
    small = fonts[2088]

    def replace_line(image, x, y, width, term, font=atlas, cw=8, ch=12, advance=7):
        # The menu's 3 flicker frames use different gray levels. Keep the color
        # of the original line and leave selection arrows untouched.
        crop = image.crop((x, y, min(image.width, x + width), y + ch))
        color = max(crop.get_flattened_data(), key=lambda c: sum(c[:3]) * c[3])
        text = render(pl['menu|' + term], font, cw, ch, color, advance)
        assert text.width <= width, (term, text.width, width)
        background = image.getpixel((x, y))
        ImageDraw.Draw(image).rectangle((x, y, min(image.width - 1, x + width - 1), y + ch - 1), fill=background)
        image.alpha_composite(text, (x, y))

    # Main menu, its submenus and keyboard/controller setup. Include all flicker
    # states and copies used in other frames; repeated image IDs are deduplicated.
    main = list(range(0, 88)) + list(range(277, 280)) + list(range(298, 302)) + list(range(304, 346)) + list(range(480, 497))
    for index in sorted({mapping[i] for i in main}):
        im = assets.image(index)
        for row, term in enumerate(['play', 'stats', 'options', 'quit']):
            # Stop before the submenu selection arrow at x=118..122.
            replace_line(im, 50, 49 + row * 14, 66, term)
        if index in {mapping[i] for i in list(range(32, 64)) + list(range(277, 280)) + list(range(336, 346)) + list(range(480, 497))}:
            for row, term in enumerate(['audio', 'controls', 'credits', 'reset']):
                replace_line(im, 127, 77 + row * 14, 82, term)
        if index in {mapping[i] for i in range(480, 497)}:
            replace_line(im, 220, 91, 130, 'setup')
            replace_line(im, 220, 105, 130, 'default')
        result[index] = im
    for index in sorted({mapping[i] for i in range(280, 298)}):
        im = assets.image(index)
        replace_line(im, 219, 77, 120, 'music')
        replace_line(im, 219, 91, 120, 'sfx')
        result[index] = im
    # Pause menu uses the smaller sprite font, on transparency.
    for index in sorted({mapping[i] for i in range(497, 537)}):
        im = assets.image(index)
        original = im.copy()
        ImageDraw.Draw(im).rectangle((9, 0, im.width - 1, im.height - 1), fill=(0, 0, 0, 0))
        for row, term in enumerate(['continue', 'retry', 'level', 'character', 'main']):
            y = row * 14
            region = original.crop((9, y, im.width, y + 8))
            color = max(region.get_flattened_data(), key=lambda c: sum(c[:3]) * c[3])
            label = render(pl['menu|' + term], atlas, 8, 12, color, 7)
            assert label.width <= im.width - 9
            im.alpha_composite(label, (9, y - 3))
        result[index] = im
    return result


def tutorial_images(assets: Assets, atlas: Image.Image, pl: dict):
    # Region heights stop above the explanatory character animations/arrows.
    heights = {11174: 29, 507: 38, 1083: 29, 1086: 17, 1166: 17, 11347: 29, 11348: 29,
               1205: 41, 1209: 41, 11773: 29, 11175: 41, 11775: 29,
               11779: 17, 11780: 17, 11781: 41, 11782: 41, 11785: 29}
    result = {}
    for index, end in heights.items():
        im = assets.image(index)
        # Only the text panel changes; the frame, arrows and character art stay.
        ImageDraw.Draw(im).rectangle((5, 5, im.width - 6, end), fill=im.getpixel((4, 4)))
        lines = pl[f'image|{index}'].split('\n')
        for row, line in enumerate(lines):
            label = render(line, atlas, 7, 9, advance=6)
            assert label.width <= im.width - 10, (index, line, label.width)
            y = 5 + row * 11
            assert y + label.height - 1 <= end, index
            im.alpha_composite(label, ((im.width - label.width) // 2, y))
        result[index] = im
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    assert args.out.resolve() != args.game.resolve()
    assert not args.out.resolve().is_relative_to(args.game.resolve()), 'Build cannot write into the game'
    inputs = {}
    for relative, expected in HASHES.items():
        raw = (args.game / relative).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise SystemExit(f'{relative}: expected {expected}, got {digest}; use original backup')
        inputs[relative] = raw
    pl = polish_by_key(ROOT)
    review = load_entries(ROOT)
    originals = {r['key']: r['english'] for r in review}
    assets = Assets(inputs['Assets.dat'])
    fonts = {i: polish_font(assets.image(i), *cell) for i, cell in FONT_CELLS.items()}
    images = dict(fonts)
    images.update(menu_images(assets, menu_map(inputs['NOT A HERO.exe']), fonts, pl))
    images.update(tutorial_images(assets, fonts[2088], pl))
    mapping = menu_map(inputs['NOT A HERO.exe'])
    images.update(menus.level_list(assets, mapping, fonts, pl))
    images.update(menus.election(assets, mapping, fonts, pl))
    images.update(menus.election_day(assets, fonts, pl))
    images.update(menus.cards(assets, fonts, pl, [int(k.split('|')[1]) for k in pl if k.startswith('card|')]))
    images.update(menus.controller(assets, fonts, pl))
    images.update(menus.shoot_her(assets, mapping, fonts, pl))
    images.update(menus.reset_confirm(assets, mapping, fonts, pl))
    images.update(menus.polish_flag(assets))
    built = {'Assets.dat': assets.build(images)}
    counts = {}
    for relative in FILES:
        built[relative], counts[relative] = rewrite_ini(inputs[relative], relative, pl, originals)
    built['NOT A HERO.exe'], counts['NOT A HERO.exe'] = exe.patch(inputs['NOT A HERO.exe'], pl, originals)
    for relative, data in built.items():
        path = args.out / 'build' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    preview = args.out / 'preview'
    preview.mkdir(parents=True, exist_ok=True)
    for index in [512, 433, 783, 1920, 17763, 1083, 1086, 1166, 11347, 1205, 11175,
                  4402, 17666, 17614, 17604, 786, 9149, 9466, 10702, 10, 1892, 149, 16828, 16952, 2757, 1161, 6170]:
        images[index].save(preview / f'{index}.png')
    sample = 'ZAŻÓŁĆ GĘŚLĄ JAŹŃ  ĄĆĘŁŃÓŚŹŻ'
    render(sample, fonts[3017], 8, 12).resize((len(sample) * 8 * 4, 48), Image.Resampling.NEAREST).save(preview / 'polish-letters.png')
    sys.path.insert(0, str(REPO / 'tools'))
    import patch
    files = [(args.game / relative, args.out / 'build' / relative, relative) for relative in built]
    report = patch.release(files, ROOT / 'docs/INSTALL-patch.txt', args.out,
                           'not-a-hero', 'Not-A-Hero', VERSION)
    with zipfile.ZipFile(report['package']) as archive:
        assert all(name.endswith('.patch') or name in {f'Not-A-Hero-PL-{VERSION}.exe', 'READ-ME.txt'} for name in archive.namelist()), 'Game asset in release!'
    report.update(entries=len(pl), changed_images=len(images), sprite_fonts=len(fonts), ini_entries=counts,
                  in_game_test='pending', build_sha256={k: hashlib.sha256(v).hexdigest() for k, v in built.items()})
    (args.out / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['entries', 'changed_images', 'sprite_fonts', 'package', 'package_bytes']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
