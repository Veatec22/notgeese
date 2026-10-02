"""QoL, not part of the PL package: widen the HUD for ultrawide (see docs/qol.md).

The HUD sits in a SizeBox whose size UI_HUD sets per `Visual.CameraAspectRatio`
(4:3 1440x1080, 16:9 1920x1080, 16:10 1280x800); UI_TutorialPopup uses a fixed
640x480 box. This rewrites the 16:9 and 16:10 widths and the popup width for the
target aspect and writes an overlay `pakchunk98-ultrawideHUD_P` to work/ultrawide/.
Carries two whole game widgets, so it is personal-use only, never shipped.

    .venv\\Scripts\\python.exe games\\labyrinth-of-the-demon-king\\tools\\ultrawide.py --aspect 32:9
"""
import argparse
import struct
from pathlib import Path

import pak
from iostore import Store, write_overlay

ROOT = Path(__file__).resolve().parents[1]
HUD = 'Shinigami/Content/Blueprints/Widgets/HUD/UI_HUD.uasset'
POPUP = 'Shinigami/Content/Blueprints/Widgets/HUD/UI_TutorialPopup.uasset'
STEM = 'pakchunk98-ultrawideHUD_P'
WIDTH_CALL = bytes.fromhex('1c84ffffff1e')  # width setter call, then float const


def names_of(data):
    at, end = struct.unpack_from('<2i', data, 24)
    end += at
    names = []
    while at < end:
        size = int.from_bytes(data[at:at + 2], 'big'); at += 2
        wide = bool(size & 0x8000); size &= 0x7fff
        length = size * (2 if wide else 1)
        names.append(data[at:at + length].decode('utf-16-le' if wide else 'utf-8')); at += length
    return names


def replace_once(data, old, new):
    at = data.find(old)
    assert at >= 0 and data.find(old, at + 1) == -1, old.hex()
    data[at:at + len(old)] = new


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, default=Path('C:/Games/Labyrinth Of The Demon King'))
    ap.add_argument('--aspect', default='32:9', help='screen aspect, e.g. 21:9 or 32:9')
    args = ap.parse_args()
    w, h = map(float, args.aspect.split(':'))
    ratio = w / h
    source = Store(args.game / 'Shinigami/Content/Paks/pakchunk0-WindowsNoEditor')

    hud = bytearray(source.read(source.paths[HUD]))
    for old_width, height in ((1920.0, 1080.0), (1280.0, 800.0)):
        replace_once(hud, WIDTH_CALL + struct.pack('<f', old_width) + b'\x16',
                     WIDTH_CALL + struct.pack('<f', height * ratio) + b'\x16')

    popup = bytearray(source.read(source.paths[POPUP]))
    names = names_of(popup)
    tag = struct.pack('<IIIIQ', names.index('WidthOverride'), 0, names.index('FloatProperty'), 0, 4) + b'\0'
    replace_once(popup, tag + struct.pack('<f', 640.0), tag + struct.pack('<f', 480.0 * ratio))

    base = ROOT / 'work' / 'ultrawide' / STEM
    report = write_overlay(source, {HUD: bytes(hud), POPUP: bytes(popup)}, base)
    base.with_suffix('.pak').write_bytes(pak.write({'Shinigami/Content/notgeese-ultrawide-hud.txt': f'HUD widened for {args.aspect}\n'.encode()}))
    print(report, '->', base.parent)


if __name__ == '__main__':
    main()
