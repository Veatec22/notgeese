"""Read-only asset survey; extracted game data stays in ignored work/."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    data = args.game / 'I Am Your Beast_Data'
    generator = TypeTreeGenerator('2022.3.5f1')
    generator.load_local_dll_folder(str(data / 'Managed'))
    result = {'stories': [], 'passages': [], 'phrases': [], 'fonts': [], 'ui': [], 'text_assets': [], 'errors': []}
    classes = Counter()
    for path in sorted(data.iterdir()):
        if not (path.suffix == '.assets' or (path.name.startswith('level') and not path.suffix)):
            continue
        env = UnityPy.load(str(path), str(data / 'globalgamemanagers.assets'))
        for obj in env.objects:
            if Path(obj.assets_file.name).name != path.name:
                continue
            ref = {'file': path.name, 'path_id': obj.path_id}
            try:
                if obj.type.name == 'TextAsset':
                    asset = obj.read()
                    result['text_assets'].append(dict(ref, name=asset.m_Name, text=asset.m_Script))
                elif obj.type.name == 'Font':
                    asset = obj.read()
                    result['fonts'].append(dict(ref, name=asset.m_Name, kind='Font', bytes=len(asset.m_FontData)))
                elif obj.type.name == 'MonoBehaviour':
                    asset = obj.read(check_read=False)
                    script = asset.m_Script.deref().read()
                    cls = script.m_ClassName
                    classes[cls] += 1
                    if cls not in ('Story', 'Passage', 'PhraseAsset', 'TMP_FontAsset', 'TextMeshProUGUI', 'TextMeshPro'):
                        continue
                    full_name = f'{script.m_Namespace}.{cls}' if script.m_Namespace else cls
                    nodes = generator.get_nodes_up(script.m_AssemblyName.removesuffix('.dll'), full_name)
                    tree = obj.read_typetree(nodes=nodes)
                    if cls == 'Story':
                        result['stories'].append(dict(ref, tree=tree))
                    elif cls == 'Passage':
                        result['passages'].append(dict(ref, tree=tree))
                    elif cls == 'PhraseAsset':
                        result['phrases'].append(dict(ref, tree=tree))
                    elif cls == 'TMP_FontAsset':
                        chars = {x['m_Unicode'] for x in tree.get('m_CharacterTable', [])}
                        result['fonts'].append(dict(ref, name=tree['m_Name'], kind=cls,
                            missing=''.join(c for c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ' if ord(c) not in chars),
                            mode=tree.get('m_AtlasPopulationMode'), source=tree.get('m_SourceFontFile'),
                            fallback=tree.get('m_FallbackFontAssetTable')))
                    elif tree.get('m_text'):
                        result['ui'].append(dict(ref, text=tree['m_text'], font=tree.get('m_fontAsset')))
            except Exception as exc:
                result['errors'].append(dict(ref, error=str(exc)))
    result['classes'] = dict(classes)
    out = ROOT / 'work'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'survey.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: len(v) for k, v in result.items()}, ensure_ascii=False))
    print(json.dumps(result['fonts'], ensure_ascii=False, indent=2))
    for story in result['stories']:
        tree = story['tree']
        print('STORY', story['file'], tree.get('m_Name'), len(tree.get('passages', [])))
    for phrase in result['phrases'][:3]:
        print('PHRASE', json.dumps(phrase, ensure_ascii=False)[:2000])


if __name__ == '__main__':
    main()
