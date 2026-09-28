"""The one translation file per game: translations/en-pl-review.json.

Builds read Polish text from here, never from their own copies. The file is a list of
`{key, namespace?, english, polish, context?, note?, max_length?}`; an entry is identified
by (namespace, key). Text is never trimmed or normalized.

    from translations import polish_by_key
    terms = polish_by_key(ROOT)          # {key: Polish text}, file order

A game with non-empty namespaces builds its own ids from `load_entries(ROOT)`.
Tools that change texts (translation batches, corrections) write through
`write_entries` or `update_polish`, in the existing file style, so the diff shows
only changed entries.
"""

from __future__ import annotations

import json
from pathlib import Path

REVIEW_FILE = Path('translations') / 'en-pl-review.json'
STYLES = [(2, True), (1, True), (4, True), (2, False), (1, False), (4, False)]


def review_path(game_root: Path) -> Path:
    return Path(game_root) / REVIEW_FILE


def load_entries(game_root: Path) -> list[dict]:
    """Entries in file order; stops on a shape error, never guesses."""
    path = review_path(game_root)
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise SystemExit(f'{path}: the file must be a list of entries.')
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(data):
        where = f'{path}: entry {index}'
        if not isinstance(entry, dict):
            raise SystemExit(f'{where}: not an object.')
        for field in ('key', 'english', 'polish'):
            if not isinstance(entry.get(field), str):
                raise SystemExit(f'{where}: missing text field "{field}".')
        namespace = entry.get('namespace', '')
        if not isinstance(namespace, str):
            raise SystemExit(f'{where}: "namespace" must be text.')
        ident = (namespace, entry['key'])
        if ident in seen:
            raise SystemExit(f'{where}: duplicate entry {namespace + "/" if namespace else ""}{entry["key"]}.')
        seen.add(ident)
    return data


def untranslated(entry: dict) -> bool:
    """Empty PL with non-empty EN: not translated yet, the game keeps the original."""
    return entry['polish'] == '' and entry['english'].strip() != ''


def polish_by_key(game_root: Path, keep_empty: bool = False) -> dict[str, str]:
    """key -> PL for games without namespaces, untranslated entries skipped.

    `keep_empty=True` for games where an empty PL is deliberate (e.g. a dropped suffix).
    """
    entries = load_entries(game_root)
    spaced = [e['key'] for e in entries if e.get('namespace')]
    if spaced:
        raise SystemExit(f'{review_path(game_root)}: entries with namespace ({spaced[0]}...); use load_entries.')
    return {e['key']: e['polish'] for e in entries if keep_empty or not untranslated(e)}


def polish_by_ref(game_root: Path) -> dict[tuple[str, str], str]:
    """(namespace, key) -> PL, untranslated entries skipped; for games with namespaces."""
    return {(e.get('namespace', ''), e['key']): e['polish'] for e in load_entries(game_root) if not untranslated(e)}


def polish_by_field(game_root: Path, field: str) -> dict:
    """entry field value -> PL, when the game identifies texts by something other than `key`
    (e.g. `id` = Unity object path ID). Untranslated entries skipped."""
    entries = load_entries(game_root)
    result = {e[field]: e['polish'] for e in entries if not untranslated(e)}
    if len(result) != sum(1 for e in entries if not untranslated(e)):
        raise SystemExit(f'{review_path(game_root)}: field "{field}" is not unique.')
    return result


def dump(entries: list[dict], indent: int = 2, newline: bool = True) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=indent) + ('\n' if newline else '')


def file_style(text: str) -> tuple[int, bool] | None:
    """Indent and trailing newline that reproduce the file byte for byte; None if none do."""
    data = json.loads(text)
    for indent, newline in STYLES:
        if dump(data, indent, newline) == text:
            return indent, newline
    return None


def write_entries(game_root: Path, entries: list[dict]) -> None:
    """Write in the current file style (new file: indent 2, trailing newline)."""
    path = review_path(game_root)
    style = file_style(path.read_text(encoding='utf-8')) if path.exists() else None
    path.write_text(dump(entries, *(style or (2, True))), encoding='utf-8', newline='\n')
    load_entries(game_root)


def update_polish(game_root: Path, polish: dict[str, str]) -> int:
    """Set PL of existing entries without namespace; an unknown key is an error. Returns the change count."""
    entries = load_entries(game_root)
    index = {e['key']: e for e in entries if not e.get('namespace')}
    unknown = [key for key in polish if key not in index]
    if unknown:
        raise SystemExit(f'{review_path(game_root)}: no entries {unknown[:5]}; a new entry needs EN from the game.')
    changed = 0
    for key, text in polish.items():
        if index[key]['polish'] != text:
            index[key]['polish'] = text
            changed += 1
    if changed:
        write_entries(game_root, entries)
    return changed
