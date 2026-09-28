"""Compile and run offline IL2CPP metadata tools. Does not start the game.

Interop is only for compiling the plugin; the player's BepInEx generates its own on first start.
Unity base libraries: any 2021.3 set works for compiling (Turbo Overkill's 2021.3.11 is reused);
unpack `https://unity.bepinex.dev/libraries/2021.3.21.zip` into work/unity-libs to match exactly.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BEP = REPO/'vendor/bepinex/il2cpp-pre2'
CSC = Path('C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe')


def managed(path):
    try:
        pe = pefile.PE(str(path), fast_load=True)
        return bool(pe.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--unity-libs', type=Path, default=ROOT/'work/unity-libs')
    args = ap.parse_args()
    libs = args.unity_libs
    if not libs.is_dir():
        fallback = REPO/'games/turbo-overkill/work/unity-libs'
        assert fallback.is_dir(), f'No Unity base libraries in {libs}'
        libs = fallback
    out = ROOT/'work/offline'
    out.mkdir(parents=True, exist_ok=True)
    refs = []
    for folder in (BEP/'dotnet', BEP/'BepInEx/core'):
        for p in folder.glob('*.dll'):
            if managed(p):
                refs.append('/r:'+str(p))
            if folder.name == 'core' or p.name.startswith('Microsoft.Extensions.'):
                shutil.copy2(p, out/p.name)
    dll = out/'GenerateInterop.dll'
    result = subprocess.run([str(CSC), '/nologo', '/noconfig', '/nostdlib+', '/target:exe', '/out:'+str(dll), *refs,
                             str(ROOT/'tools/GenerateInterop.cs')])
    if result.returncode:
        raise SystemExit(result.returncode)
    (out/'GenerateInterop.runtimeconfig.json').write_text(json.dumps({'runtimeOptions': {
        'tfm': 'net6.0', 'rollForward': 'Major', 'framework': {'name': 'Microsoft.NETCore.App', 'version': '6.0.0'}}}))
    subprocess.run(['dotnet', str(dll), str(args.game), str(ROOT/'work'), str(libs)], check=True)
    print('Unity base libraries:', libs)


if __name__ == '__main__':
    main()
