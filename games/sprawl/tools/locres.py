"""Read and write Unreal's .locres, the compiled localization resource.

One file per culture, under Content/Localization/<Target>/<culture>/. Layout:

    FGuid magic, uint8 version, int64 offset of the string table
    [v2+] uint32 total entry count
    uint32 namespace count, then per namespace:
        [v2+] uint32 hash, FString name, uint32 key count, then per key:
            [v2+] uint32 hash, FString key, uint32 source hash, int32 string index
    at the offset: uint32 count, then FString values ([v3] each with a uint32 refcount)

Two things this module deliberately does not do.

It never computes a hash. Version 3 stores a checksum for every namespace, key
and source string, and the exact function is Unreal's own; rather than guess it,
a translation is built from the English resource and carries its hashes through
unchanged - every key being translated already exists there with the right ones.
The proof that this is faithful is that re-serializing the English file returns
it byte for byte.

It does not require a culture to be complete. Whatever a culture leaves out
falls back to the native one, which is how the game's own Ukrainian file gets
away with 671 of English's 717 keys - and what makes shipping a partial
translation safe.
"""
import struct
from dataclasses import dataclass, field

MAGIC = struct.pack('<4I', 0x7574140E, 0xFC034A67, 0x9D90154A, 0x1B7F37C3)


def read_string(data, at):
    length = struct.unpack_from('<i', data, at)[0]
    at += 4
    if length == 0:
        return '', at
    if length > 0:
        return data[at:at + length - 1].decode('utf-8'), at + length
    return data[at:at + (-length * 2) - 2].decode('utf-16-le'), at + (-length) * 2


def write_string(value):
    """UTF-8 while the text is ASCII, UTF-16 otherwise - the engine's own rule."""
    if value.isascii():
        body = value.encode('utf-8') + b'\0'
        return struct.pack('<i', len(body)) + body
    body = value.encode('utf-16-le') + b'\0\0'
    return struct.pack('<i', -(len(body) // 2)) + body


@dataclass
class Entry:
    key_hash: int
    key: str
    source_hash: int
    text: str


@dataclass
class Resource:
    version: int = 3
    namespaces: list = field(default_factory=list)   # (hash, name, [Entry])

    def texts(self):
        return {(name, e.key): e.text for _, name, entries in self.namespaces for e in entries}

    def entries(self):
        for _, name, entries in self.namespaces:
            for e in entries:
                yield name, e


def load(path):
    data = path.read_bytes()
    assert data[:16] == MAGIC, 'Not a .locres file.'
    version = data[16]
    assert version in (1, 2, 3), version
    at = 17
    table_at = struct.unpack_from('<q', data, at)[0]
    at += 8
    if version >= 2:
        at += 4                                       # total entry count, recomputed on write
    namespace_count = struct.unpack_from('<I', data, at)[0]
    at += 4

    raw = []
    for _ in range(namespace_count):
        namespace_hash = 0
        if version >= 2:
            namespace_hash = struct.unpack_from('<I', data, at)[0]
            at += 4
        namespace, at = read_string(data, at)
        keys = []
        for _ in range(struct.unpack_from('<I', data, at)[0]):
            pass
        count = struct.unpack_from('<I', data, at)[0]
        at += 4
        for _ in range(count):
            key_hash = 0
            if version >= 2:
                key_hash = struct.unpack_from('<I', data, at)[0]
                at += 4
            key, at = read_string(data, at)
            source_hash = struct.unpack_from('<I', data, at)[0]
            at += 4
            index = struct.unpack_from('<i', data, at)[0]
            at += 4
            keys.append((key_hash, key, source_hash, index))
        raw.append((namespace_hash, namespace, keys))

    at = table_at
    count = struct.unpack_from('<I', data, at)[0]
    at += 4
    values = []
    for _ in range(count):
        value, at = read_string(data, at)
        if version >= 3:
            at += 4                                   # reference count, recomputed on write
        values.append(value)

    return Resource(version, [(h, n, [Entry(kh, k, sh, values[i]) for kh, k, sh, i in keys])
                              for h, n, keys in raw])


def translate(source, translations):
    """A resource carrying only the translated keys, with the source's hashes."""
    namespaces = []
    for namespace_hash, namespace, entries in source.namespaces:
        kept = [Entry(e.key_hash, e.key, e.source_hash, translations[(namespace, e.key)])
                for e in entries if (namespace, e.key) in translations]
        if kept:
            namespaces.append((namespace_hash, namespace, kept))
    carried = sum(len(entries) for _, _, entries in namespaces)
    assert carried == len(translations), f'{len(translations) - carried} keys are not in the source'
    return Resource(source.version, namespaces)


def dump(resource):
    values, index_of, references = [], {}, []
    for _, entry in resource.entries():
        if entry.text not in index_of:
            index_of[entry.text] = len(values)
            values.append(entry.text)
            references.append(0)
        references[index_of[entry.text]] += 1

    body = bytearray()
    if resource.version >= 2:
        body += struct.pack('<I', sum(len(e) for _, _, e in resource.namespaces))
    body += struct.pack('<I', len(resource.namespaces))
    for namespace_hash, namespace, entries in resource.namespaces:
        if resource.version >= 2:
            body += struct.pack('<I', namespace_hash)
        body += write_string(namespace)
        body += struct.pack('<I', len(entries))
        for entry in entries:
            if resource.version >= 2:
                body += struct.pack('<I', entry.key_hash)
            body += write_string(entry.key)
            body += struct.pack('<I', entry.source_hash)
            body += struct.pack('<i', index_of[entry.text])

    table = bytearray(struct.pack('<I', len(values)))
    for position, value in enumerate(values):
        table += write_string(value)
        if resource.version >= 3:
            table += struct.pack('<I', references[position])

    head = MAGIC + bytes([resource.version])
    return head + struct.pack('<q', len(head) + 8 + len(body)) + bytes(body) + bytes(table)
