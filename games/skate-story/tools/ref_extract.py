"""Dump Skate Story's I2 table in all languages into work/ref-all.json (reference for gender and meaning).

    .venv\\Scripts\\python.exe games\\skate-story\\tools\\ref_extract.py backups\\skate-story\\resources.assets
"""
import json
import sys
from pathlib import Path

import UnityPy

from i2 import parse, parse_languages

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    env = UnityPy.load(sys.argv[1])
    obj = next(o for o in env.objects if o.path_id == 785)
    entries, tail = parse(obj.get_raw_data())
    languages, _ = parse_languages(tail)
    names = [language[0] for language in languages]
    print(names)
    out = {key: dict(zip(names, values)) for key, kind, values, flags, touch in entries}
    target = ROOT / 'work' / 'ref-all.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out))


if __name__ == '__main__':
    main()
