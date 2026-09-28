"""Extract the English localization from the user's unencrypted pak v12."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pak', type=Path, required=True)
parser.add_argument('--oodle', type=Path, required=True)
args = parser.parse_args()
# The inspected v12 index has the same layout as the existing v11 reader.
# Keep the change local to this game rather than widening support for other games.
reader = ROOT.parent / 'sprawl/tools/game_pak.py'
namespace = {}
exec(compile(reader.read_text(encoding='utf-8').replace('version==11', 'version==12'), str(reader), 'exec'), namespace)
archive = namespace['GamePak'](args.pak, args.oodle)
data = archive.extract('PVD/Content/Localization/Game/en/Game.locres')
(ROOT / 'work').mkdir(exist_ok=True)
(ROOT / 'work/en.locres').write_bytes(data)
print(f'Extracted {len(data)} bytes; mount {archive.mount}; {archive.count} pak entries.')
