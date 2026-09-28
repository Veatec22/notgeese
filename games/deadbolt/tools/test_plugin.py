"""Plugin test without starting the game.

Copies data.win and dia_*.json from the game to work/harness (copies stay in work/, never in
the repo or package), puts the built dist/d3d9.dll and notgeese/ next to them, runs
tools/harness.cpp (32-bit) and checks what the game would see:
  - every s row of pl.tsv: the string in the STRG list is Polish,
  - c row: string changed only in its code entry, original elsewhere stays,
  - fonts: Polish letters in the (sorted) list, composed from the atlas -> work/harness/render.png,
  - dialogue: the redirected dia_fp.json is valid JSON with Polish text.

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\test_plugin.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"
"""
import argparse
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from build_plugin import compiler_environment  # noqa: E402
from strings_usage import Data  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/harness'
POLISH = 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'


def unescape(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    game = ap.parse_args().game
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / 'notgeese').mkdir(parents=True)
    shutil.copyfile(game / 'data.win', WORK / 'data.win')
    for f in game.glob('dia_*.json'):
        shutil.copyfile(f, WORK / f.name)
    dist = ROOT / 'dist'
    shutil.copyfile(dist / 'd3d9.dll', WORK / 'd3d9.dll')
    for name in ('pl.tsv', 'fonts.txt', 'labels.txt'):
        shutil.copyfile(dist / 'notgeese' / name, WORK / 'notgeese' / name)

    env = compiler_environment()
    cl = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
    subprocess.run([cl, '/nologo', '/O2', '/EHsc', '/utf-8', str(ROOT / 'tools/harness.cpp'), '/Fe:' + str(WORK / 'harness.exe')],
                   cwd=WORK, env=env, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(WORK / 'harness.exe'), str(WORK)], cwd=WORK, check=True)
    log = (WORK / 'notgeese/LogOutput.log').read_text(encoding='utf-8')
    print(log)
    assert 'Ready in' in log, 'plugin did not finish'

    failures = 0
    strings = {}
    for line in (WORK / 'out-strings.txt').read_text(encoding='utf-8').splitlines():
        i, text = line.split('\t', 1)
        strings[int(i)] = unescape(text)
    original = Data(game / 'data.win').strings()
    rows = [l.split('\t') for l in (dist / 'notgeese/pl.tsv').read_text(encoding='utf-8').splitlines()
            if l and not l.startswith('#')]
    for kind, en, pl, *rest in rows:
        en, pl = unescape(en), unescape(pl)
        if kind == 's':
            for i, t in enumerate(original):
                if t == en and strings[i] != pl:
                    print(f'STRG {i}: expected {pl!r}, got {strings[i]!r}')
                    failures += 1
        elif kind == 'c':
            idx = [i for i, t in enumerate(original) if t == en]
            if any(strings[i] != en for i in idx):
                print(f'c row changed the string globally: {en!r}')
                failures += 1
            slots = [i for i, t in strings.items() if t == pl and original[i] != pl]
            if len(slots) != 1:
                print(f'c row {en!r}: {len(slots)} slots with the translation')
                failures += 1
            else:
                # The push.s operand in the code entry points at the translation slot.
                patched = Data.__new__(Data)
                patched.d = (WORK / 'out-buffer.bin').read_bytes()
                patched.chunks = Data(game / 'data.win').chunks
                from strings_usage import disasm
                hits = 0
                for code, start, length in patched.code_entries():
                    for _, op, arg in disasm(patched, start, length, {}, {}):
                        if op == 'push' and arg and arg[0] == 'str' and arg[1] == slots[0]:
                            hits += 1
                            if code != rest[0]:
                                print(f'slot {slots[0]} used outside {rest[0]}: {code}')
                                failures += 1
                print(f'c row {en!r} -> slot {slots[0]}, {hits} uses in {rest[0]}')
                failures += hits == 0
    untouched = sum(1 for i, t in enumerate(original) if strings[i] == t)
    print(f'STRG: {len(original) - untouched} strings changed, {untouched} unchanged')

    # Fonts: sorted list, Polish letters present; render from what the game sees.
    fonts = {}
    for line in (WORK / 'out-fonts.txt').read_text(encoding='utf-8').splitlines():
        name, code, x, y, w, h, shift, off, tex, sx, sy = line.split('\t')
        fonts.setdefault(name, []).append(tuple(map(int, (code, x, y, w, h, shift, off, tex, sx, sy))))
    pages = {}
    for name, glyphs in fonts.items():
        codes = [g[0] for g in glyphs]
        if codes != sorted(codes) or len(set(codes)) != len(codes):
            print(f'{name}: glyph list unsorted or with duplicates')
            failures += 1
        missing = [c for c in POLISH if ord(c) not in codes]
        if missing:
            print(f'{name}: missing {"".join(missing)}')
            failures += 1
    rows_img = []
    sample = ["Zażółć gęślą jaźń. ZAŻÓŁĆ GĘŚLĄ JAŹŃ.", "'E': OTWÓRZ DRZWI  Nieźle, żniwiarzu!"]
    for name, glyphs in fonts.items():
        table = {g[0]: g for g in glyphs}
        tex, sx, sy = glyphs[0][7], glyphs[0][8], glyphs[0][9]
        if tex not in pages:
            pages[tex] = Image.open(WORK / f'out-page{tex}.png').convert('RGBA')
        page = pages[tex]
        for text in sample:
            width = sum(table.get(ord(c), table[ord('?')])[5] for c in text) + 8
            height = max(g[4] for g in glyphs) + 4
            row = Image.new('RGBA', (width, height), (20, 20, 24, 255))
            x = 4
            for c in text:
                code, gx, gy, w, h, shift, off, *_ = table.get(ord(c), table[ord('?')])
                row.alpha_composite(page.crop((sx + gx, sy + gy, sx + gx + w, sy + gy + h)), (x + off, 2))
                x += shift
            rows_img.append(row)
    W = max(r.width for r in rows_img)
    sheet = Image.new('RGBA', (W, sum(r.height for r in rows_img)), (20, 20, 24, 255))
    y = 0
    for r in rows_img:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(WORK / 'render.png')

    # Labels on graphics: frames cut from re-encoded pages = what labels.py computes.
    import labels
    from inspect_game import DataWin
    dw = DataWin(game / 'data.win')
    ops = labels.build()
    import struct as _s
    spr = {}
    for p in dw.plist('SPRT'):
        name = dw.cstr(dw.u32(p))
        spr[name] = [dw.u32(p + 60 + 4 * i) for i in range(dw.u32(p + 56))]
    originals = {(n, k): img for n, k, img in dw.sprite_frames({op[1] for op in ops})}
    checked = 0
    for (name, k), img in originals.items():
        if not any(op[1] == name and op[2] == k for op in ops):
            continue
        sx, sy, sw, sh, *_, tex = _s.unpack_from('<11H', dw.d, spr[name][k])
        page = pages.get(tex) or Image.open(WORK / f'out-page{tex}.png').convert('RGBA')
        pages[tex] = page
        got = page.crop((sx, sy, sx + sw, sy + sh))
        want = labels.apply(img.copy(), ops, name, k)
        if list(got.getdata()) != list(want.getdata()):
            print(f'{name}/{k}: graphic after the plugin differs from the recipe')
            failures += 1
        checked += 1
    print(f'Labeled graphics: {checked} frames match the recipe' if not failures else '')
    failures += 'Labels: 15 drawn, 0 left' not in log

    # Dialogue through the redirect.
    redirected = WORK / 'out-dia_fp.json'
    if not redirected.exists():
        print('dia_fp.json was not redirected')
        failures += 1
    else:
        data = json.loads(redirected.read_text(encoding='utf-8'))
        text = data['map_mission1']['Description']
        print('dia_fp map_mission1:', text[:60])
        failures += 'Świece' not in text
    print('RESULT:', 'OK' if not failures else f'{failures} failures')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
