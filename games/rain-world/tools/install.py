"""Author test: copy the built mod into the game or remove it.

The mod is a new folder in StreamingAssets/mods; no game file is overwritten, so removing the
folder (--remove) replaces a backup. Enabling the mod in REMIX and picking the language stay
with the player, as in the readme.

    .venv\\Scripts\\python.exe games\\rain-world\\tools\\install.py [--game ...] [--remove]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rw  # noqa: E402
from build import MOD_ID, ROOT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, default=rw.DEFAULT_GAME)
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()

    target = rw.streaming(args.game) / 'mods' / MOD_ID
    if target.exists():
        shutil.rmtree(target)
    if args.remove:
        print(f'Removed {target}')
        return 0
    source = ROOT / 'dist' / MOD_ID
    if not source.exists():
        raise SystemExit('Missing dist/notgeese-polski; run tools/build.py first.')
    shutil.copytree(source, target)
    print(f'Zainstalowano {target}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
