"""Give the Latin font set fallbacks so Polish letters have somewhere to come from.

Every font in the game is a static atlas, so a glyph it does not carry renders
as a box. Only the `beer money` family covers `ąćęłńóśźżĄĆĘŁŃÓŚŹŻ`.

Polish uses the Latin set, the one English uses (build.py points the font
switch there). Its fonts carry `ł ó Ł Ó` and nothing else Polish, so each gets
the `beer money` font that matches its role:

  Dead Stock SDF                    buttons, trick notifications -> beer money SDF
  Sure Shot SDF - title background  arena title, back layer     -> beer money SDF - title background
  Sure Shot SDF - title foreground  arena title, front layer    -> beer money SDF - title foreground

`Sure Shot SDF`, the text font, already falls back to `beer money SDF` in the
game as shipped. The sizes match closely: a lowercase `o` is 0.38 of the point
size in Sure Shot and 0.35 in beer money.

The Russian set was tried first and dropped: its button font `Abys-Regular SDF`
is capitals only and has no Polish letter at all, so every Polish letter came
from the fallback's lowercase at half the height of the capitals around it.

A fallback is only consulted for characters the font itself does not have, and
none of these three has a fallback list today. So nothing any other language
renders can change: the characters this adds are the ones that are boxes now.
It is also the game's own idiom - `Sure Shot SDF` already falls back to
JejuHallasan, beer money, ardclaowaisongg30 and 851CHIKARA so that a Latin menu
can show CJK.

This rewrites resources.assets, which is 836 MB, so it is a separate step from
`build.py`. The text lives in the DLL.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

HERE = Path(__file__).resolve().parent
GAME = HERE.parent
DATA = Path('BOOMERANG X_Data')
RELATIVE = DATA / 'resources.assets'
ORIGINAL = 'f663c3c3ba23f7534572f35cf5e8e38fa30846a5d7203aba04b8eb69418dd247'
UNITY = '2020.1.17f1'
FALLBACKS = {
    'Dead Stock SDF': 'beer money SDF',
    'Sure Shot SDF - title background': 'beer money SDF - title background',
    'Sure Shot SDF - title foreground': 'beer money SDF - title foreground',
}
POLISH = 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'


def font_nodes(managed):
    generator = TypeTreeGenerator(UNITY)
    generator.load_local_dll_folder(str(managed))
    return generator.get_nodes_up('Unity.TextMeshPro', 'TMPro.TMP_FontAsset')


def fonts(objects, nodes):
    """Every TMP font asset in the file, by name."""
    out = {}
    for obj in objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        try:
            tree = obj.read_typetree(nodes=nodes)
        except Exception:
            continue
        if not isinstance(tree, dict) or 'm_CharacterTable' not in tree:
            continue
        out[str(tree['m_Name'])] = (obj, tree)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, required=True,
                        help='The game folder, or the original resources.assets')
    parser.add_argument('--managed', type=Path,
                        help='The Managed folder the type trees come from')
    parser.add_argument('--out', type=Path, default=GAME / 'dist')
    args = parser.parse_args()

    source = args.source / RELATIVE if args.source.is_dir() else args.source
    managed = args.managed or source.parent / 'Managed'
    digest = hashlib.sha256()
    with open(source, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b''):
            digest.update(chunk)
    assert digest.hexdigest() == ORIGINAL, (f'{source} is not the original ({digest.hexdigest()}). '
                                            'Build from the game as shipped, or from the backup.')
    nodes = font_nodes(managed)

    environment = UnityPy.load(str(source))
    table = fonts(environment.objects, nodes)
    changed = []
    for name, provider_name in FALLBACKS.items():
        assert name in table, f'{name} is not in {source}'
        assert provider_name in table, f'{provider_name} is not in {source}'
        provider, provider_tree = table[provider_name]
        missing = [c for c in POLISH
                   if ord(c) not in {e['m_Unicode'] for e in provider_tree['m_CharacterTable']}]
        assert not missing, f'{provider_name} cannot supply {"".join(missing)}'

        obj, tree = table[name]
        entry = {'m_FileID': 0, 'm_PathID': provider.path_id}
        had = list(tree['m_FallbackFontAssetTable'])
        assert entry not in had, f'{name} already falls back to {provider_name}'
        tree['m_FallbackFontAssetTable'] = had + [entry]
        obj.save_typetree(tree, nodes)
        assets = obj.assets_file
        changed.append({'font': name, 'path_id': obj.path_id, 'fallback': provider_name,
                        'fallbacks_before': len(had), 'fallbacks_after': len(had) + 1})

    target = args.out / RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(assets.save())

    # Read the result back. `table` now holds the intended state - the two edited
    # trees were mutated in place - so this checks the additions landed and that
    # every other font's fallback list came through untouched.
    rebuilt = fonts(UnityPy.load(str(target)).objects, nodes)
    assert set(rebuilt) == set(table), 'the set of fonts changed'
    for name, (_, tree) in rebuilt.items():
        refs = [f['m_PathID'] for f in tree['m_FallbackFontAssetTable']]
        wanted = [f['m_PathID'] for f in table[name][1]['m_FallbackFontAssetTable']]
        assert refs == wanted, f'{name}: fallbacks read back as {refs}, wanted {wanted}'
        chars = {e['m_Unicode'] for e in tree['m_CharacterTable']}
        assert chars == {e['m_Unicode'] for e in table[name][1]['m_CharacterTable']},             f'{name}: its own glyphs changed'

    print(json.dumps({'built': str(target),
                      'bytes': os.path.getsize(target),
                      'source_bytes': os.path.getsize(source),
                      'changed': changed}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
