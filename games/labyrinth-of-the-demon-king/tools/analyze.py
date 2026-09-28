"""Extract localization and verify codecs/fonts without modifying or running the game."""
import argparse
import hashlib
import json
import sys
import re
import struct
from pathlib import Path
from game_pak import GamePak
import locres
import pak

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, review_path, write_entries  # noqa: E402
PAK_SHA = 'e2be58acee1ecdbe04b3147612b298a2112791b98a2fc2d80658433bc91f3d48'
EN_SHA = 'a21b8c409d78fd066ef0a5cd9f4e41efc11dccf6bea74a321ec7d35387cad846'


def has_glyph(data, cp):
    tables = {data[12+i*16:16+i*16].decode(): struct.unpack_from('>II', data, 20+i*16)
              for i in range(struct.unpack_from('>H', data, 4)[0])}
    base = tables['cmap'][0]
    for i in range(struct.unpack_from('>H', data, base+2)[0]):
        platform, enc, offset = struct.unpack_from('>HHI', data, base+4+8*i)
        if platform not in (0, 3): continue
        at = base+offset
        fmt = struct.unpack_from('>H', data, at)[0]
        if fmt == 4 and cp <= 65535:
            n = struct.unpack_from('>H', data, at+6)[0]//2
            for j in range(n):
                end = struct.unpack_from('>H', data, at+14+2*j)[0]
                start = struct.unpack_from('>H', data, at+16+2*n+2*j)[0]
                if start <= cp <= end:
                    delta = struct.unpack_from('>h', data, at+16+4*n+2*j)[0]
                    rp = at+16+6*n+2*j
                    ro = struct.unpack_from('>H', data, rp)[0]
                    glyph = ((cp+delta)&65535) if not ro else struct.unpack_from('>H', data, rp+ro+2*(cp-start))[0]
                    if ro and glyph: glyph = (glyph+delta)&65535
                    if glyph: return True
        elif fmt == 12:
            for j in range(struct.unpack_from('>I', data, at+12)[0]):
                start, end, glyph = struct.unpack_from('>III', data, at+16+12*j)
                if start <= cp <= end and glyph+cp-start: return True
    return False


def main():
    if not __debug__: raise RuntimeError('Validation requires assertions; do not use -O.')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    original = args.game/'Shinigami/Content/Paks/pakchunk0-WindowsNoEditor.pak'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == PAK_SHA, 'Unsupported game build'
    source = GamePak(original)
    work, translations = ROOT/'work', ROOT/'translations'
    work.mkdir(exist_ok=True); translations.mkdir(exist_ok=True)
    enpath = 'Shinigami/Content/Localization/Game/en/Game.locres'
    data = source.extract(enpath)
    assert hashlib.sha256(data).hexdigest() == EN_SHA
    enfile = work/'en.locres'; enfile.write_bytes(data)
    english = locres.load(enfile)
    assert locres.dump(english) == data
    assert len(english.texts()) == 1120
    polish = polish_by_key(ROOT) if review_path(ROOT).exists() else {}
    assert polish.keys() <= {e.key for _, e in english.entries()}
    review = [{'key': e.key, 'english': e.text, 'polish': polish.get(e.key, ''),
               'namespace': ns, 'status': 'translated' if e.key in polish else 'untranslated'}
              for ns,e in english.entries()]
    write_entries(ROOT, review)
    cultures = {}
    for name in source.files:
        if re.fullmatch('Shinigami/Content/Localization/Game/[^/]+/Game.locres', name):
            path = work/'cultures'/name.split('/')[-2]/'Game.locres'
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source.extract(name))
            cultures[name.split('/')[-2]] = len(locres.load(path).texts())
    fonts = {}
    for name in source.files:
        if name.startswith('Shinigami/Content/Fonts/') and name.endswith('.ufont'):
            font = source.extract(name)
            fonts[name] = {'missing_polish': ''.join(c for c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ' if not has_glyph(font, ord(c)))}
    # A codec probe, not a vertical or a release. Kept only under work/.
    key = next((ns,e.key) for ns,e in english.entries() if e.text == 'Language')
    sample = locres.translate(english, {key: 'Język — zażółć gęślą jaźń'})
    probe = work/'codec-probe.locres'; probe.write_bytes(locres.dump(sample))
    assert locres.load(probe).texts() == {key: 'Język — zażółć gęślą jaźń'}
    probe_pak = work/'codec-probe_P.pak'
    inner = 'Shinigami/Content/Localization/Game/pl/Game.locres'
    probe_pak.write_bytes(pak.write({inner: probe.read_bytes()}))
    assert GamePak(probe_pak).extract(inner) == probe.read_bytes()
    report = {'entries': len(review), 'english_characters': sum(len(r['english']) for r in review),
              'pak_sha256': PAK_SHA, 'english_locres_sha256': EN_SHA, 'cultures': cultures,
              'fonts': fonts, 'original_roundtrip': True, 'polish_codec_and_pak_roundtrip': True,
              'installed': False, 'game_started': False, 'in_game_test': 'not performed'}
    (work/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='fonts'},ensure_ascii=True))


if __name__ == '__main__': main()
