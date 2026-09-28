"""Build BPM's Polish overlay pak.

Polish rides in the game's unused `ja` culture: the language list in C++ has a slot for
Japanese but the game ships no Japanese text (docs/technical.md). The pak carries:

  BPM/Content/Localization/Game/ja/Game.locres   ours: English resource, Polish where translated
  BPM/Content/Fonts/MotorBlockFinalCyr.ufont       game font + 16 Polish letters (fonts_pl.py)
  BPM/Content/Fonts/RunyTunesRevisitedNF.ufont     game font + 16 Polish letters
  Engine/.../icudt64l/lang/en.res                  ICU data: the name of `ja` reads „Polski”

Inputs come from the player's own copy of the game (work/extract, via extract.py), never
from the repository. Output: dist/BPM-PL_P.pak.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fonts_pl
import locres
import pak
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_ref  # noqa: E402
EXTRACT = ROOT / 'work/extract/BPM/Content'
EXTRACT_ROOT = ROOT / 'work/extract'
OUT = ROOT / 'dist/BPM-PL_P.pak'

ICU_EN = 'Engine/Content/Internationalization/icudt64l/lang/en.res'
FONTS = {'Fonts/MotorBlockFinalCyr.ufont': 'motorblock', 'Fonts/RunyTunesRevisitedNF.ufont': 'runytunes'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def rename_japanese(data):
    """The language list shows ICU's English name of the `ja` culture. In en.res it is
    one implicit-length UTF-16 string, NUL on both sides; overwrite it in place with a
    shorter one and pad with NULs, so no offset in the bundle moves."""
    old = '\x00Japanese\x00'.encode('utf-16-le')
    assert data.count(old) == 1, data.count(old)
    new = '\x00Polski\x00'.encode('utf-16-le')
    new += b'\x00' * (len(old) - len(new))
    return data.replace(old, new)


def main():
    pinned = json.loads((ROOT / 'tools/sources.json').read_text(encoding='utf-8'))
    for relative, expected in pinned.items():
        got = sha256((EXTRACT_ROOT / relative).read_bytes())
        if got != expected:
            sys.exit(f'{relative}: sha256 {got}, expected {expected} - other game version?')

    source = locres.load(EXTRACT / 'Localization/Game/en/Game.locres')
    english = source.texts()
    polish = polish_by_ref(ROOT)
    unknown = set(polish) - set(english)
    assert not unknown, f'{len(unknown)} keys not in the game: {sorted(unknown)[:5]}'
    texts = {key: polish.get(key, text) for key, text in english.items()}
    body = locres.dump(locres.translate(source, texts))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    check = OUT.with_suffix('.check.locres')
    check.write_bytes(body)
    assert locres.load(check).texts() == texts
    check.unlink()

    files = {'BPM/Content/Localization/Game/ja/Game.locres': body}
    for relative, style in FONTS.items():
        font = fonts_pl.open_font(EXTRACT / relative)
        fonts_pl.extend(font, style)
        built = OUT.parent / Path(relative).name
        font.save(built)
        cmap = TTFont(built).getBestCmap()
        assert all(ord(letter) in cmap for letter in fonts_pl.LETTERS), relative
        files['BPM/Content/' + relative] = built.read_bytes()
        built.unlink()

    icu = (EXTRACT_ROOT / ICU_EN).read_bytes()
    files[ICU_EN] = rename_japanese(icu)

    archive = pak.write(files)
    assert pak.read(archive) == ('../../../', files)
    OUT.write_bytes(archive)
    print(f'{OUT.name}: {len(archive)} B, {len(polish)}/{len(english)} entries in Polish')


if __name__ == '__main__':
    main()
