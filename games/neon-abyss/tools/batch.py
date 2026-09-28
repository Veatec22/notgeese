"""Neon Abyss translation batches.

    python tools/batch.py show [prefix] [limit] -> untranslated as `key @@ text`
    python tools/batch.py put FILE              -> add lines `key @@ text`; \\n = newline
    python tools/batch.py stats

translations/en-pl-review.json is the only translation file: English from work/source.json
(tools/extract.py) and Polish; empty `polish` = not translated yet. Text entries that are really
asset names (font paths, sprite names) aren't translated; the plugin copies them from English.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402

TOKEN = re.compile(r'\{[^}]*\}|</?[a-z]+(?:=[^>]*)?>|\[i2s_[^\]]*\]')
RESOURCE = re.compile(r'^(Fonts & Materials/.*|[a-z0-9]+(_[a-z0-9]+)+|-+|\.+|\?+|v\{\[Version\]\})$')


def english():
    data = json.loads((ROOT / 'work/source.json').read_text(encoding='utf-8'))
    index = [language['code'] for language in data['languages']].index('en-US')
    return {t['key']: t['values'][index] for t in data['terms']
            if t['type'] == 0 and t['values'][index].strip() and not RESOURCE.match(t['values'][index])}


def check(key, source, text):
    assert text.strip(), ('empty', key)
    assert '\\n' not in text, ('literal \\n', key)
    assert sorted(TOKEN.findall(source)) == sorted(TOKEN.findall(text)), ('tags', key)


def save(source, polish):
    rows = [{'key': key, 'english': text, 'polish': polish.get(key, '')} for key, text in source.items()]
    write_entries(ROOT, rows)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    source = english()
    polish = polish_by_key(ROOT)
    unknown = polish.keys() - source.keys()
    assert not unknown, ('keys not in the game', sorted(unknown)[:5])

    if command == 'show':
        prefix = sys.argv[2] if len(sys.argv) > 2 else ''
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
        todo = [(k, v) for k, v in source.items() if k not in polish and k.startswith(prefix)]
        for key, text in todo[:limit]:
            print(f'{key} @@ ' + text.replace('\n', '\\n'))
        print(f'# {min(limit, len(todo))} of {len(todo)}', file=sys.stderr)
    elif command == 'put':
        added = 0
        for line in Path(sys.argv[2]).read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            key, text = line.split(' @@ ', 1)
            key, text = key.strip(), text.strip().replace('\\n', '\n')
            assert key in source, ('unknown key', key)
            check(key, source[key], text)
            polish[key] = text
            added += 1
        save(source, polish)
        print(f'added {added}, total {len(polish)}/{len(source)}')
    elif command == 'stats':
        save(source, polish)
        print(json.dumps({'translated': len(polish), 'total': len(source)}))
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
