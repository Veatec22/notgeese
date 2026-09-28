"""Read-only text inventory: I2 terms, scene UI and raw Timeline subtitles -> review file + work/.

Keeps existing Polish and notes on re-extraction. The scene scan takes ~10 min and is cached in
work/scan.json; --reuse skips it.
"""
import argparse
import json
import os
import re
import struct
import sys
from collections import Counter
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, review_path, write_entries  # noqa: E402

UNITY = '2021.3.21f1'
DATA = 'El Paso Elsewhere_Data'
PL = 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'
# Scene texts of dev tools shipped in the build (Graphy, RuntimeInspector, Quantum Console,
# HDRP debug UI, level picker) and placeholders; never shown in normal play.
DEBUG_PATH = re.compile(r'Graphy|Runtime ?Inspector|Runtime ?Hierarchy|Quantum|Console|Debug|ReferencePicker|'
                        r'ColorPicker|SelectPrompt|(Bounds|Rect|Array|Hierarchy|Transform|TextureReference)Field|'
                        r'Scene Display', re.I)
PLACEHOLDER = re.compile(r'^[\s#0-9.,:%x@\[\]\-+<>/=]*$|^[A-Z]$|^v\.\d+$|^(New Text|Button|Option A|TEST|wibble)$')
# A Timeline subtitle clip holds an I2 term; a few hold the text itself.
I2_KEY = re.compile(r'^(EPE |Main Menu - |Subtitles - |Ticker Message - )')
# Texts built or set by code (IL2CPP string literals), found in metadata or the plugin log.
# 'pattern': {0} stands for a number or name the game inserts.
CODE = [
    ('pattern', 'CHAPTER {0}', 'Save slot and chapter select; scene template "CHAPTER 17"'),
    ('pattern', 'SLOT {0}', 'Save slot; scene template "SLOT 1"'),
    ('pattern', 'Press any key to remap.\n\nCancelling in {0}...', 'Key remapping countdown'),
    ('code', 'ENABLE SUBTITLES', 'Cutscene pause menu, pair of "DISABLE SUBTITLES"'),
    ('pattern', 'Press {0} to reload', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Press {0} to shoot', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Press {0} to slow-dive.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Press {0} to enter slow motion.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Press {0} to use painkillers.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Press {0} to stake.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Move and press {0} to roll.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'Use {0} and {1} to change weapons.', 'Tutorial prompt (IL2CPP literal)'),
    ('pattern', 'You can also dive with {0}.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'Look for their light beacons.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'Free all innocents.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'Try it out.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'You can hold the dive button to stay down.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', "Roll out of the angel's blast and kill it.", 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'Rolling makes you invulnerable.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'The painkillers are kicking in...', 'Tutorial prompt (IL2CPP literal)'),
    ('code', 'You can break wooden objects for more stakes.', 'Tutorial prompt (IL2CPP literal)'),
    ('code', '<voffset=0.6em><size=80%>Difficulty Preset:', 'Save slot (plugin log 0.1)'),
    ('code', 'Movement', 'Key binding list (plugin log 0.1)'),
    ('code', 'Move Y', 'Key binding list (plugin log 0.1)'),
    ('code', 'Move X', 'Key binding list (plugin log 0.1)'),
    ('code', 'Move Forward', 'Key binding list (plugin log 0.1)'),
    ('code', 'Move Backward', 'Key binding list (plugin log 0.1)'),
    ('code', 'Strafe Right', 'Key binding list (plugin log 0.1)'),
    ('code', 'Strafe Left', 'Key binding list (plugin log 0.1)'),
    ('code', 'Space', 'Key binding list (plugin log 0.1)'),
    ('code', 'Dive', 'Key binding list (plugin log 0.1)'),
    ('code', 'Left Shift', 'Key binding list (plugin log 0.1)'),
    ('code', 'Roll', 'Key binding list (plugin log 0.1)'),
    ('code', 'Combat & Interaction', 'Key binding list (plugin log 0.1)'),
    ('code', 'Use', 'Key binding list (plugin log 0.1)'),
    ('code', 'Slow Motion', 'Key binding list (plugin log 0.1)'),
    ('code', 'Fire', 'Key binding list (plugin log 0.1)'),
    ('code', 'Left Mouse Button', 'Key binding list (plugin log 0.1)'),
    ('code', 'Reload', 'Key binding list (plugin log 0.1)'),
    ('code', 'Melee', 'Key binding list (plugin log 0.1)'),
    ('code', 'Heal', 'Key binding list (plugin log 0.1)'),
    ('code', 'Tab', 'Key binding list (plugin log 0.1)'),
    ('code', 'Shoot-dodge', 'Key binding list (plugin log 0.1)'),
    ('code', 'Right Mouse Button', 'Key binding list (plugin log 0.1)'),
    ('code', 'Next Weapon', 'Key binding list (plugin log 0.1)'),
    ('code', 'Mouse Wheel Up', 'Key binding list (plugin log 0.1)'),
    ('code', 'Prev Weapon', 'Key binding list (plugin log 0.1)'),
    ('code', 'Mouse Wheel Down', 'Key binding list (plugin log 0.1)'),
    ('pattern', 'Weapon {0}', 'Key binding list (plugin log 0.1)'),
    ('code', 'EMPTY', 'Empty save slot (plugin log 0.1)'),
    ('code', 'Custom', 'Difficulty preset name (plugin log 0.1)'),
    ('code', 'Intended', 'Difficulty preset name (plugin log 0.1)'),
    ('code', 'Challenging', 'Difficulty preset name (plugin log 0.1)'),
    ('code', '<voffset=0.6em><size=80%>Custom preset:', 'Save slot modifiers (plugin log 0.1)'),
    ('code', '<voffset=0.6em><size=80%>Save has no modifiers.', 'Save slot modifiers (plugin log 0.1)'),
    ('code', 'Tutorial', 'Level name in save selector (plugin log 0.1)'),
    ('code', 'LOADING', 'Loading screen, animated dots (plugin log 0.1)'),
    ('pattern', 'LOADING{0}', 'Loading screen, animated dots (plugin log 0.1)'),
    ('code', 'Use the MOUSE to aim', 'Tutorial prompt (plugin log 0.1)'),
    ('code', 'Use WASD to move', 'Tutorial prompt (plugin log 0.1)'),
    ('code', 'Quit to Menu', 'Pause menu (plugin log 0.1)'),
    ('code', 'Settings ', 'Pause menu (plugin log 0.1)'),
]


class I2Reader:
    """I2 LanguageSourceAsset without a typetree (the generator lays out TermData wrong)."""

    def __init__(self, raw: bytes):
        self.raw, self.p = raw, 0

    def u32(self):
        v = struct.unpack_from('<i', self.raw, self.p)[0]
        self.p += 4
        return v

    def align(self):
        self.p = (self.p + 3) & ~3

    def string(self):
        n = self.u32()
        v = self.raw[self.p:self.p + n].decode('utf-8')
        self.p += n
        self.align()
        return v

    def read(self):
        self.p = 28  # after m_GameObject, m_Enabled, m_Script
        name = self.string()
        self.p += 12  # three bools (aligned), empty Assets list, one flag
        terms = []
        for _ in range(self.u32()):
            term, kind = self.string(), self.u32()
            langs = [self.string() for _ in range(self.u32())]
            flags = self.u32()  # Flags byte[]
            self.p += flags
            self.align()
            touched = [self.string() for _ in range(self.u32())]
            terms.append({'term': term, 'type': kind, 'languages': langs, 'touched': touched})
        self.p += 12
        languages = []
        for _ in range(self.u32()):
            lang, code = self.string(), self.string()
            self.p += 4  # flags byte, aligned
            languages.append((lang, code))
        return name, terms, languages


def read_i2(data: Path):
    env = UnityPy.load(str(data / 'resources.assets'))
    sources = [o for o in env.objects if o.type.name == 'MonoBehaviour'
               and o.read(check_read=False).m_Script.deref().read().m_ClassName == 'LanguageSourceAsset']
    assert len(sources) == 1, 'expected one I2 LanguageSourceAsset'
    name, terms, languages = I2Reader(sources[0].get_raw_data()).read()
    assert name == 'I2Languages' and languages[0] == ('English', 'en'), (name, languages)
    assert all(len(t['languages']) == len(languages) and t['type'] == 0 for t in terms)
    return terms, languages


def path_of(mb):
    names = []
    try:
        go = mb.m_GameObject.deref().read()
        tr = go.m_Components[0].deref().read()  # m_Transform is None in UnityPy for these files
        names.append(go.m_Name)
        while tr.m_Father and tr.m_Father.m_PathID:
            tr = tr.m_Father.deref().read()
            names.append(tr.m_GameObject.deref().read().m_Name)
    except Exception:
        pass
    return '/'.join(reversed(names))


def scan_scenes(data: Path, game: Path):
    gen = TypeTreeGenerator(UNITY)
    gen.load_local_game(str(game))
    cache = {}

    def nodes(assembly, name):
        if (assembly, name) not in cache:
            base = gen.get_nodes(assembly.removesuffix('.dll'), name)  # IL2CPP: no .dll suffix
            cache[assembly, name] = TypeTreeNode.from_list(
                [TypeTreeNode(x.m_Level, x.m_Type, x.m_Name, 0, 0, m_MetaFlag=x.m_MetaFlag) for x in base])
        return cache[assembly, name]

    order = lambda p: (re.sub(r'\d+', '', p.name), int(re.sub(r'\D', '', p.name) or -1))
    files = sorted((p for p in data.iterdir() if p.suffix == '.assets' or re.fullmatch(r'level\d+', p.name)), key=order)
    texts, lockeys, subtitles, classes, fonts = {}, Counter(), Counter(), Counter(), []
    for f in files:
        env = UnityPy.load(str(f))  # keep a reference: deref() fails once the environment is collected
        for obj in env.objects:
            if os.path.basename(obj.assets_file.name) != f.name:
                continue
            if obj.type.name == 'Font':
                font = obj.read()
                fonts.append({'file': f.name, 'name': font.m_Name, 'kind': 'Font', 'bytes': len(font.m_FontData or b'')})
                continue
            if obj.type.name != 'MonoBehaviour':
                continue
            mb = obj.read(check_read=False)
            try:
                script = mb.m_Script.deref().read()
            except Exception:
                continue
            cls = script.m_ClassName
            full = f'{script.m_Namespace}.{cls}' if script.m_Namespace else cls
            classes[full] += 1
            if cls not in ('Text', 'TextMeshProUGUI', 'TextMeshPro', 'LocalizeText', 'SubtitleTrackAsset', 'TMP_FontAsset'):
                continue
            t = obj.read_typetree(nodes=nodes(script.m_AssemblyName, full))
            if cls == 'LocalizeText':
                lockeys[t['LocKey']] += 1
            elif cls == 'SubtitleTrackAsset':
                subtitles[t['Text']] += 1
            elif cls == 'TMP_FontAsset':
                chars = {x['m_Unicode'] for x in t['m_CharacterTable']}
                fonts.append({'file': f.name, 'name': t['m_Name'], 'kind': cls, 'mode': t['m_AtlasPopulationMode'],
                              'characters': len(chars), 'missing_polish': ''.join(c for c in PL if ord(c) not in chars),
                              'fallbacks': len(t['m_FallbackFontAssetTable'])})
            else:
                text = t.get('m_text', t.get('m_Text')) or ''
                if not text.strip():
                    continue
                entry = texts.setdefault(text, {'count': 0, 'files': [], 'paths': []})
                entry['count'] += 1
                if f.name not in entry['files']:
                    entry['files'].append(f.name)
                if len(entry['paths']) < 2:
                    entry['paths'].append(path_of(mb))
        print(f.name, flush=True)
    return {'texts': texts, 'lockeys': lockeys, 'subtitle_keys': subtitles, 'classes': classes, 'fonts': fonts}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--reuse', action='store_true', help='reuse work/scan.json from an earlier scan')
    args = ap.parse_args()
    data = args.game / DATA
    terms, languages = read_i2(data)
    i2_terms = {t['term'] for t in terms}

    scan_path = ROOT / 'work/scan.json'
    if args.reuse and scan_path.exists():
        scan = json.loads(scan_path.read_text(encoding='utf-8'))
    else:
        scan = scan_scenes(data, args.game)
        scan_path.parent.mkdir(parents=True, exist_ok=True)
        scan_path.write_text(json.dumps(scan, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    old = {(e.get('namespace', ''), e['key']): e for e in load_entries(ROOT)} if review_path(ROOT).exists() else {}
    rows = []

    def add(namespace, key, english, context):
        row = {'key': key, 'namespace': namespace, 'english': english,
               'polish': old.get((namespace, key), {}).get('polish', ''), 'context': context}
        if note := old.get((namespace, key), {}).get('note'):
            row['note'] = note
        rows.append(row)

    for namespace, key, context in CODE:
        add(namespace, key, key, context)
    for t in terms:
        if t['languages'][0]:
            add('i2', t['term'], t['languages'][0], t['term'])
    raw_subtitles = sorted(k for k in scan['subtitle_keys'] if k not in i2_terms and not I2_KEY.match(k))
    for text in raw_subtitles:
        add('subtitle', text, text, 'Timeline subtitle without an I2 term')
    skipped = {}
    for text, info in sorted(scan['texts'].items(), key=lambda kv: -kv[1]['count']):
        if PLACEHOLDER.match(text.strip()) or any(DEBUG_PATH.search(p) for p in info['paths']):
            skipped[text] = info['paths'][:1]
        else:
            add('ui', text, text, info['paths'][0] if info['paths'] else '')
    (ROOT / 'translations').mkdir(parents=True, exist_ok=True)
    write_entries(ROOT, rows)

    count = Counter(r['namespace'] for r in rows)
    chars = Counter()
    for r in rows:
        chars[r['namespace']] += len(r['english'])
    report = {
        'unity': UNITY, 'backend': 'IL2CPP x64',
        'i2': {'terms': len(terms), 'english_characters': sum(len(t['languages'][0]) for t in terms),
               'languages': languages,
               'filled_other': {lang: sum(bool(t['languages'][i]) for t in terms) for i, (lang, _) in enumerate(languages) if i}},
        'entries': dict(count), 'characters': dict(chars),
        'lockeys': scan['lockeys'], 'subtitle_track_clips': sum(scan['subtitle_keys'].values()),
        'dangling_keys': sorted(k for k in set(scan['lockeys']) | set(scan['subtitle_keys'])
                                if k not in i2_terms and I2_KEY.match(k)),
        'ui_skipped': skipped, 'fonts': scan['fonts'],
        'text_classes': {k: v for k, v in scan['classes'].items() if re.search(r'Text|Subtitle|Locali|Ticker|Chapter|Caption', k)},
        'game_modified': False,
    }
    (ROOT / 'work/analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('entries', 'characters', 'dangling_keys')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
