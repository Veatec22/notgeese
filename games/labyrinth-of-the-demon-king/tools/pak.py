"""Write a minimal Unreal .pak - enough to deliver files a game does not already have.

A packaged build reads its content out of .pak archives and does not go looking
on disk, which is why dropping a loose .locres into the game folder does nothing:
the file is there, and nothing ever enumerates it. Files have to arrive in a pak.

This writes version 11, the same version SPRAWL's own archive uses, with every
entry stored uncompressed - so nothing here needs Oodle, which the game links
statically and ships no library for.

    [per file] 53-byte entry header, then the bytes
    [full directory index]  directory -> filename -> offset into the encoded entries
    [primary index]  mount point, count, seed, the two index descriptors, encoded entries
    [footer]  magic, version, index offset and size, SHA-1 of the index, compression names

The archive declares no path-hash index. Unreal accepts that and falls back to
the directory index, which spares us guessing at another of its hash functions.

Nothing here rewrites the game's own pak: a second .pak in Content/Paks is
mounted alongside it, and these files are new rather than replacements.
"""
import hashlib
import struct

MAGIC = 0x5A6F12E1
VERSION = 11
MOUNT_POINT = '../../../'
FOOTER_SIZE = 221
COMPRESSION_SLOTS = 5
NAME_LENGTH = 32


def fstring(value):
    body = value.encode('utf-8') + b'\0'
    return struct.pack('<i', len(body)) + body


def entry_header(offset, size, digest):
    """FPakEntry as it is repeated in front of the data. Unreal writes offset 0 here."""
    return (struct.pack('<qqq', 0, size, size)      # offset, size, uncompressed size
            + struct.pack('<i', 0)                  # compression method: none
            + digest
            + b'\0'                                 # flags
            + struct.pack('<I', 0))                 # compression block size


def encode_entry(offset, size):
    """The packed form the index stores: everything 32-bit safe, uncompressed, no blocks."""
    assert offset < 1 << 32 and size < 1 << 32, 'This writer only handles small archives.'
    flags = 0x80000000 | 0x40000000 | 0x20000000    # offset, uncompressed size and size are 32-bit
    return struct.pack('<III', flags, offset, size)


def write(files, seed=0):
    """`files` maps a path below the mount point to its bytes."""
    assert files, 'Nothing to pack.'

    data, encoded, placed = bytearray(), bytearray(), {}
    for path, body in files.items():
        offset = len(data)
        digest = hashlib.sha1(body).digest()
        data += entry_header(offset, len(body), digest) + body
        placed[path] = len(encoded)
        encoded += encode_entry(offset, len(body))

    directories = {}
    for path in files:
        directory, _, name = path.rpartition('/')
        directories.setdefault(directory + '/', {})[name] = placed[path]
        # UE culture discovery traverses parents, including empty directories.
        parts = directory.split('/')
        directories.setdefault('', {})
        for depth in range(1, len(parts)):
            directories.setdefault('/'.join(parts[:depth]) + '/', {})

    listing = bytearray(struct.pack('<I', len(directories)))
    for directory, names in directories.items():
        listing += fstring(directory)
        listing += struct.pack('<I', len(names))
        for name, at in names.items():
            listing += fstring(name)
            listing += struct.pack('<I', at)

    listing_offset = len(data)
    index_offset = listing_offset + len(listing)

    index = bytearray()
    index += fstring(MOUNT_POINT)
    index += struct.pack('<I', len(files))
    index += struct.pack('<Q', seed)
    index += struct.pack('<I', 0)                   # no path hash index
    index += struct.pack('<I', 1)                   # a full directory index follows
    index += struct.pack('<QQ', listing_offset, len(listing))
    index += hashlib.sha1(bytes(listing)).digest()
    index += struct.pack('<I', len(encoded))
    index += encoded
    index += struct.pack('<i', 0)                   # no entries outside the encoded array

    footer = bytearray(bytes(16) + b'\0')                       # the index is not encrypted
    footer += struct.pack('<II', MAGIC, VERSION)
    footer += struct.pack('<qq', index_offset, len(index))
    footer += hashlib.sha1(bytes(index)).digest()
    footer += b'\0' * (NAME_LENGTH * COMPRESSION_SLOTS)
    assert len(footer) == FOOTER_SIZE, len(footer)

    return bytes(data) + bytes(listing) + bytes(index) + bytes(footer)


def read(archive):
    """Parse back what `write` produced, so a build can check its own output."""
    assert archive[-FOOTER_SIZE:-FOOTER_SIZE + 16] == bytes(16), 'Unexpected encryption key GUID.'
    assert archive[-FOOTER_SIZE + 16] == 0, 'Index is marked encrypted.'
    magic, version = struct.unpack_from('<II', archive, len(archive) - FOOTER_SIZE + 17)
    assert magic == MAGIC and version == VERSION, (hex(magic), version)
    index_offset, index_size = struct.unpack_from('<qq', archive, len(archive) - FOOTER_SIZE + 25)
    stored = archive[len(archive) - FOOTER_SIZE + 41:len(archive) - FOOTER_SIZE + 61]
    index = archive[index_offset:index_offset + index_size]
    assert hashlib.sha1(index).digest() == stored, 'Index hash does not match.'

    def read_string(data, at):
        length = struct.unpack_from('<i', data, at)[0]
        return data[at + 4:at + 4 + length - 1].decode('utf-8'), at + 4 + length

    mount, at = read_string(index, 0)
    count = struct.unpack_from('<I', index, at)[0]; at += 4 + 8 + 4
    assert struct.unpack_from('<I', index, at)[0] == 1, 'No directory index.'
    at += 4
    listing_offset, listing_size = struct.unpack_from('<QQ', index, at); at += 16
    listing_hash = index[at:at + 20]; at += 20
    encoded_size = struct.unpack_from('<I', index, at)[0]; at += 4
    encoded = index[at:at + encoded_size]

    listing = archive[listing_offset:listing_offset + listing_size]
    assert hashlib.sha1(listing).digest() == listing_hash, 'Directory index hash does not match.'

    out, at = {}, 0
    directories = struct.unpack_from('<I', listing, at)[0]; at += 4
    for _ in range(directories):
        directory, at = read_string(listing, at)
        names = struct.unpack_from('<I', listing, at)[0]; at += 4
        for _ in range(names):
            name, at = read_string(listing, at)
            where = struct.unpack_from('<I', listing, at)[0]; at += 4
            _, offset, size = struct.unpack_from('<III', encoded, where)
            body = archive[offset + 53:offset + 53 + size]
            header = archive[offset:offset + 53]
            assert struct.unpack_from('<q', header, 8)[0] == size
            assert header[28:48] == hashlib.sha1(body).digest(), name
            out[directory.lstrip('/') + name] = body
    assert len(out) == count, (len(out), count)
    return mount, out
