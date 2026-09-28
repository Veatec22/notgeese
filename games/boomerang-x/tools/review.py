"""Write translations/en-pl-review.json: the English table beside the Polish.

Reads the original DLL, not a built one - the build overwrites each row's
`description` with Polish, so the developers' notes survive only here. They are
the context a translator wants. Length is not a constraint worth reporting: the
build lends room between rows, and `max_length` (the table's `max_char_limit`) is the authors' own
note about what fits on screen, which the game does not enforce either.

Polish comes from the review file itself, the only translation file.
The table has two rows `difficulty_select_prompt` with different English; the game
finds one Polish text for both, so the review keeps one entry and notes the other.
"""
import argparse
import sys
from pathlib import Path

import table

HERE = Path(__file__).resolve().parent
GAME = HERE.parent
sys.path.insert(0, str(GAME.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402
RELATIVE = Path('BOOMERANG X_Data') / 'Managed' / 'Assembly-CSharp.dll'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True,
                        help='The original Assembly-CSharp.dll, or the game folder holding it')
    args = parser.parse_args()

    source = args.source / RELATIVE if args.source.is_dir() else args.source
    polish = polish_by_key(GAME)

    entries, by_key = [], {}
    for row in table.rows(table.Assembly(source)):
        english = row['columns']['english']['text']
        if row['id'] in by_key:
            by_key[row['id']]['note'] = (f'Tabela gry ma drugi wiersz z tym kluczem: EN {english!r} '
                                         f'({row["description"]}). Oba dostają ten polski tekst.')
            continue
        by_key[row['id']] = {'key': row['id'], 'english': english,
                             'polish': polish.get(row['id'], ''),
                             'context': row['description']}
        if row['max_char_limit'] > 0:  # 0 = no limit
            by_key[row['id']]['max_length'] = row['max_char_limit']
        entries.append(by_key[row['id']])

    write_entries(GAME, entries)
    print({'rows': len(entries), 'translated': sum(1 for e in entries if e['polish'])})


if __name__ == '__main__':
    main()
