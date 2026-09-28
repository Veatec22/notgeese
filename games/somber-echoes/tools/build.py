"""Build Polish locres plus a runtime language selector and a verified release ZIP."""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, polish_by_key  # noqa: E402
sys.path.insert(0, str(ROOT.parent / 'bpm' / 'tools'))
from game_pak import GamePak
import locres
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
import pak

PAK_NAME = 'pakchunk99-notgeese-PL_P.pak'
PACKAGE = 'Somber-Echoes-PL-0.1.zip'
RUNTIME_SHA = 'b954f036b10e9abb0c0c41599311ab1accc53e30515aeed7e48ee22c5b3b1280'
# Pak file order as in the first full release (it followed the old pl.json order).
TARGETS = ['StringTables', 'Dialog', 'Challenges', 'Updated1', 'Updated2', 'Updated3', 'Updated4', 'Journal']


def tokens(text):
    return sorted(re.findall(r'\[ICON:[^\]]+\]|\{[^{}]+\}|</?[^>]+>', text))


def build(output, runtime):
    if not __debug__:
        raise RuntimeError('Build validation requires Python without -O.')
    translations = polish_by_key(ROOT)
    review = load_entries(ROOT)
    english = {row['key']: row['english'] for row in review}
    source_rows = json.loads((ROOT / 'work/english.json').read_text(encoding='utf-8'))
    assert english == {row['key']: row['english'] for row in source_rows}, 'Incomplete review'
    assert len(translations) == len(source_rows), 'Incomplete translation'
    grouped = {}
    for key, text in translations.items():
        target, namespace, entry = key.split('/', 2)
        assert text and tokens(text) == tokens(english[key]), key
        grouped.setdefault(target, {})[(namespace, entry)] = text
    grouped = dict(sorted(grouped.items(), key=lambda item: (TARGETS.index(item[0]) if item[0] in TARGETS else len(TARGETS), item[0])))
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for target, texts in grouped.items():
        source = locres.load(ROOT / 'work' / f'{target}.locres')
        source_texts = source.texts()
        for (namespace, key), text in texts.items():
            assert source_texts[(namespace, key)] == english[f'{target}/{namespace}/{key}']
        result = locres.translate(source, texts)
        data = locres.dump(result)
        check = output / f'{target}.locres'
        check.write_bytes(data)
        assert locres.load(check).texts() == texts
        for culture in ('pl',):
            files[f'SomberEchoes/Content/Localization/{target}/{culture}/{target}.locres'] = data
    # Exact allowlist: only generated translations, no fonts, configs or game assets.
    expected = {f'SomberEchoes/Content/Localization/{target}/{culture}/{target}.locres'
                for target in grouped for culture in ('pl',)}
    assert set(files) == expected
    destination = output / 'SomberEchoes/Content/Paks' / PAK_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(pak.write(files))
    archive = GamePak(destination, bytes(32))
    assert set(archive.files) == expected
    for path, content in files.items():
        assert archive.extract(path) == content
    runtime_data = runtime.read_bytes()
    assert hashlib.sha256(runtime_data).hexdigest() == RUNTIME_SHA, 'Unexpected UE4SS archive'
    prefix = 'SomberEchoes/Binaries/Win64/'
    payload = {destination.relative_to(output).as_posix(): destination.read_bytes(),
               'READ-ME.txt': (ROOT / 'docs/INSTALL.txt').read_bytes()}
    with zipfile.ZipFile(runtime) as archive:
        for member in ('dwmapi.dll', 'ue4ss/UE4SS.dll', 'ue4ss/LICENSE', 'ue4ss/UE4SS-settings.ini'):
            payload[prefix + member] = archive.read(member)
    payload[prefix + 'ue4ss/Mods/mods.txt'] = b'notgeesePL : 1\n'
    payload[prefix + 'ue4ss/Mods/mods.json'] = b'[{"mod_name":"notgeesePL","mod_enabled":true}]\n'
    payload[prefix + 'ue4ss/Mods/notgeesePL/Scripts/main.lua'] = (ROOT / 'plugin/main.lua').read_bytes()
    assert len(payload) == 9
    assert not any(Path(name).suffix in ('.uasset', '.uexp', '.ufont', '.ubulk') for name in payload)
    with zipfile.ZipFile(output / PACKAGE, 'w', zipfile.ZIP_DEFLATED) as package:
        for path, data in payload.items():
            package.writestr(path, data)
    with zipfile.ZipFile(output / PACKAGE) as package:
        assert set(package.namelist()) == set(payload)
        assert package.testzip() is None
        for path, data in payload.items():
            assert package.read(path) == data
    report = dict(version='0.1', entries=len(translations), cultures=['pl'],
                  in_game_test='vertical 0.1 confirmed; selector and full translation pending',
                  zip_bytes=(output / PACKAGE).stat().st_size,
                  files={name: hashlib.sha256(data).hexdigest() for name, data in payload.items()})
    (output / 'build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'Verified {len(translations)} translations, {len(files)} resources: {output / PACKAGE}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--runtime', type=Path, default=ROOT.parent / 'holy-shoot/work/ue4ss/UE4SS_v3.0.1-1140-gf58e8f84.zip')
    args = parser.parse_args()
    build(args.out_dir, args.runtime)
