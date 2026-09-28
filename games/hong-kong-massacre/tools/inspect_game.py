"""Read-only asset survey; extracted game data stays in ignored work/."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = Path(__file__).resolve().parents[1]
UNITY = '2017.4.17f1'
PL = 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
SKIP_CLASSES = {'TMP_FontAsset', 'TMP_SpriteAsset', 'TMP_Settings', 'TMP_StyleSheet'}


def strings(node, path=''):
    """Yield (path, value) for every non-trivial string in a type tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from strings(value, f'{path}.{key}' if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from strings(value, f'{path}[{i}]')
    elif isinstance(node, str) and any(c.isalpha() for c in node):
        yield path, node


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    data = args.game / 'THKM_Data'
    generator = TypeTreeGenerator(UNITY)
    generator.load_local_dll_folder(str(data / 'Managed'))
    result = {'text_assets': [], 'fonts': [], 'mono': [], 'videos': [], 'errors': []}
    classes = Counter()
    nodes_cache = {}
    files = [p for p in sorted(data.iterdir())
             if p.suffix == '.assets' or p.name == 'globalgamemanagers'
             or (p.name.startswith('level') and not p.suffix)]
    for path in files:
        env = UnityPy.load(str(path))
        for obj in env.objects:
            if Path(obj.assets_file.name).name != path.name:
                continue
            ref = {'file': path.name, 'path_id': obj.path_id}
            try:
                kind = obj.type.name
                if kind == 'TextAsset':
                    asset = obj.read()
                    text = asset.m_Script
                    if isinstance(text, bytes):
                        text = text.decode('utf-8', 'replace')
                    result['text_assets'].append(dict(ref, name=asset.m_Name, size=len(text), text=text[:4000]))
                elif kind == 'Font':
                    asset = obj.read()
                    result['fonts'].append(dict(ref, name=asset.m_Name, kind='Font',
                                                bytes=len(asset.m_FontData or b'')))
                elif kind == 'VideoClip':
                    asset = obj.read()
                    result['videos'].append(dict(ref, name=asset.m_Name))
                elif kind == 'MonoBehaviour':
                    asset = obj.read(check_read=False)
                    script = asset.m_Script.deref().read()
                    cls = script.m_ClassName
                    full_name = f'{script.m_Namespace}.{cls}' if script.m_Namespace else cls
                    assembly = script.m_AssemblyName.removesuffix('.dll')
                    classes[f'{assembly}:{full_name}'] += 1
                    key = (assembly, full_name)
                    if key not in nodes_cache:
                        nodes_cache[key] = generator.get_nodes_up(assembly, full_name)
                    tree = obj.read_typetree(nodes=nodes_cache[key])
                    if cls == 'TMP_FontAsset':
                        chars = {x['m_Unicode'] for x in tree.get('m_CharacterTable', [])}
                        result['fonts'].append(dict(ref, name=tree['m_Name'], kind=cls,
                            missing=''.join(c for c in PL if ord(c) not in chars),
                            chars=len(chars), fallback=tree.get('fallbackFontAssets')))
                        continue
                    if cls in SKIP_CLASSES:
                        continue
                    found = [(p, v) for p, v in strings(tree)
                             if not p.endswith('m_Name') and p != 'm_Name']
                    if found:
                        result['mono'].append(dict(ref, cls=full_name, name=tree.get('m_Name'),
                                                   strings=found))
            except Exception as exc:
                result['errors'].append(dict(ref, error=f'{type(exc).__name__}: {exc}'))
        print(path.name, file=sys.stderr, flush=True)
    result['classes'] = dict(classes.most_common())
    out = ROOT / 'work'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'survey.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8', errors='backslashreplace')
    print(json.dumps({k: len(v) for k, v in result.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
