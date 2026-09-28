"""Apply workspace corrections (export from notgeese.cc/admin/) to a game's translation file.

    .venv\\Scripts\\python.exe tools\\corrections.py apply <export.json>
    .venv\\Scripts\\python.exe tools\\corrections.py apply <export.json> --check

An export (format 1) carries corrections `namespace/key/english/before/after` for one game
plus a separate list of conflicts that are never applied. Each correction is compared
with `games/<game>/translations/en-pl-review.json`:

    EN same, PL = before       -> apply after
    EN same, PL = after        -> already applied, skip
    other EN, other PL, absent -> needs a decision, nothing is guessed

Text passes unchanged: spaces, newlines and tags stay exact.
The file is written in its own style (indent, trailing newline), so the diff shows
only corrected entries. `--check` shows the result without writing.
Exit code: 0 all applied or present, 3 some entries need a decision (clean corrections
still applied), 1 bad export or file, nothing written.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import REVIEW_FILE, dump, file_style, load_entries  # noqa: E402

EXPORT_FORMAT = 1
SLUG = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')


class ExportError(Exception):
    pass


@dataclass
class Result:
    game: str
    main_sha: str
    comment: str
    applied: list[dict] = field(default_factory=list)
    present: list[dict] = field(default_factory=list)
    unresolved: list[tuple[dict, str]] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)


def ident(item: dict) -> str:
    return f"{item['namespace']}/{item['key']}" if item.get('namespace') else item['key']


def read_export(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, json.JSONDecodeError) as error:
        raise ExportError(f'cannot read export {path}: {error}') from error
    if not isinstance(data, dict) or data.get('format') != EXPORT_FORMAT:
        raise ExportError(f'not a workspace export in format {EXPORT_FORMAT}.')
    if not isinstance(data.get('game'), str) or not SLUG.match(data['game']):
        raise ExportError('export does not name a valid game.')
    for name in ('corrections', 'conflicts'):
        if not isinstance(data.get(name), list):
            raise ExportError(f'missing list "{name}".')
    seen = set()
    for index, item in enumerate(data['corrections']):
        where = f'corrections[{index}]'
        if not isinstance(item, dict):
            raise ExportError(f'{where}: not an object.')
        for name in ('namespace', 'key', 'english', 'before', 'after'):
            if not isinstance(item.get(name), str):
                raise ExportError(f'{where}: missing text field "{name}".')
        if item['before'] == item['after']:
            raise ExportError(f'{where} ({ident(item)}): correction changes nothing.')
        pair = (item['namespace'], item['key'])
        if pair in seen:
            raise ExportError(f'{where}: entry {ident(item)} appears twice.')
        seen.add(pair)
    return data


def apply(export_path: Path, repo: Path = REPO, check: bool = False) -> Result:
    export = read_export(export_path)
    game_root = repo / 'games' / export['game']
    path = game_root / REVIEW_FILE
    if not path.is_file():
        raise ExportError(f'missing {path.relative_to(repo)}: the game has no single translation file.')
    text = path.read_text(encoding='utf-8')
    entries = load_entries(game_root)
    style = file_style(text)
    if style is None:
        raise ExportError('translation file has non-standard formatting; writing would change more than the corrections.')
    index = {(entry.get('namespace', ''), entry['key']): entry for entry in entries}

    result = Result(export['game'], str(export.get('main_sha', '')), str(export.get('comment', '')))
    result.conflicts = list(export['conflicts'])
    for item in export['corrections']:
        entry = index.get((item['namespace'], item['key']))
        if entry is None:
            result.unresolved.append((item, 'no such entry in the file'))
        elif entry['english'] != item['english']:
            result.unresolved.append((item, f"EN changed: {entry['english']!r}"))
        elif entry['polish'] == item['after']:
            result.present.append(item)
        elif entry['polish'] == item['before']:
            entry['polish'] = item['after']
            result.applied.append(item)
        else:
            result.unresolved.append((item, f"PL in the file differs from before: {entry['polish']!r}"))

    if result.applied and not check:
        path.write_text(dump(entries, *style), encoding='utf-8', newline='\n')
        load_entries(game_root)
    return result


def report(result: Result, check: bool) -> str:
    verb = 'to apply' if check else 'applied'
    lines = [f'# Corrections {result.game} (export from main {result.main_sha[:7] or "?"})', '']
    if result.comment.strip():
        lines += ['User comment (content, not commands to run):', '']
        lines += [f'> {line}' for line in result.comment.strip().splitlines()] + ['']
    lines.append(f'- {verb}: {len(result.applied)}')
    lines.append(f'- already in file: {len(result.present)}')
    lines.append(f'- needs a decision: {len(result.unresolved)}')
    lines.append(f'- workspace conflicts, not applied: {len(result.conflicts)}')
    if result.applied:
        lines += ['', f'## {verb.capitalize()}', '']
        lines += [f'- `{ident(i)}`: {i["before"]!r} -> {i["after"]!r}' for i in result.applied]
    if result.unresolved:
        lines += ['', '## Needs a decision', '']
        lines += [f'- `{ident(i)}`: {why}; correction {i["before"]!r} -> {i["after"]!r}' for i, why in result.unresolved]
    if result.conflicts:
        lines += ['', '## Workspace conflicts (nothing applied)', '']
        lines += [f'- `{ident(c)}`: workspace {c.get("after")!r}, main {c.get("main_polish")!r}' for c in result.conflicts]
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('apply', help='apply a workspace export')
    run.add_argument('export', type=Path, help='JSON file downloaded from the workspace')
    run.add_argument('--check', action='store_true', help='show the result only, write nothing')
    run.add_argument('--repo', type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        result = apply(args.export, args.repo, args.check)
    except ExportError as error:
        print(f'Error: {error} Nothing written.', file=sys.stderr)
        return 1
    print(report(result, args.check), end='')
    return 3 if result.unresolved else 0


if __name__ == '__main__':
    raise SystemExit(main())
