"""Reads GameMaker data.win (GMS2, bytecode 17) as far as the translation needs.

Only what we touch: chunk list, sprites, texture page items (TPAG), texture pages (TXTR)
and the audio list (AUDO). All pointers in the file are absolute offsets from its start.
"""
from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

SPRITE_HEADER = 76      # from the name to the frame count, sprite version 1 (special -1)
TPAG_SIZE = 22


def u32(d, o):
    return struct.unpack_from('<I', d, o)[0]


@dataclass
class Tpag:
    offset: int
    src_x: int
    src_y: int
    src_w: int
    src_h: int
    tgt_x: int
    tgt_y: int
    tgt_w: int
    tgt_h: int
    bound_w: int
    bound_h: int
    texture: int

    def pack(self) -> bytes:
        return struct.pack('<11H', self.src_x, self.src_y, self.src_w, self.src_h,
                           self.tgt_x, self.tgt_y, self.tgt_w, self.tgt_h,
                           self.bound_w, self.bound_h, self.texture)


@dataclass
class Sprite:
    index: int
    list_slot: int        # pointer offset in the SPRT list
    offset: int
    name: str
    width: int
    height: int
    frames: list[int]     # pointers to TPAG
    frames_at: int        # frame count offset
    tail: bytes           # masks and everything after the frame list, to the end of the structure


class DataWin:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        d = self.data
        if d[:4] != b'FORM':
            raise ValueError(f'{path}: not a data.win file')
        self.chunks: dict[str, tuple[int, int]] = {}
        order = []
        p = 8
        while p < len(d):
            name = d[p:p + 4].decode('ascii')
            size = u32(d, p + 4)
            self.chunks[name] = (p + 8, size)
            order.append(name)
            p += 8 + size
        self.order = order
        self._textures: dict[int, Image.Image] = {}

    def string(self, ptr: int) -> str:
        n = u32(self.data, ptr - 4)
        return self.data[ptr:ptr + n].decode('utf-8')

    def pointer_list(self, chunk: str) -> tuple[int, list[int]]:
        start, _ = self.chunks[chunk]
        n = u32(self.data, start)
        return start, [u32(self.data, start + 4 + 4 * i) for i in range(n)]

    def sprites(self) -> dict[str, Sprite]:
        start, ptrs = self.pointer_list('SPRT')
        ordered = sorted(set(ptrs))
        end_of = {a: b for a, b in zip(ordered, ordered[1:])}
        end_of[ordered[-1]] = sum(self.chunks['SPRT'])
        out = {}
        for i, sp in enumerate(ptrs):
            d = self.data
            fa = sp + SPRITE_HEADER
            count = u32(d, fa)
            frames = [u32(d, fa + 4 + 4 * k) for k in range(count)]
            tail = d[fa + 4 + 4 * count:end_of[sp]]
            s = Sprite(i, start + 4 + 4 * i, sp, self.string(u32(d, sp)),
                       u32(d, sp + 4), u32(d, sp + 8), frames, fa, tail)
            out[s.name] = s
        return out

    def tpag(self, ptr: int) -> Tpag:
        return Tpag(ptr, *struct.unpack_from('<11H', self.data, ptr))

    def texture_entries(self) -> list[int]:
        return self.pointer_list('TXTR')[1]

    def texture(self, index: int) -> Image.Image:
        if index not in self._textures:
            entry = self.texture_entries()[index]
            png = u32(self.data, entry + 8)
            self._textures[index] = Image.open(io.BytesIO(self.data[png:])).convert('RGBA')
        return self._textures[index]

    def frame_image(self, ptr: int) -> Image.Image:
        """Frame at full sprite size, with a transparent background."""
        t = self.tpag(ptr)
        img = Image.new('RGBA', (t.bound_w, t.bound_h), (0, 0, 0, 0))
        if t.src_w and t.src_h:
            crop = self.texture(t.texture).crop((t.src_x, t.src_y, t.src_x + t.src_w, t.src_y + t.src_h))
            if (t.tgt_w, t.tgt_h) != (t.src_w, t.src_h):
                crop = crop.resize((t.tgt_w, t.tgt_h), Image.NEAREST)
            img.paste(crop, (t.tgt_x, t.tgt_y))
        return img
