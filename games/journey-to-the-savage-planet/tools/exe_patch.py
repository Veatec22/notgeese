"""Add Polish as a 12th language to the game's culture list (GOG exe, in memory; the build diffs it).

The list behind the Subtitles Language selector is a global TArray<FTowersCulture> built by one
static initializer (RVA 0xF3FF0): eleven unrolled {Code, NativeDisplayName} FString pairs,
`Num = 11`, `ResizeForCopy(11)`, a loop copying 11 pairs, then cleanup. Three changes:

1. `mov dword [Num], 11` → 12 and `ResizeForCopy(11)` → 12: the array gets a 12th slot.
   The copy loop keeps its own count (11), so slot 12 is left for us.
2. The instruction right after the loop jumps to a cave: 253 bytes of int3 padding between
   functions (RVA 0x9C703..0x9C800, no .pdata entry, never executed).
3. Cave code fills slot 12 with {"pl", "Polski"}: both strings allocated with FMemory::Malloc
   (the array's destructor frees them at exit like the others), then replays the displaced
   instruction and jumps back.

Only RIP-relative addressing and rel32 calls: no relocations needed. Everything is checked
against the expected original bytes; any mismatch refuses.
"""
import struct

INIT_NUM = 0xF442A          # c7 05 <rel32> 0b 00 00 00   mov dword [array.Num], 11
INIT_RESIZE = 0xF4437       # 41 8d 55 0b                 lea edx, [r13+11]
LOAD_DATA = 0xF444B         # 48 8b 1d <rel32>            mov rbx, [array.Data]
AFTER_LOOP = 0xF44F5        # 4c 8d 0d <rel32>            lea r9, [destructor]
RESUME = AFTER_LOOP + 7
CAVE = 0x9C710              # inside the int3 run 0x9C703..0x9C800
CAVE_END = 0x9C800
MALLOC = 0xA2D190           # FMemory::Malloc(SIZE_T, uint32)
MEMCPY = 0x254829A          # CRT memcpy
ELEMENT = 0x20              # sizeof(FTowersCulture): two FStrings
CODE, NAME = 'pl', 'Polski'


class Image:
    def __init__(self, data):
        self.data = data
        pe = struct.unpack_from('<I', data, 0x3C)[0]
        count = struct.unpack_from('<H', data, pe + 6)[0]
        opt = struct.unpack_from('<H', data, pe + 20)[0]
        self.sections = []
        for i in range(count):
            at = pe + 24 + opt + 40 * i
            vsize, va, rsize, raw = struct.unpack_from('<IIII', data, at + 8)
            self.sections.append((va, max(vsize, rsize), raw))

    def off(self, rva):
        for va, size, raw in self.sections:
            if va <= rva < va + size:
                return rva - va + raw
        raise ValueError(hex(rva))

    def read(self, rva, n):
        o = self.off(rva)
        return bytes(self.data[o:o + n])

    def write(self, rva, blob):
        o = self.off(rva)
        self.data[o:o + len(blob)] = blob


def rel(src_end, target):
    return struct.pack('<i', target - src_end)


def expect(img, rva, prefix):
    got = img.read(rva, len(prefix))
    if got != prefix:
        raise ValueError(f'unexpected bytes at {rva:#x}: {got.hex()} (expected {prefix.hex()})')


def rip_target(img, rva, length):
    """Target of an instruction's trailing rel32 RIP displacement ending at rva+length."""
    disp = struct.unpack('<i', img.read(rva + length - 4, 4))[0]
    return rva + length + disp


def cave_code(array_data, destructor):
    code = bytearray()
    at = lambda: CAVE + len(code)
    pl = (CODE + '\0').encode('utf-16-le')
    name = (NAME + '\0').encode('utf-16-le')

    code += b'\x48\x8b\x1d' + rel(at() + 7, array_data)              # mov rbx, [array.Data]
    code += b'\x48\x81\xc3' + struct.pack('<I', 11 * ELEMENT)        # add rbx, 11*32
    fixups = []
    for field, text in ((0x00, pl), (0x10, name)):
        code += b'\xb9' + struct.pack('<I', len(text))               # mov ecx, bytes
        code += b'\x31\xd2'                                          # xor edx, edx
        code += b'\xe8' + rel(at() + 5, MALLOC)                      # call FMemory::Malloc
        code += b'\x48\x89\x43' + bytes([field])                     # mov [rbx+field], rax
        code += b'\x48\x89\xc1'                                      # mov rcx, rax
        fixups.append((len(code) + 3, text))
        code += b'\x48\x8d\x15' + b'\0\0\0\0'                        # lea rdx, [rip+literal]
        code += b'\x41\xb8' + struct.pack('<I', len(text))           # mov r8d, bytes
        code += b'\xe8' + rel(at() + 5, MEMCPY)                      # call memcpy
        chars = len(text) // 2
        code += b'\x48\xb8' + struct.pack('<II', chars, chars)       # mov rax, Num|Max<<32
        code += b'\x48\x89\x43' + bytes([field + 8])                 # mov [rbx+field+8], rax
    code += b'\x4c\x8d\x0d' + rel(at() + 7, destructor)              # lea r9, [destructor] (displaced)
    code += b'\xe9' + rel(at() + 5, RESUME)                          # jmp back
    while len(code) % 2:
        code += b'\xcc'
    for pos, text in fixups:
        literal = CAVE + len(code)
        code[pos:pos + 4] = rel(CAVE + pos + 4, literal)
        code += text
    return bytes(code)


def add_polish(exe: bytearray) -> dict:
    img = Image(exe)
    expect(img, INIT_NUM, b'\xc7\x05')
    assert img.read(INIT_NUM + 6, 4) == struct.pack('<I', 11)
    expect(img, INIT_RESIZE, b'\x41\x8d\x55\x0b')
    expect(img, LOAD_DATA, b'\x48\x8b\x1d')
    expect(img, AFTER_LOOP, b'\x4c\x8d\x0d')
    array_data = rip_target(img, LOAD_DATA, 7)
    num_field = INIT_NUM + 10 + struct.unpack('<i', img.read(INIT_NUM + 2, 4))[0]
    assert num_field == array_data + 8, (hex(num_field), hex(array_data))
    destructor = rip_target(img, AFTER_LOOP, 7)
    assert img.read(CAVE - 13, CAVE_END - CAVE + 13) == b'\xcc' * (CAVE_END - CAVE + 13)

    code = cave_code(array_data, destructor)
    assert CAVE + len(code) <= CAVE_END, len(code)
    img.write(INIT_NUM + 6, struct.pack('<I', 12))
    img.write(INIT_RESIZE, b'\x41\x8d\x55\x0c')
    img.write(AFTER_LOOP, b'\xe9' + rel(AFTER_LOOP + 5, CAVE) + b'\x90\x90')
    img.write(CAVE, code)
    return {'cave': hex(CAVE), 'cave_bytes': len(code), 'array': hex(array_data), 'destructor': hex(destructor)}
