"""Review file and tag check.

    .venv\\Scripts\\python.exe games\\katana-zero\\tools\\review.py

Refreshes translations/en-pl-review.json (key, English, Polish from the file itself, Russian
as context of the slot we take) and checks the translation carries the same tags as the
original: colors and effects in square brackets and line breaks. Asterisks are pauses in
speech; their count is only reported, since Polish word order differs.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402

TAG = re.compile(r'\[[^\]]*\]')


def main() -> int:
    texts = {t['key']: t for t in json.loads((ROOT / 'work' / 'texts.json').read_text(encoding='utf-8'))}
    pl = polish_by_key(ROOT)
    errors, notes = [], []
    rows = []
    for key, t in texts.items():
        if key not in pl:
            continue
        en, tr = t['en'], pl[key]
        if TAG.findall(en) != TAG.findall(tr):
            errors.append(f'{key}: tags {TAG.findall(en)} -> {TAG.findall(tr)}')
        if en.count('\n') != tr.count('\n'):
            errors.append(f'{key}: line breaks {en.count(chr(10))} -> {tr.count(chr(10))}')
        if en.replace('*', '').strip() and TAG.sub('', en).count('*') != TAG.sub('', tr).count('*'):
            notes.append(f'{key}: pauses * {TAG.sub("", en).count("*")} -> {TAG.sub("", tr).count("*")}')
        rows.append({'key': key, 'english': en, 'polish': tr, 'context': t['ru']})
    write_entries(ROOT, rows)
    for n in notes:
        print('note:', n)
    for e in errors:
        print('ERROR:', e)
    print(f'{len(rows)} entries in the review file, {len(errors)} errors, {len(notes)} notes')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
