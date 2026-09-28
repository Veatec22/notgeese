"""Build a partial Polish locres overlay; never modify the game installation."""
import hashlib
import json
import re
import sys
import zipfile
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1'
if not __debug__:
    raise RuntimeError('Validation requires assertions; run without -O.')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, default=ROOT / 'work/ue4ss/UE4SS_v3.0.1-1140-gf58e8f84.zip')
args = parser.parse_args()
runtime_bytes = args.runtime.read_bytes()
assert hashlib.sha256(runtime_bytes).hexdigest() == 'b954f036b10e9abb0c0c41599311ab1accc53e30515aeed7e48ee22c5b3b1280', 'Unexpected third-party runtime'
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
sys.path.insert(0, str(ROOT / 'tools'))
import locres
import pak
import iostore_empty
import batch

source = locres.load(ROOT / 'work/en.locres')
# en-pl-review.json is the only translation file; `namespace|key` names
# an entry inside the build.
polish = batch.load_polish()
english = {batch.ident(ns, key): text for (ns, key), text in source.texts().items()}
assert set(polish) <= set(english), sorted(set(polish) - set(english))[:5]
for name, text in polish.items():
    batch.check(name, english[name], text)
translations = {tuple(name.split('|', 1)): text for name, text in polish.items()}
data = locres.dump(locres.translate(source, translations))
out = ROOT / 'dist'
out.mkdir(exist_ok=True)
resource = out / 'Game.locres'
resource.write_bytes(data)
assert locres.load(resource).texts() == translations
files = {'PVD/Content/Localization/Game/pl/Game.locres': data}
assert list(files) == ['PVD/Content/Localization/Game/pl/Game.locres']
archive = pak.write(files, seed=47419669)
assert pak.read(archive)[1] == files
name = 'pakchunk99-notgeesePL_P.pak'
(out / name).write_bytes(archive)
# UE5 IoStore mounts a .pak only together with its container; ship an empty one.
CONTAINER_ID = 0x4E6965476573694C  # "LiseGeiN": fixed, unique to this overlay
utoc, ucas = iostore_empty.build(CONTAINER_ID)
assert iostore_empty.parse(utoc, ucas) == CONTAINER_ID
stem = name[:-len('.pak')]
(out / (stem + '.utoc')).write_bytes(utoc)
(out / (stem + '.ucas')).write_bytes(ucas)
payload = {'Windows/PVD/Content/Paks/' + name: archive,
           'Windows/PVD/Content/Paks/' + stem + '.utoc': utoc,
           'Windows/PVD/Content/Paks/' + stem + '.ucas': ucas,
           'READ-ME.txt': (ROOT / 'docs/INSTALL.txt').read_bytes()}
prefix = 'Windows/PVD/Binaries/Win64/'
with zipfile.ZipFile(args.runtime) as runtime:
    # Ship only the loader, its settings and MIT license. No cheat/debug mods.
    for member in ('dwmapi.dll', 'ue4ss/UE4SS.dll', 'ue4ss/LICENSE', 'ue4ss/UE4SS-settings.ini'):
        payload[prefix + member] = runtime.read(member)
payload[prefix + 'ue4ss/Mods/mods.txt'] = b'notgeesePL : 1\n'
payload[prefix + 'ue4ss/Mods/mods.json'] = b'[{"mod_name":"notgeesePL","mod_enabled":true}]\n'
for script in ('main.lua', 'selector.lua'):
    payload[prefix + 'ue4ss/Mods/notgeesePL/Scripts/' + script] = (ROOT / 'plugin' / script).read_bytes()
assert len(payload) == 12
assert not any(Path(p).suffix in ('.uasset', '.uexp', '.ufont') for p in payload)
assert len(ucas) < 1024, 'IoStore companion must stay an empty container header'
release = out / f'Holy-Shoot-PL-{VERSION}.zip'
with zipfile.ZipFile(release, 'w', zipfile.ZIP_DEFLATED) as z:
    for path, body in payload.items():
        z.writestr(path, body)
with zipfile.ZipFile(release) as z:
    assert z.testzip() is None and set(z.namelist()) == set(payload)
    for path, body in payload.items():
        assert z.read(path) == body
report = {'version': VERSION, 'translated': len(translations), 'total': len(source.texts()),
          'runtime': 'UE4SS v3.0.1-1140-gf58e8f84 (MIT)',
          'files': {path: hashlib.sha256(body).hexdigest() for path, body in payload.items()},
          'zip_bytes': release.stat().st_size, 'in_game_test': 'pending'}
(out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f'{len(translations)}/{len(source.texts())} entries; verified locres and pak round trips.')
print('Source SHA256:', hashlib.sha256((ROOT / 'work/en.locres').read_bytes()).hexdigest())
