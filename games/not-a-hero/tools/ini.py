"""Translatable entries of NOT A HERO's INI files, shared by extract and build.

Terms are `file|section|key`. A repeated section (chat.ini has three
[PASSIVEUP7]) gets `~2`, `~3` on its later occurrences.
"""
import re

from fonts import encode

FILES = ['Src/talk.ini', 'Src/ENDS.ini', 'Src/chat.ini', 'Src/LEVELS/SETTINGS.ini']
# Tokens the engine acts on. `#`/`^` pace the text and trigger events counted
# per line, so their counts must survive; `$...$` are substitutions.
CONTROL = re.compile(r'\$(?:END|LEVELSELECT|RESTART)\$|@')
PLACEHOLDER = re.compile(r'\$[A-Z_]+\$')
SETTINGS_TEXT = re.compile(r'NAME|DESC|ACH\dNAME|SECRETTEXT')


def is_text(relative: str, section: str, key: str, value: str) -> bool:
    if relative.endswith('SETTINGS.ini'):
        return bool(SETTINGS_TEXT.fullmatch(key))
    # Lines made only of pacing markers and control tokens stay as they are.
    if not re.sub(r'[#^\s]|\$END\$|\$LEVELSELECT\$|\$RESTART\$|\+\+', '', value):
        return False
    if relative.endswith('chat.ini'):
        return key.isdigit()
    if not section.split('~')[0].isdigit():
        return section != 'P'  # word pools; [P] in ENDS.ini is a name table
    return key.isdigit() or bool(re.fullmatch(r'TEXT\d+', key))


def entries(raw: bytes, relative: str):
    """Yield (line_index, term, value) for every translatable line."""
    seen = {}
    section = None
    for index, line in enumerate(raw.decode('cp1252').splitlines()):
        if line.startswith('['):
            name = line.strip()[1:-1]
            seen[name] = seen.get(name, 0) + 1
            section = name if seen[name] == 1 else f'{name}~{seen[name]}'
        elif '=' in line and section is not None:
            key, value = line.split('=', 1)
            if is_text(relative, section, key, value):
                yield index, f'{relative}|{section}|{key}', value


def check(term: str, english: str, polish: str) -> list[str]:
    """Problems that would break the engine, not style."""
    problems = []
    if sorted(CONTROL.findall(english)) != sorted(CONTROL.findall(polish)):
        problems.append('control tokens differ')
    allowed = set(PLACEHOLDER.findall(english))
    # English appends S for plurals; Polish uses the singular name as a label.
    if '$SUBJECTOBJECTS$' in allowed:
        allowed.add('$SUBJECTOBJECT$')
    extra = set(PLACEHOLDER.findall(polish)) - allowed
    if extra:
        problems.append(f'new placeholders {sorted(extra)}')
    for mark in '#^':
        if english.count(mark) != polish.count(mark):
            problems.append(f'{mark} count {english.count(mark)} -> {polish.count(mark)}')
    try:
        encode(polish)
    except UnicodeEncodeError as error:
        problems.append(f'not encodable: {error}')
    return problems
