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
    ap.add_argument('--ultrawide-width', type=int, default=0)
    ap.add_argument('--no-translation', action='store_true',
                    help='ultrawide mod package alone: no pl.tsv/fonts.txt/labels.txt next to the DLL')
    ap.add_argument('--dist', type=Path, default=ROOT / 'dist')
    args = ap.parse_args()
    game = args.game
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / 'notgeese').mkdir(parents=True)
    shutil.copyfile(game / 'data.win', WORK / 'data.win')
    for f in game.glob('dia_*.json'):
        shutil.copyfile(f, WORK / f.name)
    dist = args.dist
    shutil.copyfile(dist / 'd3d9.dll', WORK / 'd3d9.dll')
    if args.no_translation and not args.ultrawide_width:
        raise SystemExit('--no-translation needs --ultrawide-width')
    for name in () if args.no_translation else ('pl.tsv', 'fonts.txt', 'labels.txt'):
        shutil.copyfile(dist / 'notgeese' / name, WORK / 'notgeese' / name)
    if args.ultrawide_width:
        (WORK / 'ultrawide').mkdir()
        (WORK / 'ultrawide/settings.ini').write_text(
            f'[Ultrawide]\nEnabled=1\nVirtualWidth={args.ultrawide_width}\n', encoding='ascii')

    env = compiler_environment()
    cl = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
    subprocess.run([cl, '/nologo', '/O2', '/EHsc', '/utf-8', str(ROOT / 'tools/harness.cpp'), '/Fe:' + str(WORK / 'harness.exe')],
                   cwd=WORK, env=env, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(WORK / 'harness.exe'), str(WORK)], cwd=WORK, check=True)
    # The log sits in the folder of the installed package: notgeese\ with PL, ultrawide\ alone.
    log = (WORK / ('ultrawide' if args.no_translation else 'notgeese') / 'LogOutput.log').read_text(encoding='utf-8')
    if args.no_translation:
        assert not (WORK / 'notgeese/LogOutput.log').exists() and not (WORK / 'notgeese/cache').exists()
    print(log)
    assert 'Ready in' in log, 'plugin did not finish'
    want_width = args.ultrawide_width or 960
    cached = list(map(int, (WORK / 'out-runner-size.txt').read_text().split()))
    assert cached == [want_width, 540, want_width, 540], f'Runner output still has old aspect: {cached}'
    # Inspect the actual DLL's memory writes, including the dynamically created mission camera.
    source = Data(game / 'data.win')
    patched_buffer = (WORK / 'out-buffer.bin').read_bytes()
    import struct
    camera_changes = set()
    rs, _ = source.chunks['ROOM']
    for i in range(source.u32(rs)):
        p = source.u32(rs + 4 + 4 * i)
        vl = source.u32(p + 44)
        for j in range(source.u32(vl)):
            view = source.u32(vl + 4 + 4 * j)
            if not source.u32(view):
                continue
            for off in (view + 12, view + 28):
                want = args.ultrawide_width or 960
                assert struct.unpack_from('<I', patched_buffer, off)[0] == want
                if args.ultrawide_width:
                    camera_changes.update(range(off, off + 4))
            assert struct.unpack_from('<I', patched_buffer, view + 20)[0] == 0
    # Read the DLL's actual replacement instructions. Both draw origin and main-menu
    # hit rectangles derive from the same tx; load's fixed hit center follows the list.
    variables = source.chains('VARI', 3, 20, 0, 12, 16)
    from strings_usage import disasm
    main_reads, load_centers = 0, 0
    for name, start, length in source.code_entries():
        if name == 'gml_Object_oMain_Draw_0':
            for off, op, arg in disasm(source, start, length, {}, variables):
                if not arg or arg[1] not in ('view_xview', 'view_wview'):
                    continue
                if args.ultrawide_width:
                    assert struct.unpack_from('<I', patched_buffer, off - 8)[0] == 0xc0000000
                    value = struct.unpack_from('<d', patched_buffer, off - 4)[0]
                    expected = (args.ultrawide_width - 960) / 2 if arg[1] == 'view_xview' else 960
                    assert value == expected
                    assert struct.unpack_from('<I', patched_buffer, off + 4)[0] == 0x07500000
                else:
                    assert patched_buffer[off - 8:off + 8] == source.d[off - 8:off + 8]
                main_reads += 1
        elif name == 'gml_Object_oLoadGame_Draw_0':
            for off, op, arg in disasm(source, start, length, {}, variables):
                if source.u32(off) == 0x840f0212:
                    center = 530 + (args.ultrawide_width - 960) // 2 if args.ultrawide_width else 530
                    assert struct.unpack_from('<I', patched_buffer, off)[0] == 0x840f0000 | center
                    # List is drawn at view_wview/2 - 130; hit test permits +/-180
                    # around the original center 530. Preserve their relative geometry.
                    list_left = (args.ultrawide_width or 960) / 2 - 130
                    assert center - list_left == 180
                    load_centers += 1
    assert (main_reads, load_centers) == (9, 1)
    for name, start, length in source.code_entries():
        if name not in ('gml_Script_init_screen', 'gml_Object_oLoadRoom_Other_10'):
            continue
        hits = 0
        from strings_usage import disasm
        for off, op, _ in disasm(source, start, length, {}, {}):
            if source.u32(off) == 0x840f03c0:
                want = 0x840f0000 | (args.ultrawide_width or 960)
                assert struct.unpack_from('<I', patched_buffer, off)[0] == want
                hits += 1
                if args.ultrawide_width:
                    camera_changes.update(range(off, off + 4))
        assert hits == (1 if name == 'gml_Script_init_screen' else 2)
    # Nothing else in ROOM may change; lighting and mouse code stay byte-identical.
    for off in range(rs, rs + source.chunks['ROOM'][1]):
        if off not in camera_changes:
            assert patched_buffer[off] == source.d[off]
    for name, start, length in source.code_entries():
        if name in ('gml_Object_oLighting_Create_0', 'gml_Object_oLighting_Step_2', 'gml_Script_move_mouse'):
            assert patched_buffer[start:start + length] == source.d[start:start + length]
    if args.ultrawide_width:
        assert f'Ultrawide: {args.ultrawide_width}x540, 12 room views, 3 code constants' in log
    else:
        assert 'Ultrawide:' not in log
    print('Camera memory verification: OK')

    if args.no_translation:
        # Mod alone: wide cameras, every string and font exactly as in the game.
        assert 'translation off, ultrawide only' in log and 'Ready in' in log
        seen = dict(l.split('	', 1) for l in (WORK / 'out-strings.txt').read_text(encoding='utf-8').splitlines())
        original = Data(game / 'data.win').strings()
        assert all(unescape(seen[str(i)]) == t for i, t in enumerate(original)), 'ultrawide-only mode changed strings'
        assert 'Strings:' not in log and 'Polish glyphs' not in log and 'Labels:' not in log
        print('Ultrawide-only verification: OK (no text, font or label changes)')
        return

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
    failures += f'Labels: {len(labels.LABELS)} drawn, 0 left' not in log

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
