"""Build the public minimap ZIP: unmodified BepInEx + own plugin + readme. No game files.

Run build.py first (it compiles the plugin against the local interop). The ZIP goes to
<game>/dist and, with the BepInEx source archive (LGPL), to site/public/pobierz.
"""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

MOD = Path(__file__).resolve().parents[1]
GAME = MOD.parents[1]
REPO = GAME.parents[1]
VERSION = '1.1.0'
BEP_VERSION = '6.0.0-be.788'
BEP_COMMIT = '5b766a3b7f6c164d4798924a93f3acf4db769d06'
BINARY = REPO/'vendor/bepinex'/f'BepInEx-Unity.IL2CPP-win-x64-{BEP_VERSION}.zip'
SOURCE = REPO/'vendor/bepinex'/f'BepInEx-source-{BEP_VERSION}.zip'
DLL = GAME/'dist/minimap/BepInEx/plugins/notgeese.SilverPinesMinimap.dll'
PUBLIC = REPO/'site/public/pobierz'
PREFIX = 'BepInEx/plugins/SilverPinesMinimap/'
CFG = (b'[Logging]\n\nUnityLogListening = false\n\n'
       b'[Logging.Console]\n\nEnabled = false\n\n'
       b'[Logging.Disk]\n\nEnabled = true\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    source = (MOD/'plugin/Plugin.cs').read_text(encoding='utf-8')
    assert f'Version = "{VERSION}"' in source, 'Plugin version differs from release version'
    dll = DLL.read_bytes()
    assert DLL.stat().st_mtime >= (MOD/'plugin/Plugin.cs').stat().st_mtime, 'Stale DLL: run build.py'
    readme = (MOD/'docs/README.txt').read_text(encoding='utf-8').replace('{version}', VERSION)
    with zipfile.ZipFile(BINARY) as official, zipfile.ZipFile(SOURCE) as sources:
        files = {n: official.read(n) for n in official.namelist() if not n.endswith('/')}
        official_names = set(files)
        files.update({
            'BepInEx-LICENSE.txt': sources.read(f'BepInEx-{BEP_COMMIT}/LICENSE'),
            'BepInEx/config/BepInEx.cfg': CFG,
            PREFIX+'notgeese.SilverPinesMinimap.dll': dll,
            PREFIX+'LICENSE.txt': (REPO/'LICENSE').read_bytes(),
            'README-Minimap.txt': readme.replace('\n', '\r\n').encode('utf-8'),
            'dotnet/LICENSE.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/LICENSE.TXT').read_bytes(),
            'dotnet/THIRD-PARTY-NOTICES.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/THIRD-PARTY-NOTICES.TXT').read_bytes(),
        })
    forbidden = re.compile(r'(^|/)(?:GameAssembly\.dll|Assembly-CSharp\.dll|CarpenterScripts\.dll|UnityPlayer\.dll'
                           r'|global-metadata\.dat|level\d+|globalgamemanagers)$|\.(?:assets|bundle|resS|resource)$', re.I)
    for name, data in files.items():
        assert not forbidden.search(name), f'Game file in package: {name}'
        assert not any(p in name.lower().split('/') for p in ('interop', 'dummy', 'unity-libs', 'cache')), name
        # Nothing from the local machine (paths, folder names) may end up in the package.
        if name not in official_names:
            assert not re.search(rb'(?<![A-Za-z])[A-Za-z]:\\[A-Za-z]', data), f'Local path in {name}'
    out = GAME/'dist'/f'SilverPines-Minimap-{VERSION}.zip'
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None and set(archive.namelist()) == set(files)
    shutil.copy2(SOURCE, out.parent/SOURCE.name)
    for path in (out, SOURCE):
        shutil.copy2(path, PUBLIC/path.name)
    print(json.dumps({'package': str(out), 'bytes': out.stat().st_size, 'sha256': sha(out.read_bytes()),
                      'files': len(files), 'plugin_bytes': len(dll), 'bepinex': BEP_VERSION,
                      'published': [str(PUBLIC/out.name), str(PUBLIC/SOURCE.name)]}))


if __name__ == '__main__':
    main()
