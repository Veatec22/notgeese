"""Diagnostic build: Polish in the Italian slot, labelled "Polski" in the language selector.

The game's language list is 11 codes wired into the exe; its options widget forces the saved
subtitle language to one of them, so a new `pl` culture is reset to English. This probe
tests the slot route instead:

- dist/probe/Towers/Content/Paks/Towers-WindowsNoEditor_pl_P.pak with
  Localization/Game/it-IT/Game.locres: plain UI strings (unnamed namespace, no markup)
  prefixed "ĄŁ ", the rest left out (falls back to the English source).
- dist/probe/Towers/Binaries/Win64/Towers-Win64-Shipping.exe: the GOG exe with its one
  "Italiano" literal (culture display name) overwritten in place by "Polski".

Not a release artifact.
"""
import argparse
import hashlib
from pathlib import Path
import locres
import pak

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/extract/Towers/Content/Localization/Game/en/Game.locres'
OUT = ROOT / 'dist/probe'
LOCRES = 'Towers/Content/Localization/Game/it-IT/Game.locres'
PAK = 'Towers/Content/Paks/Towers-WindowsNoEditor_pl_P.pak'
EXE = 'Towers/Binaries/Win64/Towers-Win64-Shipping.exe'
EXE_SHA256 = 'b0ee2d93f627bfbda553f89fc9e01ba9026cfac1650b2e126c126a1d0528bc1a'   # GOG, 71 628 288 B
LABEL_AT = 0x296F810
OLD_LABEL = 'Italiano'.encode('utf-16-le') + b'\0\0'
NEW_LABEL = 'Polski'.encode('utf-16-le').ljust(len(OLD_LABEL), b'\0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path, help='Game folder (the one holding Towers.exe)')
    args = parser.parse_args()

    exe = bytearray((args.game / EXE).read_bytes())
    digest = hashlib.sha256(exe).hexdigest()
    if digest != EXE_SHA256:
        raise SystemExit(f'Unexpected exe {digest}, expected {EXE_SHA256}. Nothing written.')
    assert exe[LABEL_AT:LABEL_AT + len(OLD_LABEL)] == OLD_LABEL
    assert exe.count('Italiano'.encode('utf-16-le')) == 1
    exe[LABEL_AT:LABEL_AT + len(NEW_LABEL)] = NEW_LABEL

    english = locres.load(SOURCE)
    marked = {(ns, key): 'ĄŁ ' + text for (ns, key), text in english.texts().items()
              if ns == '' and text.strip() and '<' not in text and '{' not in text}
    body = locres.dump(locres.translate(english, marked))
    check = OUT / 'check.locres'
    check.parent.mkdir(parents=True, exist_ok=True)
    check.write_bytes(body)
    assert locres.load(check).texts() == marked
    check.unlink()
    archive = pak.write({LOCRES: body})
    assert pak.read(archive) == (pak.MOUNT_POINT, {LOCRES: body})

    for relative, data in ((PAK, archive), (EXE, exe)):
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f'{len(marked)} marked of {len(english.texts())}; pak {len(archive)} B; exe label at {LABEL_AT:#x} -> Polski')


if __name__ == '__main__':
    main()
