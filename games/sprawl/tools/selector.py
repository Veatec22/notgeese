"""Add Polish to SPRAWL's cooked PC locale map and build a native flag texture.

Pinned to the inspected UE4.27 assets; no Blueprint bytecode is rewritten.
Name hashes follow UAssetAPI CRCGenerator (validated against all source names).
"""
import hashlib
import struct
import zlib
from pathlib import Path

from asset import Asset

LOCALE = 'Sprawl/Content/StringTables/LocaleInfo_PC'
FLAG_SOURCE = 'Sprawl/Content/Textures/UI/Flags/ukraine'
FLAG = 'Sprawl/Content/Textures/UI/Flags/polska_'
SOURCE_HASHES = {
    LOCALE+'.uasset': '5ba3255b7f0d65b8669f7b6ba034b33f81b113ca1255cc58c2b36c6a38089289',
    LOCALE+'.uexp': '85754f7369704149c04f914cb473d6e0f5a59301c9e98bcdfa174e7efe1b4873',
    FLAG_SOURCE+'.uasset': '14c0fb88c8557bb9db6343dd035b7a3d76e352520bedf95c743ef333c0f64787',
    FLAG_SOURCE+'.uexp': '7a7a1535c76708373b7d47bb0da91916a16fe8bb7cd4c95c362099f6457e62cb',
}


def namehash(text):
    h = 0
    for byte in text.upper().encode('ascii'):
        crc = ((h ^ byte) & 255) << 24
        for _ in range(8):
            crc = ((crc << 1) ^ (0x04c11db7 if crc & 0x80000000 else 0)) & 0xffffffff
        h = (h >> 8) ^ crc
    return (h & 65535) | ((zlib.crc32(text.encode('utf-32-le')) & 65535) << 16)


def fs(text):
    value = text.encode('ascii') + b'\0'
    return struct.pack('<i', len(value)) + value


def put(data, at, value, fmt='I'):
    struct.pack_into('<' + fmt, data, at, value)


def locale_map(asset):
    h, b = bytearray(asset.h), bytearray(asset.b)
    assert len(h) == 2022 and len(b) == 1498
    assert len(asset.imports) == 25 and len(asset.exports) == 1
    assert struct.unpack_from('<I', b, 45)[0] == 11
    # Existing map entries are preserved byte for byte. Clone the English row,
    # giving the new localized name a separate text identity.
    row = bytearray(b[49:177])
    assert row[:7] == fs('en')
    row[:7] = fs('pl')
    old = b'86357CE542F929FE0C4EF1ADD0D84D32'
    row = row.replace(old, b'BC06B6F5834F43B39C98F858A2DA2270')
    row = row.replace(fs('English'), fs('Polski'))
    put(row, 23, 58)  # FriendlyName FText payload: one byte shorter.
    assert struct.unpack_from('<i', row, len(row)-12)[0] == -24
    put(row, len(row)-12, -27, 'i')
    b[49:49] = row
    put(b, 45, 12)
    put(b, 16, 1441 + len(row))

    new_names = ['/Game/Textures/UI/Flags/polska_', 'Polska_']
    names = b''.join(fs(n) + struct.pack('<I', namehash(n)) for n in new_names)
    old_import = 1158
    assert struct.unpack_from('<I', h, 69)[0] == old_import
    h[old_import:old_import] = names
    # Append imports so all existing package indices stay valid.
    imports = struct.pack('<QQiQ', 12, 33, 0, 41)
    imports += struct.pack('<QQiQ', 13, 37, -26, 42)
    export_at = 1858 + len(names)
    h[export_at:export_at] = imports
    delta = len(names) + len(imports)
    export_at += len(imports)
    # Add the flag to the export's serialization dependencies before the two
    # class dependencies, preserving the existing dependency order.
    h[-8:-8] = struct.pack('<i', -27)
    for at in [61, 73, 165, 189]:
        put(h, at, struct.unpack_from('<I', asset.h, at)[0] + delta)
    put(h, 69, old_import + len(names))
    put(h, 24, len(h))
    put(h, 41, 43)
    put(h, 117, 43)  # generation name count
    put(h, 65, 27)
    put(h, 185, 14)
    put(h, 169, len(h) + len(b) - 4, 'Q')
    put(h, export_at+28, len(b)-4, 'Q')
    put(h, export_at+36, len(h), 'Q')
    put(h, export_at+92, 12)
    return bytes(h), bytes(b)


def flag_texture(asset):
    h, b = bytearray(asset.h), bytearray(asset.b)
    assert len(h) == 922 and len(b) == 57954
    # Equal-length names keep all package offsets unchanged.
    for old, new in [('/Game/Textures/UI/Flags/ukraine', '/Game/Textures/UI/Flags/polska_'),
                     ('Ukraine', 'Polska_')]:
        source = fs(old) + struct.pack('<I', namehash(old))
        replacement = fs(new) + struct.pack('<I', namehash(new))
        assert len(source) == len(replacement) and h.count(source) == 1
        h = h.replace(source, replacement)
    # Native uncompressed 120x120 BGRA mip. Preserve the original icon alpha mask;
    # write the Polish bicolour directly in the game's texture format.
    assert b[282:294] == b'PF_B8G8R8A8\0'
    assert struct.unpack_from('<II', b, 266) == (120, 120)
    pixels_at = 326
    assert struct.unpack_from('<I', b, 310)[0] == 57600
    for y in range(120):
        colour = bytes((255, 255, 255)) if y < 60 else bytes((60, 20, 220))
        for x in range(120):
            at = pixels_at + (120*y+x)*4
            b[at:at+3] = colour
    # A distinct lighting GUID prevents identity reuse by derived texture data.
    b[106:122] = hashlib.md5(b'notgeese-sprawl-polish-flag').digest()
    return bytes(h), bytes(b)


def build_assets(source_dir, output_dir):
    for name, digest in SOURCE_HASHES.items():
        assert hashlib.sha256((Path(source_dir)/name).read_bytes()).hexdigest() == digest, name
    output_dir = Path(output_dir)
    files = {}
    for original, target, patch in [(LOCALE, LOCALE, locale_map), (FLAG_SOURCE, FLAG, flag_texture)]:
        source = Asset(Path(source_dir)/(original+'.uasset'))
        header, body = patch(source)
        for extension, data in [('.uasset', header), ('.uexp', body)]:
            path = target + extension
            out = output_dir/path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            files[path] = data
        checked = Asset(output_dir/(target+'.uasset'))
        assert checked.exports[0]['offset'] == len(header)
        assert checked.exports[0]['size'] == len(body)-4
        if target == LOCALE:
            assert checked.imports[-1] == ('/Script/Engine', 'Texture2D', -26, 'Polska_')
            assert checked.names[-2:] == ['/Game/Textures/UI/Flags/polska_', 'Polska_']
            assert body[49+127:49+127+len(source.b[49:1482])] == source.b[49:1482]
    return files
