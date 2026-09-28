"""Extract The Hong Kong Massacre texts into translations/en-pl-review.json.

Read-only on the game dir. Existing Polish is kept by key; entries whose English changed keep
their Polish and get a note. Key kinds (the plugin reads the same prefixes):

  dlg/<conversation>/<entry>   Dialogue Text field in the Dialogue System database "THKM"
  ui/<English>                 exact text set on a UnityEngine.UI.Text (scenes, data, code)
  fmt/<English with {0}>       label + value built by code ("DEATHS: " + n)
  rewired/<field>              Rewired control mapper LanguageData field

    .venv\\Scripts\\python.exe games\\hong-kong-massacre\\tools\\extract.py --game "C:\\Games\\The Hong Kong Massacre"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

ROOT = Path(__file__).resolve().parents[1]
UNITY = '2017.4.17f1'
DATABASE = 'THKM'

# UI.Text values that are editor placeholders, asset-store samples, debug panels or fixed art.
UI_SKIP = {
    'Button', 'New Text', 'Label', 'Name', 'Subtitle', 'Title', 'Content Text', 'Input Field',
    'Alert Message', 'Response 1', 'Response 2', 'Response 3', 'Response 4', 'Option A',
    'NAME NAME', 'Scene Info', 'Tip Header', 'Scene description is here and can also go over multiple lines if the text requires it.',
    "Tip Descrtiption goes here and can span multiple lines. Of course only if that's required.",
    'This is an example scene with all features. Use this as a baseline to create your own loading scene!',
    'DEBUG', 'GOD MODE', 'UNLIMITED AMMO', 'UNLOCK ALL LEVELS', 'UNLOCK ALL UPGRADES', 'GET WEAPON POINTS',
    'END OF DEMO\nTHANK YOU FOR PLAYING', 'MADE BY', 'MUSIC BY', 'VRESKI\n\n\nPROFESSOR KLIQ',
    'WWW.THEHONGKONGMASSACRE.COM', 'Beretta 92', 'BERRETTA 92F', '1500 P', '500p', 'DUAL',
    'FIRST COME FIRST SERVED', 'First Enemy Killed', 'Look Sensitivity', 'SCORE', 'TEAHOUSE',
}
UI_SKIP_RE = re.compile(r'^[\d\s:%.+\-<>/]*$|^TIME: 00|^UNLOCK BERRETTA|^\n+CREDITS|[\u4e00-\u9fff]')

# Hardcoded in Assembly-CSharp and passed to Text.text as is.
CODE_UI = [
    'NO RECORD', 'SHOW FRIENDS', 'SHOW TOP 100', 'SHOW USER RANK', 'TOP 100', 'FRIENDS', 'USER RANK',
    'START LEVEL', 'SELECT', 'CLIP SIZE', 'RELOAD SPEED', 'FIRE RATE', 'MOVEMENT SPEED', 'START',
    'UNLOCK', 'UNLOCK UPGRADE?', 'UPGRADE WEAPON', 'BUY UPGRADE', 'BACK', 'COMPLETED',
]
# Label + value concatenations (LevelDataBaseUI.ShowLevelStats, WeaponItemUnlockConfirmBase.Show).
CODE_FMT = [
    'TIME: {0}', 'BEST TIME: {0}', 'SLOWMOTION: {0}', 'DEATHS: {0}', 'ENEMIES KILLED: {0}',
    'SHOTS FIRED: {0}', 'WEAPONS PICKED UP: {0}', 'SHOTS MISSED: {0}', 'TOTAL TIME: {0}',
    'DIVES: {0}', 'DOORS DESTROYED: {0}', 'TOTAL ENEMIES KILLED: {0}', 'UNLOCK {0}?',
    'CLEAR LEVEL UNDER {0}',
]
# Dialogue speakers whose label is a role, not a name.
ROLE_NAMES = ['Police Officer', 'Bartender', 'Chef Lung', 'Mr Tequila', 'Anthony "The Boss" Tsang']


def fields(obj: dict) -> dict:
    return {f['title']: f['value'] for f in obj.get('fields', [])}


def load(data: Path, generator: TypeTreeGenerator, name: str):
    """Yield (class, tree) for MonoBehaviours of one serialized file."""
    env = UnityPy.load(str(data / name))
    cache = {}
    for obj in env.objects:
        if Path(obj.assets_file.name).name != name or obj.type.name != 'MonoBehaviour':
            continue
        try:
            script = obj.read(check_read=False).m_Script.deref().read()
        except Exception:
            continue
        full = f'{script.m_Namespace}.{script.m_ClassName}' if script.m_Namespace else script.m_ClassName
        key = (script.m_AssemblyName.removesuffix('.dll'), full)
        try:
            if key not in cache:
                cache[key] = generator.get_nodes_up(*key)
            yield script.m_ClassName, obj.read_typetree(nodes=cache[key])
        except Exception:
            continue


def dialogue(data: Path, generator: TypeTreeGenerator) -> list[dict]:
    for cls, tree in load(data, generator, 'sharedassets50.assets'):
        if cls == 'DialogueDatabase' and tree.get('m_Name') == DATABASE:
            break
    else:
        raise SystemExit(f'Dialogue database {DATABASE} not found.')
    actors = {a['id']: fields(a).get('Name', '') for a in tree['actors']}
    out, keys = [], {}
    for conv in tree['conversations']:
        title = fields(conv).get('Title', '')
        entries = {e['id']: e for e in conv['dialogueEntries']}
        order, seen = [], set()

        def walk(i):
            if i in seen or i not in entries:
                return
            seen.add(i)
            order.append(i)
            for link in entries[i]['outgoingLinks']:
                if link['destinationConversationID'] == conv['id']:
                    walk(link['destinationDialogueID'])

        walk(0)
        order += [i for i in entries if i not in seen]
        for i in order:
            f = fields(entries[i])
            text = f.get('Dialogue Text', '')
            if not text.strip():
                continue
            speaker = actors.get(int(f.get('Actor') or 0), '') or '?'
            listener = actors.get(int(f.get('Conversant') or 0), '') or '?'
            key = f'dlg/{title}/{i}'
            if key in keys:
                # Two conversations share a title ("Boss_5"); one entry serves both if equal.
                if keys[key] != text:
                    raise SystemExit(f'{key}: same key, different text')
                continue
            keys[key] = text
            out.append({'key': key, 'english': text, 'context': f'{title}: {speaker} → {listener}'})
    return out


def ui(data: Path, generator: TypeTreeGenerator) -> tuple[list[dict], list[dict]]:
    texts: dict[str, str] = {}
    rewired: list[dict] = []

    def add(text: str, context: str):
        if text and text.strip() and text not in UI_SKIP and not UI_SKIP_RE.search(text):
            texts.setdefault(text, context)

    files = [p.name for p in sorted(data.iterdir())
             if p.suffix == '.assets' or (p.name.startswith('level') and not p.suffix)]
    for name in files:
        for cls, tree in load(data, generator, name):
            if cls == 'Text':
                add(tree.get('m_Text', ''), f'label ({name})')
            elif cls == 'Dropdown':
                for option in (tree.get('m_Options') or {}).get('m_Options', []):
                    add(option.get('m_Text', ''), f'dropdown option ({name})')
            elif cls == 'LevelItemData' and name == 'sharedassets0.assets':
                scene = tree.get('Scene') or '?'
                add(tree.get('LevelName', ''), f'level title ({scene})')
                add(tree.get('LevelNameLocation', ''), f'level location ({scene})')
                add((tree.get('SimpleName') or '').strip(), f'boss epithet ({scene})')
            elif cls == 'WeaponItemData':
                add(tree.get('ItemName', ''), 'weapon name')
            elif cls == 'CutsceneTextIntroBase':
                for intro in tree.get('_IntroTexts', []):
                    add(intro.get('Text', ''), 'intro card: when')
                    add(intro.get('DateText', ''), 'intro card: date')
            elif cls == 'ConversationSettingBase':
                add(tree.get('TimeDate', ''), 'conversation card: date')
            elif cls == 'LoadingScreenConfig':
                for tip in tree.get('gameTips', []):
                    add(tip.get('header', ''), 'loading tip: header')
                    add(tip.get('description', ''), 'loading tip')
            elif cls == 'LanguageData' and not rewired:
                for field, value in tree.items():
                    if field.startswith('_') and isinstance(value, str) and value.strip():
                        rewired.append({'key': f'rewired/{field}', 'english': value,
                                        'context': 'control mapper (Rewired); {n} = inserted name'})
        print(name, file=sys.stderr, flush=True)
    for text in CODE_UI:
        texts.setdefault(text, 'set by code')
    for text in ROLE_NAMES:
        texts[text] = 'speaker label in dialogue'
    entries = [{'key': f'ui/{t}', 'english': t, 'context': c} for t, c in texts.items()]
    entries += [{'key': f'fmt/{t}', 'english': t, 'context': 'label + value set by code; keep {0}'}
                for t in CODE_FMT]
    return entries, rewired


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', type=Path, required=True)
    args = parser.parse_args()
    data = args.game / 'THKM_Data'
    generator = TypeTreeGenerator(UNITY)
    generator.load_local_dll_folder(str(data / 'Managed'))

    labels, rewired = ui(data, generator)
    fresh = dialogue(data, generator) + labels + rewired

    path = ROOT / 'translations' / 'en-pl-review.json'
    old = {e['key']: e for e in json.loads(path.read_text(encoding='utf-8'))} if path.exists() else {}
    out = []
    for entry in fresh:
        prev = old.get(entry['key'])
        entry['polish'] = prev['polish'] if prev else ''
        if prev and prev.get('note'):
            entry['note'] = prev['note']
        if prev and prev['english'] != entry['english'] and prev['polish']:
            entry['note'] = 'English changed since translation: ' + prev['english']
        out.append({k: entry[k] for k in ('key', 'english', 'polish', 'context', 'note') if k in entry})
    gone = sorted(set(old) - {e['key'] for e in out})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    kinds = {}
    for e in out:
        kinds[e['key'].split('/')[0]] = kinds.get(e['key'].split('/')[0], 0) + 1
    print(json.dumps({'entries': len(out), 'kinds': kinds,
                      'translated': sum(1 for e in out if e['polish']), 'dropped': gone}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
