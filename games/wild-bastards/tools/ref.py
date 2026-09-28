"""Show EN + FR (+ other languages) for keys matching a regex; needs work/ref-<lang>.json from tools/analyze.py.

.venv\\Scripts\\python.exe games\\wild-bastards\\tools\\ref.py <regex> [lang,lang]   -> key | EN | FR ...
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = json.loads((ROOT / 'translations/en-pl-review.json').read_text(encoding='utf-8'))
langs = sys.argv[2].split(',') if len(sys.argv) > 2 else ['fr']
refs = {l: json.loads((ROOT / f'work/ref-{l}.json').read_text(encoding='utf-8')) for l in langs}
pat = re.compile(sys.argv[1])
for r in REVIEW:
    if pat.search(r['key']) and r['english'].strip():
        print(r['key'], '|', r['english'].replace('\n', '\\n'))
        for l in langs:
            print('   ', l, '|', refs[l].get(r['key'], '').replace('\n', '\\n'))
