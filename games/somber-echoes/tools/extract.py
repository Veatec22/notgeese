"""Extract native localization from the installed GOG game; never launch it."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'bpm' / 'tools'))
from game_pak import GamePak
import locres


def extract(game):
    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    archive = GamePak(game / 'SomberEchoes/Content/Paks/pakchunk0-Windows.pak', bytes(32))
    rows = []
    for path in archive.files:
        if path.startswith('SomberEchoes/Content/Localization/') and '/en/' in path and path.endswith('.locres'):
            destination = work / Path(path).name
            destination.write_bytes(archive.extract(path))
            resource = locres.load(destination)
            for namespace, entry in resource.entries():
                rows.append(dict(key=f'{destination.stem}/{namespace}/{entry.key}', english=entry.text))
    (work / 'english.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Extracted {len(rows)} entries')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, default=Path(r'C:\Games\Somber Echoes'))
    extract(parser.parse_args().game)
