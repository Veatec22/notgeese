"""Compile and run offline IL2CPP metadata tools. Does not start the game."""
from pathlib import Path
import json,shutil,subprocess
import pefile
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
BEP=REPO/'vendor/bepinex/il2cpp-pre2'
CSC=Path('C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe')

def managed(path):
    try:
        pe=pefile.PE(str(path),fast_load=True)
        return bool(pe.OPTIONAL_HEADER.DATA_DIRECTORY[14].VirtualAddress)
    except Exception:return False

def main():
    out=ROOT/'work/offline';out.mkdir(parents=True,exist_ok=True)
    refs=[]
    for folder in (BEP/'dotnet',BEP/'BepInEx/core'):
        for p in folder.glob('*.dll'):
            if managed(p):refs.append('/r:'+str(p))
            if folder.name=='core' or p.name.startswith('Microsoft.Extensions.'):
                shutil.copy2(p,out/p.name)
    dll=out/'GenerateInterop.dll'
    result=subprocess.run([str(CSC),'/nologo','/noconfig','/nostdlib+','/target:exe','/out:'+str(dll),*refs,str(ROOT/'tools/GenerateInterop.cs')])
    if result.returncode:raise SystemExit(result.returncode)
    (out/'GenerateInterop.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net6.0','rollForward':'Major','framework':{'name':'Microsoft.NETCore.App','version':'6.0.0'}}}))
    subprocess.run(['dotnet',str(dll),'C:/Games/Turbo Overkill',str(ROOT/'work'),str(ROOT/'work/unity-libs')],check=True)

if __name__=='__main__':main()
