"""Map native string literals to the GML functions that use them (read-only).

YYC compiles GML to x86. Each script/object event is listed in a table of
{name pointer, function pointer} pairs; string constants are loaded by code as
32-bit immediates. For every literal we record which GML functions reference it,
so runner diagnostics can be separated from game text and each text gets context.
Writes work/strings.json only.
"""
import argparse
import bisect
import json
import re
import struct
from pathlib import Path

import numpy as np
import pefile

ROOT = Path(__file__).resolve().parents[1]


def extract(game):
    pe = pefile.PE(str(game / 'Heat_Signature.exe'), fast_load=True)
    image = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    sections = {s.Name.rstrip(b'\0').decode(): s for s in pe.sections}
    text = sections['.text']
    t0, t1 = text.VirtualAddress, text.VirtualAddress + text.Misc_VirtualSize
    data_ranges = [(s.VirtualAddress, s.VirtualAddress + s.Misc_VirtualSize)
                   for n, s in sections.items() if n in ('.rdata', '.data')]

    # 1. Function table: consecutive (name_ptr -> "gml_...", func_ptr -> .text) pairs.
    names = {}
    for m in re.finditer(rb'gml_[A-Za-z0-9_]+\x00', image):
        names[m.start() + base] = m.group()[:-1].decode()
    functions = {}
    for lo, hi in data_ranges:
        words = np.frombuffer(image[lo:hi - (hi - lo) % 4], dtype='<u4')
        for shift in range(4):
            w = np.frombuffer(image[lo + shift:lo + shift + (hi - lo - shift) // 4 * 4], dtype='<u4')
            for i in np.nonzero(np.isin(w[:-1], np.fromiter(names, dtype=np.uint32)))[0]:
                func = int(w[i + 1])
                if t0 <= func - base < t1:
                    functions.setdefault(func - base, names[int(w[i])])
    starts = sorted(functions)
    # MSVC pads between functions with int3 up to 16-byte alignment. Runner code is
    # interleaved with GML, so each GML function ends at its first ret + padding.
    padding = re.compile(rb'(?:\xc3|\xc2..)\xcc+', re.S)
    ends = []
    for k, start in enumerate(starts):
        limit = starts[k + 1] if k + 1 < len(starts) else start + 0x100000
        end = limit
        for m in padding.finditer(image, start, limit):
            if m.end() % 16 == 0:
                end = m.end()
                break
        ends.append(end)
    lo_code, hi_code = starts[0], ends[-1]

    # 2. Code immediates pointing at string starts.
    code = image[t0:t1]
    xrefs = {}
    for shift in range(4):
        w = np.frombuffer(code[shift:shift + (len(code) - shift) // 4 * 4], dtype='<u4').astype(np.int64) - base
        mask = np.zeros(len(w), dtype=bool)
        for lo, hi in data_ranges:
            mask |= (w >= lo) & (w < hi)
        for i in np.nonzero(mask)[0]:
            xrefs.setdefault(int(w[i]), []).append(t0 + shift + int(i) * 4)

    strings = []
    for target, refs in xrefs.items():
        if target == 0 or image[target - 1] != 0:
            continue  # must start right after a terminator
        end = image.find(b'\0', target, target + 4096)
        if end <= target:
            continue
        raw = image[target:end]
        try:
            value = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if not re.search(r'[A-Za-z]', value) or any(ord(c) < 32 and c not in '\r\n\t' for c in value):
            continue
        users = set()
        for ref in refs:
            # Instruction bytes before the immediate: mov [esp+X], imm32 / push imm32 / mov reg, imm32.
            if not (lo_code <= ref < hi_code):
                continue
            i = bisect.bisect_right(starts, ref) - 1
            if i >= 0 and ref < ends[i]:
                users.add(functions[starts[i]])
        if users:
            strings.append(dict(rva=target, text=value, functions=sorted(users), refs=len(refs)))
    strings.sort(key=lambda s: s['rva'])
    out = ROOT / 'work/strings.json'
    out.write_text(json.dumps(strings, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(functions)} GML functions; {len(strings)} referenced literals -> {out}')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    extract(p.parse_args().game)
