"""Survey of DEADBOLT files (GameMaker Studio 1.4, VM, bytecode 15).

Reads data.win and dia_*.json from the game dir, changes nothing there.
Writes to work/: chunk and font list (inspection.json), all STRG strings (strg.json),
translation candidates (candidates.json) and previews of a few sprites with text
(sprites/*.png).

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\inspect_game.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"
"""
from __future__ import annotations

import argparse
import io
import json
import re
import struct
from pathlib import Path

from PIL import Image

WORK = Path(__file__).resolve().parents[1] / 'work'
POLISH = set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')
TEXT_SPRITES = ['sTutorial', 'sMissionFolder', 'sMissionFinished', 'sLogo', 'sPortalSign']


class DataWin:
    def __init__(self, path: Path):
        self.d = path.read_bytes()
        assert self.d[:4] == b'FORM'
        self.chunks: dict[str, tuple[int, int]] = {}
        o = 8
        while o < len(self.d):
            size = self.u32(o + 4)
            self.chunks[self.d[o:o + 4].decode()] = (o + 8, size)
            o += 8 + size

    def u32(self, o):
        return struct.unpack_from('<I', self.d, o)[0]

    def cstr(self, p):
        return self.d[p:self.d.index(b'\0', p)].decode('utf-8', 'replace')

    def plist(self, chunk):
        s, size = self.chunks[chunk]
        return [self.u32(s + 4 + 4 * i) for i in range(self.u32(s))] if size else []

    def gen8(self):
        g = self.chunks['GEN8'][0]
        return {
            'bytecode': self.d[g + 1],
            'name': self.cstr(self.u32(g + 0x28)),
            'version': '.'.join(map(str, struct.unpack_from('<4I', self.d, g + 0x2C))),
            'display_name': self.cstr(self.u32(g + 0x64)),
        }

    def fonts(self):
        out = []
        for p in self.plist('FONT'):
            gl = p + 40
            codes = [struct.unpack_from('<H', self.d, self.u32(gl + 4 + 4 * i))[0]
                     for i in range(self.u32(gl))]
            out.append({
                'name': self.cstr(self.u32(p)), 'face': self.cstr(self.u32(p + 4)),
                'size': self.u32(p + 8),
                'range': [struct.unpack_from('<H', self.d, p + 20)[0], self.u32(p + 24)],
                'glyphs': len(codes),
                'polish': ''.join(chr(c) for c in codes if chr(c) in POLISH),
            })
        return out

    def strings(self):
        return [self.cstr(p + 4) for p in self.plist('STRG')]

    def sprite_frames(self, names):
        pages = [self.u32(p + 4) for p in self.plist('TXTR')]
        cache = {}
        for p in self.plist('SPRT'):
            name = self.cstr(self.u32(p))
            if name not in names:
                continue
            for k in range(self.u32(p + 56)):
                t = self.u32(p + 60 + 4 * k)
                sx, sy, sw, sh, *_, tex = struct.unpack_from('<11H', self.d, t)
                if tex not in cache:
                    png = pages[tex]
                    end = self.d.index(b'IEND', png) + 8
                    cache[tex] = Image.open(io.BytesIO(self.d[png:end])).convert('RGBA')
                yield name, k, cache[tex].crop((sx, sy, sx + sw, sy + sh))


def candidate(s: str) -> bool:
    return (re.search(r'[A-Za-z]{2,}[ :.!?]', s) is not None
            and not re.match(r'(gml_|steam_|obj|scr)', s)
            and not re.search(r'[{};]', s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    game = ap.parse_args().game
    WORK.mkdir(exist_ok=True)

    dw = DataWin(game / 'data.win')
    strings = dw.strings()
    cands = [s for s in strings if candidate(s)]

    dialog = {}
    for f in sorted(game.glob('dia_*.json')):
        text = f.read_text(encoding='utf-8')
        dialog[f.name] = re.findall(r'"(?:Dialogue|Name|Description)":\s*"((?:[^"\\]|\\.)*)"', text)

    report = {
        'gen8': dw.gen8(),
        'chunks': {k: v[1] for k, v in dw.chunks.items()},
        'fonts': dw.fonts(),
        'strg_total': len(strings),
        'strg_candidates': len(cands),
        'strg_candidate_words': len(' '.join(cands).split()),
        'dialog_entries': sum(map(len, dialog.values())),
        'dialog_words': len(' '.join(v for vs in dialog.values() for v in vs).split()),
    }
    (WORK / 'inspection.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (WORK / 'strg.json').write_text(json.dumps(strings, ensure_ascii=False, indent=0), encoding='utf-8')
    (WORK / 'candidates.json').write_text(json.dumps(cands, ensure_ascii=False, indent=0), encoding='utf-8')

    out = WORK / 'sprites'
    out.mkdir(exist_ok=True)
    for name, k, img in dw.sprite_frames(set(TEXT_SPRITES)):
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(out / f'{name}_{k}.png')

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
