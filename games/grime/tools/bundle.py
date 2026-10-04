"""Keep GRIME's original UnityFS blocks while appending a replacement I2 object."""
import struct

from UnityPy.helpers.CompressionHelper import compress_lz4, decompress_lz4
from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter


def replace_source(bundle, obj, patched):
    reader = EndianBinaryReader(bundle, endian='>')
    if reader.read_string_to_null() != 'UnityFS' or reader.read_int() != 8:
        raise ValueError('Unsupported bundle header')
    reader.read_string_to_null()
    reader.read_string_to_null()
    size_position = reader.Position
    if reader.read_long() != len(bundle):
        raise ValueError('Bundle size mismatch')
    compressed_size, raw_size, flags = reader.read_u_int(), reader.read_u_int(), reader.read_u_int()
    if flags != 579:
        raise ValueError(f'Unsupported bundle flags: {flags}')
    reader.align_stream(16)
    info = EndianBinaryReader(decompress_lz4(reader.read_bytes(compressed_size), raw_size), endian='>')
    info.read_bytes(16)
    blocks = [(info.read_u_int(), info.read_u_int(), info.read_u_short())
              for _ in range(info.read_int())]
    nodes = [[info.read_long(), info.read_long(), info.read_u_int(), info.read_string_to_null()]
             for _ in range(info.read_int())]
    reader.align_stream(16)
    data_position = reader.Position
    file = obj.assets_file
    if file.header.version != 22 or file.header.endian != '<':
        raise ValueError('Unsupported serialized file')
    node = next(node for node in nodes if node[3] == file.name)
    old_file = file.reader.bytes
    if node[1] != len(old_file):
        raise ValueError('Serialized file size mismatch')
    # Relocate only the source object; leave old bytes unreferenced in the local built file.
    # This avoids re-encoding publisher asset blocks in the delta.
    padding = bytes(-len(old_file) % 8)
    appended = padding + patched
    append_at = node[0] + node[1]
    pattern = struct.pack('<qqIi', obj.path_id, obj.byte_start - file.header.data_offset,
                          obj.byte_size, obj.type_id)
    metadata = old_file[:file.header.data_offset]
    if metadata.count(pattern) != 1:
        raise ValueError('Cannot uniquely locate I2 object metadata')
    entry = metadata.index(pattern)
    edits = {
        node[0] + 24: struct.pack('>q', len(old_file) + len(appended)),
        node[0] + entry + 8: struct.pack('<qI', len(old_file) + len(padding) - file.header.data_offset,
                                       len(patched)),
    }
    for other in nodes:
        if other is node:
            other[1] += len(appended)
        elif other[0] >= append_at:
            other[0] += len(appended)
    output_blocks, output_data = [], []

    def encode(data):
        for start in range(0, len(data), 131072):
            chunk = data[start:start + 131072]
            compressed = compress_lz4(chunk)
            output_blocks.append((len(chunk), len(compressed), 3))
            output_data.append(compressed)

    raw_offset = 0
    inserted = False
    applied = set()
    for length, compressed_length, block_flags in blocks:
        compressed = bundle[data_position:data_position + compressed_length]
        data_position += compressed_length
        end = raw_offset + length
        touching = {pos: value for pos, value in edits.items() if raw_offset <= pos < end}
        insertion = not inserted and raw_offset <= append_at <= end
        if touching or insertion:
            if block_flags & 63 != 3:
                raise ValueError('Unexpected compression in a modified block')
            data = bytearray(decompress_lz4(compressed, length))
            for pos, value in touching.items():
                local = pos - raw_offset
                if local + len(value) > length:
                    raise ValueError('Metadata edit crosses a block boundary')
                data[local:local + len(value)] = value
                applied.add(pos)
            if insertion:
                local = append_at - raw_offset
                encode(bytes(data[:local]))
                encode(appended)
                encode(bytes(data[local:]))
                inserted = True
            else:
                encode(bytes(data))
        else:
            output_blocks.append((length, compressed_length, block_flags))
            output_data.append(compressed)
        raw_offset = end
    if not inserted or applied != edits.keys() or data_position != len(bundle):
        raise ValueError('Bundle rewrite did not consume the expected data')
    info_writer = EndianBinaryWriter(b'\0' * 16, endian='>')
    info_writer.write_int(len(output_blocks))
    for length, compressed_length, block_flags in output_blocks:
        info_writer.write_u_int(length)
        info_writer.write_u_int(compressed_length)
        info_writer.write_u_short(block_flags)
    info_writer.write_int(len(nodes))
    for offset, length, node_flags, name in nodes:
        info_writer.write_long(offset)
        info_writer.write_long(length)
        info_writer.write_u_int(node_flags)
        info_writer.write_string_to_null(name)
    info_bytes = info_writer.bytes
    compressed_info = compress_lz4(info_bytes)
    writer = EndianBinaryWriter(bundle[:size_position], endian='>')
    writer.write_long(0)
    writer.write_u_int(len(compressed_info))
    writer.write_u_int(len(info_bytes))
    writer.write_u_int(flags)
    writer.align_stream(16)
    writer.write_bytes(compressed_info)
    writer.align_stream(16)
    for data in output_data:
        writer.write_bytes(data)
    length = writer.Position
    writer.Position = size_position
    writer.write_long(length)
    return writer.bytes
