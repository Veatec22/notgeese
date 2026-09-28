"""Compare 1st and 2nd person gendered forms: the game's Russian column vs our Polish.

Prints entries where RU says "я …ла" and PL "-łem" (or the reverse), and the same for "ты".
A hint, not a verdict: Russian translators also worked without context.
Needs work/ref-all.json from tools/ref_extract.py.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import polish_by_key  # noqa: E402

NOT = {'stołem', 'kołem', 'aniołem', 'popiołem', 'czołem', 'dołem', 'tyłem', 'pomysłem', 'hasłem', 'masłem', 'złam', 'połam', 'reklam', 'wysyłam'}
M1, F1 = r'\b\w+ł(?:em|bym)\b', r'\b\w+ł(?:am|abym)\b'
M2, F2 = r'\b\w+ł(?:eś|byś)\b', r'\b\w+ł(?:aś|abyś)\b'


def ru_gender(text, pronoun):
    text = re.sub(r'<[^>]+>|\*\w+\*', ' ', text)
    found = set()
    for sentence in re.split(r'[.!?\n…]', text):
        if re.search(r'\b' + pronoun + r'\b', sentence, re.I):
            if re.search(r'\b\w{2,}(?:ла|лась)\b', sentence):
                found.add('f')
            if re.search(r'\b\w{2,}[аеиоуыяё](?:л|лся)\b|\b(?:шёл|пришёл|нашёл|ушёл|пошёл|вошёл|мог|смог|помог|лёг|съел)\b', sentence):
                found.add('m')
    return found


def pl_gender(text, masculine, feminine):
    found = set()
    if [w for w in re.findall(masculine, text, re.I) if w.lower() not in NOT]:
        found.add('m')
    if [w for w in re.findall(feminine, text, re.I) if w.lower() not in NOT]:
        found.add('f')
    return found


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    reference = json.loads((ROOT / 'work/ref-all.json').read_text(encoding='utf-8'))
    polish = polish_by_key(ROOT)
    for key, row in reference.items():
        if key not in polish:
            continue
        r1, p1 = ru_gender(row['Russian'], 'я'), pl_gender(polish[key], M1, F1)
        r2, p2 = ru_gender(row['Russian'], 'ты'), pl_gender(polish[key], M2, F2)
        if (r1 and p1 and not r1 & p1) or (r2 and p2 and not r2 & p2):
            print(key, '|', row['TYPE'], '| ja RU', r1, 'PL', p1, '| ty RU', r2, 'PL', p2)
            print('   RU:', row['Russian'].replace('\n', ' ')[:150])
            print('   PL:', polish[key].replace('\n', ' ')[:150])


if __name__ == '__main__':
    main()
