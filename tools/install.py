"""Install a built translation into a game directory, or restore the originals.

For testing only - what players get is a drag-and-drop package, not a script.
Every file is copied to backups/<game>/ before it is overwritten, and a file
that already has a backup is never backed up again, so running this twice can
never overwrite good originals with patched ones.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True, help='The game data folder to write into')
    parser.add_argument('--built', type=Path, help='Built folder to install, e.g. games/<game>/dist/<Name>_Data')
    parser.add_argument('--backup', type=Path, required=True, help='Where the originals are kept')
    parser.add_argument('--restore', action='store_true', help='Copy the backup back over the game instead')
    args = parser.parse_args()

    game, backup = args.game.resolve(), args.backup.resolve()
    if not game.is_dir():
        raise SystemExit(f'Not a directory: {game}')

    if args.restore:
        files = sorted(p for p in backup.rglob('*') if p.is_file())
        if not files:
            raise SystemExit(f'Nothing to restore from {backup}')
        for source in files:
            target = game / source.relative_to(backup)
            shutil.copy2(source, target)
            assert digest(target) == digest(source), str(source)
        print(json.dumps({'restored': len(files), 'from': str(backup), 'into': str(game)}))
        return

    if args.built is None:
        raise SystemExit('--built is required unless --restore is given')
    built = args.built.resolve()
    files = sorted(p for p in built.rglob('*') if p.is_file())
    if not files:
        raise SystemExit(f'Nothing to install from {built}')

    backup.mkdir(parents=True, exist_ok=True)
    saved, kept = 0, 0
    for source in files:
        relative = source.relative_to(built)
        target, keep = game / relative, backup / relative
        if not target.exists():
            raise SystemExit(f'{target} does not exist - wrong game folder?')
        if keep.exists():
            kept += 1                      # an earlier run already saved the original
        else:
            keep.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, keep)
            assert digest(keep) == digest(target), str(relative)
            saved += 1

    installed = 0
    for source in files:
        target = game / source.relative_to(built)
        shutil.copy2(source, target)
        assert digest(target) == digest(source), str(source)
        installed += 1

    print(json.dumps({'installed': installed, 'backed_up': saved, 'already_backed_up': kept,
                      'backup': str(backup), 'game': str(game),
                      'restore_with': f'python tools/install.py --game "{game}" --backup "{backup}" --restore'}))


if __name__ == '__main__':
    main()
