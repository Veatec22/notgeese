"""Extract the game's LocalizationSet tables from resources.assets.

Writes work/ref-<code>.json for all 11 languages and adds missing English entries to
translations/en-pl-review.json (existing Polish is never touched). Reads only.

    .venv\\Scripts\\python.exe games\\lovers-in-a-dangerous-spacetime\\tools\\extract.py --game "C:\\Games\\Lovers in a Dangerous Spacetime"
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries, review_path, write_entries  # noqa: E402

DATA = 'LoversInADangerousSpacetime_Data'
PREFIX = 'Localization-'


def read_string(raw: bytes, pos: int) -> tuple[str, int]:
    length = struct.unpack_from('<i', raw, pos)[0]
    pos += 4
    text = raw[pos:pos + length].decode('utf-8')
    return text, (pos + length + 3) & ~3


def read_set(raw: bytes) -> dict | None:
    """LocalizationSet without a typetree: MonoBehaviour header (28 bytes), m_Name,
    Language {name, code, systemLanguage}, StringKeyValuePair[] {key, value}."""
    name, pos = read_string(raw, 28)
    if not name.startswith(PREFIX):
        return None
    language, pos = read_string(raw, pos)
    code, pos = read_string(raw, pos)
    system_language, count = struct.unpack_from('<ii', raw, pos)
    pos += 8
    pairs = []
    for _ in range(count):
        key, pos = read_string(raw, pos)
        value, pos = read_string(raw, pos)
        pairs.append((key, value))
    assert pos == len(raw), f'{name}: {len(raw) - pos} bytes left over'
    return {'name': language, 'code': code, 'system_language': system_language, 'pairs': pairs}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()

    env = UnityPy.load(str(args.game / DATA / 'resources.assets'))
    sets = {}
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        table = read_set(obj.get_raw_data())
        if table:
            sets[table['code']] = table
    assert 'en-us' in sets, 'English table not found; is this the game dir?'

    work = ROOT / 'work'
    work.mkdir(exist_ok=True)
    for code, table in sets.items():
        (work / f'ref-{code}.json').write_text(
            json.dumps(dict(table['pairs']), ensure_ascii=False, indent=1), encoding='utf-8')

    path = review_path(ROOT)
    entries = load_entries(ROOT) if path.exists() else []
    known = {entry['key']: entry for entry in entries}
    added = changed = 0
    for key, english in sets['en-us']['pairs']:
        if key not in known:
            entries.append({'key': key, 'english': english, 'polish': ''})
            added += 1
        elif known[key]['english'] != english:
            print(f'English changed: {key}')
            changed += 1
    path.parent.mkdir(exist_ok=True)
    write_entries(ROOT, entries)

    counts = {code: len(table['pairs']) for code, table in sorted(sets.items())}
    print(f'Languages: {counts}')
    print(f'Review file: {len(entries)} entries, {added} added, {changed} with changed English.')


if __name__ == '__main__':
    main()
