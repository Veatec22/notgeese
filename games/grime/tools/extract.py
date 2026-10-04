"""Extract GRIME's I2 source; never write to the game installation."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
RELATIVE = Path('GRIME_Data/data.unity3d')
OBJECT = 190


class Reader:
    def __init__(self, raw, position=56):
        self.raw, self.pos = raw, position

    def number(self):
        value = struct.unpack_from('<i', self.raw, self.pos)[0]
        self.pos += 4
        return value

    def text(self):
        size = self.number()
        if not 0 <= size <= len(self.raw) - self.pos:
            raise ValueError(f'Invalid string length at {self.pos - 4}')
        value = self.raw[self.pos:self.pos + size].decode('utf-8')
        self.pos = (self.pos + size + 3) & ~3
        return value


def parse_layout(raw):
    if raw[32:43] != b'I2Languages':
        raise ValueError('Not the expected I2 source')
    reader = Reader(raw)
    terms = []
    for _ in range(reader.number()):
        key, kind = reader.text(), reader.number()
        # Description exists in managed metadata but is not serialized in this build.
        values = [reader.text() for _ in range(reader.number())]
        count = reader.number()
        if not 0 <= count <= len(raw) - reader.pos:
            raise ValueError(f'Invalid flags length for {key}')
        flags = list(raw[reader.pos:reader.pos + count])
        reader.pos = (reader.pos + count + 3) & ~3
        touch = [reader.text() for _ in range(reader.number())]
        terms.append({'key': key, 'type': kind, 'values': values,
                      'flags': flags, 'touch': touch})
    terms_end = reader.pos
    reader.number()  # CaseInsensitiveTerms
    reader.number()  # OnMissingTranslation
    reader.text()    # mTerm_AppName
    languages = []
    for _ in range(reader.number()):
        languages.append({'name': reader.text(), 'code': reader.text(),
                          'flags': reader.number()})
    if len({term['key'] for term in terms}) != len(terms):
        raise ValueError('Duplicate I2 keys')
    if not all(len(term['values']) == len(languages) for term in terms):
        raise ValueError('Inconsistent language columns')
    return {'terms': terms, 'languages': languages}, terms_end, reader.pos


def parse(raw):
    return parse_layout(raw)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    path = args.game / RELATIVE
    env = UnityPy.load(str(path))
    source = next(obj for obj in env.objects
                  if obj.type.name == 'MonoBehaviour' and obj.path_id == OBJECT)
    result = parse(source.get_raw_data())
    result['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    result['unity'] = source.assets_file.unity_version
    out = ROOT / 'work/source.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Extracted {len(result['terms'])} entries, {len(result['languages'])} languages to {out}")
    print(f"SHA-256: {result['sha256']}")


if __name__ == '__main__':
    main()
