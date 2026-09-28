"""Read-only inventory of the game's I2 Localization table.

Writes translations/en-pl-review.json (key, english, polish, context) keeping existing
Polish, work/analysis.json with counts, and work/ref-<code>.json with the other official
languages (game content for local comparison only, ignored by git). Never modifies the game.

Usage: python analyze.py --game "C:/SteamLibrary/steamapps/common/<Game>"
"""
import argparse
import collections
import json
import sys
import re
import struct
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, review_path, write_entries  # noqa: E402


class Reader:
    def __init__(self, raw, pos):
        self.raw, self.pos = raw, pos

    def int(self):
        value = struct.unpack_from('<i', self.raw, self.pos)[0]
        self.pos += 4
        return value

    def str(self):
        length = self.int()
        if not 0 <= length <= len(self.raw) - self.pos:
            raise ValueError('string length')
        value = self.raw[self.pos:self.pos + length].decode('utf-8')
        self.pos = (self.pos + length + 3) & ~3
        return value

    def skip_bytes(self):
        length = self.int()
        if not 0 <= length <= 4096:
            raise ValueError('byte array length')
        self.pos = (self.pos + length + 3) & ~3


def read_terms(raw, pos, has_description):
    """mTerms: Term, TermType, [Description], Languages[], Flags(byte[]), Languages_Touch[]."""
    r = Reader(raw, pos)
    count = r.int()
    if not 10 <= count <= 50000:
        raise ValueError('term count')
    terms = []
    for _ in range(count):
        key, kind = r.str(), r.int()
        if not 0 <= kind <= 20:
            raise ValueError('term type')
        description = r.str() if has_description else ''
        languages = [r.str() for _ in range(r.int())]
        r.skip_bytes()
        touched = r.int()
        if not 0 <= touched <= 60:
            raise ValueError('touch count')
        for _ in range(touched):
            r.str()
        terms.append({'key': key, 'kind': kind, 'context': description, 'texts': languages})
    return terms, r.pos


def read_languages(raw, pos):
    for start in range(pos, min(pos + 400, len(raw)), 4):
        r = Reader(raw, start)
        try:
            count = r.int()
            if not 1 <= count <= 60:
                continue
            found = []
            for _ in range(count):
                name, code = r.str(), r.str()
                r.int()
                found.append((name, code))
            if all(name and re.fullmatch(r'[a-z]{2}(-[A-Za-z]{2,4})?', code) for name, code in found):
                return found
        except (ValueError, struct.error, UnicodeDecodeError):
            continue
    raise ValueError('language list not found')


def find_source(data):
    env = UnityPy.load(str(data / 'resources.assets'))
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        raw = obj.get_raw_data()
        length = struct.unpack_from('<i', raw, 28)[0]
        if 0 < length < 200 and raw[32:32 + length] == b'I2Languages':
            return obj, raw
    raise SystemExit('I2Languages not found in resources.assets')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    data = next(args.game.glob('*_Data'))
    obj, raw = find_source(data)
    # The term list starts after the MonoBehaviour header and three aligned bools (offset 56
    # in both Blue Manchu games); older I2 stores a Description per term. Detect, don't assume.
    parsed = None
    for has_description in (True, False):
        try:
            parsed = read_terms(raw, 56, has_description) + (has_description,)
            break
        except (ValueError, struct.error, UnicodeDecodeError):
            continue
    if parsed is None:
        raise SystemExit('Unsupported I2 layout')
    terms, end, has_description = parsed
    languages = read_languages(raw, end)
    codes = [code for _, code in languages]
    en = next(i for i, c in enumerate(codes) if c.startswith('en'))
    assert not any(c.startswith('pl') for c in codes), 'Polish already present'

    polish = polish_by_key(ROOT) if review_path(ROOT).exists() else {}
    keys = [t['key'] for t in terms]
    assert len(set(keys)) == len(keys), 'duplicate terms'
    rows = []
    for t in terms:
        english = t['texts'][en] if len(t['texts']) > en else ''
        if not english.strip() and t['key'] not in polish:
            continue  # empty game term: nothing to translate or review
        row = {'key': t['key'], 'english': english, 'polish': polish.get(t['key'], '')}
        if t['context']:
            row['context'] = t['context']
        rows.append(row)
    # Terms the plugin adds because the game has none (e.g. the menu label Language/Polish).
    for key in sorted(set(polish) - set(keys)):
        rows.append({'key': key, 'english': '', 'polish': polish[key],
                     'context': 'Nowy termin dodawany przez plugin; gra go nie ma.'})
    (ROOT / 'translations').mkdir(parents=True, exist_ok=True)
    (ROOT / 'work').mkdir(parents=True, exist_ok=True)
    write_entries(ROOT, rows)
    for i, code in enumerate(codes):
        if i == en:
            continue
        ref = {t['key']: t['texts'][i] for t in terms if i < len(t['texts'])}
        (ROOT / 'work' / f'ref-{code}.json').write_text(json.dumps(ref, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    categories = collections.Counter(k.split('/')[0] if '/' in k else '(root)' for k in keys)
    report = {
        'unity': obj.assets_file.unity_version, 'asset': 'resources.assets', 'path_id': obj.path_id,
        'i2_term_description_field': has_description, 'languages': languages,
        'terms': len(terms), 'nonempty_en': sum(bool(r['english']) for r in rows),
        'en_characters': sum(len(r['english']) for r in rows),
        'with_context': sum('context' in r for r in rows),
        'categories': categories.most_common(), 'game_modified': False,
    }
    (ROOT / 'work/analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'categories'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
