"""Verify the plugin's address discovery against an EXE without executing it."""
import argparse
import struct
from pathlib import Path
import pefile


def verify(path):
    pe = pefile.PE(str(path))
    data = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    sections = pe.sections

    def executable(rva):
        return any(s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize
                   and s.Characteristics & 0x20000000 for s in sections)

    def find(needle, code):
        result = []
        for s in sections:
            if not s.Characteristics & 0x40000000 or bool(s.Characteristics & 0x20000000) != code:
                continue
            start = s.VirtualAddress
            end = start + min(s.Misc_VirtualSize, s.SizeOfRawData)
            offset = data.find(needle, start, end)
            while offset >= 0:
                result.append(offset)
                offset = data.find(needle, offset + 1, end)
        return result

    def builtin(name):
        targets = set()
        for text in find(name.encode() + b'\0', False):
            for ref in find(struct.pack('<I', base + text), True):
                if data[ref - 6] == 0x68 and data[ref - 1] == 0x68 and data[ref + 4] == 0xE8:
                    target = struct.unpack_from('<I', data, ref - 5)[0] - base
                    if executable(target):
                        targets.add(target)
        assert len(targets) == 1, (name, targets)
        return targets.pop()

    def relative(call):
        assert data[call] == 0xE8
        target = call + 5 + struct.unpack_from('<i', data, call + 1)[0]
        assert executable(target)
        return target

    setter = builtin('draw_set_font')
    width = builtin('string_width')
    font = builtin('font_add_sprite_ext')
    getter = builtin('font_get_first')
    assert data[getter:getter + 12] == bytes.fromhex('8b442414566a005083ceffe8')
    assert data[getter + 16:getter + 18] == bytes.fromhex('50e8')
    assert executable(relative(getter + 17))
    for name in ['sprite_add', 'sprite_get_number', 'string_height']:
        builtin(name)
    assert data[setter:setter + 8] == bytes.fromhex('8b4424146a0050e8')
    assert data[setter + 12:setter + 14] == b'\x50\xe8'
    assert data[setter + 18:setter + 22] == bytes.fromhex('83c40cc3')
    assert data[width + 31:width + 39] == bytes.fromhex('6aff8bf06aff56e8')
    core = relative(width + 38)
    pattern = bytes.fromhex('8b4c24408b5424388d442418505152e8')
    sites = [i for i in range(core, core + 230) if data[i:i + len(pattern)] == pattern]
    assert len(sites) == 1
    splitter = relative(sites[0] + 15)
    assert data[splitter:splitter + 10] == bytes.fromhex('83ec0c568b74241485f6')
    assert data[font:font + 14] == bytes.fromhex('53568b74241c576a005683cbffe8')
    result = {'font_add_sprite_ext_rva': hex(font), 'set_font_core_rva': hex(relative(setter + 13)),
              'splitter_rva': hex(splitter), 'status': 'static ABI/discovery checks passed; no runtime test'}
    print(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    verify(parser.parse_args().exe)
