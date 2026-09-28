"""Read-only technical survey; writes only to the game's repository work directory."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(game):
    exe = (game / 'Heat_Signature.exe').read_bytes()
    forms = []
    for match in re.finditer(b'FORM', exe):
        base = match.start()
        end = base + 8 + struct.unpack_from('<I', exe, base + 4)[0]
        if end <= len(exe) and exe[base + 8:base + 12] == b'GEN8':
            forms.append((base, end))
    if len(forms) != 1:
        raise ValueError(f'Expected one embedded GameMaker FORM, found {forms}')
    base, end = forms[0]
    data = exe[base:end]
    u32 = lambda offset: struct.unpack_from('<I', data, offset)[0]
    cstr = lambda offset: data[offset:data.index(b'\0', offset)].decode('utf-8')
    chunks = {}
    pos = 8
    while pos < len(data):
        tag = data[pos:pos + 4].decode('ascii')
        size = u32(pos + 4)
        chunks[tag] = (pos + 8, size)
        pos += 8 + size
    assert pos == len(data)
    fonts = []
    start = chunks['FONT'][0]
    for i in range(u32(start)):
        offset = u32(start + 4 + i * 4)
        count = u32(offset + 40)
        codes = [struct.unpack_from('<H', data, u32(offset + 44 + j * 4))[0]
                 for j in range(count)]
        fonts.append(dict(name=cstr(u32(offset)), family=cstr(u32(offset + 4)),
                          size=u32(offset + 8), glyphs=count,
                          min_code=min(codes), max_code=max(codes),
                          polish_present=''.join(c for c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ' if ord(c) in codes)))
    dialogs = []
    for path in sorted((game / 'Dialog').glob('*.txt')):
        for line_no, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if line.strip() and not re.fullmatch(r'\[.*\]', line.strip()):
                dialogs.append(dict(key=f'Dialog/{path.name}:{line_no}', english=line, polish=''))
    # Candidates only: native literals include diagnostics and fragments, not a translation count.
    literals = [dict(offset=m.start(), text=m.group().decode('ascii'))
                for m in re.finditer(rb'[\x20-\x7e]{4,}\x00', exe[:base])
                if re.search(rb'[A-Za-z]{2,} [A-Za-z]{2,}', m.group())]
    for literal in literals:
        literal['text'] = literal['text'].rstrip('\0')
    report = dict(exe_bytes=len(exe), exe_sha256=hashlib.sha256(exe).hexdigest(),
                  form_offset=base, form_bytes=len(data), chunks=chunks, fonts=fonts,
                  dialog_files=len(list((game / 'Dialog').glob('*.txt'))),
                  dialog_lines=len(dialogs), native_multiword_candidates=len(literals),
                  native_gml_names=len(set(re.findall(rb'gml_[A-Za-z0-9_]+', exe[:base]))))
    out = ROOT / 'work'
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [('inspection.json', report), ('dialog-review.json', dialogs),
                        ('native-candidates.json', literals)]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path)
    inspect(parser.parse_args().game)
