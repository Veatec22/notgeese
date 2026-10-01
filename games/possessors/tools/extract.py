"""Extract every culture of the game's localization tables from the user's pak v11."""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
from game_pak import GamePak  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game', type=Path, default=Path(r'C:\Games\Possessor(s)'))
parser.add_argument('--oodle', type=Path, required=True, help='local oodle-data-shared.dll (never shipped)')
args = parser.parse_args()

archive = GamePak(args.game / 'Pose/Content/Paks/Pose-Windows.pak', args.oodle)
out = ROOT / 'work' / 'loc'
pattern = re.compile(r'Pose/Content/Localization/([^/]+)/([^/]+)/\1\.locres')
count = 0
for path in archive.files:
    match = pattern.fullmatch(path)
    if match:
        table, culture = match.groups()
        target = out / culture / f'{table}.locres'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.extract(path))
        count += 1
(ROOT / 'work' / 'DefaultGame.ini').write_bytes(archive.extract('Pose/Config/DefaultGame.ini'))
print(f'Extracted {count} locres; mount {archive.mount}; {archive.count} pak entries.')
