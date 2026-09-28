"""Build the Polish localization resource for SPRAWL.

The game keeps one .locres per culture under Content/Localization/Game/. Eleven
were shipped; Polish was not, although the project's own Game.locmeta lists `pl`
among its 32 target cultures. The released game has a flag-based language
selector. The Polish entry, flag and persistence have passed in-game testing.

The archive includes the full 717-entry pl/Game.locres, the extended locale map
and a separate Polish flag. All existing languages remain available.

Never writes into the game directory; output goes to a separate folder.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import locres
import pak
import selector
from validate_translations import validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, polish_by_ref  # noqa: E402
VERSION = '0.1'
CULTURE = 'pl'
INSIDE = f'Sprawl/Content/Localization/Game/{CULTURE}/Game.locres'
ARCHIVE = 'Sprawl-WindowsNoEditor_pl_P.pak'
PATH_HASH_SEED = 47419669          # the seed the game's own archive carries

# en/Game.locres as shipped in Sprawl-WindowsNoEditor.pak, GOG build checked 2026-09-19.
SOURCE_SHA256 = '514cdb17b9add2a80828bed6178da326e77f0bbef766a8cd9fa6cc44d06c65f7'


def main():
    if not __debug__:
        raise RuntimeError('Run without -O: validation assertions are required.')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, default=ROOT / 'translations/en.locres',
                        help="The game's own en/Game.locres, extracted from the pak")
    parser.add_argument('--output', type=Path, default=ROOT / 'dist', help='Separate output directory')
    parser.add_argument('--assets', type=Path, default=ROOT / 'work/assets',
                        help='Extracted original locale and flag assets for the Polish selector')
    args = parser.parse_args()

    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f'{args.source.name}: unsupported or already modified source.\n'
                         f'  expected SHA-256 {SOURCE_SHA256}\n'
                         f'  got               {digest}\nNothing was written.')

    english = locres.load(args.source)
    available = english.texts()

    translations = polish_by_ref(ROOT)
    unknown = [k for k in translations if k not in available]
    assert not unknown, f'Keys not present in the English resource: {unknown[:5]}'
    review = load_entries(ROOT)
    validate(english, translations, review)

    polish = locres.translate(english, translations)
    data = locres.dump(polish)

    destination = args.output.resolve() / Path(INSIDE).parent
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / 'Game.locres'
    target.write_bytes(data)

    # --- verification: read the built file back and compare it to what went in ---
    built = locres.load(target)
    assert built.version == english.version
    assert built.texts() == translations, 'The built resource does not read back as written.'
    by_key = {(n, e.key): e for n, e in english.entries()}
    for namespace, entry in built.entries():
        original = by_key[(namespace, entry.key)]
        assert entry.key_hash == original.key_hash, entry.key
        assert entry.source_hash == original.source_hash, entry.key
    carried = {h for h, _, _ in built.namespaces}
    assert carried <= {h for h, _, _ in english.namespaces}, 'A namespace hash was invented.'

    # --- the archive: a packaged build reads its content out of paks, never off disk ---
    files = selector.build_assets(args.assets, args.output.resolve() / 'selector')
    files[INSIDE] = data
    assert not any('/en/' in name for name in files), 'English must stay untouched.'
    archive = pak.write(files, seed=PATH_HASH_SEED)
    bundle = args.output.resolve() / ARCHIVE
    bundle.write_bytes(archive)
    mount, packed = pak.read(archive)
    assert mount == pak.MOUNT_POINT and packed == files, 'The archive does not read back.'

    release = args.output.resolve() / f'SPRAWL-PL-{VERSION}.zip'
    with zipfile.ZipFile(release, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        package.write(bundle, f'Sprawl/Content/Paks/{ARCHIVE}')
        package.write(ROOT / 'docs/INSTALL.txt', 'READ-ME.txt')

    print(json.dumps({
        'version': VERSION,
        'culture': CULTURE,
        'translated': len(translations),
        'of_entries': sum(len(e) for _, _, e in english.namespaces),
        'polish_characters': sum(len(v) for v in translations.values()),
        'namespaces': {name: len(entries) for _, name, entries in polish.namespaces},
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest()[:16],
        'locres': str(target),
        'archive': str(bundle),
        'archive_bytes': len(archive),
        'zip': str(release),
        'install_as': f'Sprawl/Content/Paks/{ARCHIVE}',
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
