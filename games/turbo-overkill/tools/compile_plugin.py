"""Compile against offline-generated IL2CPP bindings; never executes the game."""
import subprocess
from prepare_interop import BEP, CSC, ROOT, managed

def compile_plugin():
    refs = []
    for folder in (BEP/'dotnet', BEP/'BepInEx/core', ROOT/'work/interop'):
        for path in folder.glob('*.dll'):
            if managed(path):
                refs.append('/r:'+str(path))
    output = ROOT/'work/notgeese.TurboOverkill.dll'
    result = subprocess.run([str(CSC), '/nologo', '/noconfig', '/nostdlib+', '/optimize+',
                    '/target:library', '/out:'+str(output), *refs,
                    str(ROOT/'plugin/Plugin.cs')])
    if result.returncode:
        raise SystemExit('Plugin compilation failed.')
    return output

if __name__ == '__main__':
    compile_plugin()
