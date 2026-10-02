"""Build the BepInEx plugin package: Polish for Anger Foot without replacing game files.

Reads a GUID -> Polish map from the original resources.assets (en-pl-review.json points
to an entry by `id`, the Unity object path ID, which the plugin cannot see in game),
compiles the plugin and assembles the archive with BepInEx, texts and readme.

    .venv\\Scripts\\python.exe games\\anger-foot\\tools\\build_plugin.py --game "C:\\Games\\Anger Foot"
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

import UnityPy

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import polish_by_field  # noqa: E402

sys.path.insert(0, str(TOOLS))
from assets import SLOT, parse_entry, rd  # noqa: E402

VERSION = '0.2'
DATA = 'Anger Foot_Data'
PLUGIN_FOLDER = 'notgeeseAngerFoot'

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
    'Assembly-CSharp-firstpass.dll',  # home of ScriptableEnum, which LocalizationLanguage inherits
]

BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def guid_of(raw: bytes, entry: dict) -> str:
    """The GUID sits after the twelve translations, right before the asset path."""
    position = entry['list_start'] + 4
    for _ in range(12):
        position += 12
        _, position = rd(raw, position)
    guid, _ = rd(raw, position)
    return guid


def write_terms(game: Path, destination: Path) -> tuple[int, int]:
    """An entry's `id` is the path_id; the plugin recognizes entries by GUID."""
    polish = polish_by_field(ROOT, 'id')
    env = UnityPy.load(str(game / DATA / 'resources.assets'))

    lines = []
    entries = 0
    seen = set()
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        raw = obj.get_raw_data()
        try:
            entry = parse_entry(raw)
        except Exception:
            continue
        if not entry:
            continue
        entries += 1
        text = polish.get(obj.path_id)
        if not text:
            continue
        guid = guid_of(raw, entry)
        assert guid not in seen, f'duplicate GUID {guid}'
        seen.add(guid)
        assert '\t' not in guid and '\t' not in text, entry['key']
        lines.append(f'{guid}\t' + text.replace('\n', '\\n'))

    assert entries >= 1700, f'only {entries} text entries found; wrong file?'
    assert len(lines) == len(polish), f'translated {len(polish)}, matched {len(lines)}'
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines), entries


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
    out = ROOT / 'dist' / f'Anger-Foot-PL-{VERSION}.zip'
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

        archive.write(work / 'notgeeseAngerFoot.dll', f'BepInEx/plugins/{PLUGIN_FOLDER}/notgeeseAngerFoot.dll')
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

    translated, entries = write_terms(args.game.resolve(), work / 'pl.tsv')
    compile_plugin(args.game.resolve(), work / 'notgeeseAngerFoot.dll')
    archive = package(work)

    print(json.dumps({
        'version': VERSION,
        'translated': translated,
        'text_entries': entries,
        'slot': SLOT,
        'plugin_bytes': (work / 'notgeeseAngerFoot.dll').stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
        'bepinex': BEPINEX_VERSION,
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
