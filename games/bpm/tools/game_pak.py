"""Read BPM's UE pak archives (version 11, AES-encrypted index, Zlib/Oodle entries).

The AES key is read out of the game's own executable (`find_key.py`), never stored
in the repository - it lives in work/aes.key after the first run.
"""
import hashlib
import struct
import zlib
from pathlib import Path

from Crypto.Cipher import AES

MAGIC = 0x5A6F12E1
FOOTER = 221


class Reader:
    def __init__(self, data):
        self.data, self.at = data, 0

    def get(self, fmt):
        v = struct.unpack_from('<' + fmt, self.data, self.at)
        self.at += struct.calcsize('<' + fmt)
        return v[0] if len(v) == 1 else v

    def string(self):
        n = self.get('i')
        size = abs(n) * (2 if n < 0 else 1)
        b = self.data[self.at:self.at + size]
        self.at += size
        return b.decode('utf-16-le' if n < 0 else 'utf-8').rstrip('\0')


class GamePak:
    def __init__(self, path, key):
        self.path, self.key = Path(path), key
        self.aes = AES.new(key, AES.MODE_ECB)
        with self.path.open('rb') as f:
            f.seek(-FOOTER, 2)
            foot = f.read()
            self.encrypted_index = foot[16]
            magic, version, off, size = struct.unpack_from('<IIqq', foot, 17)
            assert magic == MAGIC and version == 11, (magic, version)
            self.methods = [foot[61 + 32 * i:93 + 32 * i].rstrip(b'\0').decode() for i in range(5)]
            f.seek(off)
            data = self.decrypt(f.read(size)) if self.encrypted_index else f.read(size)
            r = Reader(data)
            self.mount = r.string()
            assert self.mount.startswith('../'), 'Wrong AES key.'
            self.count = r.get('I')
            r.get('Q')
            if r.get('I'):
                r.at += 8 + 8 + 20
            assert r.get('I')
            do, ds = r.get('qq')
            r.at += 20
            n = r.get('I')
            self.encoded = r.data[r.at:r.at + n]
            f.seek(do)
            directory = f.read(ds)
            if self.encrypted_index:
                directory = self.decrypt(directory)
        r = Reader(directory)
        self.files = {}
        for _ in range(r.get('I')):
            d = r.string()
            for _ in range(r.get('I')):
                name = r.string()
                self.files[(self.mount + d + name).replace('../../../', '')] = r.get('i')

    def decrypt(self, data):
        return self.aes.decrypt(data)

    def entry(self, path):
        r = Reader(self.encoded)
        r.at = self.files[path]
        flags = r.get('I')
        blocksize = r.get('I') if flags & 63 == 63 else (flags & 63) << 11
        blocks = (flags >> 6) & 0xFFFF
        encrypted = bool(flags & (1 << 22))
        method = (flags >> 23) & 63
        off = r.get('I' if flags & 0x80000000 else 'Q')
        usize = r.get('I' if flags & 0x40000000 else 'Q')
        size = r.get('I' if flags & 0x20000000 else 'Q') if method else usize
        return dict(offset=off, usize=usize, size=size, method=method, encrypted=encrypted,
                    blocks=blocks, blocksize=blocksize)

    def extract(self, path):
        e = self.entry(path)
        with self.path.open('rb') as f:
            f.seek(e['offset'])
            header = f.read(53)
            if not e['method']:
                size = e['size']
                raw = f.read((size + 15) // 16 * 16 if e['encrypted'] else size)
                return (self.decrypt(raw) if e['encrypted'] else raw)[:size]
            f.seek(e['offset'] + 8 + 8 + 8 + 4 + 20)
            count = struct.unpack('<I', f.read(4))[0]
            spans = [struct.unpack('<qq', f.read(16)) for _ in range(count)]
            out = bytearray()
            name = self.methods[e['method'] - 1]
            for start, end in spans:
                f.seek(e['offset'] + start)
                n = end - start
                src = f.read((n + 15) // 16 * 16 if e['encrypted'] else n)
                if e['encrypted']:
                    src = self.decrypt(src)
                src = src[:n]
                if name == 'Zlib':
                    out += zlib.decompress(src)
                else:
                    raise ValueError('Compression %s not supported.' % name)
            assert len(out) == e['usize']
            return bytes(out)


def load_key(root):
    return bytes.fromhex((Path(root) / 'work' / 'aes.key').read_text().strip())
