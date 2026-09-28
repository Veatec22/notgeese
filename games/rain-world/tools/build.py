"""Build the Rain World translation as a Remix mod: plugin + Polish texts.

Compiles plugin/Plugin.cs against the installed game's libraries, turns en-pl-review.json into
text/text_pol/ files in the game's format and zips it for extraction into the game dir. The
package holds only the mod folder and the readme: the game has its own BepInEx and game files
are untouched. Writes nothing outside dist/ and work/.

    .venv\\Scripts\\python.exe games\\rain-world\\tools\\build.py [--game "C:\\Games\\Rain World"]
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import polish_by_key  # noqa: E402
VERSION = '0.1'
MOD_ID = 'notgeese-polski'
MOD_PATH = f'{rw.DATA}/StreamingAssets/mods/{MOD_ID}'
PACKAGE = f'Rain-World-PL-{VERSION}.zip'
DLL = 'notgeeseRainWorld.dll'

COMPILERS = [
    Path(r'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe'),
    Path(r'C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'),
]
GAME_REFERENCES = ['mscorlib.dll', 'System.dll', 'System.Core.dll', 'UnityEngine.dll',
                   'UnityEngine.CoreModule.dll', 'Assembly-CSharp.dll', 'Assembly-CSharp-firstpass.dll']
BEPINEX_REFERENCES = ['BepInEx.dll', '0Harmony.dll']

# Tokens the game substitutes or interprets; they must pass into the translation unchanged.
PLACEHOLDER = re.compile(r'<(?!LINE>)(?:[A-Za-z_][A-Za-z0-9_]*|[A-Z][A-Z_ ]*)>|\{[A-Za-z0-9_]*\}')

MODINFO = {
    'id': MOD_ID,
    'name': 'Polski (Not Geese)',
    'version': VERSION,
    'authors': 'Not Geese',
    'description': 'Spolszczenie Rain World. Dodaje język POLSKI w Opcje > Język. '
                   'Nie podmienia plików gry; teksty bez tłumaczenia zostają po angielsku.',
    'requirements': [],
    'requirements_names': [],
    'tags': [],
    'checksum_override_version': False,
}


def compiler() -> Path:
    for candidate in COMPILERS:
        if candidate.exists():
            return candidate
    raise SystemExit('C# compiler (csc.exe) not found.')


def compile_plugin(game: Path, output: Path) -> None:
    references = []
    for name in GAME_REFERENCES:
        path = game / rw.DATA / 'Managed' / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; is this the game dir?')
        references.append(f'/r:{path}')
    for name in BEPINEX_REFERENCES:
        # The game has its own BepInEx; the plugin binds to the one the player already has.
        path = game / 'BepInEx' / 'core' / name
        if not path.exists():
            raise SystemExit(f'Missing {path}; Rain World without built-in BepInEx? (needs 1.9+)')
        references.append(f'/r:{path}')
    command = [str(compiler()), '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/warn:4',
               '/target:library', f'/out:{output}', *references, str(ROOT / 'plugin' / 'Plugin.cs')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(result.stdout or '', result.stderr or '', sep='\n')
        raise SystemExit('Plugin compilation failed.')


def check(key: str, english: str, polish: str, problems: list[str]) -> None:
    if sorted(PLACEHOLDER.findall(english)) != sorted(PLACEHOLDER.findall(polish)):
        problems.append(f'{key}: tags {PLACEHOLDER.findall(english)} -> {PLACEHOLDER.findall(polish)}')
    if '\n' in polish or '\r' in polish:
        problems.append(f'{key}: newline (the game breaks lines with <LINE>)')
    if key.startswith('str:') and '|' in polish:
        problems.append(f'{key}: | would split the strings.txt entry')


def write_strings(folder: Path, polish: dict[str, str], english: dict[str, dict], problems: list[str]) -> int:
    lines = []
    for key, text in polish.items():
        if not key.startswith('str:'):
            continue
        k = key[4:]
        if '|' in k or not text:
            problems.append(f'{key}: empty text or | in the key')
            continue
        source = english.get(key, {}).get('english', k)
        check(key, source, text, problems)
        lines.append(f'{k}|{text}')
    # First char 0 = unencrypted file (the game strips it before parsing).
    (folder / 'strings.txt').write_text('0' + '\r\n'.join(lines), encoding='utf-8', newline='')
    return len(lines)


def write_dialogue(game: Path, folder: Path, polish: dict[str, str], problems: list[str]) -> tuple[int, int]:
    key = None
    files = lines_done = 0
    for source in rw.SOURCES:
        for path in rw.dialogue_files(game, source):
            wanted = {k for k in polish if k.startswith(f'dlg:{path.name}#')}
            if not wanted:
                continue
            key = key or rw.encryption_string(game)
            text, parsed = rw.read_dialogue(path, key)
            raw = text.split('\r\n')
            for line in parsed:
                entry = f'dlg:{path.name}#{line.index}'
                if entry in polish:
                    check(entry, line.text, polish[entry], problems)
                    raw[line.index] = line.prefix + polish[entry] + line.suffix
                    lines_done += 1
            # The "0-N…" header starts with 0, so the game reads the file as plain text.
            (folder / path.name).write_text('\r\n'.join(raw), encoding='utf-8', newline='')
            files += 1
    return files, lines_done


def package(stage: Path) -> Path:
    out = ROOT / 'dist' / PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                archive.write(path, f'{MOD_PATH}/{path.relative_to(stage).as_posix()}')
        archive.write(ROOT / 'docs' / 'INSTALL.txt', 'READ-ME.txt')

    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        # No game content in the package: everything but the readme is in our mod folder.
        stray = [n for n in names if n != 'READ-ME.txt' and not n.startswith(MOD_PATH + '/')]
        assert not stray, f'files outside the mod folder: {stray}'
        assert f'{MOD_PATH}/plugins/{DLL}' in names
        assert f'{MOD_PATH}/text/text_pol/strings.txt' in names
        assert f'{MOD_PATH}/modinfo.json' in names
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, default=rw.DEFAULT_GAME)
    args = parser.parse_args()
    game = args.game.resolve()

    polish = polish_by_key(ROOT)
    english_path = ROOT / 'work' / 'en.json'
    if not english_path.exists():
        raise SystemExit('Missing work/en.json; run tools/extract.py first.')
    english = json.loads(english_path.read_text(encoding='utf-8'))
    unknown = [k for k in polish if k not in english and k != 'str:POLISH']
    if unknown:
        print('Keys not in the game (typo or version change):', unknown[:10])

    stage = ROOT / 'dist' / MOD_ID
    if stage.exists():
        shutil.rmtree(stage)
    text = stage / 'text' / 'text_pol'
    text.mkdir(parents=True)
    (stage / 'plugins').mkdir()

    problems: list[str] = []
    strings = write_strings(text, polish, english, problems)
    files, lines = write_dialogue(game, text, polish, problems)
    if problems:
        print('\n'.join(problems))
        raise SystemExit(f'{len(problems)} translation problems; no package built.')

    compile_plugin(game, stage / 'plugins' / DLL)
    (stage / 'modinfo.json').write_text(json.dumps(MODINFO, ensure_ascii=False, indent='\t'), encoding='utf-8')
    shutil.copyfile(REPO / 'LICENSE', stage / 'LICENSE-notgeese.txt')

    archive = package(stage)
    total = len(english)
    done = sum(1 for k in polish if k in english)
    print(json.dumps({
        'version': VERSION,
        'strings': strings,
        'dialogue_files': files,
        'dialogue_lines': lines,
        'entries': {'done': done, 'total': total},
        'plugin_bytes': (stage / 'plugins' / DLL).stat().st_size,
        'package': str(archive),
        'package_bytes': archive.stat().st_size,
        'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()[:16],
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
