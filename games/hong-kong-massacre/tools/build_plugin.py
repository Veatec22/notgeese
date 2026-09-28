"""Build the BepInEx plugin package: Polish for The Hong Kong Massacre without replacing game files.

Compiles the plugin, turns en-pl-review.json into pl.tsv and assembles the archive with BepInEx,
plugin, texts and readme. Never touches the game dir (it only reads references from Managed).

    .venv\\Scripts\\python.exe games\\hong-kong-massacre\\tools\\build_plugin.py --game "C:\\Games\\The Hong Kong Massacre"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries  # noqa: E402

VERSION = '0.1'
NAME = 'The-Hong-Kong-Massacre'
DATA = 'THKM_Data'
PLUGIN_FOLDER = 'notgeeseHongKongMassacre'
DLL = 'notgeeseHongKongMassacre.dll'

BEPINEX_VERSION = '5.4.23.5'
BEPINEX = REPO / 'vendor' / 'bepinex'
BEPINEX_BINARY = BEPINEX / f'BepInEx_win_x64_{BEPINEX_VERSION}.zip'
BEPINEX_SOURCE = BEPINEX / f'BepInEx-source-{BEPINEX_VERSION}.zip'
BEPINEX_CORE = BEPINEX / 'win_x64' / 'BepInEx' / 'core'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]

GAME_REFERENCES = [
    'mscorlib.dll', 'System.dll', 'System.Core.dll',
    'UnityEngine.dll', 'UnityEngine.CoreModule.dll', 'UnityEngine.TextRenderingModule.dll',
    'UnityEngine.UI.dll', 'UnityEngine.UIModule.dll', 'DialogueSystem.dll',
]
BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']

KEY_KINDS = ('dlg/', 'ui/', 'fmt/', 'rewired/')
TOKEN = re.compile(r'\{\d+\}')


def fingerprint(text: str) -> int:
    """FNV-1a over ASCII letters and digits; the same function is in Plugin.cs."""
    value = 2166136261
    for c in text:
        if ord(c) > 127 or not c.isalnum():
            continue
        value ^= ord(c)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def escape(value: str) -> str:
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')


def write_terms(destination: Path) -> dict:
    """Translated entries -> pl.tsv: key, fingerprint, text. Checks tokens and key kinds."""
    lines, counts, problems = [], {}, []
    entries = load_entries(ROOT)
    for entry in entries:
        key, english, polish = entry['key'], entry['english'], entry['polish']
        if not key.startswith(KEY_KINDS):
            problems.append(f'{key}: unknown key kind')
        if not polish:
            continue
        if sorted(TOKEN.findall(english)) != sorted(TOKEN.findall(polish)):
            problems.append(f'{key}: placeholders differ')
        if english.count('\t') != polish.count('\t') and key.startswith('ui/'):
            problems.append(f'{key}: tab count differs (icon spacing)')
        kind = key.split('/')[0]
        counts[kind] = counts.get(kind, 0) + 1
        lines.append(f'{escape(key)}\t{fingerprint(english):08x}\t{escape(polish)}')
    if problems:
        raise SystemExit('Translation problems:\n  ' + '\n  '.join(problems))
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {'total': len(entries), 'translated': len(lines), 'by_kind': counts}


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def compile_plugin(game: Path, output: Path) -> None:
    managed = game / DATA / 'Managed'
    references = []
    for name in GAME_REFERENCES:
        path = managed / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; is this the game dir?')
        references.append(f'/r:{path}')
    for name in BEPINEX_REFERENCES:
        path = BEPINEX_CORE / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; unpack {BEPINEX_BINARY.name} into vendor/bepinex/win_x64.')
        references.append(f'/r:{path}')
    command = [str(compiler()), '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/warn:4',
               '/target:library', f'/out:{output}', *references, str(ROOT / 'plugin' / 'Plugin.cs')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(result.stdout or '', result.stderr or '', sep='\n')
        raise SystemExit('Plugin compilation failed.')


def package(work: Path) -> Path:
    out = ROOT / 'dist' / f'{NAME}-PL-{VERSION}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        with zipfile.ZipFile(BEPINEX_BINARY) as bepinex:
            for name in bepinex.namelist():
                if not name.endswith('/'):
                    archive.writestr(name, bepinex.read(name))
        with zipfile.ZipFile(BEPINEX_SOURCE) as source:
            archive.writestr('BepInEx-LICENSE.txt', source.read(f'BepInEx-{BEPINEX_VERSION}/LICENSE'))
        archive.write(work / DLL, f'BepInEx/plugins/{PLUGIN_FOLDER}/{DLL}')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv')
        archive.write(REPO / 'LICENSE', f'BepInEx/plugins/{PLUGIN_FOLDER}/LICENSE-notgeese.txt')
        archive.write(ROOT / 'docs' / 'INSTALL-plugin.txt', 'READ-ME.txt')
    shutil.copyfile(BEPINEX_SOURCE, out.parent / BEPINEX_SOURCE.name)

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert 'winhttp.dll' in names, 'BepInEx loader missing'
        assert 'BepInEx-LICENSE.txt' in names, 'BepInEx license missing'
        assert f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv' in names
        game_like = [n for n in names if re.search(r'\.(assets|resS|resource)$|^level\d+$|THKM_Data/', n)]
        assert not game_like, f'the package must not carry game files: {game_like}'
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with THKM.exe)')
    args = parser.parse_args()

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    terms = write_terms(work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / DLL)
    archive = package(work)
    print(json.dumps({
        'version': VERSION,
        'terms': terms,
        'plugin_bytes': (work / DLL).stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
