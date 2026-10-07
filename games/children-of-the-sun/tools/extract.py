"""Extract the string table LOL (English + other languages for context) from the Addressables bundles.

Writes work/source/en.json ({key, id, text, other: {locale: text}}) and refreshes
translations/en-pl-review.json: English and context from the game, existing Polish kept.

    .venv\\Scripts\\python.exe games\\children-of-the-sun\\tools\\extract.py --game "C:\\SteamLibrary\\steamapps\\common\\ChildrenOfTheSun"
"""
import argparse
import json
import sys
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries, write_entries  # noqa: E402

BUNDLES = 'ChildrenOfTheSun_Data/StreamingAssets/aa/StandaloneWindows64'
CONTEXT_LOCALES = ['de', 'ru']


def table(path: Path) -> dict:
    for obj in UnityPy.load(str(path)).objects:
        if obj.type.name == 'MonoBehaviour':
            tree = obj.read_typetree()
            if 'm_TableData' in tree:
                return {row['m_Id']: row['m_Localized'] for row in tree['m_TableData']}
            if 'm_Entries' in tree:
                return {row['m_Id']: row['m_Key'] for row in tree['m_Entries']}
    raise SystemExit(f'No table in {path}')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    bundles = args.game / BUNDLES

    keys = table(bundles / 'localization-assets-shared_assets_all.bundle')
    english = table(next(bundles.glob('localization-string-tables-english(en)_assets_all.bundle')))
    others = {code: table(next(bundles.glob(f'localization-string-tables-*({code})_assets_all.bundle')))
              for code in CONTEXT_LOCALES}

    rows = []
    for entry_id, key in keys.items():
        text = english.get(entry_id)
        if text is None:
            continue
        rows.append({'key': key, 'id': entry_id, 'text': text,
                     'other': {code: others[code].get(entry_id, '') for code in CONTEXT_LOCALES}})
    assert len({r['key'] for r in rows}) == len(rows), 'duplicate keys'
    out = ROOT / 'work' / 'source'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'en.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')

    review = ROOT / 'translations' / 'en-pl-review.json'
    old = {e['key']: e for e in load_entries(ROOT)} if review.exists() else {}
    entries = []
    for row in rows:
        previous = old.get(row['key'], {})
        entry = {'key': row['key'], 'english': row['text'], 'polish': previous.get('polish', '')}
        for field in ('context', 'note', 'max_length'):
            if previous.get(field):
                entry[field] = previous[field]
        entries.append(entry)
    review.parent.mkdir(parents=True, exist_ok=True)
    write_entries(ROOT, entries)
    print(json.dumps({'entries': len(rows), 'chars': sum(len(r['text']) for r in rows),
                      'polish_kept': sum(1 for e in entries if e['polish'])}))


if __name__ == '__main__':
    main()
