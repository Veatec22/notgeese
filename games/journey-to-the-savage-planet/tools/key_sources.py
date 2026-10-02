"""Map every Game.locres key to the assets that define it (context for translation and groups).

Scans all .uasset/.uexp/.umap in the game's pak for the key strings of the English locres.
Writes work/key-sources.json: {"<namespace>|<key>": ["Towers/Content/...", ...]}.
Analysis only; reads the pak, writes only to work/.
"""
import argparse
import json
from pathlib import Path
from game_pak import GamePak
import locres
import re

GUID = re.compile(rb"[0-9A-F]{32}")

ROOT = Path(__file__).resolve().parents[1]
PAK = 'Towers/Content/Paks/Towers-WindowsNoEditor.pak'
SOURCE = ROOT / 'work/extract/Towers/Content/Localization/Game/en/Game.locres'
OUT = ROOT / 'work/key-sources.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path, help='Game folder (the one holding Towers.exe)')
    args = parser.parse_args()
    pak = GamePak(args.game / PAK)
    english = locres.load(SOURCE)
    # Only GUID keys (blueprint and widget texts) need locating; data-table keys are row names
    # and their namespace already names the table.
    needles = {}
    for (ns, key) in english.texts():
        if GUID.fullmatch(key.encode('ascii', 'replace')):
            needles.setdefault(key.encode('ascii'), []).append(f'{ns}|{key}')
    found = {}
    names = [n for n in pak.entries if n.endswith(('.uasset', '.uexp', '.umap'))]
    for i, name in enumerate(names):
        data = pak.extract(name)
        for needle in set(GUID.findall(data)) & needles.keys():
            for id_ in needles[needle]:
                found.setdefault(id_, set()).add(name.rsplit('.', 1)[0])
        if i % 2000 == 0:
            print(f'{i}/{len(names)}', flush=True)
    OUT.write_text(json.dumps({k: sorted(v) for k, v in sorted(found.items())}, indent=1), encoding='utf-8')
    print(f'{len(found)} of {len(english.texts())} keys located -> {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
