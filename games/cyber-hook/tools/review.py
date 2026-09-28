"""Refresh translations/en-pl-review.json: EN from the game, PL from the current file.

Order as in the game CSV. Untranslated entries have an empty `polish` so the scope is visible.
The CSV DETAILS column (usually the developers' French equivalent) goes to `context`.

    .venv\Scripts\python.exe games\cyber-hook\tools\review.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402


def main():
    source = json.loads((ROOT / 'work/source/en.json').read_text(encoding='utf-8'))
    terms = polish_by_key(ROOT)
    raw_path = ROOT / 'translations/raw-keys.json'
    raw = json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else {}
    rows = []
    for row in source:
        entry = {'key': row['key'], 'english': row['text'], 'polish': terms.get(row['key'], '')}
        if row['details']:
            entry['context'] = row['details']
        rows.append(entry)
    # Lines where the game passes plain English text instead of a key.
    for key, english in raw.items():
        rows.append({'key': key, 'english': english, 'polish': terms.get(key, ''),
                     'context': 'klucz = tekst angielski (dialog bez wpisu w CSV)'})
    write_entries(ROOT, rows)
    done = sum(1 for r in rows if r['polish'])
    print(json.dumps({'rows': len(rows), 'translated': done}))


if __name__ == '__main__':
    main()
