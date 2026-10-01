"""Translation batches for Possessor(s).

    python tools/batch.py init                 -> (re)build the review file from work/loc/en, keeping Polish
    python tools/batch.py show TABLE [PREFIX]  -> untranslated entries as `key @@ text`, Russian reference below
    python tools/batch.py put FILE             -> merge `key @@ text` lines; \\n = new line
    python tools/batch.py stats

Entry key: `<Table>/<namespace>/<key>` (namespace may be empty). English comes from the
game's locres; Russian (work/loc/ru) is shown only as a gender/context hint, never stored.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
import locres  # noqa: E402

sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, review_path, untranslated, write_entries  # noqa: E402

# Menu first, then the game in rough play order; Articy scenes sorted by scene and line number.
TABLES = ['UI', 'Game', 'Narrative', 'Articy_Intro', 'Articy_Region_CampusHill',
          'Articy_Region_FluorescentPark', 'Articy_Region_SunkenCity', 'Articy_Region_Dockyard',
          'Articy_Region_InvertedPlaza', 'Articy_Region_Zooquarium', 'Articy_Region_DeadMall',
          'Articy_Region_Lab', 'Articy_Region_Dream', 'Articy_SideQuests', 'Articy_Default',
          'Articy_Inspectables']
# Real rich-text markup and placeholders. Spans like `<Rancho Mirage Flats>` are shown
# as text (the Russian table translates them), so they are not tokens.
TAG_NAMES = r'(?:i|I|b|small|xsmall|x-large|Header|Boss|Item|item|Location|Default|Keyword\.Item|[Dd][Ll]ang(?:\.\w+)?)'
TOKEN = re.compile(r'</>|<' + TAG_NAMES + r'>|<\w+ id="[^"]*"\s*/?>|\{[^{}]+\}')


def tokens(text):
    return sorted(TOKEN.findall(text))


def scene_order(key):
    match = re.search(r'DFr_(.+?)_(\d{4})_0x', key)
    return (match.group(1), int(match.group(2)), key) if match else (key, 0, key)


def english(culture='en'):
    rows = {}
    for table in TABLES:
        path = ROOT / 'work' / 'loc' / culture / f'{table}.locres'
        if not path.exists():
            continue
        texts = locres.load(path).texts()
        if table.startswith('Articy'):
            order = sorted(texts, key=lambda k: scene_order(k[1]))
        else:
            order = sorted(texts, key=lambda k: (k[0], texts[k].lower(), k[1]))
        for namespace, key in order:
            rows[f'{table}/{namespace}/{key}'] = texts[(namespace, key)]
    return rows


def check(name, source, text):
    assert source.count('\n') == text.count('\n'), ('new lines', name)
    assert tokens(source) == tokens(text), ('tokens', name, tokens(source), tokens(text))
    assert '�' not in text, ('replacement char', name)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    command = sys.argv[1]
    source = english()
    if command == 'init':
        old = {e['key']: e for e in load_entries(ROOT)} if review_path(ROOT).exists() else {}
        rows = []
        for key, text in source.items():
            polish = old[key]['polish'] if key in old and old[key]['english'] == text else ''
            rows.append({'key': key, 'english': text, 'polish': polish})
        write_entries(ROOT, rows)
        print('entries', len(rows), 'kept', sum(1 for r in rows if r['polish']))
        return
    entries = load_entries(ROOT)
    index = {e['key']: e for e in entries}
    if command == 'show':
        table = sys.argv[2]
        prefix = sys.argv[3] if len(sys.argv) > 3 else ''
        russian = english('ru')
        rows = [e for e in entries if e['key'].startswith(f'{table}/')]
        for number, e in enumerate(rows):
            if prefix in e['key'] and untranslated(e):
                match = re.search(r'DFr_(.+?)_0x', e['key'])
                label = f'{number} {match.group(1)}' if match else e['key']
                print(f"{label} @@ " + e['english'].replace('\r', '').replace('\n', '\\n'))
                ru = russian.get(e['key'])
                if ru:
                    print('    ru: ' + ru.replace('\r', '').replace('\n', '\\n'))
    elif command == 'put':
        count = 0
        for line in Path(sys.argv[2]).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#') or line.startswith('    ru:'):
                continue
            name, text = line.split(' @@ ', 1)
            entry = index[name]
            original = entry['english']
            text = text.replace('\\n', '\r\n' if '\r\n' in original else '\n')
            check(name, original, text)
            # Keep leading/trailing spaces of the original: the game glues values to them.
            lead = original[:len(original) - len(original.lstrip(' '))]
            trail = original[len(original.rstrip(' ')):]
            entry['polish'] = lead + text.strip(' ') + trail
            count += 1
        write_entries(ROOT, entries)
        done = sum(1 for e in entries if not untranslated(e))
        print('put', count, '| translated', done, 'of', len(entries))
    elif command == 'putn':
        # `N @@ PL` lines: N = position of the entry within TABLE in file order (as `show` prints).
        table = sys.argv[2]
        rows = [e for e in entries if e['key'].startswith(f'{table}/')]
        count = 0
        for line in Path(sys.argv[3]).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            number, text = line.split(' @@ ', 1)
            entry = rows[int(number.split()[0])]
            original = entry['english']
            value = text.replace('\\n', '\r\n' if '\r\n' in original else '\n')
            check(entry['key'], original, value)
            lead = original[:len(original) - len(original.lstrip(' '))]
            trail = original[len(original.rstrip(' ')):]
            entry['polish'] = lead + value.strip(' ') + trail
            count += 1
        write_entries(ROOT, entries)
        done = sum(1 for e in entries if not untranslated(e))
        print('put', count, '| translated', done, 'of', len(entries))
    elif command == 'puten':
        # `EN @@ PL` lines: every untranslated entry of TABLE with exactly this English gets PL.
        table = sys.argv[2]
        by_english = {}
        for e in entries:
            if e['key'].startswith(f'{table}/') and untranslated(e):
                flat = e['english'].replace('\r', '').replace('\n', '\\n').strip(' ')
                by_english.setdefault(flat, []).append(e)
        count, missing = 0, []
        for line in Path(sys.argv[3]).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            source_flat, text = line.split(' @@ ', 1)
            hits = by_english.get(source_flat.strip(' '))
            if not hits:
                missing.append(source_flat)
                continue
            for entry in hits:
                original = entry['english']
                value = text.replace('\\n', '\r\n' if '\r\n' in original else '\n')
                check(entry['key'], original, value)
                lead = original[:len(original) - len(original.lstrip(' '))]
                trail = original[len(original.rstrip(' ')):]
                entry['polish'] = lead + value.strip(' ') + trail
                count += 1
        write_entries(ROOT, entries)
        for m in missing:
            print('NO MATCH:', m)
        done = sum(1 for e in entries if not untranslated(e))
        print('put', count, '| translated', done, 'of', len(entries))
    elif command == 'stats':
        for table in TABLES:
            rows = [e for e in entries if e['key'].startswith(f'{table}/')]
            done = sum(1 for e in rows if not untranslated(e))
            print(f'{table:32} {done:5}/{len(rows):5}')
        print('total', sum(1 for e in entries if not untranslated(e)), '/', len(entries))


if __name__ == '__main__':
    main()
