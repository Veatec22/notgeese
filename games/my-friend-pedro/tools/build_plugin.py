"""Build the BepInEx plugin package: Polish for My Friend Pedro without replacing game files.

Compiles the plugin, turns en-pl-review.json into pl.tsv and assembles the archive with BepInEx,
plugin, texts and readme. Never touches the game dir.

    .venv\\Scripts\\python.exe games\\my-friend-pedro\\tools\\build_plugin.py --game "C:\\Games\\My Friend Pedro"
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

from translations import polish_by_key  # noqa: E402
VERSION = '0.1'
DATA = 'My Friend Pedro - Blood Bullets Bananas_Data'
PLUGIN_FOLDER = 'notgeesePedro'

BEPINEX_VERSION = '5.4.23.5'
BEPINEX = REPO / 'vendor' / 'bepinex'
BEPINEX_BINARY = BEPINEX / f'BepInEx_win_x64_{BEPINEX_VERSION}.zip'
BEPINEX_SOURCE = BEPINEX / f'BepInEx-source-{BEPINEX_VERSION}.zip'
BEPINEX_CORE = BEPINEX / 'win_x64' / 'BepInEx' / 'core'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]

# Minimal set: mscorlib and System from the game, Unity core and the I2 Localization assembly.
GAME_REFERENCES = [
    'mscorlib.dll',
    'System.dll',
    'System.Core.dll',
    'UnityEngine.dll',
    'UnityEngine.CoreModule.dll',
    'Assembly-CSharp-firstpass.dll',
]

BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def write_terms(destination: Path) -> int:
    """Texts -> pl.tsv: key, tab, text; newlines as \\n."""
    terms = polish_by_key(ROOT)
    lines = []
    for key, value in terms.items():
        assert '\t' not in key and '\t' not in value, f'tab in {key}'
        lines.append(f'{key}\t' + value.replace('\n', '\\n'))
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines)


def compile_plugin(game: Path, output: Path) -> None:
    managed = game / DATA / 'Managed'
    references = []
    for name in GAME_REFERENCES:
        path = managed / name
        if path.exists():
            references.append(f'/r:{path}')
        elif name not in ('UnityEngine.CoreModule.dll',):
            raise SystemExit(f'Missing {path}; is this the game dir?')
    for name in BEPINEX_REFERENCES:
        path = BEPINEX_CORE / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; unpack {BEPINEX_BINARY.name} into vendor/bepinex/win_x64.')
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


def package(work: Path, terms: int) -> Path:
    out = ROOT / 'dist' / f'My-Friend-Pedro-PL-{VERSION}.zip'
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

        archive.write(work / 'notgeesePedro.dll', f'BepInEx/plugins/{PLUGIN_FOLDER}/notgeesePedro.dll')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv')
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
        assert not any(name.endswith('resources.assets') for name in names), 'the package must not carry game files'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with the .exe)')
    args = parser.parse_args()

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    terms = write_terms(work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / 'notgeesePedro.dll')
    archive = package(work, terms)

    dll = (work / 'notgeesePedro.dll').stat().st_size

    print(json.dumps({
        'version': VERSION,
        'terms': terms,
        'plugin_bytes': dll,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
