"""Build the BepInEx plugin package: Polish for Dread Templar without replacing game files.

Turns en-pl-review.json into pl.tsv (entry kind, category/key, text), compiles the plugin
and assembles the archive with BepInEx, texts and readme. Never touches the game dir.

    .venv\\Scripts\\python.exe games\\dread-templar\\tools\\build_plugin.py --game "C:\\Games\\Dread Templar"
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

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
REPO = ROOT.parents[1]

sys.path.insert(0, str(TOOLS))
from game import CATEGORIES  # noqa: E402
from texts import polish_tree  # noqa: E402

VERSION = '0.1'
DATA = 'DreadTemplar_Data'
PLUGIN_FOLDER = 'notgeeseDreadTemplar'

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
    'mscorlib.dll',
    'System.dll',
    'System.Core.dll',
    'UnityEngine.dll',
    'UnityEngine.CoreModule.dll',
    'Assembly-CSharp.dll',
]

BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def escape(value: str) -> str:
    """Backslash, newline and tab (the last one separates columns)."""
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')


def write_terms(destination: Path) -> tuple[int, int]:
    """Texts: category -> key -> {text, name}. The plugin asks for "category/key"."""
    polish = polish_tree()
    unknown = [c for c in polish if c not in CATEGORIES]
    assert not unknown, f'unknown categories: {unknown}'

    lines = []
    texts = names = 0
    for category, entries in polish.items():
        for key, entry in entries.items():
            path = f'{category}/{key}'
            assert '\t' not in path, path
            text = entry.get('text')
            # Some entries carry numbers (speaker id) instead of text.
            if isinstance(text, str) and text:
                lines.append(f't\t{path}\t' + escape(text))
                texts += 1
            name = entry.get('name')
            # Names are sometimes numbers (speaker id); those are skipped.
            if isinstance(name, str) and name:
                lines.append(f'n\t{path}\t' + escape(name))
                names += 1

    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return texts, names


def compile_plugin(game: Path, output: Path) -> None:
    managed = game / DATA / 'Managed'
    references = []
    for name in GAME_REFERENCES:
        path = managed / name
        if path.exists():
            references.append(f'/r:{path}')
        elif name != 'UnityEngine.CoreModule.dll':
            raise SystemExit(f'Missing {path}; is this the game dir?')
    for name in BEPINEX_REFERENCES:
        path = BEPINEX_CORE / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; unpack {BEPINEX_BINARY.name} into {BEPINEX_CORE.parents[1]}.')
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
        log = output.parent / 'compile.log'
        log.write_text((result.stdout or '') + '\n' + (result.stderr or ''), encoding='utf-8')
        raise SystemExit(f'Plugin compilation failed; details in {log}')


def package(work: Path) -> Path:
    out = ROOT / 'dist' / f'Dread-Templar-PL-{VERSION}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        with zipfile.ZipFile(BEPINEX_BINARY) as bepinex:
            for name in bepinex.namelist():
                if name.endswith('/') or name == 'changelog.txt':
                    continue
                archive.writestr(name, bepinex.read(name))

        # LGPL-2.1 requires the license; sources go next to the package.
        with zipfile.ZipFile(BEPINEX_SOURCE) as source:
            archive.writestr('BepInEx-LICENSE.txt', source.read(f'BepInEx-{BEPINEX_VERSION}/LICENSE'))

        archive.write(work / 'notgeeseDreadTemplar.dll', f'BepInEx/plugins/{PLUGIN_FOLDER}/notgeeseDreadTemplar.dll')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv')
        archive.write(ROOT / 'docs/INSTALL-plugin.txt', 'READ-ME.txt')
        archive.write(REPO / 'LICENSE', f'BepInEx/plugins/{PLUGIN_FOLDER}/LICENSE-notgeese.txt')

    shutil.copyfile(BEPINEX_SOURCE, out.parent / BEPINEX_SOURCE.name)

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert 'winhttp.dll' in names, 'BepInEx loader missing'
        assert 'BepInEx-LICENSE.txt' in names, 'BepInEx license missing'
        assert not any(name.endswith(('.assets', '.resS', '.resource')) for name in names), \
            'the package must not contain game assets'
        assert not any(name.startswith(DATA) or name.startswith('level') for name in names), \
            'the package must not contain game files'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with the .exe)')
    args = parser.parse_args()

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    texts, names = write_terms(work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / 'notgeeseDreadTemplar.dll')
    archive = package(work)

    print(json.dumps({
        'version': VERSION,
        'texts': texts,
        'names': names,
        'plugin_bytes': (work / 'notgeeseDreadTemplar.dll').stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
