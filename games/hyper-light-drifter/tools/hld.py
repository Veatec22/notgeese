"""Shared reading of Hyper Light Drifter files: .txt texts and GameMaker data in the exe.

Texts: `MenuText.txt` and `Phrases.txt` (UTF-8, CRLF). An entry starts with a header
`=|KEY|n` or `PHR|KEY|n`, then one `LANG|text` line each for ENG, FRN, SPA, JAP, GER,
ITA, RUS. Lines without `|` are author comments ("15 Chars max").
The code set is compiled into the exe, so Polish takes the `ITA|` lines.

Data: GameMaker Studio 1.4 (bytecode 16, YYC) keeps the whole `data.win` as a FORM block
inside the `.data` section of `HyperLightDrifter.exe` and reads it straight from the exe
image in memory. Pointers in the block count from its in-memory start, so they may also
point into other exe sections; reading translates them through RVAs.
"""
from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

EXE = 'HyperLightDrifter.exe'
TEXT_FILES = {'MenuText': 'MenuText.txt', 'Phrases': 'Phrases.txt'}
HASHES = {
    EXE: '88a941c33fd1b1a9a7b44cae363b8a275652c6075f60828e65dce81e948f07ec',
    'MenuText.txt': '9f1c36b28f4d2b017b99ab480982e5ef37d18dfafdd7a57a09579c67eb700a2e',
    'Phrases.txt': 'e9f7aa1835baf3bc21d70362d2f94329026cf64c3a9daad38440f61271e07d63',
}
LANGS = ('ENG', 'FRN', 'SPA', 'JAP', 'GER', 'ITA', 'RUS')
SLOT = 'ITA'
HEADER = re.compile(r'^(=|PHR)\|(.+)\|(\d+)$')

BOM = '\ufeff'


# --- texts ----------------------------------------------------------------------

@dataclass
class Entry:
    key: str            # `MenuText/CONTINUE`
    number: int
    lines: dict         # language -> line index in the file
    note: str           # author comment before the entry ("15 Chars max")


def read_text(raw: bytes) -> list[str]:
    """File lines; the BOM (MenuText.txt has one, Phrases.txt doesn't) stays in the first."""
    lines = raw.decode('utf-8').split('\r\n')
    assert all('\n' not in l and '\r' not in l for l in lines)
    return lines


def write_text(lines: list[str]) -> bytes:
    return '\r\n'.join(lines).encode('utf-8')


def entries(name: str, lines: list[str]) -> list[Entry]:
    result, current, note = [], None, ''
    for i, line in enumerate(lines):
        match = HEADER.match(line.lstrip(BOM))
        if match:
            current = Entry(f'{name}/{match[2]}', int(match[3]), {}, note)
            result.append(current)
            note = ''
        elif line[:4].rstrip('|') in LANGS and line[3:4] == '|':
            assert current and line[:3] not in current.lines, (name, i, line)
            current.lines[line[:3]] = i
        elif line.strip():
            note = line.strip()
    keys = [e.key for e in result]
    assert len(keys) == len(set(keys)), 'duplicate keys'
    assert all(set(e.lines) == set(LANGS) for e in result), 'entry without all languages'
    return result


def value(lines: list[str], entry: Entry, lang: str) -> str:
    return lines[entry.lines[lang]][4:]


def load_texts(game: Path) -> dict[str, tuple[list[str], list[Entry]]]:
    out = {}
    for name, file in TEXT_FILES.items():
        lines = read_text((game / file).read_bytes())
        out[name] = (lines, entries(name, lines))
    return out


# --- dane GameMakera ------------------------------------------------------------

@dataclass
class Section:
    header: int         # section header offset in the file
    name: bytes
    vsize: int
    rva: int
    raw_size: int
    raw: int


def sections(data: bytes | bytearray) -> list[Section]:
    nt = struct.unpack_from('<I', data, 0x3c)[0]
    count, opt_size = struct.unpack_from('<H12xH', data, nt + 6)
    table = nt + 24 + opt_size
    out = []
    for i in range(count):
        h = table + 40 * i
        name, vsize, rva, raw_size, raw = struct.unpack_from('<8sIIII', data, h)
        out.append(Section(h, name.rstrip(b'\0'), vsize, rva, raw_size, raw))
    return out


@dataclass
class Glyph:
    at: int             # structure offset in the file
    char: str
    x: int
    y: int
    w: int
    h: int
    shift: int
    offset: int


@dataclass
class Font:
    name: str
    at: int
    atlas: tuple        # (x, y, w, h) on the texture page
    page: int
    glyphs: dict        # znak -> Glyph


class GameData:
    def __init__(self, data: bytes | bytearray):
        self.d = data
        start = data.find(b'FORM\x00')
        while start >= 0 and data[start + 8:start + 12] != b'GEN8':
            start = data.find(b'FORM', start + 1)
        assert start >= 0, 'no FORM block'
        self.base = start
        self.end = start + 8 + self.u32(start + 4)
        self.chunks = {}
        o = start + 8
        while o < self.end:
            name = bytes(data[o:o + 4]).decode('ascii')
            self.chunks[name] = (o + 8, self.u32(o + 4))
            o += 8 + self.u32(o + 4)
        assert o == self.end
        assert data[self.chunks['GEN8'][0] + 1] == 16, 'oczekiwany bytecode 16'
        self.sections = sections(data)
        self.form_rva = self.rva(start)

    def rva(self, offset: int) -> int:
        for s in self.sections:
            if s.raw <= offset < s.raw + s.raw_size:
                return s.rva + offset - s.raw
        raise ValueError(hex(offset))

    def offset(self, rva: int) -> int:
        for s in self.sections:
            if s.rva <= rva < s.rva + min(s.raw_size, s.vsize):
                return s.raw + rva - s.rva
        raise ValueError(f'RVA {rva:#x} outside file data')

    def u32(self, o: int) -> int:
        return struct.unpack_from('<I', self.d, o)[0]

    def ptr(self, o: int) -> int:
        """A FORM block pointer as a file offset."""
        value = self.u32(o)
        if self.base + value < self.end:
            return self.base + value
        return self.offset(self.form_rva + value)

    def string(self, o: int) -> str:
        at = self.ptr(o)
        return bytes(self.d[at:at + self.u32(at - 4)]).decode('utf-8')

    def items(self, chunk: str) -> list[int]:
        o = self.chunks[chunk][0]
        return [self.ptr(o + 4 + 4 * i) for i in range(self.u32(o))]

    def font(self, name: str) -> Font:
        for at in self.items('FONT'):
            if self.string(at) != name:
                continue
            tpag = self.ptr(at + 28)
            v = struct.unpack_from('<11H', self.d, tpag)
            glyphs = {}
            g = at + 40
            for i in range(self.u32(g)):
                ga = self.ptr(g + 4 + 4 * i)
                c, x, y, w, h, shift, offset = struct.unpack_from('<5H2h', self.d, ga)
                glyphs[chr(c)] = Glyph(ga, chr(c), x, y, w, h, shift, offset)
            return Font(name, at, v[:4], v[10], glyphs)
        raise KeyError(name)

    def page_slot(self, page: int) -> int:
        """Offset of the PNG pointer field in a texture page entry."""
        return self.items('TXTR')[page] + 4

    def page_png(self, page: int) -> tuple[int, int]:
        """Position and length of a texture page PNG (to the end of the IEND chunk)."""
        at = self.ptr(self.page_slot(page))
        assert bytes(self.d[at:at + 8]) == b'\x89PNG\r\n\x1a\n'
        o = at + 8
        while True:
            n = struct.unpack_from('>I', self.d, o)[0]
            kind = bytes(self.d[o + 4:o + 8])
            o += 12 + n
            if kind == b'IEND':
                return at, o - at

    def page_image(self, page: int) -> Image.Image:
        at, span = self.page_png(page)
        return Image.open(io.BytesIO(bytes(self.d[at:at + span]))).convert('RGBA')
