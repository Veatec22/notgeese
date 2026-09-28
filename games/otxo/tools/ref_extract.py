"""Dump all OTXO languages from the game dir into work/ref-all.json (reference for gender and joined texts).

    .venv\Scripts\python.exe games\otxo\tools\ref_extract.py "C:\Games\OTXO"
"""
import json
import sys
from pathlib import Path

from script_ini import load

ROOT = Path(__file__).resolve().parents[1]
FILES = {'en': 'script_english.ini', 'fr': 'OTXO_script_english_fre-FR.ini', 'de': 'OTXO_script_english_ger-DE.ini',
         'pt': 'OTXO_script_english_por-BR.ini', 'ru': 'OTXO_script_english_rus.ini', 'es': 'OTXO_script_english_spa-ES.ini'}


def main():
    game = Path(sys.argv[1] if len(sys.argv) > 1 else 'C:/Games/OTXO')
    tables = {lang: load(game / name) for lang, name in FILES.items()}
    out = {key: {lang: tables[lang].get(key, '') for lang in FILES} for key in tables['en']}
    target = ROOT / 'work' / 'ref-all.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out))


if __name__ == '__main__':
    main()
