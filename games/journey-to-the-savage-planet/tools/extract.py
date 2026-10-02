"""Extract the game's texts and reference files; create or check the translation file.

    extract.py <game folder>

- work/extract/Towers/Content/Localization/**: every culture's Game.locres and Untold.locres
  (English is the source, the rest are references for gender and terms).
- work/ref-<culture>.json: the same tables as JSON for reading.
- translations/en-pl-review.json: created from the English locres if missing (Polish empty,
  context = asset(s) that define a GUID key, from work/key-sources.json when present);
  if present, only checked: every English text must match the game's.

Reads the pak, writes only to work/ and (once) translations/.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import locres
from game_pak import GamePak

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, review_path  # noqa: E402

PAK = 'Towers/Content/Paks/Towers-WindowsNoEditor.pak'
WORK = ROOT / 'work'
LOCALIZATION = 'Towers/Content/Localization/'
ENGLISH = WORK / 'extract' / LOCALIZATION / 'Game/en/Game.locres'
# en/Game.locres in the GOG build (exe b0ee2d93…); the build pins the same hash.
ENGLISH_SHA256 = '71b0a06c8a34ded2f7444c1c1d93c725ac20ac9980904ff2511bc4839e5c61f0'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('game', type=Path, help='Game folder (the one holding Towers.exe)')
    args = parser.parse_args()

    pak = GamePak(args.game / PAK)
    for name in pak.entries:
        if name.startswith(LOCALIZATION):
            target = WORK / 'extract' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(pak.extract(name))
    digest = hashlib.sha256(ENGLISH.read_bytes()).hexdigest()
    if digest != ENGLISH_SHA256:
        print(f'warning: English locres {digest} differs from the pinned {ENGLISH_SHA256}; '
              'the game changed, re-inspect before building.')

    for culture_dir in sorted((WORK / 'extract' / LOCALIZATION / 'Game').iterdir()):
        if culture_dir.is_dir():
            table = locres.load(culture_dir / 'Game.locres').texts()
            rows = [{'namespace': n, 'key': k, 'text': v} for (n, k), v in table.items()]
            (WORK / f'ref-{culture_dir.name}.json').write_text(
                json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')

    english = locres.load(ENGLISH)
    path = review_path(ROOT)
    if path.exists():
        entries = load_entries(ROOT)
        texts = english.texts()
        changed = [e['key'] for e in entries if texts.get((e.get('namespace', ''), e['key'])) != e['english']]
        missing = len(texts) - len(entries)
        print(json.dumps({'entries': len(entries), 'english_changed': len(changed), 'missing': missing,
                          'first_changed': changed[:5]}))
        return

    sources_file = WORK / 'key-sources.json'
    sources = json.loads(sources_file.read_text(encoding='utf-8')) if sources_file.exists() else {}
    entries = []
    for namespace, entry in english.entries():
        row = {'key': entry.key, 'namespace': namespace, 'english': entry.text, 'polish': ''}
        where = sources.get(f'{namespace}|{entry.key}')
        if where:
            row['context'] = ', '.join(p.removeprefix('Towers/Content/') for p in where)
        entries.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{path.relative_to(ROOT)}: {len(entries)} entries created')


if __name__ == '__main__':
    main()
