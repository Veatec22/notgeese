"""Heat Signature Polish texts from translations/en-pl-review.json.

Two kinds of entries in one file:

- game text: `key` = English literal (EXE, dialogue or a template with {0}), `polish`;
- grammar of item names the game builds from [modifiers] and a noun. In Polish the noun
  goes first, adjectives after it agreeing in gender (m/f/n), and "tail" modifiers
  at the end:
  `item-noun:<EN>` — rzeczownik, pole `gender` = m / f / n;
  `item-modifier:<EN>`: three adjective forms "m / ż / n";
  `item-tail:<EN>`: indeclinable trailing modifier.

New translation batches are merged by `assemble.py` via `merge`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, untranslated, write_entries  # noqa: E402

ITEM = 'item-'
GENDERS = {'m', 'f', 'n'}


def plain() -> dict[str, str]:
    """EN -> PL of game texts in file order, without untranslated entries and item grammar."""
    result = {}
    for e in load_entries(ROOT):
        if e['key'].startswith(ITEM) or untranslated(e):
            continue
        if e['key'] != e['english']:
            raise SystemExit(f'{e["key"]!r}: a game text key must be its English wording.')
        result[e['key']] = e['polish']
    return result


def items() -> dict:
    """Item grammar: nouns {EN: [noun, gender]}, modifiers {EN: [m, ż, n]}, tails {EN: text}."""
    out = {'nouns': {}, 'modifiers': {}, 'tails': {}}
    for e in load_entries(ROOT):
        kind, _, english = e['key'].partition(':')
        if kind == 'item-noun':
            if e.get('gender') not in GENDERS:
                raise SystemExit(f'{e["key"]}: field "gender" must be one of {sorted(GENDERS)}.')
            out['nouns'][english] = [e['polish'], e['gender']]
        elif kind == 'item-modifier':
            forms = e['polish'].split(' / ')
            if len(forms) != 3 or not all(f.strip() == f and f for f in forms):
                raise SystemExit(f'{e["key"]}: PL must have three forms "m / ż / n", got {e["polish"]!r}.')
            out['modifiers'][english] = forms
        elif kind == 'item-tail':
            out['tails'][english] = e['polish']
        elif e['key'].startswith(ITEM):
            raise SystemExit(f'{e["key"]}: unknown item entry kind.')
    return out


def merge(batch: dict[str, str], context: dict[str, str], overwrite: bool = True) -> tuple[int, int]:
    """Add game texts EN -> PL: new ones before the item grammar, existing ones changed
    (or kept when `overwrite=False`). Returns (changed, added)."""
    entries = load_entries(ROOT)
    index = {e['key']: e for e in entries}
    changed = added = 0
    fresh = []
    for en, pl in batch.items():
        if en.startswith(ITEM):
            raise SystemExit(f'{en!r}: item grammar is edited in item-* entries.')
        if en in index:
            if overwrite and index[en]['polish'] != pl:
                index[en]['polish'] = pl
                changed += 1
        else:
            fresh.append({'key': en, 'english': en, 'polish': pl, 'context': context.get(en, '')})
            added += 1
    first_item = next((i for i, e in enumerate(entries) if e['key'].startswith(ITEM)), len(entries))
    entries[first_item:first_item] = fresh
    if changed or added:
        write_entries(ROOT, entries)
    return changed, added
