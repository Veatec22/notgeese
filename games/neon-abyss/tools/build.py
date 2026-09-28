"""Build the BepInEx plugin package: Polish for Neon Abyss without replacing game files.

Compiles the plugin, turns en-pl-review.json into pl.tsv and assembles the archive with BepInEx,
plugin, texts and readme. Never touches the game dir.

    .venv\\Scripts\\python.exe games\\neon-abyss\\tools\\build.py --game "C:\\Games\\Neon Abyss"
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

from translations import polish_by_key  # noqa: E402
VERSION = '0.1'
PACKAGE = f'Neon-Abyss-PL-{VERSION}.zip'
DATA = 'NeonAbyss_Data'
PLUGIN_FOLDER = 'notgeeseNeonAbyss'
PLUGIN_DLL = 'notgeeseNeonAbyss.dll'

BEPINEX_VERSION = '5.4.23.5'
BEPINEX = REPO / 'vendor' / 'bepinex'
BEPINEX_BINARY = BEPINEX / f'BepInEx_win_x64_{BEPINEX_VERSION}.zip'
BEPINEX_SOURCE = BEPINEX / f'BepInEx-source-{BEPINEX_VERSION}.zip'
BEPINEX_CORE = BEPINEX / 'win_x64' / 'BepInEx' / 'core'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]

# mscorlib and System from the game, Unity modules, I2 Localization (firstpass) and TextMeshPro.
# Assembly-CSharp left out on purpose: the plugin finds the game's menu classes by name.
GAME_REFERENCES = [
    'mscorlib.dll',
    'System.dll',
    'System.Core.dll',
    'UnityEngine.dll',
    'UnityEngine.CoreModule.dll',
    'UnityEngine.TextRenderingModule.dll',
    'UnityEngine.TextCoreModule.dll',
    'UnityEngine.UI.dll',
    'Assembly-CSharp-firstpass.dll',
    'Unity.TextMeshPro.dll',
]

BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']
TOKEN = re.compile(r'\{[^}]*\}|</?[a-z]+(?:=[^>]*)?>|\[i2s_[^\]]*\]')


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def english_terms() -> dict[str, str]:
    source = ROOT / 'work' / 'source.json'
    if not source.exists():
        raise SystemExit('Missing work/source.json; run tools/extract.py first.')
    data = json.loads(source.read_text(encoding='utf-8'))
    index = [language['code'] for language in data['languages']].index('en-US')
    return {term['key']: term['values'][index] for term in data['terms'] if term['type'] == 0}


def write_terms(destination: Path) -> int:
    """Texts -> pl.tsv: key, tab, text; newlines as \\n. Checks tags."""
    terms = polish_by_key(ROOT)
    english = english_terms()
    lines = []
    for key, value in terms.items():
        assert key in english, f'unknown key {key}'
        assert value and '\t' not in key and '\t' not in value, f'empty text or tab in {key}'
        assert '\\n' not in value, f'literal \\n in {key}'
        assert sorted(TOKEN.findall(value)) == sorted(TOKEN.findall(english[key])), f'tags in {key}'
        lines.append(f'{key}\t' + value.replace('\n', '\\n'))
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines)


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
    out = ROOT / 'dist' / PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        # BepInEx straight from the official release; changelog skipped, it's clutter in the game dir.
        with zipfile.ZipFile(BEPINEX_BINARY) as bepinex:
            for name in bepinex.namelist():
                if name.endswith('/') or name == 'changelog.txt':
                    continue
                archive.writestr(name, bepinex.read(name))

        # LGPL-2.1 requires the license; sources lie next to the package.
        with zipfile.ZipFile(BEPINEX_SOURCE) as source:
            archive.writestr('BepInEx-LICENSE.txt', source.read(f'BepInEx-{BEPINEX_VERSION}/LICENSE'))

        archive.write(work / PLUGIN_DLL, f'BepInEx/plugins/{PLUGIN_FOLDER}/{PLUGIN_DLL}')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv')
        archive.write(ROOT / 'docs/INSTALL.txt', 'READ-ME.txt')
        archive.write(REPO / 'LICENSE', f'BepInEx/plugins/{PLUGIN_FOLDER}/LICENSE-notgeese.txt')

    shutil.copyfile(BEPINEX_SOURCE, out.parent / BEPINEX_SOURCE.name)

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert 'winhttp.dll' in names, 'BepInEx loader missing'
        assert 'BepInEx-LICENSE.txt' in names, 'BepInEx license missing'
        assert f'BepInEx/plugins/{PLUGIN_FOLDER}/pl.tsv' in names
        assert not any(name.startswith(DATA) or name.endswith(('.assets', '.resS')) for name in names), \
            'the package must not carry game files'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with NeonAbyss.exe)')
    args = parser.parse_args()

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    terms = write_terms(work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / PLUGIN_DLL)
    archive = package(work)

    print(json.dumps({
        'version': VERSION,
        'terms': terms,
        'plugin_bytes': (work / PLUGIN_DLL).stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
