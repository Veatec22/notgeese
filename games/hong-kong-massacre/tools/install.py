"""Installs/removes The Hong Kong Massacre PL package in the local game for testing. Never starts the game.

Writes a manifest (what was there before) to backups/hong-kong-massacre/plugin/manifest.json and
checks that the game's exe and data files stayed untouched.

    .venv\\Scripts\\python.exe games\\hong-kong-massacre\\tools\\install.py --game "C:\\Games\\The Hong Kong Massacre"
    .venv\\Scripts\\python.exe games\\hong-kong-massacre\\tools\\install.py --game "..." --restore
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from build_plugin import NAME, VERSION

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BACKUP = REPO / 'backups/hong-kong-massacre/plugin'
EXE = 'THKM.exe'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def game_files(game: Path):
    """Exe and the small top-level data files; the big resources are never opened for writing."""
    return [game / EXE, game / 'UnityPlayer.dll', *sorted((game / 'THKM_Data').glob('globalgamemanagers*')),
            *sorted((game / 'THKM_Data' / 'Managed').glob('*.dll'))]


def main(game: Path, restore: bool):
    game = game.resolve(strict=True)
    if not (game / EXE).is_file():
        raise SystemExit('Not a The Hong Kong Massacre directory')
    running = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {EXE}', '/FO', 'CSV', '/NH'])
    if EXE.lower().encode() in running.lower():
        raise SystemExit('Close the game before install/restore')
    manifest_path = BACKUP / 'manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else None
    if old and Path(old['game']).resolve() != game:
        raise SystemExit('The manifest belongs to another installation')

    if restore:
        if not old or not old.get('installed'):
            raise SystemExit('No recorded installation')
        for name, sha in old['installed'].items():
            path = game / name
            if path.exists() and digest(path) != sha and not name.endswith('pl.tsv'):
                raise SystemExit(f'Changed since install, leaving it: {path}')
        for name in old['installed']:
            path = game / name
            if old['original'].get(name) is None:
                path.unlink(missing_ok=True)
            else:
                shutil.copy2(BACKUP / name, path)
        # BepInEx creates config, cache and logs next to its files; remove the dir if it wasn't there before.
        if not old.get('bepinex_existed'):
            shutil.rmtree(game / 'BepInEx', ignore_errors=True)
        old['installed'] = {}
        manifest_path.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
        print('Restored the pre-install state.')
        return

    archive = ROOT / 'dist' / f'{NAME}-PL-{VERSION}.zip'
    with ZipFile(archive) as z:
        if z.testzip():
            raise SystemExit('Broken package')
        data = {name: z.read(name) for name in z.namelist() if not name.endswith('/')}
    before = {str(p.relative_to(game)): digest(p) for p in game_files(game)}
    BACKUP.mkdir(parents=True, exist_ok=True)
    record = old or {'game': str(game), 'original': {}, 'installed': {},
                     'bepinex_existed': (game / 'BepInEx').exists()}
    for name in sorted(data):
        target = game / name
        if name not in record['original']:
            record['original'][name] = digest(target) if target.exists() else None
            if target.exists():
                backup = BACKUP / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
    record['original_game_files'] = before
    record['installed'] = {name: hashlib.sha256(value).hexdigest() for name, value in data.items()}
    manifest_path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    for name, value in data.items():
        target = game / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    after = {str(p.relative_to(game)): digest(p) for p in game_files(game)}
    assert before == after
    print(f'Installed {len(data)} files from {archive.name}; {len(after)} game files unchanged.')
    print(f'Manifest: {manifest_path}')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    p.add_argument('--restore', action='store_true')
    a = p.parse_args()
    main(a.game, a.restore)
