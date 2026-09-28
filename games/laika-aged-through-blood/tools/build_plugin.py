"""Build the BepInEx plugin package: Polish for Laika: Aged Through Blood without replacing game files.

Checks en-pl-review.json against the game's English texts (work/source/en.json from extract.py),
compiles the plugin, writes the texts as pl.tsv and zips BepInEx, plugin, texts and readme.
Never touches the game dir.

    .venv\\Scripts\\python.exe games\\laika-aged-through-blood\\tools\\build_plugin.py --game "C:\\Games\\Laika Aged Through Blood"
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
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import polish_by_key  # noqa: E402

VERSION = '0.1'
DATA = 'Laika Aged through Blood_Data'
PLUGIN = 'notgeeseLaika'
PACKAGE = 'Laika-Aged-Through-Blood-PL'

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
    'netstandard.dll',
    'System.dll',
    'System.Core.dll',
    'System.Xml.dll',
    'UnityEngine.dll',
    'UnityEngine.CoreModule.dll',
    'UnityEngine.TextCoreFontEngineModule.dll',  # Glyph, GlyphRect, FaceInfo
    'UnityEngine.TextRenderingModule.dll',       # Font, source of dynamic fonts
    'UnityEngine.UI.dll',                        # TMP_Text inherits Graphic
    'Unity.TextMeshPro.dll',
    'Assembly-CSharp-firstpass.dll',             # Language (M2H Localization)
    'Assembly-CSharp.dll',                       # SettingsViewItem
]
BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']

# TMP tags and game inserts that must pass into the translation unchanged.
TOKENS = re.compile(r'\{\d+\}|<sprite[^>]*>|</?(?:color|size|b|i|u|s|link)\b[^>]*>|<br>')


def tokens(text: str) -> Counter:
    return Counter(TOKENS.findall(text))


def check(terms: dict[str, str]) -> dict:
    """Key must be a game key; {0}, <sprite>, <color> and <br> as in the original."""
    source = json.loads((ROOT / 'work/source/en.json').read_text(encoding='utf-8'))
    english = {row['key']: row for row in source}
    problems, long = [], []
    for key, value in terms.items():
        row = english.get(key)
        if row is None:
            problems.append(f'{key}: no such key in the game')
            continue
        if '\t' in value or '\n' in value or '\r' in value:
            problems.append(f'{key}: tab or line break in text (the game breaks lines with <br>)')
        if tokens(row['text']) != tokens(value):
            problems.append(f'{key}: wstawki {sorted(tokens(row["text"]).elements())} != {sorted(tokens(value).elements())}')
        plain = TOKENS.sub('', value)
        if 'limit' in row and len(plain) > row['limit'] and len(plain) > len(TOKENS.sub('', row['text'])):
            long.append(f'{key}: {len(plain)} > limit {row["limit"]} (EN {len(TOKENS.sub("", row["text"]))})')
    if problems:
        raise SystemExit('en-pl-review.json has errors:\n  ' + '\n  '.join(problems))
    with_text = [r for r in source if r['text']]
    return {
        'game_texts': len(with_text),
        'translated': sum(1 for r in with_text if r['key'] in terms),
        'over_limit': long,
    }


def write_terms(terms: dict[str, str], destination: Path) -> int:
    lines = [f'{key}\t{value}' for key, value in terms.items()]
    # newline='\n': otherwise Python on Windows writes CRLF.
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return len(lines)


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
            raise SystemExit(f'Missing {path}; unpack {BEPINEX_BINARY.name} into {BEPINEX_CORE.parents[1]}.')
        references.append(f'/r:{path}')

    command = [
        str(compiler()),
        '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/warn:4',
        '/target:library',
        f'/out:{output}',
        *references,
        *[str(p) for p in sorted((ROOT / 'plugin').glob('*.cs'))],
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        log = output.parent / 'compile.log'
        log.write_text((result.stdout or '') + '\n' + (result.stderr or ''), encoding='utf-8')
        raise SystemExit(f'Plugin compilation failed; details in {log}')


def package(work: Path) -> Path:
    out = ROOT / 'dist' / f'{PACKAGE}-{VERSION}.zip'
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

        archive.write(work / f'{PLUGIN}.dll', f'BepInEx/plugins/{PLUGIN}/{PLUGIN}.dll')
        archive.write(work / 'pl.tsv', f'BepInEx/plugins/{PLUGIN}/pl.tsv')
        archive.write(ROOT / 'docs/INSTALL-plugin.txt', 'READ-ME.txt')
        archive.write(REPO / 'LICENSE', f'BepInEx/plugins/{PLUGIN}/LICENSE-notgeese.txt')

    shutil.copyfile(BEPINEX_SOURCE, out.parent / BEPINEX_SOURCE.name)

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert 'winhttp.dll' in names, 'BepInEx loader missing'
        assert 'BepInEx-LICENSE.txt' in names, 'BepInEx license missing'
        assert not any(name.endswith(('.assets', '.resS', '.resource', '.unity3d', '.bank')) for name in names), \
            'the package must not contain game files'
        assert not any(name.startswith(DATA) for name in names), 'the package must not contain game files'

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='game dir (the one with Laika Aged through Blood.exe)')
    args = parser.parse_args()

    terms = polish_by_key(ROOT)
    stats = check(terms)

    work = ROOT / 'work' / 'plugin'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    entries = write_terms(terms, work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / f'{PLUGIN}.dll')
    archive = package(work)

    print(json.dumps({
        'version': VERSION,
        'entries': entries,
        **stats,
        'plugin_bytes': (work / f'{PLUGIN}.dll').stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
