"""Build the Polish resources.assets from the original (input for tools/patch.py release); never launches."""
import argparse
import hashlib
import json
import sys
import re
import struct
from pathlib import Path
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from i2 import parse, parse_languages, integer, string

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402
SHA = '3e65be29272f5879bd907a0d0c7f8134f5b5bd35902263dc65381bb0c3a7a82c'
PL = 15
FONT_MAP = {
    'Fonts/BigCaslon': 'ru-serif-bigcaslon Regular',
    'Fonts/BigCaslon SDF': 'ru-serif-bigcaslon Regular SDF',
    'Fonts/Cochin': 'ru-serif-bigcaslon Regular',
    'Fonts/Cochin SDF': 'ru-serif-bigcaslon Regular SDF',
    'Fonts/HelveticaRounded-Bold': 'LiberationSans',
    'Fonts/HelveticaRounded-Bold SDF': 'LiberationSans SDF',
    'Fonts/IMFellDoublePica-Italic SDF': 'IMFellDoublePica-Italic SDF',
    'Fonts/IMFellDoublePica-Regular SDF': 'IMFellDoublePica-Regular SDF',
    'Fonts/PortraitDialogue-Text': 'ru-serif-bigcaslon Regular SDF',
}


def serialize(header, rows, tail):
    out = bytearray(header + integer(len(rows)))
    for key, kind, values, flags, touch in rows:
        out += string(key) + integer(kind) + integer(len(values))
        out += b''.join(string(v) for v in values)
        out += integer(len(flags)) + flags + bytes(-len(flags) % 4)
        out += integer(len(touch)) + b''.join(string(v) for v in touch)
    return bytes(out) + tail


def main():
    if not __debug__:
        raise RuntimeError('Run without -O; validation assertions are required.')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original', type=Path, required=True)
    ap.add_argument('--managed', type=Path, required=True)
    ap.add_argument('--extract', action='store_true')
    args = ap.parse_args()
    assert hashlib.sha256(args.original.read_bytes()).hexdigest() == SHA, 'Unsupported original'
    env = UnityPy.load(str(args.original))
    objects = {o.path_id: o for o in env.objects}
    obj = objects[785]
    raw = obj.get_raw_data()
    rows, tail = parse(raw)
    assert len(rows) == 2314
    assert serialize(raw[:56], rows, tail) == raw
    langs, end = parse_languages(tail)
    assert len(langs) == 20 and langs[PL] == ('Polish', 'pl', integer(1))
    pl = polish_by_key(ROOT)
    source = {k: v[0] for k, t, v, _, _ in rows if t == 0}
    assert len(source) == 2305 and pl.keys() == source.keys(), 'Incomplete translation'
    tokens = lambda s: re.findall(r'<[^>]+>|\{[^}]+\}|\*\w+\*|\*\*|\([A-Z]\)', s)
    for key, value in pl.items():
        assert isinstance(value, str) and value.strip() and '\ufffd' not in value, key
        assert tokens(value) == tokens(source[key]), f'Tokens: {key}'
        assert value.count('\n') == source[key].count('\n'), f'Line breaks: {key}'
    notes = json.loads((ROOT / 'translations/review-notes.json').read_text(encoding='utf-8'))
    assert notes.keys() <= source.keys()
    review = [{'key': k, 'english': v[0], 'polish': pl[k],
               'context': v[2], 'status': 'review_requested' if k in notes else 'translated',
               **({'notes': notes[k]} if k in notes else {})}
              for k, t, v, _, _ in rows if t == 0]
    review_path = ROOT / 'translations/en-pl-review.json'
    if args.extract:
        write_entries(ROOT, review)
        print(json.dumps({'translated': sum(bool(x['polish']) for x in review), 'total': len(review)}))
        return
    assert json.loads(review_path.read_text(encoding='utf-8')) == review
    # Verify the existing font source relationships; no global font asset is changed.
    gen = TypeTreeGenerator('6000.0.45f1')
    gen.load_local_dll_folder(str(args.managed))
    nodes = gen.get_nodes_up('Unity.TextMeshPro', 'TMPro.TMP_FontAsset')
    for font_id, source_id in [(810, 555), (797, 556), (798, 569), (789, 566)]:
        font = objects[font_id].read_typetree(nodes=nodes)
        assert font['m_AtlasPopulationMode'] == 1
        assert font['m_SourceFontFile'] == {'m_FileID': 0, 'm_PathID': source_id}
    sans = objects[791].read_typetree(nodes=nodes)
    assert {'m_FileID': 0, 'm_PathID': 789} in sans['m_FallbackFontAssetTable']
    # Source's final field is its 49-item asset-reference array. Register existing sans fonts.
    asset_start = len(tail) - (4 + 49 * 12)
    assert struct.unpack_from('<i', tail, asset_start)[0] == 49 and asset_start > end
    refs = [struct.unpack_from('<iq', tail, asset_start+4+i*12) for i in range(49)]
    for ref in [(0, 566), (0, 791)]:
        if ref not in refs:
            refs.append(ref)
    new_tail = bytearray(tail[:12] + integer(20))
    for i, (name, code, flags) in enumerate(langs):
        new_tail += string(name) + string(code) + (integer(0) if i == PL else flags)
    new_tail += tail[end:asset_start] + integer(len(refs))
    new_tail += b''.join(struct.pack('<iq', *ref) for ref in refs)
    patched_rows = []
    for k, t, values, flags, touch in rows:
        vs, fs, ts = values.copy(), bytearray(flags), touch.copy()
        assert len(vs) == len(fs) == 20
        vs[PL] = FONT_MAP[k] if t else pl[k]
        fs[PL] = 0
        if ts:
            assert len(ts) == 20
            ts[PL] = vs[PL]
        patched_rows.append((k, t, vs, bytes(fs), ts))
    patched = serialize(raw[:56], patched_rows, bytes(new_tail))
    assert parse(patched) == (patched_rows, bytes(new_tail))
    before = {i: o.get_raw_data() for i, o in objects.items()}
    obj.set_raw_data(patched)
    target = ROOT / 'dist/SkateStory_Data/resources.assets'
    assert target.resolve() != args.original.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(obj.assets_file.save())
    after = {o.path_id: o.get_raw_data() for o in UnityPy.load(str(target)).objects}
    assert before.keys() == after.keys()
    assert [i for i in before if before[i] != after[i]] == [785]
    assert after[785] == patched
    for old, new in zip(rows, parse(after[785])[0]):
        assert old[:2] == new[:2]
        for col in range(20):
            if col != PL:
                assert old[2][col] == new[2][col] and old[3][col] == new[3][col]
                if old[4]:
                    assert old[4][col] == new[4][col]
    print(json.dumps({'translated': sum(bool(x['polish']) for x in review), 'total': len(review),
                      'changed_objects': [785], 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                      'output': str(target)}))


if __name__ == '__main__':
    main()
