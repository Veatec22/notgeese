"""Compile the minimap plugin into <game>/dist/minimap; never installs or launches the game.

Compiles against the interop the player's BepInEx generated in <game>/BepInEx/interop (read only).
"""
import argparse
import subprocess
from pathlib import Path

import pefile

MOD = Path(__file__).resolve().parents[1]
GAME = MOD.parents[1]
REPO = GAME.parents[1]
BEP = REPO/'vendor/bepinex/il2cpp-be788'
CSC = Path('C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe')
NAME = 'notgeese.SilverPinesMinimap'


def managed(path):
    try:
        pe = pefile.PE(str(path), fast_load=True)
        return bool(pe.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    args = ap.parse_args()
    interop = args.game/'BepInEx/interop'
    assert (interop/'CarpenterScripts.dll').is_file(), f'No generated interop in {interop}; start the game once with BepInEx.'
    refs = ['/r:'+str(p) for folder in (BEP/'dotnet', BEP/'BepInEx/core', interop)
            for p in sorted(folder.glob('*.dll')) if managed(p)]
    out = GAME/'dist/minimap/BepInEx/plugins'
    out.mkdir(parents=True, exist_ok=True)
    dll = out/(NAME+'.dll')
    rsp = GAME/'work/minimap.rsp'
    rsp.parent.mkdir(parents=True, exist_ok=True)
    rsp.write_text('\n'.join(f'"{a}"' for a in [*refs, *map(str, sorted((MOD/'plugin').glob('*.cs')))]), encoding='utf-8')
    result = subprocess.run([str(CSC), '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/target:library',
                             '/nowarn:1701,1702', '/out:'+str(dll), '@'+str(rsp)])
    if result.returncode:
        raise SystemExit('Plugin compilation failed.')
    print(f'Built {dll} ({dll.stat().st_size} bytes); own code only, no game assets.')


if __name__ == '__main__':
    main()
