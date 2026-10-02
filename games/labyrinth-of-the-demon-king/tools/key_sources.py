"""Find which game assets define each locres key (for translations/structure.yaml).

    key_sources.py --game <game folder>

Reads the uncompressed IoStore container pakchunk0 read-only, searches every .uasset/.umap chunk
for the review file's keys and writes work/key-sources.json: {key: [[asset path, offset], ...]}.
The offset of a key inside a DataTable follows row order (used for dialogue sequences).
"""
import argparse
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = 'Shinigami/Content/Paks/pakchunk0-WindowsNoEditor'


def read_string(data, at):
    size = struct.unpack_from('<i', data, at)[0]
    assert 0 < size < 10000
    return data[at + 4:at + 4 + size - 1].decode('utf-8'), at + 4 + size


def directory(data):
    """Return {path: chunk index}, chunk (offset, length) list, block table offset, block size."""
    assert data[:16] == b'-==--==--==--==-' and data[16] == 3
    header, count, block_count, _, _, _, block_size, dirsize, _ = struct.unpack_from('<9I', data, 20)
    chunks_at = header + count * 12
    chunks = [(int.from_bytes(data[chunks_at + i * 10:chunks_at + i * 10 + 5], 'big'),
               int.from_bytes(data[chunks_at + i * 10 + 5:chunks_at + i * 10 + 10], 'big')) for i in range(count)]
    blocks_at = chunks_at + count * 10
    at = blocks_at + block_count * 12
    end = at + dirsize
    mount, at = read_string(data, at)
    n = struct.unpack_from('<I', data, at)[0]; at += 4
    dirs = [struct.unpack_from('<4I', data, at + i * 16) for i in range(n)]; at += n * 16
    n = struct.unpack_from('<I', data, at)[0]; at += 4
    files = [struct.unpack_from('<3I', data, at + i * 12) for i in range(n)]; at += n * 12
    n = struct.unpack_from('<I', data, at)[0]; at += 4
    names = []
    for _ in range(n):
        s, at = read_string(data, at)
        names.append(s)
    assert at == end
    paths = {}

    def walk(index, prefix):
        _, child, _, file = dirs[index]
        while child != 0xffffffff:
            walk(child, prefix + names[dirs[child][0]] + '/')
            child = dirs[child][2]
        while file != 0xffffffff:
            name, nxt, user = files[file]
            paths[prefix + names[name]] = user
            file = nxt
    walk(0, '')
    return paths, chunks, blocks_at, block_size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', required=True)
    base = Path(parser.parse_args().game) / CONTAINER
    toc = base.with_suffix('.utoc').read_bytes()
    paths, chunks, blocks_at, block_size = directory(toc)
    entries = json.load(open(ROOT / 'translations/en-pl-review.json', encoding='utf-8'))
    keys = {e['key'].encode('ascii'): e['key'] for e in entries}
    found = {}
    with base.with_suffix('.ucas').open('rb') as cas:
        for path, index in paths.items():
            if not path.startswith('Shinigami/') or not path.endswith(('.uasset', '.umap')):
                continue
            offset, length = chunks[index]
            out = bytearray()
            for block in range(offset // block_size, (offset + length - 1) // block_size + 1):
                b = toc[blocks_at + 12 * block:blocks_at + 12 * (block + 1)]
                physical = int.from_bytes(b[:5], 'little')
                size = int.from_bytes(b[5:8], 'little')
                assert b[11] == 0 and size == int.from_bytes(b[8:11], 'little')  # uncompressed
                cas.seek(physical)
                raw = cas.read(size)
                start = max(0, offset - block * block_size)
                out += raw[start:min(size, offset + length - block * block_size)]
            data = bytes(out)
            for k, key in keys.items():
                at = data.find(k)
                if at >= 0:
                    found.setdefault(key, []).append([path.removeprefix('Shinigami/Content/'), at])
    (ROOT / 'work').mkdir(exist_ok=True)
    (ROOT / 'work/key-sources.json').write_text(json.dumps(found, indent=1, sort_keys=True), encoding='utf-8')
    print(json.dumps({'keys': len(keys), 'located': len(found)}))


if __name__ == '__main__':
    main()
