"""Validate the full translation against the original locres and EN/PL review."""
import json
import sys
import re
import unicodedata
from collections import Counter
from pathlib import Path

import locres

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))

from translations import load_entries, polish_by_ref  # noqa: E402
# Angle-bracket sound descriptions are visible prose, not formatting tags.
MARKUP = re.compile(r'</>|<(?:red|amber|blink)>|<img\b[^>]*>')
PLACEHOLDERS = re.compile(r'\{[^{}]+\}|%(?:\d+\$)?[sdf]|&(?:lt|gt|amp);')


def validate(source, translations, review):
    expected = source.texts()
    keyed = {(row['namespace'], row['key']): row for row in review}
    assert len(keyed) == len(review), 'Duplicate review keys.'
    assert translations.keys() == expected.keys(), 'Translation keys do not cover the source exactly.'
    assert keyed.keys() == expected.keys(), 'Review keys do not cover the source exactly.'
    for key, original in expected.items():
        text = translations[key]
        assert isinstance(text, str) and text.strip(), f'Empty translation: {key}'
        assert keyed[key]['english'] == original, f'Changed English source in review: {key}'
        assert keyed[key]['polish'] == text, f'Review out of sync: {key}'
        assert MARKUP.findall(text) == MARKUP.findall(original), f'Changed markup/icons: {key}'
        assert Counter(PLACEHOLDERS.findall(text)) == Counter(PLACEHOLDERS.findall(original)), f'Changed placeholders: {key}'
        assert '\ufffd' not in text, f'Unicode replacement character: {key}'
        assert not any(unicodedata.category(c) == 'Cc' and c not in '\r\n\t' for c in text), f'Unexpected control character: {key}'
        assert '[TEST PL]' not in text, f'Diagnostic marker: {key}'
    return {'translated': len(translations), 'source_entries': len(expected),
            'namespaces': dict(Counter(ns or '(none)' for ns, _ in expected)),
            'polish_characters': sum(map(len, translations.values()))}


def main():
    source = locres.load(ROOT / 'translations/en.locres')
    translations = polish_by_ref(ROOT)
    review = load_entries(ROOT)
    print(json.dumps(validate(source, translations, review), ensure_ascii=True))


if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Run without -O; validation assertions are required.')
    main()
