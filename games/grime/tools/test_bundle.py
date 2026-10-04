"""Synthetic UnityFS coverage for source relocation and untouched resource streams."""
import struct
from types import SimpleNamespace
import unittest

from UnityPy.helpers.CompressionHelper import compress_lz4, decompress_lz4
from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter
from bundle import replace_source


def make_bundle(data, nodes):
    chunks = [data[i:i + 131072] for i in range(0, len(data), 131072)]
    compressed = [compress_lz4(chunk) for chunk in chunks]
    info = EndianBinaryWriter(b'\0' * 16, endian='>')
    info.write_int(len(chunks))
    for chunk, block in zip(chunks, compressed):
        info.write_u_int(len(chunk))
        info.write_u_int(len(block))
        info.write_u_short(3)
    info.write_int(len(nodes))
    for offset, size, name in nodes:
        info.write_long(offset)
        info.write_long(size)
        info.write_u_int(4)
        info.write_string_to_null(name)
    packed = compress_lz4(info.bytes)
    writer = EndianBinaryWriter(endian='>')
    writer.write_string_to_null('UnityFS')
    writer.write_int(8)
    writer.write_string_to_null('5.x.x')
    writer.write_string_to_null('2021.3.30f1')
    size_pos = writer.Position
    writer.write_long(0)
    writer.write_u_int(len(packed))
    writer.write_u_int(len(info.bytes))
    writer.write_u_int(579)
    writer.align_stream(16)
    writer.write_bytes(packed)
    writer.align_stream(16)
    for block in compressed:
        writer.write_bytes(block)
    size = writer.Position
    writer.Position = size_pos
    writer.write_long(size)
    return writer.bytes


def unpack(bundle):
    reader = EndianBinaryReader(bundle, endian='>')
    reader.read_string_to_null()
    reader.read_int()
    reader.read_string_to_null()
    reader.read_string_to_null()
    assert reader.read_long() == len(bundle)
    compressed_size, raw_size = reader.read_u_int(), reader.read_u_int()
    reader.read_u_int()
    reader.align_stream(16)
    info = EndianBinaryReader(decompress_lz4(reader.read_bytes(compressed_size), raw_size), endian='>')
    info.read_bytes(16)
    blocks = [(info.read_u_int(), info.read_u_int(), info.read_u_short())
              for _ in range(info.read_int())]
    nodes = [(info.read_long(), info.read_long(), info.read_u_int(), info.read_string_to_null())
             for _ in range(info.read_int())]
    reader.align_stream(16)
    packed = [reader.read_bytes(size) for _, size, _ in blocks]
    return b''.join(decompress_lz4(block, size) for block, (size, _, _) in zip(packed, blocks)), nodes, packed


class BundleTests(unittest.TestCase):
    def fixture(self, file_size=300003):
        original = bytearray(bytes(range(256)) * (file_size // 256 + 1))[:file_size]
        struct.pack_into('>q', original, 24, file_size)
        header = SimpleNamespace(version=22, endian='<', data_offset=4096)
        file = SimpleNamespace(name='resources.assets', header=header,
                               reader=SimpleNamespace(bytes=bytes(original)))
        obj = SimpleNamespace(assets_file=file, path_id=190, byte_start=8192,
                              byte_size=64, type_id=10)
        struct.pack_into('<qqIi', original, 80, 190, 8192 - 4096, 64, 10)
        file.reader.bytes = bytes(original)
        resources = b'external texture bytes' * 18000
        return bytes(original), resources, obj

    def test_relocation_preserves_every_other_byte_and_resource_node(self):
        original, resources, obj = self.fixture()
        bundle = make_bundle(original + resources,
                             [(0, len(original), 'resources.assets'),
                              (len(original), len(resources), 'resources.assets.resS')])
        replacement = b'new I2 source' * 14000  # Larger than one compression block.
        built = replace_source(bundle, obj, replacement)
        data, nodes, blocks = unpack(built)
        padding = bytes(-len(original) % 8)
        expected = bytearray(original)
        struct.pack_into('>q', expected, 24, len(original) + len(padding) + len(replacement))
        struct.pack_into('<qI', expected, 88, len(original) + len(padding) - 4096, len(replacement))
        self.assertEqual(data, bytes(expected) + padding + replacement + resources)
        self.assertEqual(nodes[0][1], len(original) + len(padding) + len(replacement))
        self.assertEqual(nodes[1][0], nodes[0][1])
        old_blocks = unpack(bundle)[2]
        self.assertIn(old_blocks[1], blocks)  # Unmodified middle block is byte-identical.

    def test_refuses_ambiguous_object_metadata(self):
        original, resources, obj = self.fixture()
        duplicate = bytearray(original)
        duplicate[160:184] = duplicate[80:104]
        obj.assets_file.reader.bytes = bytes(duplicate)
        bundle = make_bundle(bytes(duplicate) + resources,
                             [(0, len(duplicate), 'resources.assets'),
                              (len(duplicate), len(resources), 'resources.assets.resS')])
        with self.assertRaisesRegex(ValueError, 'uniquely'):
            replace_source(bundle, obj, b'new source')


if __name__ == '__main__':
    unittest.main()
