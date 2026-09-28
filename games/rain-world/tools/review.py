"""Refresh translations/en-pl-review.json: EN and context from game texts (work/en.json), PL from the file.

    .venv\\Scripts\\python.exe games\\rain-world\\tools\\review.py

New entries come from `batch.py merge`. `context` is Polish (shown in the workspace).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, write_entries  # noqa: E402


def row_for(key: str, text: str, english: dict) -> dict:
    """Entry: EN from the game (or from the key for our own entries), PL and context (where the text comes from)."""
    source = english.get(key, {})
    row = {'key': key, 'english': source.get('english', key.split(':', 1)[1]), 'polish': text}
    notes = []
    if source.get('context'):
        notes.append('w kodzie: ' + ', '.join(source['context'].split(', ')[:3]))
    if source.get('source') and source['source'] != 'base':
        notes.append('dodatek: ' + source['source'])
    if key not in english:
        notes.append('wpis dodany przez spolszczenie')
    if notes:
        row['context'] = '; '.join(notes)
    return row


def main() -> int:
    english = json.loads((ROOT / 'work/en.json').read_text(encoding='utf-8'))
    rows = [row_for(e['key'], e['polish'], english) for e in load_entries(ROOT)]
    write_entries(ROOT, rows)
    print(f'{len(rows)} entries')
    return 0


if __name__ == '__main__':
    sys.exit(main())
