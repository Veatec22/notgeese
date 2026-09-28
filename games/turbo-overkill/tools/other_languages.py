"""Read-only: dump another official language table next to review keys (work/ref-<lang>.json).

Used as evidence for the translation bible (speaker gender, noun gender, ambiguity).
The output is game content for local analysis only and is ignored by git.
"""
import argparse
import json
from pathlib import Path
import UnityPy

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--lang', default='russian(ru)')
    args = ap.parse_args()
    bundles = args.game/'Turbo Overkill_Data/StreamingAssets/aa/StandaloneWindows64'
    shared = {}
    for obj in UnityPy.load(str(bundles/'localization-assets-shared_assets_all.bundle')).objects:
        if obj.type.name == 'MonoBehaviour':
            tree = obj.read_typetree()
            if 'm_Entries' in tree:
                shared[obj.path_id] = tree
    out = {}
    env = UnityPy.load(str(bundles/f'localization-string-tables-{args.lang}_assets_all.bundle'))
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        tree = obj.read_typetree()
        if 'm_TableData' not in tree:
            continue
        guid = shared[tree['m_SharedData']['m_PathID']]['m_TableCollectionNameGuidString']
        for entry in tree['m_TableData']:
            out[f"{guid}:{entry['m_Id']}"] = entry['m_Localized']
    code = args.lang.split('(')[-1].rstrip(')')
    target = ROOT/'work'/f'ref-{code}.json'
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(target, len(out))


if __name__ == '__main__':
    main()
