"""Dread Templar Polish texts from translations/en-pl-review.json.

The game keeps texts as category -> key -> fields (`text`, `name`). The translation file
has one entry per text field: `namespace` = category, `key` = `<key>/<field>`.
Numeric fields (speaker id) are not text to translate; the Polish version keeps them as
in English, so they come from the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, untranslated  # noqa: E402

import game  # noqa: E402


def review_rows(english: dict, polish: dict[tuple[str, str], str]) -> list[dict]:
    """Translation file entries in game order; `polish` as from `translated()`."""
    rows = []
    for category, key, entry in game.entries(english):
        for field, text in entry.items():
            if isinstance(text, str):
                ref = (category, f'{key}/{field}')
                rows.append({'namespace': category, 'key': ref[1], 'english': text, 'polish': polish.get(ref, '')})
    return rows


def translated() -> dict[tuple[str, str], str]:
    return {(e['namespace'], e['key']): e['polish'] for e in load_entries(ROOT) if not untranslated(e)}


def polish_tree(english: dict | None = None) -> dict:
    """Category -> key -> Polish fields, in game order.

    With `english` (the game's `eng` block) the tree also has numeric fields and every
    category, i.e. a full `"pol"` block for the game's JSON. Without it: texts only.
    """
    polish = translated()
    if english is None:
        tree: dict = {}
        for (category, ref), text in polish.items():
            key, field = ref.rsplit('/', 1)
            tree.setdefault(category, {}).setdefault(key, {})[field] = text
        return tree
    tree = {category: {} for category in game.CATEGORIES}
    for category, key, entry in game.entries(english):
        fields = {}
        for field, value in entry.items():
            if not isinstance(value, str):
                fields[field] = value
            elif (category, f'{key}/{field}') in polish:
                fields[field] = polish[(category, f'{key}/{field}')]
        if fields:
            tree[category][key] = fields
    return tree
