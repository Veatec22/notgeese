"""Reads texts from Katana ZERO.exe (GameMaker, YYC-compiled code, x86).

The game has no text files. GML was compiled to C++, so every line is a constant in
.data, and the assignment `array[language * 32000 + n] = "text"` is a few instructions
with immediates:

    mov dword ptr [esp+28h], <GML line number>   ; call stack for error messages
    mov ecx, [esp+..]                             ; variable holding the array
    mov dword ptr [esp], <language*32000 + n>     ; index
    call <pobierz element>
    mov dword ptr [esp], <string address>         ; value
    call <ustaw napis>

The UI screen does the same via `[esp+4]`. Languages always come in the same order,
one after another: EN, JA, KO, DE, FR, ES, PT, RU, ZH-Hans, ZH-Hant.

An entry's key is the GML function name and the source line of the English version
(`init_lines:79`). YYC stores the line number in every assignment and passes the function
name at its start, so both come from the file, not from us.
"""
from __future__ import annotations

import bisect
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

import pefile

LANGS = ['en', 'ja', 'ko', 'de', 'fr', 'es', 'pt', 'ru', 'zh-hans', 'zh-hant']
STRIDE = 32000
RU = LANGS.index('ru')

# mov dword ptr [esp+d8], imm32  |  mov dword ptr [esp], imm32
MOV_ESP = re.compile(rb'\xc7(?:\x44\x24(.)|\x04\x24)(.{4})', re.S)
# the function name goes on the stack as mov [esp+d8|d32], imm32 or push imm32
NAME_REF = re.compile(rb'(?:\xc7(?:\x44\x24.|\x04\x24|\x84\x24.{4})|\x68)(.{4})', re.S)
GML_NAME = re.compile(rb'gml_[A-Za-z0-9_]+\x00')


@dataclass
class Entry:
    fn: str
    line: int | None
    index: int
    text: dict[str, str] = field(default_factory=dict)
    sites: dict[str, int] = field(default_factory=dict)   # imm32 offset in the file
    name: str | None = None                                # key of menu entries

    @property
    def key(self) -> str:
        return self.name or f'{short(self.fn)}:{self.line}'


def short(fn: str) -> str:
    for p in ('gml_Script_', 'gml_Object_'):
        if fn.startswith(p):
            return fn[len(p):]
    return fn


class Exe:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        text = self.pe.sections[0]
        self.t0 = text.PointerToRawData
        self.t1 = self.t0 + text.SizeOfRawData
        data = next(s for s in self.pe.sections if s.Name.rstrip(b'\0') == b'.data')
        self.dlo = self.base + data.VirtualAddress
        self.dhi = self.dlo + data.SizeOfRawData

    def va(self, off: int) -> int:
        return self.base + self.pe.get_rva_from_offset(off)

    def off(self, va: int) -> int:
        return self.pe.get_offset_from_rva(va - self.base)

    def cstr(self, va: int) -> str:
        o = self.off(va)
        return self.data[o:self.data.index(b'\0', o)].decode('utf-8')

    def is_string(self, va: int) -> bool:
        return self.dlo <= va < self.dhi

    def _function_starts(self) -> tuple[list[int], list[str]]:
        """Places where code passes a GML function name (function start)."""
        names = {}
        lo = self.pe.sections[1].PointerToRawData
        hi = self.off(self.dhi - 1)
        for m in GML_NAME.finditer(self.data, lo, hi):
            names[struct.pack('<I', self.va(m.start()))] = m.group()[:-1].decode()
        refs = []
        for m in NAME_REF.finditer(self.data, self.t0, self.t1):
            name = names.get(m.group(1))
            if name:
                refs.append((m.start(), name))
        refs.sort()
        return [r[0] for r in refs], [r[1] for r in refs]

    def movs(self):
        for m in MOV_ESP.finditer(self.data, self.t0, self.t1):
            disp = m.group(1)[0] if m.group(1) is not None else 0
            yield m.start(), disp, struct.unpack('<I', m.group(2))[0], m.end() - 4

    def entries(self) -> list[Entry]:
        """All multilingual entries: 10 versions of the same line next to each other."""
        fpos, fnames = self._function_starts()
        recs = []
        line = idx = None
        for o, disp, imm, imm_off in self.movs():
            if disp in (0, 4):
                if self.is_string(imm):
                    try:
                        s = self.cstr(imm)
                    except (UnicodeDecodeError, ValueError):
                        idx = None
                        continue
                    if idx and o - idx[0] < 80:
                        i = bisect.bisect_right(fpos, o) - 1
                        ln = line[1] if line and o - line[0] < 80 else None
                        recs.append((fnames[i] if i >= 0 else '?', ln, idx[1], s, imm_off))
                    idx = None
                elif imm < STRIDE * len(LANGS):
                    idx = (o, imm)
                else:
                    idx = None
            elif imm < 200000:
                line = (o, imm)
        out: list[Entry] = []
        cur = None
        for fn, ln, index, s, imm_off in recs:
            lang, k = divmod(index, STRIDE)
            code = LANGS[lang]
            if lang == 0 or cur is None or cur.index != k or code in cur.text or cur.fn != fn:
                cur = Entry(fn, ln, k)
                out.append(cur)
            cur.text[code] = s
            cur.sites[code] = imm_off
        return [e for e in out if len(e.text) == len(LANGS)]

    def menu_entries(self) -> list[Entry]:
        """Menus and settings: 10 versions of a string created in turn, closed by "end".

            mov dword ptr [esp+4], <adres napisu>
            call <create string>             ; x11: EN ... ZH-Hant, "end"

        Then all eleven go to a script that picks the current language's version.
        The key is the function and the English string (numbered on repeats).
        """
        fpos, fnames = self._function_starts()
        pat = re.compile(rb'\xc7\x44\x24\x04(.{4})\xe8(.{4})', re.S)
        run, runs = [], []
        for m in pat.finditer(self.data, self.t0, self.t1):
            imm, rel = struct.unpack('<Ii', m.group(1) + m.group(2))
            target = self.va(m.end()) + rel
            if run and (m.start() - run[-1][0] > 40 or target != run[-1][3]):
                runs.append(run)
                run = []
            if self.is_string(imm):
                try:
                    run.append((m.start(), self.cstr(imm), m.start() + 4, target))
                except (UnicodeDecodeError, ValueError):
                    run = []
            else:
                run = []
        runs.append(run)
        out, seen = [], {}
        for r in runs:
            for i in range(len(r) - 10):
                chunk = r[i:i + 11]
                if chunk[10][1] != 'end' or (i and r[i - 1][1] != 'end'):
                    continue
                j = bisect.bisect_right(fpos, chunk[0][0]) - 1
                fn = fnames[j] if j >= 0 else '?'
                en = chunk[0][1]
                n = seen[(fn, en)] = seen.get((fn, en), 0) + 1
                e = Entry(fn, None, 0)
                e.name = f'{short(fn)}:{en}' + (f'#{n}' if n > 1 else '')
                for code, (o, s, imm_off, _) in zip(LANGS, chunk):
                    e.text[code] = s
                    e.sites[code] = imm_off
                out.append(e)
        return out

    def references(self, va: int) -> list[int]:
        """imm32 offsets in code pointing at a given address."""
        pat = re.escape(struct.pack('<I', va))
        return [self.t0 + m.start() for m in re.finditer(pat, self.data[self.t0:self.t1])]

    def find_string(self, s: str) -> int:
        """Address of the zero-terminated string exactly equal to `s` (single occurrence)."""
        raw = b'\0' + s.encode('utf-8') + b'\0'
        hits = [m.start() + 1 for m in re.finditer(re.escape(raw), self.data)]
        if len(hits) != 1:
            raise ValueError(f'string {s!r}: {len(hits)} occurrences, expected one')
        return self.va(hits[0])
