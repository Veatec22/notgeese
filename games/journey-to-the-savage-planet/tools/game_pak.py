"""Read the game's UE4 pak (v7, unencrypted index, zlib blocks) and extract entries."""
import struct, hashlib, zlib
from pathlib import Path

MAGIC = 0x5A6F12E1


class Reader:
    def __init__(self, data):
        self.data = data
        self.at = 0

    def get(self, fmt):
        v = struct.unpack_from('<' + fmt, self.data, self.at)
        self.at += struct.calcsize('<' + fmt)
        return v[0] if len(v) == 1 else v

    def string(self):
        n = self.get('i')
        b = self.data[self.at:self.at + abs(n) * (2 if n < 0 else 1)]
        self.at += len(b)
        return b.decode('utf-16-le' if n < 0 else 'utf-8').rstrip('\0')


class GamePak:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('rb') as f:
            f.seek(-61, 2)
            foot = f.read(61)
            encrypted = foot[16]
            magic, version, off, size = struct.unpack_from('<IIqq', foot, 17)
            assert magic == MAGIC and version == 7 and not encrypted, (hex(magic), version, encrypted)
            f.seek(off)
            index = f.read(size)
            assert hashlib.sha1(index).digest() == foot[41:61]
        r = Reader(index)
        self.mount = r.string()
        self.entries = {}
        for _ in range(r.get('I')):
            name = r.string()
            offset, size, usize, method = r.get('qqqi')
            r.at += 20
            blocks = [r.get('qq') for _ in range(r.get('I'))] if method else []
            enc = r.get('B')
            block_size = r.get('I')
            assert not enc
            self.entries[name] = (offset, size, usize, method, blocks, block_size)
        assert r.at == len(index)

    def header_size(self, name):
        """Bytes of the in-data entry header that precedes the payload."""
        method, blocks = self.entries[name][3], self.entries[name][4]
        return 53 + (4 + 16 * len(blocks) if method else 0)

    def extract(self, name):
        offset, size, usize, method, blocks, _ = self.entries[name]
        with self.path.open('rb') as f:
            if not method:
                f.seek(offset + self.header_size(name))
                data = f.read(size)
            else:
                assert method == 1, method
                out = bytearray()
                for start, end in blocks:
                    f.seek(offset + start)
                    out += zlib.decompress(f.read(end - start))
                data = bytes(out)
        assert len(data) == usize, (name, len(data), usize)
        return data
