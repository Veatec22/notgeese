"""Read-only: dump the official I2 languages next to review keys (work/ref-<code>.json).

Used as evidence for the translation bible (speaker gender, ambiguity).
The output is game content for local analysis only and is ignored by git.

    .venv\\Scripts\\python.exe games\\shotgun-cop-man\\tools\\other_languages.py --game "<game dir>"
"""
import argparse
import json
import struct
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH_ID = 4903  # I2 LanguageSourceAsset in resources.assets


def parse(raw):
    """I2 terms: (key, kind, texts per language, flags, touch) plus the tail after the terms."""
    pos = 56

    def integer():
        nonlocal pos
        value = struct.unpack_from('<i', raw, pos)[0]
        pos += 4
        return value

    def string():
        nonlocal pos
        length = integer()
        assert 0 <= length <= len(raw) - pos
        value = raw[pos:pos + length].decode('utf-8')
        pos = (pos + length + 3) & ~3
        return value

    entries = []
    for _ in range(integer()):
        key, kind = string(), integer()
        languages = [string() for _ in range(integer())]
        length = integer()
        flags = raw[pos:pos + length]
        pos = (pos + length + 3) & ~3
        touch = [string() for _ in range(integer())]
        entries.append((key, kind, languages, flags, touch))
    return entries, raw[pos:]


def parse_languages(tail):
    """Language rows (name, code, flags) after the terms."""
    # CaseInsensitiveTerms (aligned bool), OnMissingTranslation, empty mTerm_AppName.
    assert tail[:12] == b'\0\0\0\0\3\0\0\0\0\0\0\0'
    count = struct.unpack_from('<i', tail, 12)[0]
    position = 16
    rows = []
    for _ in range(count):
        fields = []
        for _ in range(2):
            length = struct.unpack_from('<i', tail, position)[0]
            position += 4
            fields.append(tail[position:position + length].decode('utf-8'))
            position = (position + length + 3) & ~3
        flags = tail[position:position + 4]
        position += 4
        rows.append((*fields, flags))
    return rows, position


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    env = UnityPy.load(str(args.game/'Shotgun Cop Man_Data/resources.assets'))
    raw = next(o for o in env.objects if o.path_id == SOURCE_PATH_ID).get_raw_data()
    entries, tail = parse(raw)
    languages, _ = parse_languages(tail)
    (ROOT/'work').mkdir(exist_ok=True)
    for index, (name, code, _flags) in enumerate(languages):
        out = {key: texts[index] for key, _kind, texts, _f, _t in entries if index < len(texts)}
        target = ROOT/'work'/f'ref-{code or name}.json'
        target.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(name, code, len(out), target.name)


if __name__ == '__main__':
    main()
