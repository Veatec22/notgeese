"""Build a Polish Boomerang X out of the original Assembly-CSharp.dll.

The game has ten languages and no room for an eleventh: the table's shape is
fixed by `Data`'s field list, and widening it would mean renumbering metadata.
So Polish moves into a field the table already carries and nobody reads -
`description`, the developers' note about each row. Three small code patches
then make the game reach for it:

  1. localization_manager.get_translation - the default arm of its switch says
     "LOCALIZATION ERROR". Overwritten with `return row.description`, so any
     language past the ninth is Polish. Exactly sixteen bytes, padded with nops.
  2. font_manager.get_font - its default arm returns null. One byte of the
     branch offset points it at the Latin set that English uses. Its fonts carry
     ł ó themselves and fonts.py gives them fallbacks for the rest.
  3. options_screen.on_reading_save_complete - two literal tens bound the loops
     that fill the language dropdown. Eleven now, so index 10 gets an entry.

A note can be shorter than the text that has to live in it. Since each note is
referenced once, by its own row, two rows can trade notes: swap the `ldstr`
operands in Init and the room goes where it is needed. See `lend_room`.

Nothing moves and nothing grows: every patch is written over bytes of the same
length, in the file's own place. That is why the whole build is a byte edit of
the original DLL rather than a recompile.
"""
import argparse
import hashlib
import json
import sys
import struct
from pathlib import Path

import table

HERE = Path(__file__).resolve().parent
GAME = HERE.parent
sys.path.insert(0, str(GAME.parents[1] / 'tools'))

from translations import polish_by_key  # noqa: E402
ORIGINAL = '1c0ac29aad888faa7439ec57ea7da4976a74c6936aefd7b388a3e9fe904e0b40'
RELATIVE = Path('BOOMERANG X_Data') / 'Managed' / 'Assembly-CSharp.dll'
VERSION = '0.1'

ENGLISH = 0                       # language.english; French, German and Spanish share its arm
DESCRIPTION = 0x04001F62          # Data::description

NOP, LDARG_1, LDFLD, RET, BR_S, SWITCH, LDC_I4_S, BLT_S = \
    0x00, 0x03, 0x7B, 0x2A, 0x2B, 0x45, 0x1F, 0x32


def switch_arms(body):
    """(offset just past the switch's br.s, its default target, every case target)."""
    assert body[1] == SWITCH, 'method does not open with a switch'
    count = struct.unpack_from('<I', body, 2)[0]
    targets = [struct.unpack_from('<i', body, 6 + 4 * index)[0] for index in range(count)]
    after = 6 + 4 * count
    assert body[after] == BR_S, 'no default branch after the switch'
    return after, after + 2 + body[after + 1], [after + t for t in targets]


def patch_get_translation(image, out):
    """The default arm returns the row's description instead of an error string."""
    start, size = image.method('localization_manager', 'get_translation')
    body = image.data[start:start + size]
    _, default, _ = switch_arms(body)
    tail = size - default
    assert tail == 16, f'default arm is {tail} bytes, expected 16'
    assert body[default] == 0x72 and body[default + 10] == 0x72, 'default arm is not the error path'
    assert image.string(struct.unpack_from('<I', body, default + 11)[0]) == 'LOCALIZATION ERROR'

    arm = bytes([LDARG_1, LDFLD]) + struct.pack('<I', DESCRIPTION) + bytes([RET])
    out[start + default:start + size] = arm + bytes([NOP]) * (tail - len(arm))
    return {'method': 'localization_manager.get_translation', 'at': start + default, 'bytes': tail}


def patch_get_font(image, out):
    """The default arm falls into the Latin set - the one English, French, German and Spanish use.

    The Russian set was the first choice, for its text font. But its button font,
    `Abys-Regular SDF`, is capitals only and has no Polish letter at all, so every
    Polish letter came from the lowercase of the fallback, at half the height of
    the capitals around it. The Latin fonts carry `Ó ó Ł ł` themselves and take
    the rest from `beer money` fallbacks of nearly matching size (see fonts.py).
    """
    start, size = image.method('font_manager', 'get_font')
    body = image.data[start:start + size]
    branch, default, targets = switch_arms(body)
    assert body[default] == 0x14, 'default arm is not `ldnull`'
    latin = targets[ENGLISH]
    assert latin != default and body[latin] == 0x02, 'English arm is not `ldarg.0`'
    assert targets[:4] == [latin] * 4, 'English, French, German and Spanish no longer share an arm'
    offset = latin - (branch + 2)
    assert -128 <= offset <= 127
    out[start + branch + 1] = offset & 0xFF
    return {'method': 'font_manager.get_font', 'at': start + branch + 1,
            'from': body[branch + 1], 'to': offset}


def patch_dropdown(image, out):
    """Both loops that fill the language dropdown count to eleven."""
    start, size = image.method('options_screen', 'on_reading_save_complete')
    body = image.data[start:start + size]
    found = [at for at in range(size - 3)
             if body[at] == LDC_I4_S and body[at + 1] == 10 and body[at + 2] == BLT_S]
    assert len(found) == 2, f'expected two `ldc.i4.s 10; blt.s` loops, found {len(found)}'
    for at in found:
        out[start + at + 1] = 11
    return {'method': 'options_screen.on_reading_save_complete',
            'at': [start + at + 1 for at in found], 'from': 10, 'to': 11}


def lend_room(rows, text_of):
    """Which description literal each row's text is written into.

    A row whose Polish outgrows its own note swaps literals with a row that has
    room to spare. The notes are dead storage and each is referenced once, by
    its own row, so the `ldstr` operands in Init can simply be exchanged - only
    the pair moves, everyone else stays put.
    """
    room = {row['description_token']: len(row['description']) for row in rows}
    held = [row['description_token'] for row in rows]          # row index -> literal
    need = [len(text_of(row)) for row in rows]

    everyone = range(len(rows))
    short = sorted((i for i in everyone if need[i] > room[held[i]]), key=lambda i: -need[i])
    spare = sorted((i for i in everyone if need[i] <= room[held[i]]),
                   key=lambda i: -room[held[i]])
    for i in short:
        donor = next((d for d in spare if room[held[d]] >= need[i]
                      and need[d] <= room[held[i]]), None)
        assert donor is not None, \
            f"nothing can lend {rows[i]['id']} the {need[i]} characters it needs"
        held[i], held[donor] = held[donor], held[i]
        spare.remove(donor)
    return held, room


def blob(image, token):
    """(where a user string's characters start, how many of them there are)."""
    base, _ = image.streams['#US']
    at = base + (token & 0xFFFFFF)
    first = image.data[at]
    if first & 0x80 == 0:
        length, at = first, at + 1
    elif first & 0xC0 == 0x80:
        length, at = ((first & 0x3F) << 8) | image.data[at + 1], at + 2
    else:
        length = ((first & 0x1F) << 24) | (image.data[at + 1] << 16) \
                 | (image.data[at + 2] << 8) | image.data[at + 3]
        at += 4
    return at, (length - 1) // 2


def write_description(image, out, token, text):
    """Overwrite one description in place, padded with spaces to its old length."""
    at, room = blob(image, token)
    assert len(text) <= room, f'{len(text)} characters will not fit in {room}'
    padded = text.ljust(room)
    out[at:at + 2 * room] = padded.encode('utf-16-le')
    # The byte after the characters tells the runtime the string is not plain ASCII.
    out[at + 2 * room] = 1 if any(c > '\x7f' for c in padded) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, required=True,
                        help='The original Assembly-CSharp.dll, or the game folder holding it')
    parser.add_argument('--out', type=Path, default=GAME / 'dist', help='Where to build')
    args = parser.parse_args()

    source = args.source
    if source.is_dir():
        source = source / RELATIVE
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == ORIGINAL, (f'{source} is not the original DLL ({digest}). '
                                'Build from the game as shipped, or from the backup.')

    polish = polish_by_key(GAME)
    image = table.Assembly(source)
    out = bytearray(raw)

    patches = [patch_get_translation(image, out), patch_get_font(image, out),
               patch_dropdown(image, out)]

    rows = table.rows(image)
    known = {row['id'] for row in rows}       # `difficulty_select_prompt` is on two rows
    unknown = sorted(set(polish) - known)
    assert not unknown, f'not rows of the table: {unknown}'

    # Rows with no Polish yet fall back to English rather than a developer's note.
    def text_of(row):
        return polish.get(row['id'], row['columns']['english']['text'])

    held, room = lend_room(rows, text_of)
    borrowed = [{'id': row['id'], 'needs': len(text_of(row)),
                 'own_room': len(row['description']), 'room_now': room[held[index]]}
                for index, row in enumerate(rows) if held[index] != row['description_token']]

    for index, row in enumerate(rows):
        write_description(image, out, held[index], text_of(row))
        if held[index] != row['description_token']:
            struct.pack_into('<I', out, row['description_at'], held[index])

    target = args.out / RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bytes(out))

    assert len(out) == len(raw), 'the build changed the file size'
    readback = {row['id']: row['description'] for row in table.rows(table.Assembly(target))}
    for identifier, text in polish.items():
        assert readback[identifier].rstrip() == text.rstrip(), \
            f'{identifier}: read back {readback[identifier]!r}'

    # This build assembles no package: the code file is entirely third-party, so the
    # player gets only the difference, via `tools/patch.py release` (docs/technical.md).
    print(json.dumps({'built': str(target), 'sha256': hashlib.sha256(bytes(out)).hexdigest(),
                      'translated': len(polish), 'rows': len(rows),
                      'borrowed_room': borrowed, 'patches': patches},
                     indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
