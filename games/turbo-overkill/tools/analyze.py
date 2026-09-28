"""Read-only localization inventory; writes review and analysis only in the repo."""
import argparse
import json
import re
import struct
import sys
from pathlib import Path
import UnityPy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parents[1]/'tools'))
from translations import polish_by_key,review_path,write_entries  # noqa: E402

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True);args=ap.parse_args()
    data=args.game/'Turbo Overkill_Data';aa=data/'StreamingAssets/aa';bundles=aa/'StandaloneWindows64'
    shared={}
    for obj in UnityPy.load(str(bundles/'localization-assets-shared_assets_all.bundle')).objects:
        if obj.type.name!='MonoBehaviour':continue
        t=obj.read_typetree()
        if 'm_Entries' in t:shared[obj.path_id]=t
    polish=polish_by_key(ROOT) if review_path(ROOT).exists() else {}
    rows=[];tables={};roundtrips=[]
    enpath=bundles/'localization-string-tables-english(en)_assets_all.bundle'
    env=UnityPy.load(str(enpath))
    for obj in env.objects:
        if obj.type.name!='MonoBehaviour':continue
        t=obj.read_typetree()
        if 'm_TableData' not in t:continue
        s=shared[t['m_SharedData']['m_PathID']];names={x['m_Id']:x['m_Key'] for x in s['m_Entries']}
        table=s['m_TableCollectionName'];guid=s['m_TableCollectionNameGuidString']
        tables[table]={'entries':len(t['m_TableData']),'characters':sum(len(x['m_Localized']) for x in t['m_TableData'])}
        raw=obj.get_raw_data();obj.save_typetree(t);assert obj.get_raw_data()==raw
        roundtrips.append(table)
        for entry in t['m_TableData']:
            key=guid+':'+str(entry['m_Id'])
            if not entry['m_Localized'].strip() and key not in polish:continue  # empty game entry
            rows.append({'key':key,'english':entry['m_Localized'],'polish':polish.get(key,''),
                         'context':f"{table}: {names[entry['m_Id']]}",  # shown in the workspace, structure.yaml rules
                         'table':table,'entry_id':entry['m_Id'],'term':names[entry['m_Id']]})
    assert len({x['key'] for x in rows})==len(rows)
    metadata=(data/'il2cpp_data/Metadata/global-metadata.dat').read_bytes()
    magic,version=struct.unpack_from('<II',metadata);assert magic==0xfab11baf
    # Metadata string heap has individual NUL-terminated type/member names.
    offset,size=struct.unpack_from('<II',metadata,24)
    names=metadata[offset:offset+size].split(b'\0')
    evidence=sorted({n.decode('utf-8','replace') for n in names if len(n)<100 and re.search(rb'UiLanguageSelector|SetLanguage_|GetTranslatedSubtitle|LocalizedFont|LocalizeCommon',n)})
    catalog=json.loads((aa/'catalog.json').read_text())
    report={'unity':re.search(rb'20\d\d\.\d+\.\d+[abfp]\d+',enpath.read_bytes()[:100]).group().decode(),'backend':'IL2CPP x64',
            'metadata_version':version,'entries':len(rows),'nonempty':sum(bool(x['english']) for x in rows),
            'characters':sum(len(x['english']) for x in rows),'tables':tables,'byte_identical_typetree_roundtrips':roundtrips,
            'language_bundles':[p.name for p in bundles.glob('localization-string-tables-*.bundle')],
            'metadata_symbols':evidence,'font_catalog_hints':[x for x in catalog['m_InternalIds'] if 'Fonts & Materials/' in x],
            'font_glyph_coverage':'not verified','plugin_runtime_test':'not performed','game_modified':False}
    (ROOT/'work').mkdir(parents=True,exist_ok=True);(ROOT/'translations').mkdir(parents=True,exist_ok=True)
    write_entries(ROOT,rows)
    (ROOT/'work/analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()
