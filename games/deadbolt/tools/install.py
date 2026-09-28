"""Installs/removes the DEADBOLT PL package in the local game for testing. Never starts the game.

Writes a manifest (what was there before) to backups/deadbolt/plugin/manifest.json
and checks the game files (exe, data.win, dia_*.json) stayed untouched.

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\install.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"
    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\install.py --game "..." --restore
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from build_plugin import FILES, PACKAGE

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BACKUP = REPO / 'backups/deadbolt/plugin'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def game_files(game: Path):
    return [game / 'deadbolt_game.exe', game / 'data.win', *sorted(game.glob('dia_*.json'))]


def main(game: Path, restore: bool):
    game = game.resolve(strict=True)
    if not (game / 'deadbolt_game.exe').is_file():
        raise SystemExit('Not a DEADBOLT directory')
    running = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq deadbolt_game.exe', '/FO', 'CSV', '/NH'])
    if b'deadbolt_game.exe' in running.lower():
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
            if path.exists() and digest(path) != sha:
                raise SystemExit(f'Changed since install, leaving it: {path}')
        for name in old['installed']:
            path = game / name
            if old['original'].get(name) is None:
                path.unlink(missing_ok=True)
            else:
                shutil.copy2(BACKUP / name, path)
        # The plugin creates the notgeese dir (log, dialogue cache); remove it whole if it wasn't there before.
        # Old manifests describe the directory used by the previous release.
        legacy = 'notgeese_existed' not in old and 'niegesi_existed' in old
        folder = 'NieGesi' if legacy else 'notgeese'
        existed_key = 'niegesi_existed' if legacy else 'notgeese_existed'
        if not old.get(existed_key):
            shutil.rmtree(game / folder, ignore_errors=True)
        old['installed'] = {}
        manifest_path.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
        print('Restored the pre-install state.')
        return

    if old and 'notgeese_existed' not in old:
        raise SystemExit('First restore the previous installation with --restore and archive its backup.')
    archive = ROOT / 'dist' / PACKAGE
    with ZipFile(archive) as z:
        if sorted(z.namelist()) != sorted(FILES) or z.testzip():
            raise SystemExit('Unexpected package contents')
        data = {name: z.read(name) for name in FILES}
    before = {str(p.relative_to(game)): digest(p) for p in game_files(game)}
    BACKUP.mkdir(parents=True, exist_ok=True)
    record = old or {'game': str(game), 'original': {}, 'installed': {},
                     'notgeese_existed': (game / 'notgeese').exists()}
    for name in sorted(FILES):
        target = game / name
        if old and name in old['installed'] and target.exists() and digest(target) != old['installed'][name]:
            raise SystemExit(f'Installed file changed, not overwriting: {target}')
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
    print(f'Installed {len(data)} files; exe, data.win and {len(after) - 2} dia_*.json files unchanged.')
    print(f'Manifest: {manifest_path}')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    p.add_argument('--restore', action='store_true')
    a = p.parse_args()
    main(a.game, a.restore)
