"""Compile against offline-generated IL2CPP bindings; never executes the game."""
import subprocess

from prepare_interop import BEP, CSC, ROOT, managed

NAME = 'notgeese.ElPasoElsewhere'


def compile_plugin():
    refs = []
    for folder in (BEP/'dotnet', BEP/'BepInEx/core', ROOT/'work/interop'):
        for path in folder.glob('*.dll'):
            if managed(path):
                refs.append('/r:'+str(path))
    output = ROOT/'work'/(NAME+'.dll')
    result = subprocess.run([str(CSC), '/nologo', '/noconfig', '/nostdlib+', '/optimize+', '/unsafe+',
                             '/target:library', '/out:'+str(output), *refs,
                             *[str(p) for p in sorted((ROOT/'plugin').glob('*.cs'))]])
    if result.returncode:
        raise SystemExit('Plugin compilation failed.')
    return output


if __name__ == '__main__':
    compile_plugin()
