"""Player package: two creating patches, the applier and READ-ME.txt.

    python release.py "<BPM>\\WindowsNoEditor" <version>

Runs build.py first. The pak patch rebuilds dist/BPM-PL_P.pak from slices of the
player's pakchunk0 (the two fonts and ICU's en.res, located through the decrypted
index); the signature patch copies an existing .sig of the game under our pak's name.
Output: dist/BPM-PL-<version>-latka.zip.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
import build
import patch
from game_pak import GamePak, load_key

PAKS = 'BPM/Content/Paks'
MAIN = f'{PAKS}/pakchunk0-WindowsNoEditor.pak'
SIGNATURE = f'{PAKS}/pakchunk0_s4-WindowsNoEditor.sig'
SLICED = [
    'BPM/Content/Fonts/MotorBlockFinalCyr.ufont',
    'BPM/Content/Fonts/RunyTunesRevisitedNF.ufont',
    'Engine/Content/Internationalization/icudt64l/lang/en.res',
]
ENTRY_HEADER = 53   # uncompressed v11 entry: offset, sizes, method, SHA-1, flags, block size


def slices(game):
    archive = GamePak(game / MAIN, load_key(ROOT))
    spans = []
    for name in SLICED:
        entry = archive.entry(name)
        assert not entry['method'] and not entry['encrypted'], name
        spans.append(f"{MAIN}@{entry['offset'] + ENTRY_HEADER}+{entry['size']}")
        assert patch.read_sources(game, spans[-1]) == archive.extract(name), name
    return ';'.join(spans)


def main():
    game, version = Path(sys.argv[1]), sys.argv[2]
    build.main()
    dist = ROOT / 'dist'
    signature = dist / 'BPM-PL_P.sig'
    shutil.copyfile(game / SIGNATURE, signature)
    size = signature.stat().st_size
    result = patch.release(
        [(game, dist / 'BPM-PL_P.pak', f'{PAKS}/BPM-PL_P.pak', {'sources': slices(game), 'create': True}),
         (game, signature, f'{PAKS}/BPM-PL_P.sig', {'sources': f'{SIGNATURE}@0+{size}', 'create': True})],
        ROOT / 'docs/INSTALL.txt', dist, 'bpm', 'BPM', version)
    for item in result['patches']:
        print(f"{Path(item['patch']).name}: {item['patch_bytes']} B, own bytes {item['added_bytes']}")
    print(f"{result['package']}: {result['package_bytes']} B")


if __name__ == '__main__':
    main()
