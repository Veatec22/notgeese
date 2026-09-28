"""I2 table layout for the pinned Skate Story resources asset."""
import struct

def parse(raw):
    pos = 56
    def integer():
        nonlocal pos
        value = struct.unpack_from('<i', raw, pos)[0]
        pos += 4
        return value
    def string():
        nonlocal pos
        length = integer()
        assert 0 <= length <= len(raw) - pos
        value = raw[pos:pos + length].decode('utf-8')
        pos = (pos + length + 3) & ~3
        return value
    entries = []
    for _ in range(integer()):
        key, kind = string(), integer()
        languages = [string() for _ in range(integer())]
        length = integer()
        flags = raw[pos:pos+length]
        pos = (pos + length + 3) & ~3
        touch = [string() for _ in range(integer())]
        entries.append((key, kind, languages, flags, touch))
    return entries, raw[pos:]

def integer(n):
    return struct.pack('<i', n)

def string(s):
    data = s.encode('utf-8')
    return integer(len(data)) + data + b'\0' * (-len(data) % 4)

def parse_languages(tail):
    # CaseInsensitiveTerms (aligned bool), OnMissingTranslation, empty mTerm_AppName.
    assert tail[:12] == b'\0\0\0\0\1\0\0\0\0\0\0\0'
    count = struct.unpack_from('<i', tail, 12)[0]
    position = 16
    rows = []
    for _ in range(count):
        fields = []
        for _ in range(2):
            length = struct.unpack_from('<i', tail, position)[0]
            position += 4
            fields.append(tail[position:position+length].decode('utf-8'))
            position = (position + length + 3) & ~3
        flags = tail[position:position+4]
        position += 4
        rows.append((*fields, flags))
    return rows, position

