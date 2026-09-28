"""Build the plugin package ZIP in dist/. Game files and interop are never distributed."""
import collections
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from compile_plugin import NAME, compile_plugin

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from translations import load_entries, untranslated  # noqa: E402

VERSION = '0.1'
BEP_VERSION = '6.0.0-pre.2'
BINARY = REPO/'vendor/bepinex'/f'BepInEx-Unity.IL2CPP-win-x64-{BEP_VERSION}.zip'
SOURCE = REPO/'vendor/bepinex'/f'BepInEx-source-{BEP_VERSION}.zip'
PREFIX = 'BepInEx/plugins/notgeeseElPasoElsewhere/'
# Namespace in en-pl-review.json → map in pl.json read by the plugin.
MAPS = {'i2': 'i2', 'ui': 'text', 'subtitle': 'text', 'code': 'text', 'pattern': 'pattern'}
TOKENS = re.compile(r'</?[a-zA-Z][^>]*>|\{\d+\}')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def texts():
    """pl.json for the plugin, built from en-pl-review.json; not stored in the repo."""
    entries = load_entries(ROOT)
    plugin = {name: {} for name in set(MAPS.values())}
    for e in entries:
        ns = e.get('namespace', '')
        assert ns in MAPS, f'unknown namespace {ns}'
        if untranslated(e):
            continue
        source, value = e['english'], e['polish']
        assert value.strip() and '�' not in value, e['key']
        assert value.count('\r') == source.count('\r'), ('CR', e['key'])  # TMP moves the pen back on \r
        assert collections.Counter(TOKENS.findall(source)) == collections.Counter(TOKENS.findall(value)), ('tokens', e['key'])
        assert value.count('\n') == source.count('\n'), ('newlines', e['key'])
        target = plugin[MAPS[ns]]
        assert target.get(e['key'], value) == value, ('conflicting texts', e['key'])
        target[e['key']] = value
    translated = sum(len(m) for m in plugin.values())
    assert plugin['i2'] and plugin['text'], 'nothing translated'
    data = (json.dumps(plugin, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8')
    return data, translated, len(entries)


def main():
    pl, count, total = texts()
    dll = compile_plugin()
    out = ROOT/'dist'/f'El-Paso-Elsewhere-PL-{VERSION}.zip'
    out.parent.mkdir(parents=True, exist_ok=True)
    readme = (ROOT/'docs/INSTALL-plugin.txt').read_text(encoding='utf-8').replace('{version}', VERSION)
    with zipfile.ZipFile(BINARY) as official, zipfile.ZipFile(SOURCE) as sources:
        expected = {n: official.read(n) for n in official.namelist() if not n.endswith('/')}
        expected.update({
            'BepInEx-LICENSE.txt': sources.read(f'BepInEx-{BEP_VERSION}/LICENSE'),
            PREFIX+NAME+'.dll': dll.read_bytes(),
            PREFIX+'pl.json': pl,
            PREFIX+'LICENSE-notgeese.txt': (REPO/'LICENSE').read_bytes(),
            'READ-ME.txt': readme.replace('\n', '\r\n').encode('utf-8'),
            'BepInEx/config/BepInEx.cfg': b'[Logging.Console]\nEnabled = false\n\n[Logging.Disk]\nEnabled = true\n',
            'dotnet/LICENSE.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/LICENSE.TXT').read_bytes(),
            'dotnet/THIRD-PARTY-NOTICES.TXT': (REPO/'vendor/bepinex/dotnet-6.0.7-licenses/THIRD-PARTY-NOTICES.TXT').read_bytes(),
        })
    forbidden = re.compile(r'(^|/)(?:GameAssembly\.dll|Assembly-CSharp(?:-firstpass)?\.dll|UnityPlayer\.dll|global-metadata\.dat'
                           r'|level\d+|globalgamemanagers)$|\.(?:assets|bundle|resS|resource|ttf|otf)$', re.I)
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
    report = {'version': VERSION, 'translated': count, 'entries': total, 'package': str(out),
              'package_bytes': out.stat().st_size, 'sha256': sha(out.read_bytes()),
              'plugin_bytes': dll.stat().st_size, 'bepinex': BEP_VERSION, 'files': len(expected),
              'package_validation': 'exact allowlist; official files byte-identical; no game assets',
              'game_test': 'pending user', 'files_sha256': {n: sha(d) for n, d in expected.items()}}
    (ROOT/'work/build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'files_sha256'}))


if __name__ == '__main__':
    main()
