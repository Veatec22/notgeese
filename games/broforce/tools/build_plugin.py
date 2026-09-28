"""Build the BepInEx plugin package: Polish for Broforce without replacing game files.

Compiles the plugin, turns en-pl-review.json into pl.tsv, refreshes its EN from the game and
assembles the archive with BepInEx, plugin, texts and readme. Never touches the game dir.

    .venv\\Scripts\\python.exe games\\broforce\\tools\\build_plugin.py --game "C:\\Games\\Broforce"
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

from translations import polish_by_key, write_entries  # noqa: E402

VERSION = '0.1'
DATA = 'Broforce_Data'
PLUGIN_FOLDER = 'notgeeseBroforce'
PLUGIN_DLL = 'notgeeseBroforce.dll'
PACKAGE = f'Broforce-PL-{VERSION}.zip'

BEPINEX_VERSION = '5.4.23.5'
BEPINEX = REPO / 'vendor' / 'bepinex'
BEPINEX_BINARY = BEPINEX / f'BepInEx_win_x64_{BEPINEX_VERSION}.zip'
BEPINEX_SOURCE = BEPINEX / f'BepInEx-source-{BEPINEX_VERSION}.zip'
BEPINEX_CORE = BEPINEX / 'win_x64' / 'BepInEx' / 'core'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]

# mscorlib and System from the game, Unity modules, game code (Localisation) and BitCode (Singleton, LanguageManager base).
GAME_REFERENCES = [
    'mscorlib.dll',
    'System.dll',
    'System.Core.dll',
    'UnityEngine.dll',
    'UnityEngine.CoreModule.dll',
    'UnityEngine.TextRenderingModule.dll',
    'UnityEngine.UI.dll',
    'Assembly-CSharp.dll',
    'BitCode.dll',
]

BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']
SOURCES = ['Plugin.cs', 'PolishGlyphs.cs', 'PolishText3D.cs']


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def load_terms() -> dict[str, str]:
    return polish_by_key(ROOT)


def write_terms(terms: dict[str, str], destination: Path) -> int:
    """Texts -> pl.tsv: key, tab, text; newlines as \\n."""
    lines = []
    for key, value in terms.items():
        assert '\t' not in key and '\t' not in value, f'tab in {key}'
        assert '\r' not in value, f'CR in {key}'
        lines.append(f'{key}\t' + value.replace('\n', '\\n'))
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return len(lines)


def check_terms(terms: dict[str, str], english: dict[str, str]) -> list[str]:
    """Keys missing from the game bank and mismatched placeholders: would not show up or would crash."""
    import re
    problems = []
    for key, value in terms.items():
        if key not in english:
            problems.append(f'{key}: no such key in the game bank')
            continue
        want = sorted(re.findall(r'\{\d+\}', english[key]))
        have = sorted(re.findall(r'\{\d+\}', value))
        if want != have:
            problems.append(f'{key}: placeholders {have} instead of {want}')
        if english[key].count('<') != value.count('<'):
            problems.append(f'{key}: tag count differs from the original')
    return problems


def read_english(game: Path) -> dict[str, str]:
    """English text bank straight from resources.assets (for review and key checks)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    from bank import read_banks
    return read_banks(game / DATA / 'resources.assets')['en']


def write_review(terms: dict[str, str], english: dict[str, str]) -> int:
    """en-pl-review.json: every game bank entry, Polish where it exists."""
    review = []
    for key, value in english.items():
        if key.startswith('LANGUAGE_'):
            continue
        review.append({'key': key, 'english': value, 'polish': terms.get(key, '')})
    write_entries(ROOT, review)
    return len(review)


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
        *(str(ROOT / 'plugin' / name) for name in SOURCES),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(result.stdout or '', result.stderr or '', sep='\n')
        raise SystemExit('Plugin compilation failed.')


def package(work: Path) -> Path:
    out = ROOT / 'dist' / PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        # BepInEx straight from the official release; changelog skipped, it is clutter in the game dir.
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
        game_files = [n for n in names if n.startswith(DATA) or n.endswith(('.assets', '.assetbundle', '.resS'))]
        assert not game_files, f'the package carries no game files: {game_files}'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with Broforce.exe)')
    args = parser.parse_args()
    game = args.game.resolve()

    terms = load_terms()
    english = read_english(game)
    problems = check_terms(terms, english)
    if problems:
        print('\n'.join(problems))
        raise SystemExit('Texts do not match the game bank.')
    reviewed = write_review(terms, english)

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    count = write_terms(terms, work / 'pl.tsv')
    compile_plugin(game, work / PLUGIN_DLL)
    archive = package(work)

    print(json.dumps({
        'version': VERSION,
        'terms': count,
        'bank': reviewed,
        'plugin_bytes': (work / PLUGIN_DLL).stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
