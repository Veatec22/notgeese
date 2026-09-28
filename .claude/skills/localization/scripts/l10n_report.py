"""Translation check report for one game. Reports only; never blocks.

Usage: python l10n_report.py games/<game> [--limit 80]
Reads translations/en-pl-review.json and optionally translations/bible.yaml,
writes work/l10n-report.md (git-ignored) and prints section counts.
"""
import argparse
import collections
import json
import re
from pathlib import Path

import yaml

TOKEN = re.compile(r'\[[a-z]+:[^\]]*\]|\{[^{}]*\}|</?[a-z]+(?:=[^>]*)?>|%[sd]|\\n')
MASC = re.compile(r'\b\w+ł(?:em|bym)\b', re.I)
FEM = re.compile(r'\b\w+ł(?:am|abym)\b', re.I)
# Nouns and imperatives that only look like past-tense verb forms.
NOT_VERB = {
    'stołem', 'kołem', 'aniołem', 'popiołem', 'orłem', 'czołem', 'dołem', 'mułem',
    'wołem', 'tyłem', 'kościołem', 'żywiołem', 'ogółem', 'przemysłem', 'pomysłem',
    'zmysłem', 'węzłem', 'masłem', 'hasłem', 'rzemiosłem', 'krzesłem', 'wiosłem',
    'złam', 'połam', 'przełam', 'wyłam', 'odłam', 'nadłam', 'ułam', 'załam',
    'reklam', 'kłam', 'skłam', 'okłam',
}
# Present/future of -łać verbs ("wysyłam", "zdziałam").
NOT_VERB_SUFFIX = ('syłam', 'działam', 'wołam', 'syłabym')
ADDRESS_TY = re.compile(r'\b\w+ł(?:eś|aś)\b|\bjesteś\b', re.I)
PLURAL_PLACEHOLDER = re.compile(r'\{[^{}]+\}\s+[A-Za-z]+s\b')
EN_WORDS = re.compile(r'\b(?:the|and|you|your|with|this|that|press|click)\b', re.I)

TITLES = {
    'missing': 'Not translated', 'tokens': 'Tokens and tags',
    'gender': 'Speaker gender (per bible)', 'address': 'Form of address',
    'terms': 'Bible terms', 'consistency': 'Consistency: same EN, different PL',
    'english': 'English leftovers', 'plurals': 'Plurals with placeholders',
    'length': 'Length (clipping risk)', 'capitals': 'Capitals',
    'typography': 'Typography',
}


def is_name(word, keep):
    """Word from the name list, also inflected ("Wastera") or with dots ("Psst...")."""
    w = re.split(r"['’]", word.lower().strip('.,!?:;„”"()'))[0]
    return w in keep or any(len(k) >= 4 and w.startswith(k) for k in keep)


def load(game):
    review = json.loads((game/'translations/en-pl-review.json').read_text(encoding='utf-8'))
    path = game/'translations/bible.yaml'
    bible = yaml.safe_load(path.read_text(encoding='utf-8')) if path.exists() else {}
    return review, bible or {}


def row_id(row):
    parts = [row.get('table'), row.get('term') or row.get('key')]
    return ' '.join(str(p) for p in parts if p)


def short(text, n=140):
    text = text.replace('\n', '⏎')
    return text if len(text) <= n else text[:n-1] + '…'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('game', type=Path)
    ap.add_argument('--limit', type=int, default=80, help='max items per section in the file')
    args = ap.parse_args()
    game = args.game.resolve()
    review, bible = load(game)
    rows = [r for r in review if r.get('english', '').strip()]

    keep = [str(x).lower() for x in bible.get('keep_english') or []]
    keep += [str(p.get('name', '')).lower() for p in bible.get('characters') or []]
    keep += [w for phrase in list(keep) if ' ' in phrase for w in phrase.split()]
    stems = [str(f).lower() for t in bible.get('terms') or [] for f in t.get('forms') or []]
    settings = bible.get('settings') or {}
    dialog_re = re.compile(settings['dialog_key']) if settings.get('dialog_key') else None
    ignores = [(i['check'], re.compile(i['key'])) for i in bible.get('ignore') or []]

    found = collections.OrderedDict((name, []) for name in TITLES)

    def report(check, row, note):
        rid = row_id(row)
        if any(c == check and rx.search(rid) for c, rx in ignores):
            return
        found[check].append((rid, row['english'], row.get('polish', ''), note))

    for row in rows:
        en, pl = row['english'], row.get('polish', '')
        if not pl.strip():
            report('missing', row, 'not translated')
            continue
        if collections.Counter(TOKEN.findall(en)) != collections.Counter(TOKEN.findall(pl)):
            report('tokens', row, 'tokens/tags differ from the original')
        if PLURAL_PLACEHOLDER.search(en):
            report('plurals', row, 'number in placeholder: check 1 / 2-4 / 5+')
        low = pl.lower()
        en_words = re.findall(r"[A-Za-z][A-Za-z'’-]*", TOKEN.sub(' ', en))
        only_names = en_words and all(is_name(w, keep) for w in en_words)
        if pl.strip() == en.strip() and re.search(r'[A-Za-z]{3}', en) and not only_names and low.strip() not in keep:
            report('english', row, 'identical to the original')
        elif len(EN_WORDS.findall(pl)) >= 2:
            report('english', row, 'English words in the text')

        # Typography
        if re.search(r'"[^"]+"', pl):
            report('typography', row, 'straight quotes instead of „”')
        if re.search(r'\w - \w', pl) and not re.search(r'\w\s+- ', en):
            report('typography', row, 'hyphen instead of dash')
        if re.search(r'\s[?!:;](?:\s|$)', pl):
            report('typography', row, 'space before punctuation')
        if (en[:1] == ' ') != (pl[:1] == ' ') or (en[-1:] == ' ') != (pl[-1:] == ' '):
            report('typography', row, 'leading/trailing space differs from the original (appended number?)')
        if '  ' in pl.strip() and '  ' not in en.strip():
            report('typography', row, 'double space')

        # Capitals in short UI strings
        words = pl.split()
        if 2 <= len(words) <= 6 and not pl.isupper():
            caps = [w for prev, w in zip(words, words[1:])
                    if w[:1].isupper() and not w.isupper() and not prev.endswith(('.', '!', '?', '…'))
                    and not is_name(w, keep + stems)]
            en_caps = [w for w in en.split()[1:] if w[:1].isupper()]
            if len(caps) >= 2 and len(en_caps) >= 2:
                report('capitals', row, 'Title Case carried over from English?')

        # Length
        rid = row_id(row)
        is_dialog = bool(dialog_re and dialog_re.search(rid))
        if is_dialog:
            if len(pl) > 60 and len(pl) > len(en) * 1.35:
                report('length', row, f'subtitle {len(pl)} chars vs {len(en)} in EN')
        elif len(en) <= 30 and len(pl) > max(len(en) * 1.6, len(en) + 10):
            report('length', row, f'UI {len(pl)} chars vs {len(en)} in EN')

    # Speaker gender and form of address
    for person in bible.get('characters') or []:
        if not person.get('key'):
            continue
        rx = re.compile(person['key'])
        wrong = MASC if person.get('gender') == 'f' else FEM if person.get('gender') == 'm' else None
        formal = str(person.get('addresses_player', '')).startswith(('pan', 'pani'))
        for row in rows:
            if not rx.search(row_id(row)) or not row.get('polish'):
                continue
            name = person.get('name', person['id'])
            if wrong:
                hits = [w for w in wrong.findall(row['polish'])
                        if w.lower() not in NOT_VERB and not w.lower().endswith(NOT_VERB_SUFFIX)]
                if hits:
                    report('gender', row, f"{name} ({person['gender']}): {', '.join(hits)}")
            if formal and ADDRESS_TY.search(row['polish']):
                report('address', row, f'{name} addresses the player as pan/pani: "ty" form?')

    # Bible terms
    for term in bible.get('terms') or []:
        en_rx = re.compile(r'\b' + term['en'] + r'\b', re.I)
        forms = [f.lower() for f in term.get('forms') or [term['pl'][:5]]]
        for row in rows:
            if en_rx.search(row['english']) and row.get('polish') and not any(f in row['polish'].lower() for f in forms):
                report('terms', row, f"{term['en']} -> {term['pl']}")

    # Same short original, different translations
    groups = collections.defaultdict(list)
    for row in rows:
        if len(row['english']) <= 60 and row.get('polish'):
            groups[row['english'].strip().lower()].append(row)
    for items in groups.values():
        variants = {r['polish'].strip().lower() for r in items}
        if len(variants) > 1:
            for r in items:
                report('consistency', r, f'{len(variants)} variants for the same EN')

    out = [f'# Check report: {game.name}', '',
           'For review only. A hit is a place to look at, not a verdict.', '',
           f'Entries with text: {len(rows)}. Bible: {"yes" if bible else "none"}.', '']
    out += ['| Section | Hits |', '| --- | ---: |']
    out += [f'| {TITLES[k]} | {len(v)} |' for k, v in found.items()]
    for key, items in found.items():
        if not items:
            continue
        out += ['', f'## {TITLES[key]} ({len(items)})', '']
        for rid, en, pl, note in items[:args.limit]:
            out += [f'- `{rid}`: {note}', f'  - EN: {short(en)}', f'  - PL: {short(pl)}']
        if len(items) > args.limit:
            out.append(f'- ... and {len(items) - args.limit} more')
    target = game/'work/l10n-report.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(' '.join(f'{k}={len(v)}' for k, v in found.items()))
    print(target)


if __name__ == '__main__':
    main()
