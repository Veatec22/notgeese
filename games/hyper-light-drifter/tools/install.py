r"""Installs built files for testing or restores the originals; for the author only.

Usage:
  .venv\Scripts\python.exe games\hyper-light-drifter\tools\install.py --game "C:\Games\Hyper Light Drifter"
  .venv\Scripts\python.exe games\hyper-light-drifter\tools\install.py --game "C:\Games\Hyper Light Drifter" --restore

Originals (checksum-verified) go to backups/hyper-light-drifter/ before the first replacement;
an existing copy is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from hld import HASHES, REPO, ROOT


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    backup = REPO / 'backups/hyper-light-drifter'
    report = json.loads((ROOT / 'dist/build-report.json').read_text(encoding='utf-8'))
    built_hashes = report['build_sha256']

    # Full check first, only then write anything.
    plan = {}
    for file, expected in HASHES.items():
        target = args.game / file
        current = digest(target.read_bytes())
        saved = backup / file
        if saved.exists():
            assert digest(saved.read_bytes()) == expected, f'bad copy: {saved}'
        else:
            assert current == expected, f'{file}: unknown version and no copy'
        # Restoring may replace an older build; the verified original comes back.
        assert args.restore or current in {expected, built_hashes[file]}, f'{file}: unknown file in the game'
        # When restoring without a copy the game file is the original (checked above)
        # and it goes into the copy below.
        source = saved if args.restore else ROOT / 'dist/build' / file
        if not args.restore:
            assert digest(source.read_bytes()) == built_hashes[file], f'{file}: the build changed'
        plan[file] = source

    backup.mkdir(parents=True, exist_ok=True)
    for file in plan:
        saved = backup / file
        if not saved.exists():
            saved.write_bytes((args.game / file).read_bytes())
    for file, source in plan.items():
        target = args.game / file
        temporary = target.with_name(target.name + '.notgeese-tmp')
        temporary.write_bytes(source.read_bytes())
        os.replace(temporary, target)
        want = HASHES[file] if args.restore else built_hashes[file]
        assert digest(target.read_bytes()) == want, file
    print(('Restored' if args.restore else 'Installed') + f' {len(plan)} files; copies: {backup}')


if __name__ == '__main__':
    main()
