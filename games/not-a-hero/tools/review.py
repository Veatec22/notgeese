r"""Refresh English in translations/en-pl-review.json from the game; Polish stays.

Usage: .venv\Scripts\python.exe games/not-a-hero/tools/review.py --game "C:\Games\Not A Hero"
With the sample installed, pass --game backups\not-a-hero. Image and menu entries
keep the English description already stored in the review file.
"""
import argparse
import sys
from pathlib import Path

from ini import FILES, entries

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, polish_by_key, write_entries  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    pl = polish_by_key(ROOT)
    old = {r['key']: r for r in load_entries(ROOT)}
    rows = []
    for relative in FILES:
        for _, term, english in entries((args.game / relative).read_bytes(), relative):
            if term in pl:
                row = {'key': term, 'english': english, 'polish': pl[term]}
                if old.get(term, {}).get('context'):
                    row['context'] = old[term]['context']
                rows.append(row)
    rows += [dict(old[k], polish=pl[k]) for k in pl if k.startswith(('menu|', 'image|', 'card|', 'exe|'))]
    assert {r['key'] for r in rows} == set(pl), set(pl) ^ {r['key'] for r in rows}
    write_entries(ROOT, rows)
    print(len(rows), 'rows')


if __name__ == '__main__':
    main()
