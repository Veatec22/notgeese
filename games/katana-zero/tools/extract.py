"""Extracts texts and font maps from Katana ZERO to work/ (git-ignored).

    .venv\\Scripts\\python.exe games\\katana-zero\\tools\\extract.py --game "C:\\Games\\Katana ZERO"

- work/texts.json:    all entries: key, GML function, line, text in 10 languages,
- work/fontmaps.json: char map of every sprite font (frame order).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from exe import Exe, LANGS
from gmdata import DataWin

ROOT = Path(__file__).resolve().parents[1]

# Sprite -> frame count; the char map is recognized by length, because all fonts are
# created in one function from strings starting with a non-breaking space.
FONT_SPRITES = ['spr_textbox_font', 'spr_vcr_font', 'spr_vcr_font_tiny', 'spr_vhs_font',
                'spr_xirod_font_rus', 'spr_big_font']


def font_maps(exe: Exe, dw: DataWin) -> dict[str, str]:
    sprites = dw.sprites()
    maps = {}
    for off, disp, imm, _ in exe.movs():
        if disp == 4 and exe.is_string(imm):
            try:
                s = exe.cstr(imm)
            except (UnicodeDecodeError, ValueError):
                continue
            if s.startswith('\xa0 ') and len(s) > 90:
                maps[s] = imm
    out = {}
    for name in FONT_SPRITES:
        n = len(sprites[name].frames)
        hits = [s for s in maps if len(s) == n]
        if len(hits) != 1:
            raise SystemExit(f'{name}: {len(hits)} maps of length {n}')
        out[name] = hits[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True, type=Path)
    a = ap.parse_args()
    exe = Exe(a.game / 'Katana ZERO.exe')
    dw = DataWin(a.game / 'data.win')
    entries = exe.entries() + exe.menu_entries()
    keys = [e.key for e in entries]
    if len(keys) != len(set(keys)):
        dup = sorted({k for k in keys if keys.count(k) > 1})
        raise SystemExit(f'duplicate entry keys: {dup[:10]}')
    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    (work / 'texts.json').write_text(json.dumps(
        [{'key': e.key, 'fn': e.fn, 'line': e.line, **{l: e.text[l] for l in LANGS}} for e in entries],
        ensure_ascii=False, indent=1), encoding='utf-8')
    (work / 'fontmaps.json').write_text(json.dumps(font_maps(exe, dw), ensure_ascii=False, indent=1),
                                        encoding='utf-8')
    print(f'{len(entries)} entries, {len({e.text["en"] for e in entries})} distinct English')


if __name__ == '__main__':
    main()
