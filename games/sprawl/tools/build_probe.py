"""Build a temporary English-slot probe to isolate pak loading from culture selection.

Uses the same v11 writer as the Polish build. Never installs or launches the game.
"""
import hashlib
import json
import sys
from pathlib import Path

import build
import locres
import pak


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / 'translations/en.locres'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == build.SOURCE_SHA256
    english = locres.load(source)
    texts = english.texts()
    sys.path.insert(0, str(root.parents[1] / 'tools'))
    from translations import polish_by_ref
    for key, text in polish_by_ref(root).items():
        assert key in texts
        texts[key] = text + ' [TEST PL]'
    resource = locres.dump(locres.translate(english, texts))
    inside = 'Sprawl/Content/Localization/Game/en/Game.locres'
    archive = pak.write({inside: resource}, seed=build.PATH_HASH_SEED)
    assert pak.read(archive) == (pak.MOUNT_POINT, {inside: resource})
    output = root / 'dist/probe'
    output.mkdir(parents=True, exist_ok=True)
    target = output / build.ARCHIVE
    target.write_bytes(archive)
    print(f'{target}: {len(archive)} bytes; {len(rows)} marked entries; English slot')


if __name__ == '__main__':
    main()
