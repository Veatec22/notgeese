"""Install or restore the local test build, preserving verified original files."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from build import HASHES, ROOT, REPO


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    game = args.game.resolve()
    backup = REPO / 'backups/not-a-hero'
    report = json.loads((ROOT / 'dist/build-report.json').read_text(encoding='utf-8'))
    files = list(report['build_sha256'])
    originals = {}
    changes = {}
    # Complete preflight before touching any original, backup or target file.
    for relative, expected in HASHES.items():
        current = (game / relative).read_bytes()
        original = (backup / relative).read_bytes() if (backup / relative).exists() else current
        assert digest(original) == expected, f'Invalid original/backup: {relative}'
        originals[relative] = original
        if relative not in files:
            assert digest(current) == expected
            continue
        # Restoring may replace an older build; the verified original goes back.
        assert args.restore or digest(current) in {expected, report['build_sha256'][relative]}, f'Unknown installed file: {relative}'
        adjacent = Path(str(game / relative) + '.przed-spolszczeniem')
        if adjacent.exists():
            assert digest(adjacent.read_bytes()) == expected, f'Invalid backup: {adjacent}'
        built = (ROOT / 'dist/build' / relative).read_bytes()
        assert digest(built) == report['build_sha256'][relative]
        changes[relative] = original if args.restore else built
    for relative, data in originals.items():
        path = backup / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if relative in files:
            path = Path(str(game / relative) + '.przed-spolszczeniem')
            if not path.exists():
                path.write_bytes(data)
    for relative, data in changes.items():
        target = game / relative
        temporary = Path(str(target) + '.notgeese-tmp')
        temporary.write_bytes(data)
        os.replace(temporary, target)
        assert target.read_bytes() == data
    print(('Restored' if args.restore else 'Installed') + f' {len(changes)} files; originals: {backup}')


if __name__ == '__main__':
    main()
