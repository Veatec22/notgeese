"""Build DEADBOLT PL and the Ultrawide mod from one d3d9.dll; never installs or starts the game.

Both packages ship the same DLL (source: games/deadbolt/plugin, features switched on by their
files), so either can be extracted alone or over the other. Builds the PL ZIP through
tools/build_plugin.py, then the mod ZIP, checks the DLLs are byte-identical and copies both to
site/public/pobierz.

    .venv\\Scripts\\python.exe games\\deadbolt\\mods\\ultrawide\\tools\\release.py
"""
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

MOD = Path(__file__).resolve().parents[1]
GAME = MOD.parents[1]
REPO = GAME.parents[1]
sys.path.insert(0, str(GAME / 'tools'))
import build_plugin  # noqa: E402

VERSION = '1.0.0'
PACKAGE = f'Deadbolt-Ultrawide-{VERSION}.zip'
PUBLIC = REPO / 'site/public/pobierz'
# User-editable settings; GetPrivateProfileInt skips ; comments.
INI = ('[Ultrawide]\r\n'
       '; 1 = on, 0 = off (restart the game)\r\n'
       'Enabled=1\r\n'
       '; Virtual width at 540 px height. 0 = match the main display (21:9 -> 1280, 32:9 -> 1920)\r\n'
       'VirtualWidth=0\r\n')


def main():
    build_plugin.build()
    dist = GAME / 'dist'
    dll = (dist / 'd3d9.dll').read_bytes()
    files = {
        'd3d9.dll': dll,
        'ultrawide/settings.ini': INI.encode('ascii'),
        'ultrawide/LICENSE.txt': (REPO / 'LICENSE').read_bytes(),
        'ultrawide/LICENSE-MINHOOK.txt': (dist / 'notgeese/LICENSE-MINHOOK.txt').read_bytes(),
        'README-Ultrawide.txt': (MOD / 'docs/README.txt').read_text(encoding='utf-8')
            .replace('{version}', VERSION).replace('\n', '\r\n').encode('utf-8'),
    }
    for name, data in files.items():
        assert not name.lower().endswith(('.win', '.exe', '.ogg', '.png', '.json')), name
        if name != 'd3d9.dll':
            assert not re.search(rb'(?<![A-Za-z])[A-Za-z]:\\[A-Za-z]', data), f'Local path in {name}'
    out = dist / PACKAGE
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    pl = dist / build_plugin.PACKAGE
    with zipfile.ZipFile(out) as mod, zipfile.ZipFile(pl) as translation:
        assert mod.testzip() is None and sorted(mod.namelist()) == sorted(files)
        assert mod.read('d3d9.dll') == translation.read('d3d9.dll'), 'PL and mod DLLs differ'
        assert not any(n.startswith('ultrawide/') for n in translation.namelist()), 'PL package must not switch ultrawide on'
        assert not any(n.startswith('notgeese/') for n in mod.namelist()), 'mod files live in ultrawide/'
    for path in (out, pl):
        shutil.copy2(path, PUBLIC / path.name)
    print(json.dumps({'mod': PACKAGE, 'mod_bytes': out.stat().st_size, 'pl': pl.name, 'pl_bytes': pl.stat().st_size,
                      'dll_sha256': hashlib.sha256(dll).hexdigest(), 'published': str(PUBLIC)}))


if __name__ == '__main__':
    main()
