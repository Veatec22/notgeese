"""Translator workshop: batches of entries to translate and merging into en-pl-review.json.

    batch.py dump [--size 120]     # next untranslated entries, in game order
    batch.py merge <batch.json>    # merges a batch into translations/en-pl-review.json

`dump` shows key, English and Russian (speaker gender in the past tense).
A line whose English already has a translation elsewhere gets a "=" hint; if the batch
doesn't overwrite it, `merge` writes the hint. The last batch's entry list is in
work/last_batch.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key, write_entries  # noqa: E402

LAST = ROOT / 'work' / 'last_batch.json'


def load():
    texts = json.loads((ROOT / 'work' / 'texts.json').read_text(encoding='utf-8'))
    pl = polish_by_key(ROOT)
    return texts, pl


def order(t):
    fn = t['fn']
    rank = {'gml_Script_init_option_translations': 0, 'gml_Script_init_misc_text': 1}.get(fn, 2)
    return (rank, t['line'] if t['line'] is not None else -1)


def by_english(texts, pl):
    out = {}
    for t in texts:
        if t['key'] in pl:
            out.setdefault(t['en'], pl[t['key']])
    return out


def save(pl):
    """Translated entries in work/texts.json order, as in tools/review.py."""
    texts = json.loads((ROOT / 'work' / 'texts.json').read_text(encoding='utf-8'))
    write_entries(ROOT, [{'key': t['key'], 'english': t['en'], 'polish': pl[t['key']], 'context': t['ru']}
                         for t in texts if t['key'] in pl])


def dump(size: int):
    texts, pl = load()
    known = by_english(texts, pl)
    todo = [t for t in sorted(texts, key=order) if t['key'] not in pl]
    batch = todo[:size]
    LAST.write_text(json.dumps([t['key'] for t in batch]), encoding='utf-8')
    done = len(texts) - len(todo)
    print(f'# {done}/{len(texts)} translated, {len(batch)} in batch, {len(todo) - len(batch)} left')
    for t in batch:
        print(f"\n{t['key']}\nEN {t['en']}\nRU {t['ru']}")
        if t['en'] in known:
            print(f"= {known[t['en']]}")


def merge(path: Path):
    texts, pl = load()
    part = json.loads(path.read_text(encoding='utf-8'))
    keys = {t['key'] for t in texts}
    bad = [k for k in part if k not in keys]
    if bad:
        sys.exit(f'unknown keys: {bad[:10]}')
    pl.update(part)
    known = by_english(texts, pl)
    last = json.loads(LAST.read_text(encoding='utf-8')) if LAST.exists() else []
    en = {t['key']: t['en'] for t in texts}
    auto = 0
    for k in last:
        if k not in pl and en[k] in known:
            pl[k] = known[en[k]]
            auto += 1
    missing = [k for k in last if k not in pl]
    save(pl)
    print(f'merged {len(part)}, hints {auto}, untranslated from batch: {len(missing)} {missing[:8]}')
    print(f'total {len(pl)}/{len(texts)}')


if __name__ == '__main__':
    if sys.argv[1] == 'dump':
        dump(int(sys.argv[3]) if len(sys.argv) > 3 else 120)
    else:
        merge(Path(sys.argv[2]))
