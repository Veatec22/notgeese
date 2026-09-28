"""Minimal UE4.25-4.27 cooked asset reader and Kismet bytecode disassembler.

Analysis only: reads how a Blueprint behaves, never writes assets.
"""
import struct


class Asset:
    def __init__(self, uasset, uexp):
        self.a, self.e = uasset, uexp
        r, at = self.a, 0
        tag, legacy = struct.unpack_from('<Ii', r, at); at += 8
        assert tag == 0x9E2A83C1
        if legacy != -4:
            at += 4
        self.ue4, self.licensee = struct.unpack_from('<ii', r, at); at += 8
        n = struct.unpack_from('<i', r, at)[0]; at += 4
        at += n * 20
        self.header_size = struct.unpack_from('<i', r, at)[0]; at += 4
        _, at = self.fstr(at)
        self.flags = struct.unpack_from('<I', r, at)[0]; at += 4
        name_count, name_off = struct.unpack_from('<ii', r, at); at += 8
        if self.ue4 >= 516:
            _, at = self.fstr(at)
        at += 8
        exp_count, exp_off, imp_count, imp_off = struct.unpack_from('<iiii', r, at); at += 16
        self.names, p = [], name_off
        for _ in range(name_count):
            s, p = self.fstr(p)
            p += 4
            self.names.append(s)
        self.imports, p = [], imp_off
        for _ in range(imp_count):
            cp, cpn, cn, cnn, outer, on, onn = struct.unpack_from('<iiiiiii', r, p)
            p += 28
            self.imports.append((self.name(on, onn), self.name(cn, cnn), outer))
        self.exports, p = [], exp_off
        for _ in range(exp_count):
            cls, sup, tmpl, outer, on, onn = struct.unpack_from('<iiiiii', r, p); p += 24
            p += 4
            size, off = struct.unpack_from('<qq', r, p); p += 16
            p += 4 * 3 + 16 + 4 + 4 * 2 + 4 * 5
            self.exports.append(dict(name=self.name(on, onn), cls=cls, outer=outer, size=size, off=off))

    def fstr(self, at):
        n = struct.unpack_from('<i', self.a, at)[0]; at += 4
        if n < 0:
            s = self.a[at:at - 2 * n].decode('utf-16-le'); at += -2 * n
        else:
            s = self.a[at:at + n].decode('latin-1'); at += n
        return s.rstrip('\0'), at

    def name(self, i, n=0):
        s = self.names[i] if 0 <= i < len(self.names) else f'?{i}'
        return f'{s}_{n - 1}' if n else s

    def ref(self, i):
        if i < 0:
            return self.imports[-i - 1][0]
        if i < -len(self.imports):
            return f'?imp{i}'
        if i > 0:
            return 'exp:' + self.exports[i - 1]['name']
        return 'null'

    def export_data(self, index):
        x = self.exports[index]
        start = x['off'] - self.header_size
        return self.e[start:start + x['size']]


VARS = {0x00: 'L', 0x01: 'I', 0x6C: 'D', 0x48: 'O'}


class Disasm:
    def __init__(self, asset, code):
        self.A, self.c, self.p = asset, code, 0

    def i32(self):
        v = struct.unpack_from('<i', self.c, self.p)[0]; self.p += 4
        return v

    def u8(self):
        v = self.c[self.p]; self.p += 1
        return v

    def fname(self):
        i, n = struct.unpack_from('<ii', self.c, self.p); self.p += 8
        return self.A.name(i, n)

    def prop(self):
        parts = [self.fname() for _ in range(self.i32())]
        self.i32()
        return '.'.join(parts) or 'none'

    def obj(self):
        return self.A.ref(self.i32())

    def until(self, end):
        args = []
        while self.c[self.p] != end:
            args.append(self.expr())
        self.p += 1
        return args

    def expr(self):
        op, E = self.u8(), self.expr
        if op in VARS:
            return VARS[op] + ':' + self.prop()
        if op == 0x04: return 'return ' + E()
        if op == 0x06: return f'jump {self.i32():#x}'
        if op == 0x07: t = self.i32(); return f'jumpifnot {t:#x} ({E()})'
        if op == 0x0B: return 'nothing'
        if op == 0x0F: self.prop(); v = E(); return f'{v} = {E()}'
        if op in (0x14, 0x5F, 0x44, 0x43): v = E(); return f'{v} = {E()}'
        if op == 0x12: o = E(); self.i32(); self.prop(); return f'{o}::({E()})'
        if op == 0x19: o = E(); self.i32(); self.prop(); return f'{o}->({E()})'
        if op in (0x1B, 0x45): fn = self.fname(); return f'vcall {fn}({", ".join(self.until(0x16))})'
        if op in (0x1C, 0x68, 0x46): fn = self.obj(); return f'call {fn}({", ".join(self.until(0x16))})'
        if op == 0x1D: return str(self.i32())
        if op == 0x1E: v = struct.unpack_from('<f', self.c, self.p)[0]; self.p += 4; return str(v)
        if op == 0x1F:
            end = self.c.index(b'\0', self.p)
            s = self.c[self.p:end].decode('latin-1'); self.p = end + 1
            return repr(s)
        if op == 0x34:
            end = self.c.index(b'\0\0', self.p)
            while (end - self.p) % 2: end = self.c.index(b'\0\0', end + 1)
            s = self.c[self.p:end].decode('utf-16-le'); self.p = end + 2
            return repr(s)
        if op == 0x20: return 'obj:' + self.obj()
        if op == 0x21: return 'name:' + self.fname()
        if op == 0x24: return f'byte {self.u8()}'
        if op == 0x25: return '0'
        if op == 0x26: return '1'
        if op == 0x27: return 'true'
        if op == 0x28: return 'false'
        if op == 0x29: return self.text()
        if op == 0x2A: return 'none'
        if op == 0x2C: return f'b{self.u8()}'
        if op == 0x17: return 'self'
        if op == 0x2E: c = self.obj(); return f'cast<{c}>({E()})'
        if op == 0x31: t = E(); return f'{t} = ' +  f'[{", ".join(self.until(0x32))}]'
        if op == 0x38: t = self.u8(); return f'primcast{t}({E()})'
        if op == 0x2F: s = self.obj(); self.i32(); return f'struct<{s}>({", ".join(self.until(0x30))})'
        if op == 0x42: pr = self.prop(); return f'({E()}).{pr}'
        if op == 0x4E: return f'computedjump ({E()})'
        if op == 0x4C: return f'push {self.i32():#x}'
        if op == 0x4D: return 'pop'
        if op == 0x4F: return f'popifnot ({E()})'
        if op == 0x53: return 'end of script'
        if op == 0x5A: return 'nothing'
        if op == 0x5E: return 'wiretrace'
        if op == 0x5B: return 'wiretrace'
        if op == 0x69:
            self.u8() if False else None
            idx_off = struct.unpack_from('<H', self.c, self.p)[0]; self.p += 2
            n = struct.unpack_from('<H', self.c, self.p)[0]; self.p += 2
            idx = E(); cases = []
            for _ in range(n):
                k = E(); self.i32(); v = E(); cases.append(f'{k}:{v}')
            d = E()
            return f'switch({idx}) {{{"; ".join(cases)}; default:{d}}}'
        if op == 0x36: c = self.obj(); return f'dyncast<{c}>({E()})'
        if op == 0x33: o = self.obj(); return f'metacast<{o}>({E()})'
        if op == 0x5C: o = self.obj(); return f'icast<{o}>({E()})'
        if op in (0x10, 0x6B): t = E(); return f'{t}[{E()}]'
        if op == 0x5D: return 'nothing'
        if op == 0x65: pr = self.prop(); return f'persistent {pr} = {E()}'
        raise ValueError(f'op {op:#x} at {self.p - 1:#x}')

    def text(self):
        kind, E = self.u8(), self.expr
        if kind == 0: return 'text()'
        if kind == 1: ns = E(); k = E(); src = E(); return f'LOCTEXT({ns},{k},{src})'
        if kind == 2: return f'invtext({E()})'
        if kind == 3: return f'literal({E()})'
        if kind == 4: t = self.obj(); r = E(); return f'stringtable({t},{r})'
        return f'text?{kind}'

    def run(self):
        out = []
        while self.p < len(self.c):
            at = self.p
            try:
                s = self.expr()
            except Exception as ex:
                out.append(f'{at:#06x}: !! {ex}')
                break
            out.append(f'{at:#06x}: {s}')
        return out
