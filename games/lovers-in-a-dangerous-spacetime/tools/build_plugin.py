"""Build the BepInEx plugin package: Polish for Lovers in a Dangerous Spacetime without replacing game files.

Compiles the plugin, turns en-pl-review.json into pl.tsv and assembles the archive with BepInEx
(x86: the game is 32-bit), plugin, texts and readme. Never touches the game dir.

    .venv\\Scripts\\python.exe games\\lovers-in-a-dangerous-spacetime\\tools\\build_plugin.py --game "C:\\Games\\Lovers in a Dangerous Spacetime"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries, untranslated  # noqa: E402

VERSION = '0.1'
NAME = 'Lovers-in-a-Dangerous-Spacetime'
DATA = 'LoversInADangerousSpacetime_Data'
PLUGIN_FOLDER = 'notgeeseLovers'
PLUGIN_DLL = 'notgeeseLovers.dll'

BEPINEX_VERSION = '5.4.23.5'
BEPINEX = REPO / 'vendor' / 'bepinex'
BEPINEX_BINARY = BEPINEX / f'BepInEx_win_x86_{BEPINEX_VERSION}.zip'
BEPINEX_SOURCE = BEPINEX / f'BepInEx-source-{BEPINEX_VERSION}.zip'
# Managed core is the same in the x86 and x64 builds; only the Doorstop loader differs.
BEPINEX_CORE = BEPINEX / 'win_x64' / 'BepInEx' / 'core'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]

# Entries for texts outside the game's tables (credits, end screen): matched by exact English.
STATIC_PREFIX = 'Static.'

# Unity 5.0: one UnityEngine.dll, .NET 3.5 profile mscorlib from the game.
GAME_REFERENCES = ['mscorlib.dll', 'System.dll', 'System.Core.dll', 'UnityEngine.dll', 'UnityEngine.UI.dll',
                   'Assembly-CSharp.dll']
BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def write_table(destination: Path, rows: list[tuple[str, str]]) -> int:
    """Rows -> TSV: first column, tab, Polish; newlines as \\n; LF line ends."""
    lines = []
    for first, polish in rows:
        assert '\t' not in first and '\t' not in polish, f'tab in {first}'
        lines.append(first.replace('\r', '').replace('\n', '\\n') + '\t' + polish.replace('\r', '').replace('\n', '\\n'))
    destination.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    return len(lines)


def write_terms(work: Path) -> tuple[int, int]:
    """pl.tsv: game key -> Polish. static.tsv: exact English -> Polish for texts outside the tables."""
    entries = [entry for entry in load_entries(ROOT) if not untranslated(entry)]
    terms = [(e['key'], e['polish']) for e in entries if not e['key'].startswith(STATIC_PREFIX)]
    screen = [(e['english'], e['polish']) for e in entries if e['key'].startswith(STATIC_PREFIX)]
    return write_table(work / 'pl.tsv', terms), write_table(work / 'static.tsv', screen)


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
            raise SystemExit(f'Missing {path}; unpack the x64 BepInEx {BEPINEX_VERSION} into vendor/bepinex/win_x64.')
        references.append(f'/r:{path}')

    command = [
        str(compiler()),
        '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/warn:4',
        '/target:library',
        f'/out:{output}',
        *references,
        str(ROOT / 'plugin' / 'Plugin.cs'),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(result.stdout or '', result.stderr or '', sep='\n')
        raise SystemExit('Plugin compilation failed.')


def package(work: Path) -> Path:
    if not BEPINEX_BINARY.exists():
        raise SystemExit(f'Missing {BEPINEX_BINARY}; download it from the BepInEx {BEPINEX_VERSION} GitHub release.')
    out = ROOT / 'dist' / f'{NAME}-PL-{VERSION}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        # Whole BepInEx from the official release, docs included.
        with zipfile.ZipFile(BEPINEX_BINARY) as bepinex:
            for name in bepinex.namelist():
                if name.endswith('/'):
                    continue
                archive.writestr(name, bepinex.read(name))

        # LGPL-2.1 requires the license; sources lie next to the package.
        with zipfile.ZipFile(BEPINEX_SOURCE) as source:
            archive.writestr('BepInEx-LICENSE.txt', source.read(f'BepInEx-{BEPINEX_VERSION}/LICENSE'))

        # Unity 5.0 crashes with the default entrypoint (Application..cctor); ours starts later.
        archive.write(ROOT / 'plugin' / 'BepInEx.cfg', 'BepInEx/config/BepInEx.cfg')
        archive.write(work / PLUGIN_DLL, f'BepInEx/plugins/{PLUGIN_FOLDER}/{PLUGIN_DLL}')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv')
        archive.write(work / 'static.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/static.tsv')
        archive.write(ROOT / 'docs/INSTALL-plugin.txt', 'READ-ME.txt')
        archive.write(REPO / 'LICENSE', f'BepInEx/plugins/{PLUGIN_FOLDER}/LICENSE-notgeese.txt')

    # BepInEx sources as a separate file next to the package, same download location.
    shutil.copyfile(BEPINEX_SOURCE, out.parent / BEPINEX_SOURCE.name)

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert 'winhttp.dll' in names, 'BepInEx loader missing'
        assert 'BepInEx-LICENSE.txt' in names, 'BepInEx license missing'
        assert f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv' in names
        assert 'BepInEx/config/BepInEx.cfg' in names, 'entrypoint config missing'
        game_files = [name for name in names if name.endswith(('.assets', '.resource')) or name.startswith(DATA)]
        assert not game_files, f'the package must not carry game files: {game_files}'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with the .exe)')
    parser.add_argument('--compile-only', action='store_true', help='check that the plugin compiles; no package')
    args = parser.parse_args()

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    terms, screen = write_terms(work)
    compile_plugin(args.game.resolve(), work / PLUGIN_DLL)
    report = {'version': VERSION, 'terms': terms, 'screen_texts': screen,
              'plugin_bytes': (work / PLUGIN_DLL).stat().st_size}
    if not args.compile_only:
        archive = package(work)
        report.update({
            'package': str(archive),
            'package_bytes': archive.stat().st_size,
            'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
            'bepinex': f'win_x86 {BEPINEX_VERSION}',
        })
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
