"""Write a batch of Polish texts into translations/en-pl-review.json.

    apply_batch.py <batch.json> [...]
    apply_batch.py --by-english <map.json> [...]

A batch is a JSON object {"<namespace>|<key>": "Polish text"}; the unnamed namespace is
written as "|<key>". An unknown id is an error; nothing is written then.
With --by-english the object maps English text to Polish and fills every still untranslated
entry with exactly that English; an English text that matches nothing is an error.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import load_entries, write_entries  # noqa: E402


def main():
    entries = load_entries(ROOT)
    index = {f"{e.get('namespace', '')}|{e['key']}": e for e in entries}
    changed = 0
    args = sys.argv[1:]
    if args and args[0] == '--by-english':
        for name in args[1:]:
            mapping = json.loads(Path(name).read_text(encoding='utf-8'))
            unused = [en for en in mapping if not any(e['english'] == en for e in entries)]
            if unused:
                raise SystemExit(f'{name}: English not found {unused[:3]}; nothing written.')
            for e in entries:
                if not e['polish'] and e['english'] in mapping:
                    e['polish'] = mapping[e['english']]
                    changed += 1
        args = []
    for name in args:
        batch = json.loads(Path(name).read_text(encoding='utf-8'))
        unknown = [k for k in batch if k not in index]
        if unknown:
            raise SystemExit(f'{name}: unknown ids {unknown[:5]}; nothing written.')
        for ident, text in batch.items():
            if index[ident]['polish'] != text:
                index[ident]['polish'] = text
                changed += 1
    write_entries(ROOT, entries)
    done = sum(1 for e in entries if e['polish'] or not e['english'].strip())
    print(json.dumps({'changed': changed, 'done': done, 'total': len(entries)}))


if __name__ == '__main__':
    main()
