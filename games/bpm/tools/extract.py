"""Pull the files the build needs out of the player's own BPM install.

    python extract.py "<BPM>\\WindowsNoEditor"

Reads the AES key out of the game's executable (find_key), decrypts the pak index and
writes the needed entries under work/extract, plus the other languages' Game.locres
under work/extract too (reference only). Nothing extracted goes into the repository.
"""
import re
import struct
import sys
from pathlib import Path

from Crypto.Cipher import AES

sys.path.insert(0, str(Path(__file__).resolve().parent))
from game_pak import GamePak

ROOT = Path(__file__).resolve().parents[1]
WANTED = [
    'BPM/Content/Localization/Game/en/Game.locres',
    'BPM/Content/Fonts/MotorBlockFinalCyr.ufont',
    'BPM/Content/Fonts/RunyTunesRevisitedNF.ufont',
    'Engine/Content/Internationalization/icudt64l/lang/en.res',
]
REFERENCE = re.compile(r'BPM/Content/Localization/Game/[^/]+/Game\.locres')


def find_key(exe, pak):
    """The key is written by eight `mov dword [base+disp], imm32` stores, interleaved
    with other code. Collect such stores in a sliding window and try every 32-byte run
    against the first encrypted block of the index: it must decrypt to the mount point."""
    data = exe.read_bytes()
    with pak.open('rb') as f:
        f.seek(-221 + 25, 2)
        offset = struct.unpack('<q', f.read(8))[0]
        f.seek(offset)
        block = f.read(16)
    stores = []
    for m in re.finditer(rb'\xC7([\x40-\x47\x80-\x87\x00-\x03\x06\x07])', data):
        j = m.start(); modrm = data[j + 1]; mod = modrm >> 6; k = j + 2
        base = data[k] if modrm & 7 == 4 else modrm & 7
        if modrm & 7 == 4:
            k += 1
        if mod == 0:
            disp = 0
        elif mod == 1:
            disp = struct.unpack_from('<b', data, k)[0]; k += 1
        else:
            disp = struct.unpack_from('<i', data, k)[0]; k += 4
        stores.append((j, base, disp, data[k:k + 4]))
    tried = set()
    for a, (at, base, start, _) in enumerate(stores):
        window = {}
        for j, b, disp, imm in stores[a:a + 40]:
            if j - at > 400:
                break
            window.setdefault((b, disp), imm)
        if all((base, start + 4 * q) in window for q in range(8)):
            key = b''.join(window[(base, start + 4 * q)] for q in range(8))
            if key in tried:
                continue
            tried.add(key)
            if AES.new(key, AES.MODE_ECB).decrypt(block)[4:13] == b'../../../':
                return key
    sys.exit('AES key not found in the executable.')


def main():
    game = Path(sys.argv[1])
    paks = sorted((game / 'BPM/Content/Paks').glob('pakchunk*.pak'))
    key_file = ROOT / 'work/aes.key'
    if key_file.exists():
        key = bytes.fromhex(key_file.read_text().strip())
    else:
        key = find_key(game / 'BPM/Binaries/Win64/BPMGame-Win64-Shipping.exe', paks[0])
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(key.hex())
    out = ROOT / 'work/extract'
    found = set()
    for path in paks:
        archive = GamePak(path, key)
        for name in archive.files:
            if name in WANTED or REFERENCE.fullmatch(name):
                target = out / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extract(name))
                found.add(name)
    missing = set(WANTED) - found
    assert not missing, missing
    print(f'{len(found)} files -> {out}')


if __name__ == '__main__':
    main()
