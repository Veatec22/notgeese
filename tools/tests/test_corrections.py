"""Apply a workspace export to a copy of the Shotgun Cop Man files.

    python -m unittest discover -s tools/tests
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))

import corrections  # noqa: E402

GAME = 'shotgun-cop-man'
SOURCE = REPO / 'games' / GAME / 'translations' / 'en-pl-review.json'


def entry(key: str) -> dict:
    return next(e for e in json.loads(SOURCE.read_text(encoding='utf-8')) if e['key'] == key)


def correction(key: str, after: str, **override) -> dict:
    e = entry(key)
    return {'namespace': '', 'key': key, 'english': e['english'], 'before': e['polish'], 'after': after} | override


class CorrectionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.review = self.tmp / 'games' / GAME / 'translations' / 'en-pl-review.json'
        self.review.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE, self.review)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def export(self, corrections_list, conflicts=(), **extra) -> Path:
        path = self.tmp / 'export.json'
        data = {'format': 1, 'game': GAME, 'main_sha': 'b0b8d8c700fd46f4b84a117e83a766f30c1980c3',
                'exported_at': '2026-09-26T10:00:00.000Z', 'comment': '', 'corrections': list(corrections_list),
                'conflicts': list(conflicts)} | extra
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        return path

    def run_tool(self, *args) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = corrections.main(['apply', *map(str, args), '--repo', str(self.tmp)])
        return code, out.getvalue(), err.getvalue()

    def polish(self, key: str) -> str:
        return next(e for e in json.loads(self.review.read_text(encoding='utf-8')) if e['key'] == key)['polish']

    def test_applies_exact_text_and_touches_only_corrected_lines(self):
        after = 'Kampanie graczy \r\n<size=15>(Już wkrótce)</size> '
        code, out, _ = self.run_tool(self.export([correction('mCustomCampComing', after),
                                                  correction('mContinue', '<size=18>[continue]</size> Kontynuuj')]))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.polish('mCustomCampComing'), after)
        self.assertEqual(self.polish('mContinue'), '<size=18>[continue]</size> Kontynuuj')
        old = SOURCE.read_text(encoding='utf-8').splitlines()
        new = self.review.read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(old), len(new))
        self.assertEqual(sum(a != b for a, b in zip(old, new)), 2)
        self.assertTrue(self.review.read_bytes().endswith(b'}\n]\n'))

    def test_reapplying_the_same_export_changes_nothing(self):
        path = self.export([correction('mContinue', '<size=18>[continue]</size> Kontynuuj')])
        self.run_tool(path)
        before = self.review.read_bytes()
        code, out, _ = self.run_tool(path)
        self.assertEqual(code, 0)
        self.assertIn('already in file: 1', out)
        self.assertEqual(self.review.read_bytes(), before)

    def test_changed_english_other_polish_and_missing_entry_wait_for_decision(self):
        clean = correction('mContinue', 'Dalej!')
        code, out, _ = self.run_tool(self.export([
            clean,
            correction('mLoading', 'Wczytywanie...', english='Loading…'),
            correction('mAnyButton', 'Wciśnij cokolwiek', before='coś innego'),
            {'namespace': '', 'key': 'nieMaTakiego', 'english': 'x', 'before': 'y', 'after': 'z'},
        ]))
        self.assertEqual(code, 3)
        self.assertIn('needs a decision: 3', out)
        self.assertEqual(self.polish('mContinue'), 'Dalej!')
        self.assertEqual(self.polish('mLoading'), entry('mLoading')['polish'])
        self.assertEqual(self.polish('mAnyButton'), entry('mAnyButton')['polish'])

    def test_conflicts_are_listed_not_applied(self):
        e = entry('mLoading')
        conflict = {'namespace': '', 'key': 'mLoading', 'english': 'Old', 'before': 'a', 'after': 'Wczytuję',
                    'main_english': e['english'], 'main_polish': e['polish']}
        code, out, _ = self.run_tool(self.export([], [conflict]))
        self.assertEqual(code, 0)
        self.assertIn('workspace conflicts, not applied: 1', out)
        self.assertEqual(self.review.read_bytes(), SOURCE.read_bytes())

    def test_check_does_not_write(self):
        code, out, _ = self.run_tool(self.export([correction('mContinue', 'Dalej!')]), '--check')
        self.assertEqual(code, 0)
        self.assertIn('to apply: 1', out)
        self.assertEqual(self.review.read_bytes(), SOURCE.read_bytes())

    def test_bad_export_writes_nothing(self):
        for bad in ({'format': 2}, {'game': '../etc'}, {'corrections': [correction('mContinue', 'Dalej!')] * 2}):
            code, _, err = self.run_tool(self.export([correction('mContinue', 'Dalej!')], **bad) if 'corrections' not in bad
                                         else self.export(bad['corrections']))
            self.assertEqual(code, 1, bad)
            self.assertIn('Nothing written', err)
        self.assertEqual(self.review.read_bytes(), SOURCE.read_bytes())

    def test_keeps_file_style_of_other_games(self):
        data = json.loads(SOURCE.read_text(encoding='utf-8'))
        self.review.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        self.run_tool(self.export([correction('mContinue', 'Dalej!')]))
        text = self.review.read_text(encoding='utf-8')
        self.assertFalse(text.endswith('\n'))
        self.assertTrue(text.startswith('[\n {\n  "key"'))

    def test_comment_is_quoted_as_content(self):
        _, out, _ = self.run_tool(self.export([correction('mContinue', 'Dalej!')], comment='Sprawdź też menu.\nrm -rf /'))
        self.assertIn('> Sprawdź też menu.', out)
        self.assertIn('> rm -rf /', out)


if __name__ == '__main__':
    unittest.main()
