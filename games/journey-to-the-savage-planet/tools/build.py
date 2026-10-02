"""Build the Polish package for Journey to the Savage Planet.

    build.py <game folder> [version]

The game offers 11 cultures wired into its exe and forces the saved subtitle/UI language to one
of them (docs/technical.md). Polish is added as a 12th:

- dist/Towers-WindowsNoEditor_pl_P.pak: overlay pak with a new Localization/Game/pl/Game.locres
  built from translations/en-pl-review.json (only translated keys, the English file's hashes).
  No game file is shadowed.
- dist/<Name>-PL-<version>.patch: delta patch of the exe that appends {"pl", "Polski"} to the
  culture list (tools/exe_patch.py). Applied by the bundled applier; without it the game never
  offers Polish.
- dist/<Name>-PL-<version>.zip: pak at its game path, patch, applier, READ-ME.txt.

Reads the game, writes only to dist/ and work/. Never installs.
"""
import collections
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
import locres
import pak
import patch
import exe_patch
from translations import load_entries, polish_by_ref, untranslated  # noqa: E402

NAME = 'Journey-to-the-Savage-Planet'
SLUG = 'journey-to-the-savage-planet'
VERSION = '0.1'
DIST = ROOT / 'dist'
SOURCE = ROOT / 'work/extract/Towers/Content/Localization/Game/en/Game.locres'
SOURCE_SHA256 = '71b0a06c8a34ded2f7444c1c1d93c725ac20ac9980904ff2511bc4839e5c61f0'
CULTURE = 'pl'
INSIDE = f'Towers/Content/Localization/Game/{CULTURE}/Game.locres'
PAK_PATH = 'Towers/Content/Paks/Towers-WindowsNoEditor_pl_P.pak'
EXE = 'Towers/Binaries/Win64/Towers-Win64-Shipping.exe'
BACKUP_SUFFIX = '.przed-spolszczeniem'   # applier's backup of the original
EXE_SHA256 = 'b0ee2d93f627bfbda553f89fc9e01ba9026cfac1650b2e126c126a1d0528bc1a'   # GOG, 71 628 288 B
TOKEN = re.compile(r'<action id=[^>]*/>|\{[^{}]*\}|<\d\d:[\d.,]+>')


def check(entries):
    """Markup the game parses must survive: input icons, format arguments, subtitle timecodes."""
    problems = []
    for e in entries:
        if untranslated(e):
            continue
        if collections.Counter(TOKEN.findall(e['english'])) != collections.Counter(TOKEN.findall(e['polish'])):
            problems.append(f"{e.get('namespace', '')}|{e['key']}: markup differs")
        if e['english'].count('\n') != e['polish'].count('\n') and '<00:' in e['english']:
            problems.append(f"{e.get('namespace', '')}|{e['key']}: subtitle line count differs")
    assert not problems, '\n'.join(problems[:20])


def locres_bytes():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f'{SOURCE.name}: {digest}, expected {SOURCE_SHA256}. Run extract.py on the '
                         'supported game version. Nothing written.')
    english = locres.load(SOURCE)
    translations = polish_by_ref(ROOT)
    unknown = [k for k in translations if k not in english.texts()]
    assert not unknown, f'keys not in the English resource: {unknown[:5]}'
    check(load_entries(ROOT))
    body = locres.dump(locres.translate(english, translations))
    stage = ROOT / 'work/build/Game.locres'
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.write_bytes(body)
    built = locres.load(stage)
    assert built.texts() == translations, 'locres does not read back as written'
    hashes = {(n, e.key): (e.key_hash, e.source_hash) for n, e in english.entries()}
    assert all(hashes[(n, e.key)] == (e.key_hash, e.source_hash) for n, e in built.entries())
    return body, len(translations), len(english.texts())


def original_exe(game):
    """The pinned exe; on a machine with our package installed, the applier's backup."""
    for path in (game / EXE, game / (EXE + BACKUP_SUFFIX)):
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == EXE_SHA256:
            return path
    digest = hashlib.sha256((game / EXE).read_bytes()).hexdigest()
    raise SystemExit(f'{EXE}: {digest}, expected {EXE_SHA256} (GOG build). Nothing written.')


def patched_exe(source):
    exe = bytearray(source.read_bytes())
    info = exe_patch.add_polish(exe)
    out = ROOT / 'work/build' / Path(EXE).name
    out.write_bytes(exe)
    return out, info


def main():
    if not __debug__:
        raise RuntimeError('Run without -O: verification uses assert.')
    game = Path(sys.argv[1])
    version = sys.argv[2] if len(sys.argv) > 2 else VERSION
    DIST.mkdir(exist_ok=True)

    body, translated, total = locres_bytes()
    archive = pak.write({INSIDE: body})
    assert pak.read(archive) == (pak.MOUNT_POINT, {INSIDE: body})
    pak_file = DIST / Path(PAK_PATH).name
    pak_file.write_bytes(archive)

    source = original_exe(game)
    exe, cave = patched_exe(source)
    patch_file = DIST / f'{NAME}-PL-{version}.patch'
    patch_info = patch.build(source, exe, patch_file, SLUG, EXE)
    assert patch_info['added_bytes'] <= 256, patch_info   # three small edits and the cave

    package = DIST / f'{NAME}-PL-{version}.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(pak_file, PAK_PATH)
        zf.write(patch_file, patch_file.name)
        zf.write(patch.applier(), f'{NAME}-PL-{version}.exe')
        zf.write(ROOT / 'docs/INSTALL.txt', 'READ-ME.txt')
    with zipfile.ZipFile(package) as zf:
        assert zf.testzip() is None
        assert zf.read(PAK_PATH) == archive
        names = zf.namelist()
    # The package carries no game content: our pak, a diff, the applier and the readme.
    assert not any(n.endswith(('.uasset', '.uexp', '.ubulk', '.umap')) or n == EXE for n in names), names

    print(json.dumps({
        'version': version,
        'translated': translated,
        'of_entries': total,
        'culture': CULTURE,
        'pak': str(pak_file), 'pak_bytes': len(archive),
        'exe_patch': str(patch_file), 'exe_patch_bytes': patch_info['patch_bytes'],
        'exe_patch_own_bytes': patch_info['added_bytes'], 'exe_cave': cave,
        'zip': str(package), 'zip_bytes': package.stat().st_size,
        'zip_files': names,
    }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
