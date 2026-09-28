"""Empty IoStore v8 companion for an overlay .pak (Holy Shoot, UE 5.7).

The 0.1.2 in-game probe showed the engine mounting no file from a .pak that has
no matching .utoc/.ucas: FileExists saw en/Game.locres from the game but not our
pl/Game.locres. UE5 IoStore games mount paks through their container, so the
overlay ships an empty one: a single container-header chunk with zero packages.
No game data is copied. Layout mirrors the game's own PVD-Windows.utoc
(FIoStoreTocHeader v8, 24-byte entry meta with a BLAKE3 hash prefix) and its
container header (FIoContainerHeader version 5), both checked in work/.
"""
import struct

import blake3

MAGIC = b'-==--==--==--==-'
TOC_VERSION = 8          # PerfectHashWithOverflow, as in PVD-Windows.utoc
HEADER_SIZE = 144
BLOCK_SIZE = 0x10000
CONTAINER_HEADER_VERSION = 5
CONTAINER_HEADER_TYPE = 6
NO_PARTITION_LIMIT = 0xFFFFFFFFFFFFFFFF


def container_header(container_id):
    """FIoContainerHeader v5 with no packages, redirects or soft references."""
    body = struct.pack('<IIQ', 0x496F436E, CONTAINER_HEADER_VERSION, container_id)
    body += struct.pack('<5I', 0, 0, 0, 0, 0)   # package ids, store entries, optional x2, name batch
    body += struct.pack('<2I', 0, 0)            # localized packages, package redirects
    # Soft package references: offset and size of their block, then an empty array.
    offset = len(body) + 16
    body += struct.pack('<qq', offset, 4) + struct.pack('<I', 0)
    return body


def build(container_id):
    """Return (utoc, ucas) bytes for an uncompressed, unindexed container."""
    chunk = container_header(container_id)
    chunk_id = struct.pack('<QHBB', container_id, 0, 0, CONTAINER_HEADER_TYPE)
    blocks = []
    for start in range(0, len(chunk), BLOCK_SIZE):
        size = min(BLOCK_SIZE, len(chunk) - start)
        blocks.append(start.to_bytes(5, 'little') + size.to_bytes(3, 'little')
                      + size.to_bytes(3, 'little') + b'\0')     # method 0 = none
    header = bytearray(HEADER_SIZE)
    header[:16] = MAGIC
    struct.pack_into('<B3xIIIIIIIII', header, 16, TOC_VERSION, HEADER_SIZE, 1, len(blocks), 12,
                     0, 32, BLOCK_SIZE, 0, 1)
    struct.pack_into('<Q', header, 56, container_id)
    # 64..79 encryption key guid (none), 80 flags (none), 84 perfect hash seeds (none)
    struct.pack_into('<Q', header, 88, NO_PARTITION_LIMIT)
    offset_length = (0).to_bytes(5, 'big') + len(chunk).to_bytes(5, 'big')
    meta = blake3.blake3(chunk).digest()[:20] + bytes(4)
    utoc = bytes(header) + chunk_id + offset_length + b''.join(blocks) + meta
    return utoc, chunk


def parse(utoc, ucas):
    """Independent read-back used by the build to verify what it wrote."""
    assert utoc[:16] == MAGIC and utoc[16] == TOC_VERSION
    size, entries, block_count, block_entry, methods, _, block_size, dir_size, parts = \
        struct.unpack_from('<9I', utoc, 20)
    assert (size, entries, block_entry, methods, dir_size, parts) == (HEADER_SIZE, 1, 12, 0, 0, 1)
    container_id = struct.unpack_from('<Q', utoc, 56)[0]
    assert utoc[80] == 0 and struct.unpack_from('<I', utoc, 84)[0] == 0
    at = HEADER_SIZE
    chunk_id = utoc[at:at + 12]
    assert struct.unpack('<QHBB', chunk_id) == (container_id, 0, 0, CONTAINER_HEADER_TYPE)
    at += 12
    offset, length = int.from_bytes(utoc[at:at + 5], 'big'), int.from_bytes(utoc[at + 5:at + 10], 'big')
    at += 10 + 12 * block_count
    data = ucas[offset:offset + length]
    assert len(data) == length and utoc[at:at + 20] == blake3.blake3(data).digest()[:20]
    assert at + 24 == len(utoc)
    magic, version, header_id = struct.unpack_from('<IIQ', data, 0)
    assert (magic, version, header_id) == (0x496F436E, CONTAINER_HEADER_VERSION, container_id)
    return container_id
