"""Delta patch: we ship the difference, the player rebuilds the file from their own copy.

Used where a plugin is impossible and the translated file is too big, or belongs too
much to the publisher, to publish. The patch carries only what the translated file
changes vs the original; the rest is assembled from the file the player already
has on disk.

The format is simple and viewable in a plain editor: text header, blank line,
binary data. The header carries checksums of both sides, so applying refuses
another game version and can never silently corrupt a file.

The binary data is an op list packed with plain DEFLATE (no zlib header), which
every runtime has: .NET Framework, browsers, Python. So the applier in the package
(`<Name>-PL-<version>.exe`) needs no library. Unpacked:

    0x01 <length> <offset>          copy bytes from the original
    0x02 <length> <bytes>           insert new bytes
    0x00                            end

Format 3 adds two optional header fields. `sources` assembles the original from slices
of game files (`path@offset+length;...`), e.g. a font inside a multi-gigabyte pak;
checksums then cover the slice only. `mode create` means the result is a new file
(e.g. an extra pak), not a replacement: nothing is backed up and restoring the
original means deleting that file.

Numbers are LEB128 varints. The offset is signed (zigzag) from the end of the
previous copy, so for a file that merely shifted it is zero.
Apply implementations: here and `tools/applier/notgeesePatch.cs`; a format change
means changing both.

    python tools/patch.py release --original <file> --built <file> --readme <txt> ...
    python tools/patch.py apply   --game <game dir> --patch <patch>

`release` is one command per game: builds the patches (one per file, file
parameters can repeat), verifies them by re-applying and assembles the
package with patches, applier and readme.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
import zlib
from pathlib import Path

MAGIC = 'NOTGEESE-PATCH'
FORMAT = '2'
FORMAT_SOURCES = '3'
END, COPY, ADD = 0, 1, 2

# The original is indexed in blocks of this length. Shorter matches go to
# literals and DEFLATE squeezes them; longer blocks mean a smaller in-memory index.
BLOCK = 64
# A copy shorter than this does not pay for the op itself.
MIN_COPY = 24

ROOT = Path(__file__).resolve().parents[1]
APPLIER = ROOT / 'tools' / 'applier'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def zigzag(value: int) -> int:
    return value * 2 if value >= 0 else -value * 2 - 1


def common_length(a: memoryview, a_at: int, b: memoryview, b_at: int, limit: int) -> int:
    """How many bytes match from the given positions; compared in chunks in C."""
    length, step = 0, 4096
    while length < limit:
        size = min(step, limit - length)
        if a[a_at + length:a_at + length + size] == b[b_at + length:b_at + length + size]:
            length += size
            step = min(step * 2, 1 << 20)
        elif size <= 16:
            while length < limit and a[a_at + length] == b[b_at + length]:
                length += 1
            return length
        else:
            step = max(size // 4, 16)
    return length


def diff(source: bytes, target: bytes) -> bytes:
    """Op list that rebuilds `target` from `source`, not yet compressed."""
    src, dst = memoryview(source), memoryview(target)
    # The block index is built lazily: a file that merely shifted passes entirely
    # through the guess and never needs it.
    index: dict[int, int] = {}
    indexed = False

    def build_index() -> None:
        nonlocal indexed
        for position in range(len(source) - BLOCK, -1, -BLOCK):
            index[hash(src[position:position + BLOCK].tobytes())] = position
        indexed = True

    ops = bytearray()
    cursor = 0          # end of the last copy in the original
    pending = 0         # start of the unwritten literal in the output

    def emit_add(end: int) -> None:
        if end > pending:
            ops.append(ADD)
            ops.extend(varint(end - pending))
            ops.extend(dst[pending:end])

    def emit_copy(at: int, length: int) -> None:
        nonlocal cursor
        ops.append(COPY)
        ops.extend(varint(length))
        ops.extend(varint(zigzag(at - cursor)))
        cursor = at + length

    at, end = 0, len(target)
    while at < end:
        # First guess the file continues with the same offset as before;
        # that is most of a file that merely shifted.
        guess = cursor + (at - pending)
        if guess + MIN_COPY <= len(source) and at + MIN_COPY <= end:
            length = common_length(dst, at, src, guess, min(end - at, len(source) - guess))
            if length >= MIN_COPY:
                emit_add(at)
                emit_copy(guess, length)
                at += length
                pending = at
                continue

        found = None
        if at + BLOCK <= end:
            if not indexed:
                build_index()
            candidate = index.get(hash(dst[at:at + BLOCK].tobytes()))
            if candidate is not None and src[candidate:candidate + BLOCK] == dst[at:at + BLOCK]:
                found = candidate
        if found is None:
            at += 1
            continue

        # Extend the match backwards into the still-unwritten literal.
        back = 0
        while back < at - pending and back < found and src[found - back - 1] == dst[at - back - 1]:
            back += 1
        start, origin = at - back, found - back
        length = back + common_length(dst, at, src, found, min(end - at, len(source) - found))
        if length < MIN_COPY:
            at += 1
            continue
        emit_add(start)
        emit_copy(origin, length)
        at = start + length
        pending = at

    emit_add(end)
    ops.append(END)
    return bytes(ops)


def deflate(data: bytes) -> bytes:
    packer = zlib.compressobj(9, zlib.DEFLATED, -15, 9)
    return packer.compress(data) + packer.flush()


def inflate(data: bytes) -> bytes:
    return zlib.decompress(data, -15)


def read_varint(data: bytes, at: int) -> tuple[int, int]:
    value = shift = 0
    while True:
        byte = data[at]
        at += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, at


def run(source: bytes, ops: bytes, size: int) -> bytes:
    """Applies ops to the original. Mirror of `notgeesePatch.cs`."""
    out = bytearray()
    at = cursor = 0
    while True:
        op = ops[at]
        at += 1
        if op == END:
            break
        length, at = read_varint(ops, at)
        if op == COPY:
            delta, at = read_varint(ops, at)
            origin = cursor + ((delta >> 1) ^ -(delta & 1))
            assert 0 <= origin and origin + length <= len(source), 'patch reaches past the original'
            out += source[origin:origin + length]
            cursor = origin + length
        elif op == ADD:
            out += ops[at:at + length]
            at += length
        else:
            raise AssertionError(f'nieznana operacja {op}')
        assert len(out) <= size, 'patch produces an oversized file'
    return bytes(out)


def read_sources(game: Path, spec: str) -> bytes:
    """Original assembled from game file slices: `path@offset+length;...`."""
    out = bytearray()
    for part in spec.split(';'):
        relative, _, span = part.rpartition('@')
        offset, _, length = span.partition('+')
        with (game / relative).open('rb') as f:
            f.seek(int(offset))
            chunk = f.read(int(length))
        assert len(chunk) == int(length), f'{relative} is shorter than the patch expects'
        out += chunk
    return bytes(out)


def build(original: Path, built: Path, out: Path, game: str, relative: str,
          sources: str | None = None, create: bool = False) -> dict:
    """`sources` and `create`: see format 3 in the module doc. With `sources` the
    `original` parameter is the game directory the slices are read from."""
    source = read_sources(original, sources) if sources else original.read_bytes()
    target = built.read_bytes()
    ops = diff(source, target)
    payload = deflate(ops)

    extra = []
    if sources:
        extra.append(f'sources {sources}')
    if create:
        extra.append('mode create')
    header = '\n'.join([
        MAGIC,
        f'format {FORMAT_SOURCES if extra else FORMAT}',
        f'game {game}',
        f'file {relative}',
        *extra,
        f'source-sha256 {sha256(source)}',
        f'source-size {len(source)}',
        f'target-sha256 {sha256(target)}',
        f'target-size {len(target)}',
        '',
        '',
    ]).encode('utf-8')

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(header + payload)

    # Apply our own patch to the original and check it yields exactly the built file.
    restored = run(source, inflate(payload), len(target))
    assert restored == target, 'patch does not rebuild the built file'

    added = added_bytes(inflate(payload))
    return {
        'patch': str(out),
        'patch_bytes': out.stat().st_size,
        'added_bytes': added,
        'target_bytes': len(target),
        'share_of_file': round(out.stat().st_size / len(target) * 100, 3),
    }


def added_bytes(ops: bytes) -> int:
    """How many bytes the patch itself contributes (insert ops), before compression."""
    total, at = 0, 0
    while ops[at] != END:
        op = ops[at]
        length, at = read_varint(ops, at + 1)
        if op == COPY:
            _, at = read_varint(ops, at)
        else:
            total += length
            at += length
    return total


def read_header(raw: bytes) -> tuple[dict, bytes]:
    split = raw.find(b'\n\n')
    assert split > 0, 'not our patch'
    lines = raw[:split].decode('utf-8').splitlines()
    # Compatibility with patches distributed before the project rename.
    assert lines and lines[0] in (MAGIC, 'NIEGESI-PATCH'), 'not our patch'

    header = {}
    for line in lines[1:]:
        key, _, value = line.partition(' ')
        header[key] = value
    assert header.get('format') in (FORMAT, FORMAT_SOURCES), f'nieznana wersja formatu: {header.get("format")}'
    return header, raw[split + 2:]


def apply(game: Path, patch: Path, backup: Path | None) -> dict:
    header, payload = read_header(patch.read_bytes())
    target_file = game / header['file']
    create = header.get('mode') == 'create'
    if target_file.exists() and sha256(target_file.read_bytes()) == header['target-sha256']:
        return {'status': 'juz zainstalowane', 'file': str(target_file)}
    if 'sources' in header:
        source = read_sources(game, header['sources'])
    else:
        assert target_file.exists(), f'not found: {target_file}'
        source = target_file.read_bytes()
    digest = sha256(source)
    assert digest == header['source-sha256'], (
        'This game file is not the one the patch was made for.\n'
        f'  expected {header["source-sha256"]}\n'
        f'  got      {digest}\n'
        'If a translation is already installed, restore the original. '
        'If the game was updated, a new patch is needed.'
    )

    restored = run(source, inflate(payload), int(header['target-size']))
    assert sha256(restored) == header['target-sha256'], 'rebuilt file has a different checksum'

    if backup is not None and not create:
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(source)

    target_file.write_bytes(restored)
    return {
        'status': 'done',
        'file': str(target_file),
        'backup': str(backup) if backup else None,
        'bytes': len(restored),
    }


def applier() -> Path:
    """Player applier .exe; built from `tools/applier` when missing."""
    exe = APPLIER / 'bin' / 'notgeesePatch.exe'
    source = APPLIER / 'notgeesePatch.cs'
    icon = APPLIER / 'icon.ico'
    if not exe.exists() or exe.stat().st_mtime < max(source.stat().st_mtime, icon.stat().st_mtime):
        import subprocess
        subprocess.run([sys.executable, str(APPLIER / 'build.py')], check=True)
    return exe


def release(files: list[tuple], readme: Path, out_dir: Path,
            game: str, name: str, version: str) -> dict:
    """Patches plus a player-ready package: one command per game.

    `files` are triples (original, build output, path in the game dir), optionally
    with a fourth item: a dict of `build` args (`sources`, `create`). Each
    file gets its own patch; the applier applies every patch lying next to it.
    """
    patches, results = [], []
    stems = [Path(item[2]).stem for item in files]
    # Files with the same stem (e.g. .pak and .sig) are told apart by extension.
    label = (lambda p: p.name.replace('.', '-')) if len(set(stems)) < len(stems) else (lambda p: p.stem)
    for original, built, relative, *options in files:
        suffix = '' if len(files) == 1 else '-' + label(Path(relative))
        patch = out_dir / f'{name}-PL-{version}{suffix}.patch'
        results.append(build(original, built, patch, game, relative, **(options[0] if options else {})))
        patches.append(patch)
    exe = applier()

    package = out_dir / f'{name}-PL-{version}-latka.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for patch in patches:
            archive.write(patch, patch.name)
        # The packaged program carries the game name and version so the player knows what they run.
        archive.write(exe, f'{name}-PL-{version}.exe')
        archive.write(readme, 'READ-ME.txt')

    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        for patch in patches:
            assert archive.read(patch.name) == patch.read_bytes(), 'patch in the archive differs'

    return {'patches': results, 'package': str(package), 'package_bytes': package.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)

    make = commands.add_parser('build', help='build a patch from the original and the built file')
    make.add_argument('--original', type=Path, required=True)
    make.add_argument('--built', type=Path, required=True)
    make.add_argument('--out', type=Path, required=True)
    make.add_argument('--game-name', required=True)
    make.add_argument('--relative', required=True, help='file path inside the game dir')

    ship = commands.add_parser('release', help='build patches and assemble the player package')
    ship.add_argument('--original', type=Path, action='append', required=True,
                      help='repeatable; the n-th --original, --built and --relative form a pair')
    ship.add_argument('--built', type=Path, action='append', required=True)
    ship.add_argument('--readme', type=Path, required=True)
    ship.add_argument('--out-dir', type=Path, required=True)
    ship.add_argument('--game-name', required=True, help='game slug, e.g. skate-story')
    ship.add_argument('--relative', action='append', required=True,
                      help='file path inside the game dir')
    ship.add_argument('--package-name', required=True, help='package name, e.g. Skate-Story')
    ship.add_argument('--version', required=True)

    use = commands.add_parser('apply', help='apply a patch to your own copy of the game')
    use.add_argument('--game', type=Path, required=True, help='game dir')
    use.add_argument('--patch', type=Path, required=True)
    use.add_argument('--backup', type=Path, help='where to put the original before replacing')

    args = parser.parse_args()
    import json
    if args.command == 'build':
        result = build(args.original, args.built, args.out, args.game_name, args.relative)
    elif args.command == 'release':
        if not len(args.original) == len(args.built) == len(args.relative):
            parser.error('--original, --built and --relative must appear the same number of times')
        result = release(list(zip(args.original, args.built, args.relative)), args.readme,
                         args.out_dir, args.game_name, args.package_name, args.version)
    else:
        result = apply(args.game, args.patch, args.backup)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
