r"""Builds the Hyper Light Drifter translation into dist/build; never touches the game install.

Usage: .venv\Scripts\python.exe games\hyper-light-drifter\tools\build.py --game "C:\Games\Hyper Light Drifter"

Output (details in docs/technical.md):
- MenuText.txt, Phrases.txt: `ITA|` lines carry Polish (or English when untranslated);
  other languages byte for byte unchanged;
- HyperLightDrifter.exe: language name "ITALIANO" -> "POLSKI", 16 Polish letters of font
  f_uni drawn in the empty band at the bottom of texture page 10 and pointed to by their
  glyphs. The page's new PNG (original stream copied up to the letter band plus our rows,
  pngsplice.py) sits in a new .ngpl section at the end of the file; in FORM only this
  page's pointer changes. FORM lives in .data before the game's globals, so it can't
  grow; the runner reads it from memory, so the pointer can reach the section.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import fonts
import pngsplice
from hld import (EXE, HASHES, ROOT, SLOT, TEXT_FILES, GameData, load_texts, sections,
                 value, write_text)

sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import polish_by_key  # noqa: E402

VERSION = '0.1'
NAMES = b'ENGLISH\x00FRAN\xc3\x87AIS\x00ESPA\xc3\x91OL\x00'
OLD_NAME, NEW_NAME = b'ITALIANO\x00', b'POLSKI\x00\x00\x00'
SECTION = b'.ngpl\x00\x00\x00'
TOKEN = re.compile(r'\[[A-Za-z_]+\]')
SAMPLE = 'ZAŻÓŁĆ GĘŚLĄ JAŹŃ / zażółć gęślą jaźń / Przytrzymaj, żeby wejść.'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def translate_texts(game: Path, pl: dict) -> tuple[dict, dict]:
    built, stats = {}, {'entries': 0, 'translated': 0, 'missing': []}
    for name, (lines, items) in load_texts(game).items():
        out = list(lines)
        for e in items:
            stats['entries'] += 1
            english = value(lines, e, 'ENG')
            text = pl.get(e.key)
            if text is None:
                stats['missing'].append(e.key)
                text = english
            else:
                stats['translated'] += 1
            assert '|' not in text and '\n' not in text, e.key
            assert sorted(TOKEN.findall(text)) == sorted(TOKEN.findall(english)), (e.key, text)
            out[e.lines[SLOT]] = f'{SLOT}|{text}'
        built[TEXT_FILES[name]] = write_text(out)
    unknown = set(pl) - {e.key for _, items in load_texts(game).values() for e in items}
    assert not unknown, f'keys not in the game: {sorted(unknown)}'
    return built, stats


def patch_exe(exe: bytes) -> tuple[bytes, list[tuple[int, int]], dict]:
    data = bytearray(exe)
    changed = []

    # 1. Language name in the language picker.
    at = data.find(NAMES + OLD_NAME)
    assert at >= 0 and data.find(NAMES + OLD_NAME, at + 1) < 0, 'language name list'
    at += len(NAMES)
    data[at:at + len(OLD_NAME)] = NEW_NAME
    changed.append((at, len(OLD_NAME)))

    # 2. Litery fontu.
    gd = GameData(data)
    font = gd.font(fonts.FONT)
    page = gd.page_image(font.page)
    original_page = page.copy()
    letters = fonts.design(page, font)
    moved = fonts.placement(font)
    ax, ay = font.atlas[:2]
    # Taken on the page: every TPAG item of this page and the font's glyph cells.
    taken = [(x, y, w, h) for x, y, w, h, *_, tex in
             (struct.unpack_from('<11H', data, at) for at in gd.items('TPAG')) if tex == font.page]
    taken += [(ax + g.x, ay + g.y, g.w, g.h) for c, g in font.glyphs.items() if g.w and c not in moved]
    for char, img in letters.items():
        g = font.glyphs[char]
        assert (g.w, g.h, g.shift, g.offset) == (5, 7, 6, 0), (char, g)
        x, y = moved[char]
        w, h = img.size
        px, py = ax + x, ay + y
        assert 1 <= px and px + w < page.width and py + h < page.height, char
        clash = [r for r in taken if r[0] < px + w + 1 and px - 1 < r[0] + r[2]
                 and r[1] < py + h + 1 and py - 1 < r[1] + r[3]]
        assert not clash, (char, clash)
        taken.append((px, py, w, h))
        region = page.crop((px - 1, py - 1, px + w + 1, py + h + 1))
        assert not region.getchannel('A').getbbox(), f'cell {char} is not empty'
        page.alpha_composite(img, (px, py))
        struct.pack_into('<3H', data, g.at + 2, x, y, g.w)
        struct.pack_into('<H', data, g.at + 8, h)
        changed.append((g.at + 2, 8))

    # 3. New page PNG in the .ngpl section at the end of the exe; in FORM only the pointer changes.
    png_at, png_len = gd.page_png(font.page)
    first_row = fonts.PAGE_ROW
    assert not original_page.crop((0, first_row, page.width, page.height)).getchannel('A').getbbox()
    png = pngsplice.splice(bytes(data[png_at:png_at + png_len]), page, first_row)
    slot = gd.page_slot(font.page)
    section_rva, header = add_section(data, png, changed)
    struct.pack_into('<I', data, slot, section_rva - gd.form_rva)
    changed.append((slot, 4))
    set_checksum(data, changed)

    info = {'page': font.page, 'png_bytes': len(png), 'section_rva': section_rva,
            'moved': {c: list(v) for c, v in moved.items()}}
    return bytes(data), changed, info | {'_page': page, '_original_page': original_page}


def align(n: int, a: int) -> int:
    return (n + a - 1) // a * a


def add_section(data: bytearray, blob: bytes, changed: list) -> tuple[int, int]:
    """New read-only data section at the end of the file; returns its RVA."""
    nt = struct.unpack_from('<I', data, 0x3c)[0]
    opt = nt + 24
    sec_align, file_align = struct.unpack_from('<II', data, opt + 32)
    table = sections(data)
    last = table[-1]
    header = last.header + 40
    size_of_headers = struct.unpack_from('<I', data, opt + 60)[0]
    assert header + 40 <= size_of_headers and not any(data[header:header + 40]), 'no room for the header'
    assert last.raw + last.raw_size == len(data), 'data after the last section'
    rva = align(last.rva + last.vsize, sec_align)
    raw_at = align(len(data), file_align)
    raw_size = align(len(blob), file_align)
    data.extend(bytes(raw_at - len(data)) + blob + bytes(raw_size - len(blob)))
    struct.pack_into('<8sIIIIIIHHI', data, header, SECTION, len(blob), rva, raw_size, raw_at,
                     0, 0, 0, 0, 0x40000040)          # initialized data, read-only
    struct.pack_into('<H', data, nt + 6, len(table) + 1)
    struct.pack_into('<I', data, opt + 56, align(rva + len(blob), sec_align))
    changed += [(header, 40), (nt + 6, 2), (opt + 56, 4)]
    return rva, header


def set_checksum(data: bytearray, changed: list):
    """PE checksum (like CheckSumMappedFile), computed with numpy because the file is 628 MB."""
    opt = struct.unpack_from('<I', data, 0x3c)[0] + 24
    struct.pack_into('<I', data, opt + 64, 0)
    words = np.frombuffer(bytes(data) + b'\0' * (len(data) & 1), dtype='<u2')
    total = int(words.sum(dtype=np.uint64))
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    struct.pack_into('<I', data, opt + 64, total + len(data))
    changed.append((opt + 64, 4))


def verify_exe(original: bytes, built: bytes, changed: list[tuple[int, int]], info: dict):
    # Outside the declared spots the file is byte-identical, followed by the new section.
    last = 0
    for at, n in sorted(c for c in changed if c[0] < len(original)):
        assert original[last:at] == built[last:at], hex(last)
        last = at + n
    assert original[last:] == built[last:len(original)]

    a, b = GameData(original), GameData(built)
    assert a.chunks == b.chunks
    section = sections(built)[-1]
    assert section.name == SECTION.rstrip(b'\0') and section.rva == info['section_rva']
    fa, fb = a.font(fonts.FONT), b.font(fonts.FONT)
    at, n = b.page_png(fb.page)
    assert section.raw <= at < at + n <= section.raw + section.vsize, 'page PNG outside the new section'
    # The old PNG stays untouched where it was.
    old_at, old_n = a.page_png(fa.page)
    assert built[old_at:old_at + old_n] == original[old_at:old_at + old_n]
    page = b.page_image(fb.page)
    assert page.tobytes() == info['_page'].tobytes(), 'PNG does not read back as written'
    ax, ay = fb.atlas[:2]
    touched = set()
    for c, g in fb.glyphs.items():
        old = fa.glyphs[c]
        if c in fonts.POLISH:
            crop = page.crop((ax + g.x, ay + g.y, ax + g.x + g.w, ay + g.y + g.h))
            want = fonts.design(info['_original_page'], fa)[c]
            assert crop.getchannel('A').tobytes() == want.getchannel('A').tobytes(), c
            assert all(crop.getpixel(p) == fonts.WHITE for p in fonts.pixels(crop)), c
            touched |= {(ax + g.x + i, ay + g.y + j) for i in range(g.w) for j in range(g.h)}
        else:
            assert (g.x, g.y, g.w, g.h, g.shift, g.offset) == (old.x, old.y, old.w, old.h, old.shift, old.offset), c
    # Page pixels outside the Polish letters unchanged.
    before = np.asarray(info['_original_page'])
    after = np.asarray(page)
    ys, xs = np.nonzero((before != after).any(axis=2))
    assert set(zip(xs.tolist(), ys.tolist())) <= touched
    # Other texture pages point to the same PNGs as before.
    for p in range(len(a.items('TXTR'))):
        if p != fb.page:
            assert a.page_png(p) == b.page_png(p), p
    assert built.find(NAMES + NEW_NAME) >= 0


def verify_texts(game: Path, built: dict, pl: dict):
    from hld import entries, read_text
    orig = load_texts(game)
    for name, file in TEXT_FILES.items():
        lines = read_text(built[file])
        items = entries(name, lines)
        o_lines, o_items = orig[name]
        assert [e.key for e in items] == [e.key for e in o_items]
        assert len(lines) == len(o_lines)
        slot = {e.lines[SLOT] for e in items}
        assert all(lines[i] == o_lines[i] for i in range(len(lines)) if i not in slot), file
        for e in items:
            assert value(lines, e, SLOT) == pl.get(e.key, value(o_lines, e, 'ENG'))


def check_charset(gd: GameData, pl: dict):
    """Every text character has pixels in the font; an empty glyph has a width, so that's not enough."""
    font = gd.font(fonts.FONT)
    page = gd.page_image(font.page)
    missing = {}
    for key, text in pl.items():
        for ch in set(TOKEN.sub('', text)) - set(fonts.POLISH) - {' '}:
            if ch not in font.glyphs or not fonts.pixels(fonts.cell(page, font, ch)):
                missing.setdefault(ch, []).append(key)
    assert not missing, f'characters without a glyph in {fonts.FONT}: {missing}'


def preview(built_exe: bytes, out: Path):
    """Letter preview at 6× scale, to look at before the in-game test."""
    gd = GameData(built_exe)
    font = gd.font(fonts.FONT)
    page = gd.page_image(font.page)
    ax, ay = font.atlas[:2]
    width = sum(font.glyphs[c].shift if c in font.glyphs else 4 for c in SAMPLE) + 8
    img = Image.new('RGBA', (width, 14), (32, 22, 48, 255))
    x = 4
    for c in SAMPLE:
        g = font.glyphs[c]
        if g.w:
            img.alpha_composite(page.crop((ax + g.x, ay + g.y, ax + g.x + g.w, ay + g.y + g.h)), (x + g.offset, 2))
        x += g.shift
    img.resize((img.width * 6, img.height * 6), Image.NEAREST).save(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir or a copy of the originals')
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()

    originals = {}
    for file, expected in HASHES.items():
        data = (args.game / file).read_bytes()
        if sha(data) != expected:
            print(f'{file}: checksum {sha(data)}, expected {expected} (another version or already translated)')
            return 1
        originals[file] = data

    pl = polish_by_key(ROOT)
    check_charset(GameData(originals[EXE]), pl)
    texts, stats = translate_texts(args.game, pl)
    exe, changed, info = patch_exe(originals[EXE])
    verify_texts(args.game, texts, pl)
    verify_exe(originals[EXE], exe, changed, info)

    build = args.out / 'build'
    build.mkdir(parents=True, exist_ok=True)
    outputs = {**texts, EXE: exe}
    for file, data in outputs.items():
        (build / file).write_bytes(data)
    preview(exe, args.out / 'font-preview.png')
    report = {
        'version': VERSION,
        'entries': stats['entries'],
        'translated': stats['translated'],
        'missing': stats['missing'],
        'font': {k: v for k, v in info.items() if not k.startswith('_')},
        'original_sha256': HASHES,
        'build_sha256': {file: sha(data) for file, data in outputs.items()},
    }
    (args.out / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Entries: {stats['translated']}/{stats['entries']} translated; "
          f"page {info['page']} PNG in section .ngpl: {info['png_bytes']} B; output: {build}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
