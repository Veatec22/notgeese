"""Build a plugin-only vertical ZIP. Game files/interops are never distributed."""
import collections
import hashlib
import json
import sys
import re
import shutil
import zipfile
from pathlib import Path
from compile_plugin import compile_plugin

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))

from translations import load_entries, polish_by_key  # noqa: E402
VERSION = '0.1'
BEP_VERSION = '6.0.0-pre.2'
BINARY = REPO/'vendor/bepinex'/f'BepInEx-Unity.IL2CPP-win-x64-{BEP_VERSION}.zip'
SOURCE = REPO/'vendor/bepinex'/f'BepInEx-source-{BEP_VERSION}.zip'
PREFIX = 'BepInEx/plugins/notgeeseTurboOverkill/'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def validate_texts():
    pl = polish_by_key(ROOT)
    review = load_entries(ROOT)
    indexed = {row['key']: row for row in review}
    assert len(indexed) == len(review), 'Duplicate review key'
    assert pl and not set(pl).difference(indexed), 'Unknown translation IDs'
    tokens = re.compile(r'\[input:[^\]]+\]|\{[^{}]+\}|</?[^>]+>')
    for key, value in pl.items():
        source = indexed[key]['english']
        assert isinstance(value, str) and value.strip() and '\ufffd' not in value, key
        assert collections.Counter(tokens.findall(source)) == collections.Counter(tokens.findall(value)), ('tokens', key)
        # Hand-wrapped, indented continuation lines in dialogue logs may be joined.
        wraps = len(re.findall(r'\n[ \t]+\S', source))
        assert value.count('\n') in (source.count('\n'), source.count('\n') - wraps), ('newlines', key)
    return len(pl), len(review)

def package_texts():
    """pl.json for the plugin, built from en-pl-review.json; not stored in the repo."""
    return (json.dumps(polish_by_key(ROOT), ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def main():
    count, total = validate_texts()
    dll = compile_plugin()
    out = ROOT/'dist'/f'Turbo-Overkill-PL-{VERSION}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    # Exact allowlist and byte comparison, including every official runtime file.
    # Do not collect staging directories or game directories with rglob.
    with zipfile.ZipFile(BINARY) as official, zipfile.ZipFile(SOURCE) as sources:
        expected = {n: official.read(n) for n in official.namelist() if not n.endswith('/')}
        expected.update({
            'BepInEx-LICENSE.txt': sources.read(f'BepInEx-{BEP_VERSION}/LICENSE'),
            PREFIX+'notgeese.TurboOverkill.dll': dll.read_bytes(),
            PREFIX+'pl.json': package_texts(),
            PREFIX+'LICENSE-notgeese.txt': (REPO/'LICENSE').read_bytes(),
            'READ-ME.txt': (ROOT/'docs/INSTALL-plugin.txt').read_bytes(),
            'BepInEx/config/BepInEx.cfg': b'[Logging.Console]\nEnabled = false\n\n[Logging.Disk]\nEnabled = true\n',
            'dotnet/LICENSE.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/LICENSE.TXT').read_bytes(),
            'dotnet/THIRD-PARTY-NOTICES.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/THIRD-PARTY-NOTICES.TXT').read_bytes(),
        })
    forbidden = re.compile(r'(^|/)(?:GameAssembly\.dll|Assembly-CSharp(?:-firstpass)?\.dll|UnityPlayer\.dll|global-metadata\.dat|data\.unity3d)$|\.(?:assets|bundle|resS|resource)$', re.I)
    for name in expected:
        assert not forbidden.search(name), f'Game asset in package: {name}'
        assert not any(part in name.lower().split('/') for part in ('interop', 'dummy', 'unity-libs')), name
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in expected.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(out) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(expected)
        assert all(archive.read(n) == data for n, data in expected.items())
    shutil.copy2(SOURCE, out.parent/SOURCE.name)
    report = {'version': VERSION, 'entries': count, 'total': total, 'package': str(out),
              'package_bytes': out.stat().st_size, 'sha256': sha(out.read_bytes()),
              'plugin_bytes': dll.stat().st_size, 'bepinex': BEP_VERSION,
              'source_sha256': sha(SOURCE.read_bytes()), 'files': len(expected),
              'package_validation': 'exact allowlist; official files byte-identical; no game assets',
              'game_test': 'pending user', 'files_sha256': {n: sha(d) for n,d in expected.items()}}
    (ROOT/'work/build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'files_sha256'}))

if __name__ == '__main__':
    main()
