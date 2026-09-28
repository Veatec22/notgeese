"""Refresh translations/en-pl-review.json: English beside Polish, with speaker and addressee.

The review file is the only translation file; its `id` is the text asset's path_id.
English, context notes, speaker and addressee come from work/ref-all.json, produced by
tools/ref_extract.py from the original resources.assets.
Key format: `<path> [<speaker> > <addressee>]`, so the l10n report can match speakers
by regex. Assets with empty English have nothing to translate and are left out.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

import json  # noqa: E402

from translations import polish_by_field, write_entries  # noqa: E402

ref = json.loads((ROOT / 'work/ref-all.json').read_text(encoding='utf-8'))
pl = polish_by_field(ROOT, 'id')
rows = []
for pid, r in sorted(ref.items(), key=lambda kv: kv[1]['path']):
    if not r['en'] and int(pid) not in pl:
        continue
    key = r['path'] + (f" [{r['speaker']} > {r['to']}]" if r['speaker'] else '')
    rows.append(dict(id=int(pid), key=key, english=r['en'], polish=pl.get(int(pid), ''), context=r['note']))
write_entries(ROOT, rows)
print(len(rows), 'rows,', sum(1 for r in rows if r['polish']), 'translated')
