"""Read and rewrite OTXO's language files.

Each language is one UTF-8, CRLF file of `<number>="<text>"` lines under a single
section header - `[english]` in script_english.ini, `[french]` in
OTXO_script_english_fre-FR.ini, and so on. The files are hand-maintained and
show it: some lines carry stray characters after the closing quote, some keys
have no value at all, and the French file repeats four keys outright.

So nothing here rewrites a file from scratch. A translation is produced by taking
the English file as a template and replacing only the quoted part of the lines
being translated, which leaves every blank line, every oddity and every byte of
the rest exactly as the game already parses it.
"""
import re
from pathlib import Path

LINE = re.compile(rb'^(\d+)=')
SECTION = re.compile(rb'^\[(.+)\]$')


def split(line):
    """(before, value, after) for a `N="text"` line, or None when there is no quoted value."""
    first, last = line.find(b'"'), line.rfind(b'"')
    if first < 0 or last <= first:
        return None
    return line[:first + 1], line[first + 1:last], line[last:]


def load(path):
    """{key: text} for every line that carries a quoted value."""
    out = {}
    for line in Path(path).read_bytes().split(b'\r\n'):
        match = LINE.match(line)
        if not match:
            continue
        parts = split(line)
        if parts is None:
            continue
        out[match.group(1).decode()] = parts[1].decode('utf-8')
    return out


def section(path):
    for line in Path(path).read_bytes().split(b'\r\n'):
        found = SECTION.match(line)
        if found:
            return found.group(1).decode()
    raise AssertionError(f'{path} has no section header')


def rewrite(source, target_section, translations):
    """The English file with a new section header and the translated values spliced in."""
    lines = Path(source).read_bytes().split(b'\r\n')
    used = set()
    for position, line in enumerate(lines):
        found = SECTION.match(line)
        if found:
            lines[position] = b'[' + target_section.encode() + b']'
            continue
        match = LINE.match(line)
        if not match:
            continue
        key = match.group(1).decode()
        if key not in translations:
            continue
        parts = split(line)
        assert parts is not None, f'key {key} has no quoted value to replace'
        text = translations[key].encode('utf-8')
        assert b'"' not in text, f'key {key}: a quote in the text would break the line'
        assert b'\r' not in text and b'\n' not in text, f'key {key}: newline in the text'
        lines[position] = parts[0] + text + parts[2]
        used.add(key)
    missing = set(translations) - used
    assert not missing, f'keys not found in the source: {sorted(missing)[:5]}'
    return b'\r\n'.join(lines)
