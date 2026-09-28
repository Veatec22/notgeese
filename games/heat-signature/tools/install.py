"""Install/restore the local plugin probe with backups; never launches the game."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile
from build_plugin import VERSION
from font_assets import VARIANTS

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BACKUP = REPO / 'backups/heat-signature/plugin'
FILES = {'d3d9.dll', 'notgeese/pl.tsv', 'notgeese/LICENSE-MINHOOK.txt', 'READ-ME.txt'}
FILES |= {'notgeese/LICENSE-XOLONIUM.txt', 'notgeese/fonts/charmap.txt'}
FILES |= {f'notgeese/fonts/font-{s}-{b}-{i}.png' for s, b, i in VARIANTS}
FILES |= {f'notgeese/fonts/font-{s}-{b}-{i}.metrics' for s, b, i in VARIANTS}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(game, restore):
    game = game.resolve(strict=True)
    if not (game / 'Heat_Signature.exe').is_file():
        raise SystemExit('Not a Heat Signature installation')
    processes = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq Heat_Signature.exe', '/FO', 'CSV', '/NH'])
    if b'"heat_signature.exe"' in processes.lower():
        raise SystemExit('Close Heat Signature before installing/restoring')
    manifest_path = BACKUP / 'manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else None
    if old and Path(old['game']).resolve() != game:
        raise SystemExit('Existing backup belongs to another installation')
    for name in FILES:
        (game / name).resolve().relative_to(game)
    if restore:
        if not old or not old.get('installed'):
            raise SystemExit('No active installation recorded')
        for name, sha in old['installed'].items():
            path = game / name
            if path.exists() and digest(path) != sha:
                raise SystemExit(f'Changed since installation, preserve manually: {path}')
        for name in old['installed']:
            path = game / name
            if old['original'][name] is None:
                path.unlink(missing_ok=True)
            else:
                shutil.copy2(BACKUP / name, path)
        old['installed'] = {}
        manifest_path.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
        print('Plugin files restored; user logs retained')
        return
    if old and not old.get('installed'):
        raise SystemExit('Previous installation restored; archive its backup before a new install')
    archive = ROOT / f'dist/Heat-Signature-PL-{VERSION}.zip'
    with ZipFile(archive) as z:
        if set(z.namelist()) != FILES or z.testzip():
            raise SystemExit('Unexpected package contents')
        data = {name: z.read(name) for name in FILES}
    # Record all original game files we must leave untouched.
    unchanged = [game / 'Heat_Signature.exe', *sorted((game / 'Dialog').glob('*.txt'))]
    before = {str(p.relative_to(game)): digest(p) for p in unchanged}
    BACKUP.mkdir(parents=True, exist_ok=True)
    record = old or {'game': str(game), 'original': {}, 'installed': {}}
    for name in sorted(FILES):
        target = game / name
        if old and name in old['installed'] and target.exists() and digest(target) != old['installed'][name]:
            raise SystemExit(f'Changed installed file, will not overwrite: {target}')
        if name not in record['original']:
            record['original'][name] = digest(target) if target.exists() else None
            if target.exists():
                backup = BACKUP / name
                if backup.exists():
                    raise SystemExit(f'Untracked backup exists: {backup}')
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
    record['original_game_files'] = before
    # Save restore metadata before writing any plugin file.
    record['installed'] = {name: hashlib.sha256(value).hexdigest() for name, value in data.items()}
    manifest_path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    for name, value in data.items():
        target = game / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
        assert digest(target) == record['installed'][name]
    assert before == {str(p.relative_to(game)): digest(p) for p in unchanged}
    print(f'Installed {len(data)} files. EXE and {len(unchanged)-1} original dialogue files unchanged.')
    print(f'Restore manifest: {manifest_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    main(args.game, args.restore)
