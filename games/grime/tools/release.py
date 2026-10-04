"""Build and package GRIME's Polish translation; no install or game launch."""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import patch
from build import RELATIVE, VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--game', str(args.game)], check=True)
    result = patch.release([(args.game / RELATIVE, ROOT / 'dist' / RELATIVE, RELATIVE.as_posix())],
                           ROOT / 'docs/INSTALL-patch.txt', ROOT / 'dist', 'grime', 'GRIME', VERSION)
    with zipfile.ZipFile(result['package']) as archive:
        expected = {f'GRIME-PL-{VERSION}.patch', f'GRIME-PL-{VERSION}.exe', 'READ-ME.txt'}
        if set(archive.namelist()) != expected:
            raise ValueError('Unexpected package contents; game assets must never ship')
    print(f"Verified ZIP: {result['package']} ({result['package_bytes']} bytes)")


if __name__ == '__main__':
    main()
