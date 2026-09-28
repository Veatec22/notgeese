r"""Dump translatable INI lines to work/source.json (publisher text, not in git).

Usage: .venv\Scripts\python.exe games/not-a-hero/tools/extract.py --game "C:\Games\Not A Hero"
With the sample installed, pass --game backups\not-a-hero.
"""
import argparse
import json
from pathlib import Path

from ini import FILES, entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    result = {}
    for relative in FILES:
        for _, term, value in entries((args.game / relative).read_bytes(), relative):
            result[term] = value
    out = ROOT / 'work/source.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    counts = {}
    for term in result:
        counts[term.split('|')[0]] = counts.get(term.split('|')[0], 0) + 1
    print(len(result), counts)


if __name__ == '__main__':
    main()
