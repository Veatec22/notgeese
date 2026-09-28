"""Read Boomerang X's localization table out of Assembly-CSharp.dll.

The game keeps no data file. Its 360 rows live as IL inside one method,
SheetData.Init, which fills an array of `Data` objects. Every row is the same
shape, and always the same instructions:

    dup / ldc.i4 <row index>
    ldstr <id> / ldstr <description>
    ldc.i4 <max_char_limit> / ldc.i4 <asian_char_limit>
    ldstr x11                      the language columns
    newobj Data..ctor / stelem.ref

So the table can be read by walking the method's IL and slicing at `newobj`,
without decompiling anything. The same regularity is what makes it writable:
each column is one four-byte operand at a known offset in the method body.
"""
import struct
from pathlib import Path

import dnfile

COLUMNS = ['english', 'english_asian_source', 'french', 'german', 'spanish',
           'russian', 'brazilian_portuguese', 'japanese', 'korean',
           'chinese_traditional', 'chinese_simplified']

LDSTR, NEWOBJ, DUP, STELEM_REF = 0x72, 0x73, 0x25, 0xA2
LDC_I4, LDC_I4_S = 0x20, 0x1F
LDC_I4_0 = 0x16


class Assembly:
    """The parts of a .NET image this needs: the user string heap and one method body."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.pe = dnfile.dnPE(str(path))
        at = self.data.find(b'BSJB')
        assert at > 0, 'Not a .NET image.'
        self.metadata_at = at
        length = struct.unpack_from('<I', self.data, at + 12)[0]
        cursor = at + 16 + ((length + 3) & ~3) + 2
        count = struct.unpack_from('<H', self.data, cursor)[0]
        cursor += 2
        self.streams = {}
        for _ in range(count):
            offset, size = struct.unpack_from('<II', self.data, cursor)
            cursor += 8
            name = b''
            while self.data[cursor]:
                name += bytes([self.data[cursor]])
                cursor += 1
            cursor = (cursor + 4) & ~3
            self.streams[name.decode()] = (at + offset, size)

    def string(self, token):
        """The text an ldstr operand refers to."""
        assert token >> 24 == 0x70, hex(token)
        base, _ = self.streams['#US']
        at = base + (token & 0xFFFFFF)
        first = self.data[at]
        if first & 0x80 == 0:
            length, at = first, at + 1
        elif first & 0xC0 == 0x80:
            length = ((first & 0x3F) << 8) | self.data[at + 1]; at += 2
        else:
            length = ((first & 0x1F) << 24) | (self.data[at + 1] << 16) \
                     | (self.data[at + 2] << 8) | self.data[at + 3]; at += 4
        return self.data[at:at + length - 1].decode('utf-16-le')

    def method(self, type_name, method_name):
        """(file offset of the body, its length) for one method."""
        for row in self.pe.net.mdtables.TypeDef.rows:
            if str(row.TypeName) != type_name:
                continue
            for member in row.MethodList:
                entry = member.row
                if entry is None or str(entry.Name) != method_name or entry.Rva == 0:
                    continue
                at = self.pe.get_offset_from_rva(entry.Rva)
                if self.data[at] & 3 == 2:               # tiny header: one byte
                    return at + 1, self.data[at] >> 2
                flags = struct.unpack_from('<H', self.data, at)[0]
                size = struct.unpack_from('<I', self.data, at + 4)[0]
                return at + (flags >> 12) * 4, size
        raise AssertionError(f'{type_name}.{method_name} not found')


def rows(assembly):
    """Every row of the table, with the file offset of each column's operand."""
    start, size = assembly.method('SheetData', 'Init')
    body = assembly.data[start:start + size]

    literals, at = [], 0                      # (file offset of operand, token)
    numbers = []
    order = []                                # 's' for a string, 'n' for a number
    while at < len(body):
        op = body[at]
        if op == LDSTR:
            literals.append((start + at + 1, struct.unpack_from('<I', body, at + 1)[0]))
            order.append('s'); at += 5
        elif op == LDC_I4:
            numbers.append(struct.unpack_from('<i', body, at + 1)[0]); order.append('n'); at += 5
        elif op == LDC_I4_S:
            numbers.append(struct.unpack_from('<b', body, at + 1)[0]); order.append('n'); at += 2
        elif 0x16 <= op <= 0x1E:
            numbers.append(op - LDC_I4_0); order.append('n'); at += 1
        elif op == NEWOBJ:
            order.append('|'); at += 5
        else:
            at += _skip(body, at)

    out, literal, number = [], 0, 0
    grouped = ''.join(order).split('|')
    for group in grouped:
        if group.count('s') != 2 + len(COLUMNS) or group.count('n') < 3:
            literal += group.count('s'); number += group.count('n')
            continue
        identifier = assembly.string(literals[literal][1])
        description_at, description_token = literals[literal + 1]
        description = assembly.string(description_token)
        limits = numbers[number + 1:number + 3]
        columns = {}
        for index, column in enumerate(COLUMNS):
            offset, token = literals[literal + 2 + index]
            columns[column] = {'text': assembly.string(token), 'token': token, 'at': offset}
        out.append({'id': identifier, 'description': description,
                    'description_token': description_token,
                    'description_at': description_at,
                    'max_char_limit': limits[0], 'asian_char_limit': limits[1],
                    'columns': columns})
        literal += group.count('s'); number += group.count('n')
    return out


def _skip(body, at):
    """Bytes taken by any instruction this walker does not care about."""
    op = body[at]
    if op == 0xFE:
        second = body[at + 1]
        return 2 + (4 if second in (0x06, 0x07, 0x15, 0x16) else 2 if second in (0x09, 0x0B, 0x0C, 0x0D, 0x0E) else 0)
    if op in (0x28, 0x29, 0x6F, 0x73, 0x74, 0x75, 0x79, 0x7B, 0x7C, 0x7D, 0x7E, 0x80,
              0x8C, 0x8D, 0xA3, 0xA4, 0xD0, 0x70, 0x71, 0x38, 0x39, 0x3A, 0x3B, 0x3C,
              0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0xDD):
        return 5
    if op in (0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30,
              0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0xDE):
        return 2
    if op in (0x21, 0x23):
        return 9
    if op == 0x22:
        return 5
    return 1
