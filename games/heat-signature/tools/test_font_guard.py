"""Test the font failure fallback, without launching Heat Signature."""
import shutil
import subprocess
from build_plugin import ROOT, compiler_environment
from font_assets import build

env = compiler_environment()
compiler = shutil.which('cl.exe', path=next(v for k, v in env.items() if k.lower() == 'path'))
work = ROOT / 'work/build'
build(ROOT / 'dist/notgeese/fonts')
subprocess.run([compiler, '/nologo', '/EHsc', '/std:c++17', '/utf-8', '/MT',
                '/I' + str(ROOT / 'work/minhook-1.3.4/include'), str(ROOT / 'tools/font_guard_test.cpp'),
                *[str(work / (n + '.obj')) for n in ['buffer', 'hook', 'trampoline', 'hde32']],
                'version.lib', 'user32.lib', '/Fe:' + str(work / 'font_guard_test.exe')],
               cwd=work, env=env, check=True)
subprocess.run([str(work / 'font_guard_test.exe'), str(ROOT / 'dist')], check=True)
