"""English interface strings inside NOT A HERO.exe, replaced in place.

The Chowdren build copies these strings with fixed lengths baked into the code
(`push len; push str; call assign` and inline movq/mov copies in static
initialisers), so a Polish string may not be longer than the English one in
bytes. Shorter strings are padded with spaces: around the text when the
English has no edge spaces (centred pop-ups), at the end otherwise (labels that
keep a column). Translation keys (en-pl-review.json) are `exe|0x<file offset>`.
"""
from fonts import encode


def patch(exe: bytes, pl: dict, originals: dict) -> tuple[bytes, int]:
    result = bytearray(exe)
    count = 0
    for key, polish in pl.items():
        if not key.startswith('exe|'):
            continue
        offset = int(key.split('|')[1], 16)
        english = originals[key].encode('cp1252')
        assert exe[offset:offset + len(english) + 1] == english + b'\0', key
        assert exe[offset - 1] == 0, key
        data = encode(polish)
        assert len(data) <= len(english), (key, polish, len(data), len(english))
        spare = len(english) - len(data)
        if spare and english == english.strip():
            data = b' ' * (spare // 2) + data + b' ' * (spare - spare // 2)
        else:
            data = data + b' ' * spare
        result[offset:offset + len(data)] = data
        count += 1
    assert len(result) == len(exe)
    return bytes(result), count
