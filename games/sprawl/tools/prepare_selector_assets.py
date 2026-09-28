"""Extract pinned selector sources; never modify the game or run executables."""
import argparse
import hashlib
from pathlib import Path

from game_pak import GamePak
from selector import SOURCE_HASHES

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game-pak', type=Path, required=True)
parser.add_argument('--oodle', type=Path, required=True)
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'work/assets')
args = parser.parse_args()
archive = GamePak(args.game_pak, args.oodle)
files = {name: archive.extract(name) for name in SOURCE_HASHES}
for name, data in files.items():
    assert hashlib.sha256(data).hexdigest() == SOURCE_HASHES[name], f'Unsupported source: {name}'
for name, data in files.items():
    target = args.output/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
print(f'Extracted and checksum-verified {len(files)} selector source files.')
