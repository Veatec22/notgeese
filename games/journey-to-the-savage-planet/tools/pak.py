"""Write a minimal Unreal .pak in the game's own version 7, for files the game does not have.

A packaged build reads content only from paks, so a loose .locres is never seen.
A second pak in Content/Paks is mounted next to the game's one; our files are
new paths, nothing in the game's pak is replaced.

    [per file] 53-byte entry header (offset written as 0, as UnrealPak does), then the bytes
    [index]  mount point, count, then per file: path, FPakEntry
    [footer] 16-byte key GUID, encrypted flag, magic, version, index offset and size, SHA-1 of the index

Entries are stored uncompressed; v7 has no directory index, the engine builds one
from the paths.
"""
import hashlib
import struct

MAGIC = 0x5A6F12E1
VERSION = 7
MOUNT_POINT = '../../../'
FOOTER_SIZE = 61


def fstring(value):
    body = value.encode('utf-8') + b'\0'
    return struct.pack('<i', len(body)) + body


def entry(offset, size, digest):
    return (struct.pack('<qqq', offset, size, size)
            + struct.pack('<i', 0)                  # compression method: none
            + digest
            + b'\0'                                 # not encrypted
            + struct.pack('<I', 0))                 # compression block size


def write(files):
    """`files` maps a path below the mount point to its bytes."""
    assert files, 'Nothing to pack.'
    data, index = bytearray(), bytearray()
    index += fstring(MOUNT_POINT) + struct.pack('<I', len(files))
    for path, body in files.items():
        digest = hashlib.sha1(body).digest()
        offset = len(data)
        data += entry(0, len(body), digest) + body
        index += fstring(path) + entry(offset, len(body), digest)
    footer = bytes(16) + b'\0' + struct.pack('<IIqq', MAGIC, VERSION, len(data), len(index))
    footer += hashlib.sha1(bytes(index)).digest()
    assert len(footer) == FOOTER_SIZE
    return bytes(data) + bytes(index) + footer


def read(archive):
    """Parse back what `write` produced, so a build can check its own output."""
    foot = archive[-FOOTER_SIZE:]
    assert foot[:17] == bytes(17), 'Unexpected key GUID or encrypted index.'
    magic, version, index_offset, index_size = struct.unpack_from('<IIqq', foot, 17)
    assert magic == MAGIC and version == VERSION, (hex(magic), version)
    index = archive[index_offset:index_offset + index_size]
    assert hashlib.sha1(index).digest() == foot[41:61], 'Index hash does not match.'

    def string(at):
        n = struct.unpack_from('<i', index, at)[0]
        return index[at + 4:at + 4 + n - 1].decode('utf-8'), at + 4 + n

    mount, at = string(0)
    count = struct.unpack_from('<I', index, at)[0]
    at += 4
    out = {}
    for _ in range(count):
        path, at = string(at)
        offset, size, usize, method = struct.unpack_from('<qqqi', index, at)
        digest = index[at + 28:at + 48]
        at += 53
        assert method == 0 and size == usize
        header = archive[offset:offset + 53]
        assert header == entry(0, size, digest), path
        body = archive[offset + 53:offset + 53 + size]
        assert hashlib.sha1(body).digest() == digest, path
        out[path] = body
    assert at == len(index)
    return mount, out
