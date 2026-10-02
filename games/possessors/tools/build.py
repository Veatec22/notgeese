"""Build the Polish overlay pak (culture `pl`) and a verified release ZIP; never touches the game.

The game lists every culture it finds under Localization, so a pak with `pl` tables is
the whole install: no plugin, no game file replaced. UE5 IoStore mounts a loose .pak
only together with a container, so an empty one ships alongside (as in Holy Shoot).
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2'
PACKAGE = f'Possessors-PL-{VERSION}.zip'
PAK_STEM = 'pakchunk99-notgeesePL_P'
PAK_DIR = 'Pose/Content/Paks/'
CONTAINER_ID = 0x4E47504F53455353  # fixed, unique to this overlay
if not __debug__:
    raise RuntimeError('Validation requires assertions; run without -O.')
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
sys.path.insert(0, str(ROOT.parent / 'holy-shoot' / 'tools'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
import locres  # noqa: E402
import pak  # noqa: E402
import iostore_empty  # noqa: E402
from batch import TABLES, check, english  # noqa: E402
from translations import load_entries, untranslated  # noqa: E402

entries = load_entries(ROOT)
source = english()
assert {e['key']: e['english'] for e in entries} == source, 'Review file does not match the extracted English'
grouped = {}
for e in entries:
    if untranslated(e):
        continue
    check(e['key'], e['english'], e['polish'])
    table, namespace, key = e['key'].split('/', 2)
    grouped.setdefault(table, {})[(namespace, key)] = e['polish']

out = ROOT / 'dist'
out.mkdir(exist_ok=True)
files = {}
for table in TABLES:
    if table not in grouped:
        continue
    src = locres.load(ROOT / 'work' / 'loc' / 'en' / f'{table}.locres')
    data = locres.dump(locres.translate(src, grouped[table]))
    probe = out / f'{table}.locres'
    probe.write_bytes(data)
    assert locres.load(probe).texts() == grouped[table], table
    probe.unlink()
    files[f'Pose/Content/Localization/{table}/pl/{table}.locres'] = data
assert all(p.endswith('.locres') and '/pl/' in p for p in files)

archive = pak.write(files, seed=0x506F7365)
assert pak.read(archive)[1] == files
utoc, ucas = iostore_empty.build(CONTAINER_ID)
assert iostore_empty.parse(utoc, ucas) == CONTAINER_ID
assert len(ucas) < 1024, 'IoStore companion must stay an empty container header'

payload = {PAK_DIR + PAK_STEM + '.pak': archive,
           PAK_DIR + PAK_STEM + '.utoc': utoc,
           PAK_DIR + PAK_STEM + '.ucas': ucas,
           'READ-ME.txt': (ROOT / 'docs' / 'INSTALL.txt').read_bytes()}
assert not any(Path(p).suffix in ('.uasset', '.uexp', '.ufont', '.ubulk', '.exe', '.dll') for p in payload)
release = out / PACKAGE
with zipfile.ZipFile(release, 'w', zipfile.ZIP_DEFLATED) as z:
    for path, body in payload.items():
        z.writestr(path, body)
with zipfile.ZipFile(release) as z:
    assert z.testzip() is None and set(z.namelist()) == set(payload)
    for path, body in payload.items():
        assert z.read(path) == body
stage = out / 'Pose' / 'Content' / 'Paks'
stage.mkdir(parents=True, exist_ok=True)
for path, body in payload.items():
    if path.startswith(PAK_DIR):
        (stage / Path(path).name).write_bytes(body)

translated = sum(len(t) for t in grouped.values())
report = {'version': VERSION, 'translated': translated, 'total': len(entries), 'tables': len(files),
          'files': {p: hashlib.sha256(b).hexdigest() for p, b in payload.items()},
          'zip_bytes': release.stat().st_size, 'in_game_test': 'probes confirmed; full playthrough pending'}
(out / 'build-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f'{translated}/{len(entries)} entries in {len(files)} tables; locres, pak, IoStore and ZIP verified: {release}')
