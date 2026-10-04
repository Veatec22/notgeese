"""Build GRIME's Polish language in dist; never install or launch the game."""
import argparse
from collections import Counter
import hashlib
import re
import struct
import sys
from pathlib import Path

import UnityPy
from extract import OBJECT, RELATIVE, parse, parse_layout
from bundle import replace_source

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries

ORIGINAL = 'aea9e6c80778d895e47f0890c505dccb2f80a2e661fee84ee84074ddfc526e9d'
VERSION = '0.2'


def integer(value):
    return struct.pack('<i', value)


def string(value):
    raw = value.encode('utf-8')
    return integer(len(raw)) + raw + bytes(-len(raw) % 4)


def serialize(header, terms, tail):
    out = bytearray(header + integer(len(terms)))
    for term in terms:
        out += string(term['key']) + integer(term['type'])
        out += integer(len(term['values']))
        out += b''.join(string(value) for value in term['values'])
        flags = bytes(term['flags'])
        out += integer(len(flags)) + flags + bytes(-len(flags) % 4)
        out += integer(len(term['touch']))
        out += b''.join(string(value) for value in term['touch'])
    return bytes(out) + tail


def validate_translation(english, polish, key):
    tokens = lambda value: Counter(re.findall(r'<[^>]+>|\{[^}]+\}', value))
    if tokens(english) != tokens(polish):
        raise ValueError(f'Tokens differ: {key}')
    if '\ufffd' in polish:
        raise ValueError(f'Replacement character: {key}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    source = args.game / RELATIVE
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != ORIGINAL:
        raise SystemExit(f'Unsupported original: {digest}; expected {ORIGINAL}. Nothing written.')
    target = ROOT / 'dist' / RELATIVE
    if target.resolve() == source.resolve():
        raise SystemExit('Output cannot overwrite the original')
    env = UnityPy.load(str(source))
    obj = next(o for o in env.objects if o.type.name == 'MonoBehaviour' and o.path_id == OBJECT)
    raw = obj.get_raw_data()
    original, terms_end, languages_end = parse_layout(raw)
    if serialize(raw[:56], original['terms'], raw[terms_end:]) != raw:
        raise ValueError('Source does not round-trip')
    if len(original['terms']) != 2655 or len(original['languages']) != 13:
        raise ValueError('Unexpected source dimensions')
    entries = load_entries(ROOT)
    index = {entry['key']: entry for entry in entries}
    text_terms = {t['key']: t['values'][0] for t in original['terms'] if t['type'] == 0}
    if index.keys() != text_terms.keys():
        raise ValueError('Translation/source key mismatch')
    for key, english in text_terms.items():
        if index[key]['english'] != english:
            raise ValueError(f'Stale English: {key}')
        if index[key]['polish']:
            validate_translation(english, index[key]['polish'], key)
    rebuilt_terms = []
    for term in original['terms']:
        values, flags, touch = term['values'].copy(), term['flags'].copy(), term['touch'].copy()
        polish = index[term['key']]['polish'] if term['type'] == 0 else ''
        values.append(polish or values[0])  # Partial translations fall back to English.
        if len(flags) != 13 or (touch and len(touch) != 13):
            raise ValueError(f'Unexpected flags/touch columns: {term["key"]}')
        flags.append(flags[0])
        if touch:
            touch.append(polish or touch[0])
        rebuilt_terms.append({**term, 'values': values, 'flags': flags, 'touch': touch})
    languages = original['languages'] + [{'name': 'Polski', 'code': 'pl', 'flags': 0}]
    tail = raw[terms_end:terms_end + 12] + integer(len(languages))
    for language in languages:
        tail += string(language['name']) + string(language['code']) + integer(language['flags'])
    tail += raw[languages_end:]
    patched = serialize(raw[:56], rebuilt_terms, tail)
    expected = {'terms': rebuilt_terms, 'languages': languages}
    if parse(patched) != expected:
        raise ValueError('Patched source does not round-trip')
    before = {(o.assets_file.name, o.path_id): o.get_raw_data() for o in env.objects}
    built = replace_source(source.read_bytes(), obj, patched)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(built)
    check = UnityPy.load(str(target))
    after = {(o.assets_file.name, o.path_id): o.get_raw_data() for o in check.objects}
    changed = [key for key in before if before[key] != after[key]]
    if before.keys() != after.keys() or changed != [(obj.assets_file.name, OBJECT)]:
        raise ValueError(f'Unexpected changed objects: {changed}')
    if after[(obj.assets_file.name, OBJECT)] != patched:
        raise ValueError('Saved source mismatch')
    # Exact source columns, font references and opaque trailing fields are retained.
    for old, new in zip(original['terms'], parse(patched)['terms']):
        if old['values'] != new['values'][:13] or old['flags'] != new['flags'][:13]:
            raise ValueError(f'Original language changed: {old["key"]}')
    done = sum(bool(entry['polish']) for entry in entries)
    print(f'GRIME PL {VERSION}: {done}/{len(entries)} text entries; 2655 terms, 14 languages.')
    print('Verified: only I2 object changed; original 13 columns untouched; Polish present.')
    print(f'Output: {target}')


if __name__ == '__main__':
    main()
