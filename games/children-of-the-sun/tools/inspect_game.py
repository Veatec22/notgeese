"""Survey Children of the Sun: TMP fonts (Polish coverage), scene TMP texts, localization components."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = Path(__file__).resolve().parents[1]
PL = 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
WANTED = ('TMP_FontAsset', 'TextMeshProUGUI', 'TextMeshPro', 'LocalizeStringEvent', 'Text')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    data = args.game / 'ChildrenOfTheSun_Data'
    generator = TypeTreeGenerator('2021.3.20f1')
    generator.load_local_dll_folder(str(data / 'Managed'))
    result = {'fonts': [], 'ui': [], 'localized': [], 'errors': []}
    classes = Counter()
    for path in sorted(data.iterdir()):
        if not (path.suffix == '.assets' or (path.name.startswith('level') and not path.suffix)):
            continue
        env = UnityPy.load(str(path), str(data / 'globalgamemanagers.assets'))
        for obj in env.objects:
            if Path(obj.assets_file.name).name != path.name or obj.type.name != 'MonoBehaviour':
                continue
            ref = {'file': path.name, 'path_id': obj.path_id}
            try:
                asset = obj.read(check_read=False)
                script = asset.m_Script.deref().read()
                cls = script.m_ClassName
                classes[cls] += 1
                if cls not in WANTED:
                    continue
                full_name = f'{script.m_Namespace}.{cls}' if script.m_Namespace else cls
                nodes = generator.get_nodes_up(script.m_AssemblyName.removesuffix('.dll'), full_name)
                tree = obj.read_typetree(nodes=nodes)
                if cls == 'TMP_FontAsset':
                    chars = {x['m_Unicode'] for x in tree.get('m_CharacterTable', [])}
                    result['fonts'].append(dict(ref, name=tree['m_Name'], glyphs=len(chars),
                        missing=''.join(c for c in PL if ord(c) not in chars),
                        mode=tree.get('m_AtlasPopulationMode'), source=tree.get('m_SourceFontFile'),
                        fallback=tree.get('m_FallbackFontAssetTable')))
                elif cls == 'LocalizeStringEvent':
                    result['localized'].append(dict(ref, go=tree['m_GameObject'], string=tree.get('m_StringReference')))
                elif tree.get('m_text'):
                    result['ui'].append(dict(ref, cls=cls, go=tree['m_GameObject'], text=tree['m_text'],
                        font=tree.get('m_fontAsset') or tree.get('m_FontData')))
            except Exception as exc:
                result['errors'].append(dict(ref, error=str(exc)))
    result['classes'] = dict(classes.most_common())
    out = ROOT / 'work'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'survey.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: len(v) for k, v in result.items()}, ensure_ascii=False))
    for f in result['fonts']:
        print(f['file'], f['name'], f['glyphs'], 'mode', f['mode'], 'missing', f['missing'] or '-')


if __name__ == '__main__':
    main()
