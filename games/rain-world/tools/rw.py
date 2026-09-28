"""Shared by the Rain World tools: where the game keeps texts and how to read them.

Texts live in StreamingAssets/text/text_<lang>/ and mods/<dlc>/text/text_<lang>/:
- strings.txt: lines "key|text", the key is English text or an id; the file's first char is
  the encryption marker (0 = plain text);
- <number>[-<character>].txt: conversations, XOR-encrypted with a key depending on file number
  and language. A file starting with 0 is read without decryption.
Details in docs/technical.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import dnfile

DEFAULT_GAME = Path(r'C:/Games/Rain World')
DATA = 'RainWorld_Data'

# Order = the game's normal load order: base game, then DLCs.
SOURCES = {
    'base': 'text',
    'rwremix': 'mods/rwremix/text',
    'expedition': 'mods/expedition/text',
    'jollycoop': 'mods/jollycoop/text',
    'moreslugcats': 'mods/moreslugcats/text',
    'watcher': 'mods/watcher/text',
}

# Conversation lines that are engine instructions only, without text.
INSTRUCTIONS = {'SPECEVENT', 'PEBBLESWAIT'}


def streaming(game: Path) -> Path:
    return game / DATA / 'StreamingAssets'


def encryption_string(game: Path) -> str:
    """The game's XOR key: a long literal in Assembly-CSharp (RWCustom.Custom.encrptString).

    Not copied into the repo; read from the install and checked on 1.txt.
    """
    pe = dnfile.dnPE(str(game / DATA / 'Managed' / 'Assembly-CSharp.dll'))
    heap = pe.net.user_strings
    raw = heap.get_data_at_offset(0, heap.sizeof())
    probe = (streaming(game) / 'text/text_eng/1.txt').read_bytes().decode('utf-8-sig')
    i = 1
    while i < len(raw):
        b = raw[i]
        if b & 0x80 == 0:
            n, i = b, i + 1
        elif b & 0xC0 == 0x80:
            n, i = ((b & 0x3F) << 8) | raw[i + 1], i + 2
        else:
            n, i = ((b & 0x1F) << 24) | (raw[i + 1] << 16) | (raw[i + 2] << 8) | raw[i + 3], i + 4
        if n >= 3000:
            key = raw[i:i + n - 1].decode('utf-16-le')[54:54 + 1447]
            if decrypt_text(probe, 1, key).startswith('0-1\r\n'):
                return key
        i += n
    raise SystemExit('Encryption key not found in Assembly-CSharp.dll; different game version?')


def xor(text: str, displace: int, key: str) -> str:
    """RWCustom.Custom.xorEncrypt (positive numbers, so division as in C#)."""
    d = abs(displace * 82 + displace // 3 + displace % 322 - displace % 17 - displace * 7 % 811)
    return ''.join(chr(ord(c) ^ ord(key[(i + d) % len(key)])) for i, c in enumerate(text))


def file_number(name: str) -> int:
    """File number for the key: "12-saint.txt" -> 12, names without a number -> sum of char digits."""
    stem = Path(name).stem.lower()
    head = stem.split('-')[0]
    if head.isdigit():
        return int(head)
    return sum(ord(c) - 48 for c in stem)


def decrypt_text(text: str, number: int, key: str, language_index: int = 0) -> str:
    if text[:1] != '1':
        return text
    return '0' + xor(text, 54 + number + language_index * 7, key)[1:]


def read_text(path: Path) -> str:
    # No newline translation: the XOR key counts char positions including \r.
    return path.read_bytes().decode('utf-8-sig')


def read_strings(path: Path) -> dict[str, str]:
    text = read_text(path)
    if text[:1] == '0':
        text = text[1:]
    out = {}
    for line in text.split('\r\n'):
        if '///' in line:
            line = line.split('/')[0].rstrip()
        if '|' not in line:
            continue
        key, value = line.split('|', 1)
        out[key] = value
    return out


@dataclass
class DialogueLine:
    index: int      # line number in the file (0 = header)
    prefix: str     # instructions before the text, e.g. "0 : 15 : "
    text: str
    suffix: str     # instructions after the text, e.g. " : 40"


NUMBER = re.compile(r'^\d+$')


def split_dialogue_line(line: str) -> tuple[str, str, str] | None:
    """Split a conversation line into (prefix, text, suffix); None when there's no text."""
    if not line.strip():
        return None
    parts = line.split(' : ')
    if parts[0] in INSTRUCTIONS:
        return None
    if len(parts) > 1 and NUMBER.match(parts[0]):
        # "N : text", "N : N : text", "N : text : N": the text is the first non-number part.
        for i, part in enumerate(parts[1:], 1):
            if not NUMBER.match(part):
                prefix = ' : '.join(parts[:i]) + ' : '
                rest = parts[i:]
                tail = [p for p in rest[1:]]
                if tail and all(NUMBER.match(p) for p in tail):
                    return prefix, rest[0], ' : ' + ' : '.join(tail)
                return prefix, ' : '.join(rest), ''
        return None
    return '', line, ''


# Language index in the XOR key (order of the InGameTranslator.LanguageID ExtEnum).
LANGUAGE_INDEX = {'eng': 0, 'fre': 1, 'ita': 2, 'ger': 3, 'spa': 4, 'por': 5,
                  'jap': 6, 'kor': 7, 'rus': 8, 'chi': 9, 'tra': 10, 'tha': 11}


def read_dialogue(path: Path, key: str, language: str = 'eng') -> tuple[str, list[DialogueLine]]:
    text = decrypt_text(read_text(path), file_number(path.name), key, LANGUAGE_INDEX[language])
    lines = text.split('\r\n')
    out = []
    for i, line in enumerate(lines[1:], 1):
        parts = split_dialogue_line(line)
        if parts:
            out.append(DialogueLine(i, *parts))
    return text, out


def dialogue_files(game: Path, source: str, language: str = 'eng') -> list[Path]:
    folder = streaming(game) / SOURCES[source] / f'text_{language}'
    return sorted((p for p in folder.glob('*.txt') if p.name != 'strings.txt'),
                  key=lambda p: (file_number(p.name), p.name))
