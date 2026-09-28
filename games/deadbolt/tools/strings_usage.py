"""Where DEADBOLT code uses each STRG string (bytecode 15, GMS 1.4).

No decompilation to GML: walks each CODE entry's instructions linearly, records
`push.s <STRG index>` and what happens to the string in the next few instructions:
a function call (named via the FUNC occurrence chain), a comparison, an assignment
to a variable (VARI chains), a concatenation (`add`).

Output: work/strings-usage.json; per index: text and a list of uses
{code, next} (CODE entry name, e.g. gml_Object_oMenu_Draw_0, and the op sequence).

    .venv\\Scripts\\python.exe games\\deadbolt\\tools\\strings_usage.py --game "C:\\SteamLibrary\\steamapps\\common\\DEADBOLT"
"""
from __future__ import annotations

import argparse
import json
import struct
from collections import defaultdict
from pathlib import Path

WORK = Path(__file__).resolve().parents[1] / 'work'

# Bytecode 15 opcodes (UndertaleModTool, "new opcodes").
OPS = {
    0x07: 'conv', 0x08: 'mul', 0x09: 'div', 0x0A: 'rem', 0x0B: 'mod', 0x0C: 'add',
    0x0D: 'sub', 0x0E: 'and', 0x0F: 'or', 0x10: 'xor', 0x11: 'neg', 0x12: 'not',
    0x13: 'shl', 0x14: 'shr', 0x15: 'cmp', 0x45: 'pop', 0x86: 'dup', 0x9C: 'ret',
    0x9D: 'exit', 0x9E: 'popz', 0xB6: 'b', 0xB7: 'bt', 0xB8: 'bf', 0xBA: 'pushenv',
    0xBB: 'popenv', 0xC0: 'push', 0xC1: 'pushloc', 0xC2: 'pushglb', 0xC3: 'pushbltn',
    0x84: 'pushi', 0xD9: 'call', 0xFF: 'break',
}
TYPE_WORDS = {0: 2, 1: 1, 2: 1, 3: 2, 4: 1, 5: 1, 6: 1, 7: 1, 15: 0}  # operand words


class Data:
    def __init__(self, path: Path):
        self.d = path.read_bytes()
        self.chunks = {}
        o = 8
        while o < len(self.d):
            size = self.u32(o + 4)
            self.chunks[self.d[o:o + 4].decode()] = (o + 8, size)
            o += 8 + size

    def u32(self, o):
        return struct.unpack_from('<I', self.d, o)[0]

    def i32(self, o):
        return struct.unpack_from('<i', self.d, o)[0]

    def cstr(self, p):
        return self.d[p:self.d.index(b'\0', p)].decode('utf-8', 'replace')

    def strings(self):
        s, _ = self.chunks['STRG']
        return [self.cstr(self.u32(s + 4 + 4 * i) + 4) for i in range(self.u32(s))]

    def chains(self, chunk, header_words, entry_size, name_at, count_at, first_at):
        """Map instruction address -> name for FUNC/VARI occurrence chains."""
        s, size = self.chunks[chunk]
        out = {}
        if chunk == 'FUNC':
            n = self.u32(s)
            base = s + 4
        else:
            n = (size - 4 * header_words) // entry_size
            base = s + 4 * header_words
        for i in range(n):
            e = base + i * entry_size
            name = self.cstr(self.u32(e + name_at))
            count, addr = self.u32(e + count_at), self.u32(e + first_at)
            for _ in range(count):
                out[addr] = name
                addr += self.u32(addr + 4) & 0x07FFFFFF
        return out

    def code_entries(self):
        s, _ = self.chunks['CODE']
        for i in range(self.u32(s)):
            p = self.u32(s + 4 + 4 * i)
            name = self.cstr(self.u32(p))
            length = self.u32(p + 4)
            start = p + 12 + self.i32(p + 12)
            yield name, start, length


def disasm(data: Data, start: int, length: int, funcs, varis):
    """List (address, op, argument) for one CODE entry."""
    out = []
    o, end = start, start + length
    d = data.d
    while o < end:
        word = data.u32(o)
        op = word >> 24
        name = OPS.get(op, f'op{op:02x}')
        arg = None
        size = 4
        if op in (0xC0, 0xC1, 0xC2, 0xC3, 0x84):
            t = (word >> 16) & 0xF
            size += 4 * TYPE_WORDS.get(t, 1)
            if t == 6:
                arg = ('str', data.u32(o + 4))
            elif t == 5:
                arg = ('var', varis.get(o, '?'))
        elif op == 0xD9:
            size = 8
            arg = ('fn', funcs.get(o, '?'))
        elif op == 0x45:
            size = 8
            arg = ('var', varis.get(o, '?'))
        elif op == 0x15:
            arg = ('cmp', (word >> 8) & 0xFF)
        out.append((o, name, arg))
        o += size
    return out


# Calls where the string is an identifier, not player-facing text.
LOGIC_CALLS = ('ini_', 'asset_get_index', 'ds_map_', 'file_', 'FS_', 'shader_',
               'add_achievement', 'steam_', 'variable_', 'script_', 'sprite_',
               'audio_', 'string_replace', 'string_pos', 'string_copy', 'json_')
LOGIC_VARS = ('base_string', 'outfit', 'location', 'state', 'tname', 'tfile_name')


def classify(nxt: str) -> str:
    """'logic' when the string goes to a comparison or an identifier function, else 'display'."""
    for step in nxt.split(' ; '):
        if step == 'cmp':
            return 'logic'
        if step.startswith('call '):
            return 'logic' if step[5:].startswith(LOGIC_CALLS) else 'display'
        if step.startswith('pop '):
            return 'logic' if step[4:] in LOGIC_VARS else 'display'
    return 'display'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--dump', help='print the instructions of one CODE entry (e.g. gml_Object_oChangeRoom_Step_2)')
    args = ap.parse_args()
    game = args.game
    data = Data(game / 'data.win')
    strings = data.strings()
    funcs = data.chains('FUNC', 0, 12, 0, 4, 8)
    varis = data.chains('VARI', 3, 20, 0, 12, 16)

    if args.dump:
        for code, start, length in data.code_entries():
            if code == args.dump:
                for addr, op, arg in disasm(data, start, length, funcs, varis):
                    if arg and arg[0] == 'str':
                        arg = ('str', repr(strings[arg[1]][:60]))
                    print(f'{addr:08x} {op:8} {arg[1] if arg else ""}')
        return

    usage = defaultdict(list)
    bad = 0
    for code, start, length in data.code_entries():
        ins = disasm(data, start, length, funcs, varis)
        for k, (addr, op, arg) in enumerate(ins):
            if op != 'push' or not arg or arg[0] != 'str':
                continue
            idx = arg[1]
            if idx >= len(strings):
                bad += 1
                continue
            nxt = []
            for _, op2, arg2 in ins[k + 1:k + 7]:
                nxt.append(op2 + (f' {arg2[1]}' if arg2 and arg2[0] in ('fn', 'var') else ''))
                if op2 in ('call', 'pop', 'cmp', 'ret', 'b', 'bt', 'bf'):
                    break
            joined = ' ; '.join(nxt)
            usage[idx].append({'code': code, 'next': joined, 'kind': classify(joined)})

    result = {}
    for i in sorted(usage):
        kinds = {u['kind'] for u in usage[i]}
        result[str(i)] = {'text': strings[i],
                          'kind': kinds.pop() if len(kinds) == 1 else 'mixed',
                          'uses': usage[i]}
    WORK.mkdir(exist_ok=True)
    (WORK / 'strings-usage.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(result)} strings used in code, {bad} bad indexes, '
          f'{len(funcs)} calls, {len(varis)} variable references')


if __name__ == '__main__':
    main()
