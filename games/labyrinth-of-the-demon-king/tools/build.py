"""Build a localization-only PAK + minimal selector IoStore overlay and ZIP.

Reads local files to obtain engine keys/selector structure, never changes them.
No game checksum is used as a version gate. Unsupported serialization is rejected
at build time. Actual mounting/rendering must be tested by the user.
"""
import argparse
from collections import Counter
import hashlib
import json
import sys
import re
import tempfile
import zipfile
from pathlib import Path
import yaml
from game_pak import GamePak
from iostore import Store,write_overlay
from language_slot import PATH,patch
import locres
import pak

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, polish_by_key  # noqa: E402
VERSION='0.3'
STEM='pakchunk99-notgeesePL_P'
PAKS='Shinigami/Content/Paks'
PL_PATH='Shinigami/Content/Localization/Game/pl/Game.locres'
EN_PATH='Shinigami/Content/Localization/Game/en/Game.locres'
TOKENS=re.compile(r'\{[^{}]+\}|</>|<[A-Za-z_][^>]*>')

def validate_payload(stage, polish, expected_widget):
    """Allowlist inside both archive types; reject even a single unrelated chunk."""
    base=stage/PAKS/STEM
    expected={f'{PAKS}/{STEM}{ext}' for ext in ('.pak','.utoc','.ucas')}|{'READ-ME.txt'}
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if actual!=expected:raise ValueError(f'Unexpected payload: {actual ^ expected}')
    mount,files=pak.read(base.with_suffix('.pak').read_bytes())
    if mount!='../../../' or set(files)!={PL_PATH}:raise ValueError('PAK must contain Polish text only')
    if files[PL_PATH]!=polish:raise ValueError('Unexpected localization data')
    store=Store(base)
    if set(store.paths)!={PATH} or len(store.ids)!=2:raise ValueError('IoStore must contain only language slot and its header')
    widget=store.read(store.paths[PATH])
    if widget!=expected_widget or len(widget)>26000:raise ValueError('Unexpected/oversized selector carrier')
    for i,chunk in enumerate(store.ids):
        if chunk[11] not in (2,10):raise ValueError('Forbidden chunk type')
        if chunk[11]==10 and len(store.read(i))>1024:raise ValueError('Oversized carrier header')
    if len(widget)>=len(polish):raise ValueError('Selector carrier is not smaller than translation')
    return expected

def main():
    if not __debug__:raise RuntimeError('Do not disable build validations with -O')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',required=True,type=Path)
    args=ap.parse_args()
    game=args.game.resolve();dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    polish=polish_by_key(ROOT)
    review=load_entries(ROOT)
    assert len({x['key'] for x in review})==len(review)
    assert all(x['polish'] for x in review), 'Full release requires all reviewed entries translated'
    source=GamePak(game/PAKS/'pakchunk0-WindowsNoEditor.pak')
    en=source.extract(EN_PATH)
    with tempfile.TemporaryDirectory(prefix='labyrinth-pl-') as tmp:
        tmp=Path(tmp);enfile=tmp/'en.locres';enfile.write_bytes(en)
        english=locres.load(enfile);assert locres.dump(english)==en
        native={e.key:e.text for _,e in english.entries()}
        assert polish and polish.keys()<=native.keys()
        for item in review:
            if item['key'] not in polish:continue
            text=polish[item['key']];original=native[item['key']]
            assert original==item['english'], f'Source changed: {item["key"]}'
            assert Counter(TOKENS.findall(original))==Counter(TOKENS.findall(text)),item['key']
            assert original.count('\r\n')==text.count('\r\n'),f'Line breaks: {item["key"]}'
        pl=locres.dump(locres.translate(english,{('',key):text for key,text in polish.items()}))
        plfile=tmp/'pl.locres';plfile.write_bytes(pl)
        assert locres.load(plfile).texts()=={('',key):text for key,text in polish.items()}
        original_store=Store(game/PAKS/'pakchunk0-WindowsNoEditor')
        widget,selector=patch(original_store.read(original_store.paths[PATH]))
        stage=tmp/'stage';base=stage/PAKS/STEM
        io=write_overlay(original_store,{PATH:widget},base)
        base.with_suffix('.pak').write_bytes(pak.write({PL_PATH:pl}))
        (stage/'READ-ME.txt').write_bytes((ROOT/'docs/INSTALL.txt').read_bytes())
        expected=validate_payload(stage,pl,widget)
        output=dist/f'Labyrinth-of-the-Demon-King-PL-{VERSION}.zip'
        candidate=tmp/'candidate.zip'
        with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(expected):z.write(stage/path,path)
        with zipfile.ZipFile(candidate) as z:
            assert set(z.namelist())==expected and z.testzip() is None
            checked=tmp/'checked';z.extractall(checked)
        validate_payload(checked,pl,widget)
        output.write_bytes(candidate.read_bytes())
        report={'version':VERSION,'translated':len(polish),'total':len(native),
                'locres_bytes':len(pl),'selector':selector,'iostore':io,
                'package':str(output),'package_bytes':output.stat().st_size,
                'package_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                'file_tests':'passed','game_test':'vertical confirmed by user; full campaign not tested'}
        (dist/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('selector','iostore')},ensure_ascii=True))

if __name__=='__main__':main()
