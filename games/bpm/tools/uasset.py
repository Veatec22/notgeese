"""Read and rewrite small cooked UE4.25 packages (unversioned, split .uasset/.uexp).

Enough for BPM's Font and FontFace assets: the name table, imports, exports and
tagged properties of one export can be changed and the package written back with
every header offset recomputed. Anything the code does not understand is kept as
raw bytes and must come back unchanged, which `roundtrip()` checks.
"""
import re
import struct
import zlib

TAG = 0x9E2A83C1


def _table(poly):
    out = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFFFFFFFF if c & 0x80000000 else (c << 1) & 0xFFFFFFFF
        out.append(c)
    return out


_DEPRECATED = _table(0x04C11DB7)


def name_hashes(value):
    """FNameEntrySerialized hashes: Strihash_DEPRECATED and StrCrc32, low 16 bits each."""
    h = 0
    for ch in value:
        h = ((h >> 8) & 0x00FFFFFF) ^ _DEPRECATED[(h ^ (ord(ch.upper()) & 0xFF)) & 0xFF]
    crc = zlib.crc32(b''.join(struct.pack('<I', ord(c)) for c in value))
    return struct.pack('<HH', h & 0xFFFF, crc & 0xFFFF)


def fstring(value):
    if not value:
        return struct.pack('<i', 0)
    try:
        body = value.encode('ascii') + b'\0'
        return struct.pack('<i', len(body)) + body
    except UnicodeEncodeError:
        body = value.encode('utf-16-le') + b'\0\0'
        return struct.pack('<i', -(len(body) // 2)) + body


class Reader:
    def __init__(self, data, at=0):
        self.d, self.at = data, at

    def get(self, fmt):
        v = struct.unpack_from('<' + fmt, self.d, self.at)
        self.at += struct.calcsize('<' + fmt)
        return v[0] if len(v) == 1 else v

    def raw(self, n):
        b = self.d[self.at:self.at + n]
        self.at += n
        return b

    def fstr(self):
        n = self.get('i')
        if n < 0:
            return self.raw(-2 * n).decode('utf-16-le').rstrip('\0')
        return self.raw(n).decode('latin-1').rstrip('\0')


# Summary fields after FolderName, in order. 'o' marks offsets into the header.
SUMMARY = [
    ('PackageFlags', 'I'), ('NameCount', 'i'), ('NameOffset', 'o'),
    ('GatherableTextDataCount', 'i'), ('GatherableTextDataOffset', 'o'),
    ('ExportCount', 'i'), ('ExportOffset', 'o'), ('ImportCount', 'i'), ('ImportOffset', 'o'),
    ('DependsOffset', 'o'), ('SoftPackageReferencesCount', 'i'), ('SoftPackageReferencesOffset', 'o'),
    ('SearchableNamesOffset', 'o'), ('ThumbnailTableOffset', 'o'),
]


class Package:
    def __init__(self, uasset, uexp):
        self.uasset, self.uexp = uasset, uexp
        r = Reader(uasset)
        self.head = r.raw(0)
        tag, legacy, ue3, ue4, lic, ncustom = r.get('Iiiiii')
        assert tag == TAG and legacy == -7 and ncustom == 0 and ue4 == 0
        self.prefix = uasset[:r.at]
        self.total_header = r.get('i')
        self.folder = r.fstr()
        self.s = {}
        for name, fmt in SUMMARY:
            self.s[name] = r.get('i' if fmt == 'o' else fmt)
        self.mid_start = r.at
        # Guid, generations, engine versions, compression, source, additional packages
        r.raw(16)
        gens = r.get('i'); r.raw(8 * gens)
        r.raw(4 + 2 + 2 + 4 + 4 + 2 + 2 + 4 + 4)  # two engine versions (major,minor,patch,changelist,branch-fstr)
        self.mid = uasset[self.mid_start:r.at]
        self.mid = None  # parsed below instead, engine version strings vary in size
        r.at = self.mid_start
        r.raw(16)
        gens = r.get('i'); r.raw(8 * gens)
        for _ in range(2):
            r.get('HHHI'); r.fstr()
        r.get('I')  # compression flags
        assert r.get('i') == 0  # compressed chunks
        r.get('I')  # package source
        assert r.get('i') == 0  # additional packages to cook
        self.mid = uasset[self.mid_start:r.at]
        self.tail_fields_at = r.at
        self.asset_registry = r.get('i')
        self.bulk_start = r.get('q')
        self.world_tile = r.get('i')
        nchunks = r.get('i'); self.chunks = [r.get('i') for _ in range(nchunks)]
        self.preload_count, self.preload_offset = r.get('ii')
        self.summary_end = r.at

        r.at = self.s['NameOffset']
        self.names = []
        for _ in range(self.s['NameCount']):
            self.names.append(r.fstr())
            r.get('I')
        assert r.at == self.s['ImportOffset'], (r.at, self.s['ImportOffset'])
        self.imports = []
        for _ in range(self.s['ImportCount']):
            self.imports.append(list(r.get('iiiiiii')))
        assert r.at == self.s['ExportOffset']
        self.exports = []
        for _ in range(self.s['ExportCount']):
            self.exports.append(bytearray(r.raw(104)))
        # Everything else in the header (depends map, preload dependencies...) stays raw.
        self.rest_at = r.at
        self.rest = uasset[r.at:self.total_header]
        assert self.s['DependsOffset'] == self.rest_at
        self.bodies = []
        for x in self.exports:
            size, off = struct.unpack_from('<qq', x, 28)
            self.bodies.append(uexp[off - self.total_header:off - self.total_header + size])
        self.uexp_tail = uexp[sum(len(b) for b in self.bodies):]
        assert self.uexp_tail == struct.pack('<I', TAG)

    # -- names -----------------------------------------------------------------
    def name(self, value):
        """Index of a name, appending it if the package does not have it yet."""
        if value in self.names:
            return self.names.index(value), 0
        m = re.fullmatch(r'(.+)_(\d+)', value)
        if m and m.group(1) in self.names:
            return self.names.index(m.group(1)), int(m.group(2)) + 1
        self.names.append(value)
        return len(self.names) - 1, 0

    def label(self, index, number=0):
        s = self.names[index]
        return f'{s}_{number - 1}' if number else s

    # -- writing ---------------------------------------------------------------
    def write(self):
        names = b''.join(fstring(n) + name_hashes(n) for n in self.names)
        imports = b''.join(struct.pack('<iiiiiii', *i) for i in self.imports)

        s = dict(self.s)
        head_fixed = len(self.prefix) + 4 + len(fstring(self.folder)) + 4 * len(SUMMARY) \
            + len(self.mid) + 4 + 8 + 4 + 4 + 4 * len(self.chunks) + 8
        name_at = head_fixed
        import_at = name_at + len(names)
        export_at = import_at + len(imports)
        rest_at = export_at + 104 * len(self.exports)
        header = rest_at + len(self.rest)
        shift = rest_at - self.rest_at
        s['NameCount'], s['NameOffset'] = len(self.names), name_at
        s['ImportCount'], s['ImportOffset'] = len(self.imports), import_at
        s['ExportCount'], s['ExportOffset'] = len(self.exports), export_at
        for key in ('DependsOffset', 'SoftPackageReferencesOffset', 'SearchableNamesOffset',
                    'ThumbnailTableOffset', 'GatherableTextDataOffset'):
            if s[key] > 0:
                s[key] += shift
        preload = self.preload_offset + shift if self.preload_offset > 0 else self.preload_offset

        exports, at = [], header
        for x, body in zip(self.exports, self.bodies):
            x = bytearray(x)
            struct.pack_into('<qq', x, 28, len(body), at)
            at += len(body)
            exports.append(bytes(x))
        uexp = b''.join(self.bodies) + self.uexp_tail
        bulk = header + len(uexp) - 4

        out = bytearray(self.prefix)
        out += struct.pack('<i', header) + fstring(self.folder)
        for key, fmt in SUMMARY:
            out += struct.pack('<' + ('i' if fmt == 'o' else fmt), s[key])
        out += self.mid
        registry = self.asset_registry + shift if self.asset_registry > 0 else self.asset_registry
        out += struct.pack('<iqi', registry, bulk, self.world_tile)
        out += struct.pack('<i', len(self.chunks)) + b''.join(struct.pack('<i', c) for c in self.chunks)
        out += struct.pack('<ii', self.preload_count, preload)
        assert len(out) == name_at, (len(out), name_at)
        out += names + imports + b''.join(exports) + self.rest
        assert len(out) == header
        return bytes(out), uexp


def roundtrip(uasset, uexp):
    p = Package(uasset, uexp)
    a, e = p.write()
    return a == uasset and e == uexp


# -- tagged properties ---------------------------------------------------------

class Prop:
    def __init__(self, name, type, tag, value, guid=None):
        self.name, self.type, self.tag, self.value, self.guid = name, type, tag, value, guid

    def __repr__(self):
        return f'Prop({self.name}:{self.type}{self.tag or ""}={self.value!r})'


NATIVE_STRUCTS = {'Guid': 16, 'Vector2D': 8, 'LinearColor': 16, 'Color': 4}


class Props:
    """Tagged property (de)serializer for one package's name table."""

    def __init__(self, pkg):
        self.p = pkg

    def fname(self, r):
        i, n = r.get('ii')
        return self.p.label(i, n)

    def put_name(self, value):
        i, n = self.p.name(value)
        return struct.pack('<ii', i, n)

    def read_list(self, r):
        props = []
        while True:
            name = self.fname(r)
            if name == 'None':
                return props
            type = self.fname(r)
            size, index = r.get('ii')
            assert index == 0
            tag = None
            if type == 'StructProperty':
                tag = (self.fname(r), r.raw(16))
            elif type in ('ByteProperty', 'EnumProperty'):
                tag = self.fname(r)
            elif type == 'ArrayProperty':
                tag = self.fname(r)
            elif type == 'BoolProperty':
                tag = r.get('B')
            has_guid = r.get('B')
            guid = r.raw(16) if has_guid else None
            start = r.at
            value = self.read_value(r, type, tag, size)
            assert r.at - start == size, (name, type, r.at - start, size)
            props.append(Prop(name, type, tag, value, guid))

    def read_value(self, r, type, tag, size):
        if type == 'StructProperty':
            return self.read_struct(r, tag[0], size)
        if type == 'ArrayProperty':
            count = r.get('i')
            if tag == 'StructProperty':
                inner = dict(name=self.fname(r), type=self.fname(r))
                inner_size, _ = r.get('ii')
                inner['struct'] = self.fname(r)
                inner['guid'] = r.raw(16)
                assert r.get('B') == 0
                items = [self.read_struct(r, inner['struct'], None) for _ in range(count)]
                return dict(inner=inner, items=items)
            return dict(items=[self.read_value(r, tag, None, None) for _ in range(count)])
        if type in ('NameProperty', 'EnumProperty'):
            return self.fname(r)
        if type == 'ByteProperty':
            return self.fname(r) if tag != 'None' else r.get('B')
        if type == 'StrProperty':
            return r.fstr()
        if type == 'IntProperty':
            return r.get('i')
        if type == 'FloatProperty':
            return r.get('f')
        if type == 'ObjectProperty':
            return r.get('i')
        return r.raw(size)

    def read_struct(self, r, struct_name, size):
        if struct_name in NATIVE_STRUCTS:
            return r.raw(NATIVE_STRUCTS[struct_name])
        if struct_name == 'FontData':
            return ('FontData', self.read_fontdata(r))
        return self.read_list(r)

    def read_fontdata(self, r):
        # Cooked FFontData: bIsCooked, then FontFaceAsset; filename/hinting only when no asset.
        cooked = r.get('i')
        face = r.get('i')
        if not face:
            raise ValueError('FontData without a FontFace asset is not handled.')
        return dict(cooked=cooked, face=face, subface=r.get('i'))

    # writing
    def write_list(self, props):
        out = bytearray()
        for p in props:
            out += self.write_prop(p)
        out += self.put_name('None')
        return bytes(out)

    def write_prop(self, p):
        body = self.write_value(p.type, p.tag, p.value)
        out = bytearray(self.put_name(p.name) + self.put_name(p.type))
        out += struct.pack('<ii', len(body), 0)
        if p.type == 'StructProperty':
            out += self.put_name(p.tag[0]) + p.tag[1]
        elif p.type in ('ByteProperty', 'EnumProperty', 'ArrayProperty'):
            out += self.put_name(p.tag)
        elif p.type == 'BoolProperty':
            out += struct.pack('<B', p.tag)
        out += struct.pack('<B', 1 if p.guid else 0) + (p.guid or b'')
        return bytes(out) + body

    def write_value(self, type, tag, value):
        if type == 'StructProperty':
            return self.write_struct(tag[0], value)
        if type == 'ArrayProperty':
            items = value['items']
            out = bytearray(struct.pack('<i', len(items)))
            if tag == 'StructProperty':
                inner = value['inner']
                body = b''.join(self.write_struct(inner['struct'], v) for v in items)
                out += self.put_name(inner['name']) + self.put_name(inner['type'])
                out += struct.pack('<ii', len(body), 0)
                out += self.put_name(inner['struct']) + inner['guid'] + b'\0'
                return bytes(out) + body
            return bytes(out) + b''.join(self.write_value(tag, None, v) for v in items)
        if type in ('NameProperty', 'EnumProperty'):
            return self.put_name(value)
        if type == 'ByteProperty':
            return self.put_name(value) if tag != 'None' else struct.pack('<B', value)
        if type == 'StrProperty':
            return fstring(value)
        if type == 'IntProperty':
            return struct.pack('<i', value)
        if type == 'FloatProperty':
            return struct.pack('<f', value)
        if type == 'ObjectProperty':
            return struct.pack('<i', value)
        return value

    def write_struct(self, struct_name, value):
        if isinstance(value, bytes):
            return value
        if isinstance(value, tuple) and value[0] == 'FontData':
            v = value[1]
            return struct.pack('<iii', v['cooked'], v['face'], v['subface'])
        if isinstance(value, tuple) and value[0] == 'Int32Range':
            return value[1]
        return self.write_list(value)


def load_export(pkg, index=0):
    """Tagged properties of an export plus the raw bytes that follow them."""
    props = Props(pkg)
    r = Reader(pkg.bodies[index])
    tree = props.read_list(r)
    return props, tree, pkg.bodies[index][r.at:]
