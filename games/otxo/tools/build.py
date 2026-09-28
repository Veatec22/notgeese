"""Build the Polish language file for OTXO.

OTXO is GameMaker compiled to native code: `data.win` carries no bytecode, and
the seven language slots - their file names and their section headers - are
string literals inside OTXO_Release.exe. There is no eighth slot to fill and no
managed code to patch, so Polish has to take one of the seven over. The same
route the Japanese and Turkish fan translations took.

This build takes the **Simplified Chinese** slot, and the choice is about fonts,
not about language. Most of the game's typefaces are baked into data.win with
ASCII and Latin-1 only: they can draw 'ó' but not 'ę'. Chinese is the one slot
that loads its face from a file (yahei.ttf), and that face requests a range
covering Latin Extended-A, so every Polish letter renders. The French slot was
tried first and confirmed broken in game: 'Język' came out as 'J zyk'.
In the game's language menu Polish is therefore the Chinese flag - cosmetics,
not a defect. See README for the glyph tables behind this.

The file is not written from scratch. It is the English file with its section
header changed and the translated lines spliced in, so anything still untranslated
stays in English rather than going missing - and every blank line and oddity of
the original survives untouched. See script_ini.py.

Never writes into the game directory; output goes to a separate folder.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script_ini

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key  # noqa: E402
VERSION = '0.1'
SLOTS = {                      # slot -> section header the game looks for
    'zho-CN': 'chinese-simplified',
    'fre-FR': 'french',
    'ger-DE': 'german',
    'por-BR': 'portuguese',
    'rus': 'russian',
    'spa-ES': 'spanish',
}
SLOT = 'zho-CN'

# script_english.ini as shipped, GOG build checked 2026-09-20.
SOURCE_SHA256 = '99b2a4a2bee2502825012d71525fb743de4ffcdb065c859db2709bf53d301b0d'


def main():
    if not __debug__:
        raise RuntimeError('Run without -O: validation assertions are required.')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True, help='The OTXO folder, never written to')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist', help='Separate output directory')
    parser.add_argument('--slot', choices=sorted(SLOTS), default=SLOT,
                        help='Which language slot Polish takes over (default: %(default)s)')
    args = parser.parse_args()
    slot, section = args.slot, SLOTS[args.slot]
    target_name = f'OTXO_script_english_{slot}.ini'

    source = args.game.resolve() / 'script_english.ini'
    destination = args.output.resolve()
    if destination == args.game.resolve() or (destination / 'OTXO_Release.exe').exists():
        raise SystemExit('Choose an output directory outside the game installation.')

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if SOURCE_SHA256 and digest != SOURCE_SHA256:
        raise SystemExit(f'script_english.ini: unsupported or already modified.\n'
                         f'  expected SHA-256 {SOURCE_SHA256}\n'
                         f'  got               {digest}\nNothing was written.')

    english = script_ini.load(source)
    assert script_ini.section(source) == 'english'
    translations = polish_by_key(ROOT)
    unknown = [k for k in translations if k not in english]
    assert not unknown, f'Keys not present in the English file: {unknown[:5]}'

    built = script_ini.rewrite(source, section, translations)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / target_name
    target.write_bytes(built)

    # --- verification, against the English original ---
    readback = script_ini.load(target)
    assert script_ini.section(target) == section
    assert set(readback) == set(english), 'The set of keys changed.'
    for key, text in readback.items():
        expected = translations.get(key, english[key])
        assert text == expected, f'key {key}: {text!r} != {expected!r}'
    untouched = script_ini.rewrite(source, 'english', {})
    assert untouched == source.read_bytes(), 'The template no longer reproduces the original.'
    assert len(built.split(b'\r\n')) == len(source.read_bytes().split(b'\r\n')), 'Line count changed.'

    # --- package: one file to drop in, plus the instructions ---
    package = destination / f'OTXO-PL-{VERSION}.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(target, target_name)
        archive.write(ROOT / 'docs/INSTALL.txt', 'READ-ME.txt')
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert archive.read(target_name) == built, 'The archived file differs from the built one.'

    print(json.dumps({
        'version': VERSION,
        'slot': slot,
        'section': section,
        'translated': len(translations),
        'of_entries': len(english),
        'polish_characters': sum(len(v) for v in translations.values()),
        'bytes': len(built),
        'sha256': hashlib.sha256(built).hexdigest()[:16],
        'output': str(target),
        'install_as': target_name,
        'package': str(package),
        'package_bytes': package.stat().st_size,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
