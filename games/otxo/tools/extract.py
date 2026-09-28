"""Dump the English source text and refresh the review file.

Reads the game's own script_english.ini and refreshes translations/en-pl-review.json,
the only translation file: one row per key, English beside the Polish
already in the file (empty = not translated yet), in the file's own order. Keys with
empty English have nothing to translate and are left out.

Never writes into the game directory.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script_ini

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, review_path, write_entries  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True, help='The OTXO folder, never written to')
    args = parser.parse_args()

    english = script_ini.load(args.game / 'script_english.ini')
    polish = polish_by_key(ROOT) if review_path(ROOT).exists() else {}

    rows = [{'key': key, 'english': text, 'polish': polish.get(key, '')}
            for key, text in english.items() if text or key in polish]
    write_entries(ROOT, rows)
    out = review_path(ROOT)
    print(json.dumps({'entries': len(rows), 'translated': len(polish),
                      'english_characters': sum(len(r['english']) for r in rows),
                      'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
