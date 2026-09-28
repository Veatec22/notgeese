"""Refreshes EN and context in translations/en-pl-review.json from game originals; checks tags.

PL and the key set come from the file itself. New key: add an entry with any `english`
and the script fills in the original from the game.

Keys:
  s<index>                  STRG string (translated everywhere the code uses it)
  s<index>@<CODE entry>     STRG string only in that code entry (e.g. "Controls", which
                            is also a section name in Prefs.ini)
  j:<file>/<path>/<field>   value in dia_*.json (the plugin translates by text, so the same
                            English value elsewhere gets the same translation)

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\review.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from strings_usage import Data, disasm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, write_entries  # noqa: E402
MARKUP = re.compile(r'&[a-z!]{1,2}&|#')


def json_value(game: Path, key: str) -> str:
    path = key[2:].split('/')
    node = json.loads((game / path[0]).read_text(encoding='utf-8'))
    for part in path[1:]:
        node = node[part]
    if not isinstance(node, str):
        raise SystemExit(f'{key}: not a text value')
    return node


def contexts(data: Data, strings) -> dict[int, list[str]]:
    funcs = data.chains('FUNC', 0, 12, 0, 4, 8)
    varis = data.chains('VARI', 3, 20, 0, 12, 16)
    where: dict[int, list[str]] = {}
    for code, start, length in data.code_entries():
        for _, op, arg in disasm(data, start, length, funcs, varis):
            if op == 'push' and arg and arg[0] == 'str':
                names = where.setdefault(arg[1], [])
                short = code.replace('gml_Object_', '').replace('gml_Script_', 'script ')
                if short not in names:
                    names.append(short)
    return where


def check(key: str, en: str, pl: str) -> list[str]:
    problems = []
    if Counter(MARKUP.findall(en)) != Counter(MARKUP.findall(pl)):
        problems.append('tags &..& / # differ')
    if key.startswith('s') and en.count("'") != pl.count("'") and "'&!&" in en:
        problems.append("apostrophe count in key hint")
    # A leading space may be dropped on purpose (" times…" -> ". Spróbuj…" after a number),
    # but a trailing one means the code appends something; that one must stay.
    if (en[-1:] == ' ') != (pl[-1:] == ' '):
        problems.append('trailing space (text gets appended)')
    if any(c in pl for c in '„”–—…'):
        problems.append('character missing from game fonts (use " - ...)')
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    game = ap.parse_args().game
    data = Data(game / 'data.win')
    strings = data.strings()
    where = contexts(data, strings)
    review, errors = [], 0
    for entry in load_entries(ROOT):
        key, polish = entry['key'], entry['polish']
        if key.startswith('s'):
            index = int(key[1:].split('@')[0])
            english = strings[index]
            scope = key.split('@')[1] if '@' in key else None
            ctx = f'tylko {scope}' if scope else ', '.join(where.get(index, [])[:4])
        elif key.startswith('j:'):
            english = json_value(game, key)
            ctx = 'dialog ' + key[2:]
        else:
            raise SystemExit(f'unknown key {key}')
        for problem in check(key, english, polish):
            print(f'{key}: {problem}\n  EN {english!r}\n  PL {polish!r}')
            errors += 1
        review.append({'key': key, 'english': english, 'polish': polish, 'context': ctx})
    # The same JSON value must have one translation (the plugin translates by text).
    seen = {}
    for r in review:
        if r['key'].startswith('j:'):
            if seen.setdefault(r['english'], r['polish']) != r['polish']:
                print(f"{r['key']}: different translation of the same JSON value")
                errors += 1
    write_entries(ROOT, review)
    print(f'{len(review)} entries -> translations/en-pl-review.json; problems: {errors}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
