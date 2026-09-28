"""Compile and run the translation engine test; no game launch."""
import shutil
import subprocess
import sys
from build_plugin import ROOT, compiler_environment

env = compiler_environment()
compiler = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
work = ROOT / 'work/build'
work.mkdir(parents=True, exist_ok=True)
subprocess.run([compiler, '/nologo', '/EHsc', '/std:c++17', '/utf-8', '/O2', '/W4',
                str(ROOT / 'tools/translate_test.cpp'), '/Fe:' + str(work / 'translate_test.exe')],
               cwd=work, env=env, check=True, stdout=subprocess.DEVNULL)
tsv = ROOT / 'dist/notgeese/pl.tsv'
args = [str(tsv)] if '--tsv' in sys.argv else []
if '--preview' in sys.argv:
    args.append(sys.argv[sys.argv.index('--preview') + 1])
if '--dialogs' in sys.argv:
    args.append(sys.argv[sys.argv.index('--dialogs') + 1])
sys.exit(subprocess.run([str(work / 'translate_test.exe')] + args).returncode)
