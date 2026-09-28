"""Dump the English source text and refresh the review file.

Reads an original resources.assets and refreshes translations/en-pl-review.json,
the only translation file: one entry per text field, English beside
the Polish already in the file (empty = not translated yet), in the game's order.
Never writes into the game directory.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game
import texts

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import review_path, write_entries  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True, help='Original "DreadTemplar_Data" folder, never written to')
    args = parser.parse_args()

    data = game.load(args.game / 'resources.assets')
    english = data['eng']
    assert data['pol'] == {}, 'This build already carries Polish text.'

    polish = texts.translated() if review_path(ROOT).exists() else {}
    review = texts.review_rows(english, polish)
    missing = sum(1 for row in review if not row['polish'])
    write_entries(ROOT, review)
    out = review_path(ROOT)

    characters = sum(len(str(v)) for _, _, e in game.entries(english) for v in e.values())
    print(json.dumps({'entries': len(review), 'translated': len(review) - missing,
                      'missing': missing, 'english_characters': characters,
                      'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
