"""Translation batches for Holy Shoot.

    python tools/batch.py show [ns]      -> untranslated entries as `ns|key @@ text`
    python tools/batch.py put FILE       -> merge `ns|key @@ text` lines; \\n = new line
    python tools/batch.py stats

translations/en-pl-review.json is the only translation file:
namespace, key, english (from the game's locres) and polish; empty polish = not
translated yet. `namespace|key` is only the build's internal name for an entry.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'sprawl' / 'tools'))
import locres  # noqa: E402

sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, untranslated, write_entries  # noqa: E402

TOKEN = re.compile(r'\{[^}]+\}')


def ident(namespace, key):
    return f'{namespace}|{key}'


def load_polish():
    """{namespace|key: Polish} from the translation file, untranslated entries skipped."""
    return {ident(e.get('namespace', ''), e['key']): e['polish'] for e in load_entries(ROOT) if not untranslated(e)}


def source():
    return {ident(ns, key): text for (ns, key), text in locres.load(ROOT / 'work/en.locres').texts().items()}


def review_rows(english, polish):
    rows = []
    for name in sorted(english):
        ns, key = name.split('|', 1)
        rows.append({'namespace': ns, 'key': key, 'english': english[name], 'polish': polish.get(name, '')})
    return rows


def check(name, english, text):
    assert english.count('\n') == text.count('\n'), ('new lines', name)
    assert sorted(TOKEN.findall(english)) == sorted(TOKEN.findall(text)), ('tokens', name)


def save(english, polish):
    write_entries(ROOT, review_rows(english, polish))


def main():
    command = sys.argv[1]
    english = source()
    polish = load_polish()
    if command == 'show':
        prefix = sys.argv[2] if len(sys.argv) > 2 else None
        for name, text in sorted(english.items()):
            if name not in polish and (prefix is None or name.split('|', 1)[0] == prefix):
                print(f'{name} @@ ' + text.replace('\r', '').replace('\n', '\\n'))
    elif command == 'put':
        count = 0
        for line in Path(sys.argv[2]).read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            name, text = line.split(' @@ ', 1)
            source_text = english[name]
            text = text.replace('\\n', '\r\n' if '\r\n' in source_text else '\n')
            check(name, source_text, text)
            # Keep leading/trailing spaces of the original: the game glues values to them.
            lead = source_text[:len(source_text) - len(source_text.lstrip(' '))]
            trail = source_text[len(source_text.rstrip(' ')):]
            polish[name] = lead + text.strip(' ') + trail
            count += 1
        save(english, polish)
        print('put', count, 'translated', len(polish), 'of', len(english))
    elif command == 'stats':
        print(len(polish), 'of', len(english))


if __name__ == '__main__':
    main()
