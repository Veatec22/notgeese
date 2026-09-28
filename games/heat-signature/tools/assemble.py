"""Merge translation batches into translations/en-pl-review.json, the only translation file.

    .venv\\Scripts\\python.exe games\\heat-signature\\tools\\assemble.py work\\batches\\NN-nazwa.json [...]

A batch is an EN -> PL map. Every plain key must be a literal the game really uses
(work/strings.json from extract_strings.py) or a dialogue line (except batches with
"runtime" in the name: values seen only in a running game's log); template keys with
{0}..{9} must keep the same holes in PL, and dialogue <Tokens> must survive.
Existing entries get the new text, new ones go before the item grammar.
"""
import json
import re
import sys
from pathlib import Path

import texts

ROOT = Path(__file__).resolve().parents[1]
HOLE = re.compile(r'\{\d\}')
TOKEN = re.compile(r'<[A-Za-z]+>')


def dialog_lines():
    lines = {}
    for row in json.loads((ROOT / 'work/dialog-review.json').read_text(encoding='utf-8')):
        text = re.sub(r'\s*\{[^}]*\}\s*$', '', row['english'].strip()).lstrip('#= ').strip()
        if text:
            lines.setdefault(text, []).append(row['key'].replace('Dialog/', ''))
    return lines


def context_of(en, literals, dialog):
    if en in dialog:
        return 'Dialog: ' + ', '.join(dialog[en][:3])
    if en in literals:
        return 'EXE: ' + ', '.join(sorted(f.replace('gml_Script_', '').replace('gml_Object_', '')
                                          for f in literals[en])[:3])
    return 'Szablon: składany przez grę z fragmentów i wartości {n}'


def main():
    parts = [Path(p) for p in sys.argv[1:]]
    if not parts:
        raise SystemExit(__doc__)
    strings = json.loads((ROOT / 'work/strings.json').read_text(encoding='utf-8'))
    literals = {}
    for s in strings:
        literals.setdefault(s['text'], set()).update(s['functions'])
    dialog = dialog_lines()
    batch, errors = {}, []
    for part in parts:
        for en, value in json.loads(part.read_text(encoding='utf-8')).items():
            if HOLE.search(en):
                if sorted(HOLE.findall(en)) != sorted(HOLE.findall(value)):
                    errors.append(f'{part.name}: holes differ: {en!r}')
            elif en not in literals and en not in dialog and 'runtime' not in part.name:
                errors.append(f'{part.name}: not a game literal or dialogue line: {en!r}')
            if sorted(TOKEN.findall(en)) != sorted(TOKEN.findall(value)):
                errors.append(f'{part.name}: <Token> mismatch: {en!r}')
            if not value.strip() and en.strip():
                errors.append(f'{part.name}: empty translation: {en!r}')
            batch[en] = value
    items = texts.items()
    for group in ('nouns', 'modifiers', 'tails'):
        for en in items[group]:
            if en not in literals and not any(en in s for s in literals if len(s) < 80):
                errors.append(f'item-{group[:-1]}: unknown word {en!r}')
    if errors:
        print('\n'.join(errors))
        sys.exit(1)
    changed, added = texts.merge(batch, {en: context_of(en, literals, dialog) for en in batch})
    print(f'en-pl-review.json: {changed} changed, {added} added')


if __name__ == '__main__':
    main()
