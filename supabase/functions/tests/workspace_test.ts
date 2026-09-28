// Pure workspace rule tests: `deno test supabase/functions/tests/` from the repo root.
import { assert, assertEquals, assertThrows } from 'jsr:@std/assert@1';
import { parse as parseYaml } from 'jsr:@std/yaml@1';
import {
  buildExport,
  type DraftAction,
  type Entry,
  FormatError,
  parseReview,
  planSave,
  resolveLayout,
  settle,
  speakersFromBible,
  stateAgainst,
  UNSORTED_GROUP,
  type WorkRow,
} from '../_shared/workspace/mod.ts';

const SCM = new URL('../../../games/shotgun-cop-man/translations/', import.meta.url);
const read = (name: string) => Deno.readTextFileSync(new URL(name, SCM));

const entry = (key: string, english: string, polish: string, namespace = ''): Entry => ({ namespace, key, english, polish });
const row = (key: string, fields: Partial<WorkRow>): WorkRow => ({
  namespace: '',
  key,
  action: 'accept',
  english: 'EN',
  before: null,
  after: 'PL',
  state: 'accepted',
  missing: false,
  ...fields,
});
const base = (english: string, polish: string) => ({ english, polish });

// --- review -------------------------------------------------------------------------

Deno.test('review SCM: 485 entries, empty namespace, text unchanged', () => {
  const entries = parseReview(JSON.parse(read('en-pl-review.json')));
  assertEquals(entries.length, 485);
  assert(entries.every((e) => e.namespace === ''));
  // Text exactly as in the file (review is the only translation file).
  const raw = JSON.parse(read('en-pl-review.json')) as { key: string; polish: string }[];
  entries.forEach((e, i) => assertEquals([e.key, e.polish], [raw[i].key, raw[i].polish]));
});

Deno.test('review: never trims spaces or newlines', () => {
  const [e] = parseReview([{ key: 'k', english: ' A\r\n', polish: 'B  \n' }]);
  assertEquals([e.english, e.polish], [' A\r\n', 'B  \n']);
});

Deno.test('review: dict, duplicate and missing field are format errors, not a partial game', () => {
  assertThrows(() => parseReview({ k: 'v' }), FormatError);
  const dup = assertThrows(() => parseReview([
    { key: 'a', english: '', polish: '' },
    { key: 'a', english: '', polish: '' },
    { key: 'b', english: 'x' },
  ]), FormatError);
  assertEquals(dup.issues.length, 2);
});

Deno.test('review: the same key in different namespaces are different entries', () => {
  const entries = parseReview([
    { key: 'a', namespace: 'x', english: '', polish: '' },
    { key: 'a', english: '', polish: '' },
  ]);
  assertEquals(entries.map((e) => e.namespace), ['x', '']);
});

// --- structure -----------------------------------------------------------------------

Deno.test('structure SCM: 9 groups, all entries assigned, Pedro sequence', () => {
  const entries = parseReview(JSON.parse(read('en-pl-review.json')));
  const speakers = speakersFromBible(parseYaml(read('bible.yaml')))!;
  const layout = resolveLayout(parseYaml(read('structure.yaml')), entries, new Set(speakers.keys()));
  assertEquals(layout.groups.length, 9);
  assert(!layout.groups.some((g) => g.id === UNSORTED_GROUP.id));
  assertEquals(layout.groups.reduce((n, g) => n + g.entries.length, 0), 485);
  const pedro = layout.sequences.find((s) => s.id === 'pedro-dlc')!;
  assertEquals(pedro.lines.length, 15);
  assertEquals(pedro.lines[1], { namespace: '', key: 'PedroDLCSpeech2', speaker: 'pedro' });
  assertEquals(pedro.lines[14].speaker, undefined);
  const settings = layout.groups.find((g) => g.id === 'settings')!;
  assert(settings.entries.some((e) => e.key === 'mResolution'));
});

const entries3 = [entry('mA', '', ''), entry('mB', '', ''), entry('zz', '', ''), entry('mA', '', '', 'ns')];
const groups2 = [{ id: 'one', name: 'Jeden' }, { id: 'two', name: 'Dwa' }];

Deno.test('structure: no file gives one group in review order', () => {
  const layout = resolveLayout(null, entries3, null);
  assertEquals(layout.groups.length, 1);
  assertEquals(layout.groups[0].entries.map((e) => e.key), ['mA', 'mB', 'zz', 'mA']);
});

Deno.test('structure: assignment beats rule, first rule wins, rest goes to unsorted', () => {
  const layout = resolveLayout({
    format: 1,
    groups: groups2,
    assign: [{ key: 'mB', group: 'two' }],
    rules: [{ group: 'one', match: '^m' }, { group: 'two', match: '^mA$' }],
  }, entries3, null);
  const keys = (id: string) => layout.groups.find((g) => g.id === id)?.entries.map((e) => `${e.namespace}/${e.key}`);
  assertEquals(keys('one'), ['/mA']);
  assertEquals(keys('two'), ['/mB']);
  // A rule without namespace does not cover an entry in namespace "ns".
  assertEquals(keys(UNSORTED_GROUP.id), ['/zz', 'ns/mA']);
});

Deno.test('structure: rule by context, alone or with key', () => {
  const withContext: Entry[] = [
    { ...entry('s1', 'Volume', 'Głośność'), context: 'oPause_Step_2, oInit' },
    { ...entry('s2', 'Kill all', 'Zabij'), context: 'oPControl_Step_2' },
    { ...entry('s3', 'Tip', 'Rada') },
    { ...entry('mX', 'Menu', 'Menu'), context: 'oPause_Create_0' },
  ];
  const layout = resolveLayout({
    format: 1,
    groups: groups2,
    rules: [{ group: 'two', match: '^m', context: '^oPause' }, { group: 'one', context: '^oPause' }, { group: 'two', context: 'PControl' }],
  }, withContext, null);
  const keys = (id: string) => layout.groups.find((g) => g.id === id)?.entries.map((e) => e.key);
  assertEquals(keys('one'), ['s1']);
  assertEquals(keys('two'), ['s2', 'mX']);
  assertEquals(keys(UNSORTED_GROUP.id), ['s3']);
  const err = assertThrows(() =>
    resolveLayout({ format: 1, groups: groups2, rules: [{ group: 'one' }, { group: 'one', context: '[' }] }, withContext, null), FormatError);
  assertEquals(err.issues.length, 2);
});

Deno.test('structure: errors are collected and never pose as a missing file', () => {
  const err = assertThrows(() =>
    resolveLayout({
      format: 1,
      groups: groups2,
      assign: [{ key: 'nope', group: 'one' }, { key: 'mA', group: 'three' }],
      rules: [{ group: 'one', match: '(' }, { group: 'one', match: '^m', extra: true }],
    }, entries3, null), FormatError);
  assertEquals(err.issues.length, 4);
  assertThrows(() => resolveLayout({ format: 2, groups: groups2 }, entries3, null), FormatError);
  assertThrows(() => resolveLayout('groups: []', entries3, null), FormatError);
});

Deno.test('structure: speaker outside the bible and line outside the sequence group are errors', () => {
  const sequence = (lines: unknown[]) => ({
    format: 1,
    groups: groups2,
    rules: [{ group: 'one', match: '^m' }, { group: 'two', match: '^z' }],
    sequences: [{
      id: 's',
      name: 'S',
      group: 'one',
      order: { certainty: 'certain', source: 'keys' },
      speakers: { certainty: 'reconstructed', source: 'text' },
      lines,
    }],
  });
  const ok = resolveLayout(sequence([{ key: 'mA', speaker: 'hero' }, { key: 'mB' }]), entries3, new Set(['hero']));
  assertEquals(ok.sequences[0].lines.length, 2);
  const err = assertThrows(
    () => resolveLayout(sequence([{ key: 'mA', speaker: 'villain' }, { key: 'zz' }]), entries3, new Set(['hero'])),
    FormatError,
  );
  assertEquals(err.issues.length, 2);
});

// --- settling (docs/workspace.md) ------------------------------------------------------

const main = entry('k', 'EN', 'PL');

Deno.test('settle: acceptance', () => {
  assertEquals(stateAgainst(row('k', {}), main).state, 'accepted');
  assertEquals(stateAgainst(row('k', { after: 'inne' }), main).state, 'review');
  assertEquals(stateAgainst(row('k', { english: 'stare EN' }), main).state, 'review');
});

Deno.test('settle: correction', () => {
  const correction = (fields: Partial<WorkRow>) => row('k', { action: 'correct', before: 'PL', after: 'Nowe', state: 'pending', ...fields });
  assertEquals(stateAgainst(correction({}), main), { action: 'correct', before: 'PL', state: 'pending' });
  assertEquals(stateAgainst(correction({ before: 'stare', after: 'PL' }), main), { action: 'accept', before: null, state: 'accepted' });
  assertEquals(stateAgainst(correction({ before: 'stare' }), main).state, 'conflict');
  // An EN change wins even when PL equals "after".
  assertEquals(stateAgainst(correction({ english: 'stare EN', after: 'PL' }), main).state, 'conflict');
});

Deno.test('settle: refresh without changes adds no journal item', () => {
  const rows = [row('k', {}), row('j', { action: 'correct', before: 'X', after: 'Y', state: 'pending' })];
  const result = settle(rows, [main, entry('j', 'EN', 'X')]);
  assertEquals(result.changed, []);
  assertEquals(result.journal, []);
  assertEquals(result.rows, rows);
});

Deno.test('settle: missing on main keeps the work, a return settles normally', () => {
  const saved = row('k', { action: 'correct', before: 'PL', after: 'Nowe', state: 'pending' });
  const gone = settle([saved], []);
  assertEquals(gone.changed, [{ ...saved, missing: true }]);
  assertEquals(gone.journal.map((j) => j.kind), ['missing']);
  assertEquals(settle(gone.rows, []).journal, []);

  const back = settle(gone.rows, [entry('k', 'EN', 'Nowe')]);
  assertEquals(back.changed[0].missing, false);
  assertEquals(back.changed[0].state, 'accepted');
  assertEquals(back.journal.map((j) => j.kind), ['returned', 'settle']);
});

// --- save ---------------------------------------------------------------------------

Deno.test('save: acceptance, correction, and correction equal to main as acceptance', () => {
  const entries = [entry('a', 'EN', 'PL'), entry('b', 'EN', 'PL'), entry('c', 'EN', 'PL')];
  const plan = planSave([
    { namespace: '', key: 'a', kind: 'accept', base: base('EN', 'PL') },
    { namespace: '', key: 'b', kind: 'correct', base: base('EN', 'PL'), after: 'Nowe  \n' },
    { namespace: '', key: 'c', kind: 'correct', base: base('EN', 'PL'), after: 'PL' },
  ], entries, []);
  assert(plan.ok);
  assertEquals(plan.upserts.map((r) => [r.key, r.action, r.state, r.after]), [
    ['a', 'accept', 'accepted', 'PL'],
    ['b', 'correct', 'pending', 'Nowe  \n'],
    ['c', 'accept', 'accepted', 'PL'],
  ]);
  assertEquals(plan.journal.map((j) => j.kind), ['accept', 'correct', 'accept']);
});

Deno.test('save: one stale draft rejects the whole save', () => {
  const plan = planSave([
    { namespace: '', key: 'a', kind: 'accept', base: base('EN', 'PL') },
    { namespace: '', key: 'b', kind: 'correct', base: base('EN', 'stare'), after: 'X' },
    { namespace: '', key: 'gone', kind: 'accept', base: base('EN', 'PL') },
  ], [entry('a', 'EN', 'PL'), entry('b', 'EN', 'PL')], []);
  assert(!plan.ok);
  assertEquals(plan.stale.map((s) => [s.key, s.main]), [['b', base('EN', 'PL')], ['gone', null]]);
});

Deno.test('save: undo, conflict resolution and a repeated action', () => {
  const entries = [entry('a', 'EN', 'PL'), entry('b', 'EN', 'main')];
  const saved = [row('a', {}), row('b', { action: 'correct', before: 'stare', after: 'moje', state: 'conflict' })];
  // "Stay with mine" = a correction based on current main.
  const plan = planSave([
    { namespace: '', key: 'a', kind: 'unset', base: base('EN', 'PL') },
    { namespace: '', key: 'b', kind: 'correct', base: base('EN', 'main'), after: 'moje' },
  ], entries, saved);
  assert(plan.ok);
  assertEquals(plan.deletes, [{ namespace: '', key: 'a' }]);
  assertEquals(plan.upserts.map((r) => [r.key, r.before, r.after, r.state]), [['b', 'main', 'moje', 'pending']]);

  const twice: DraftAction[] = [
    { namespace: '', key: 'a', kind: 'accept', base: base('EN', 'PL') },
    { namespace: '', key: 'a', kind: 'unset', base: base('EN', 'PL') },
  ];
  const dup = planSave(twice, entries, []);
  assert(!dup.ok && dup.invalid.length === 1);
});

Deno.test('save: removing work only for an entry gone from main', () => {
  const saved = [row('gone', { missing: true }), row('a', {})];
  const entries = [entry('a', 'EN', 'PL')];
  const ok = planSave([{ namespace: '', key: 'gone', kind: 'forget' }], entries, saved);
  assert(ok.ok);
  assertEquals(ok.deletes, [{ namespace: '', key: 'gone' }]);
  assertEquals(ok.journal.map((j) => j.kind), ['forget']);
  const refused = planSave([{ namespace: '', key: 'a', kind: 'forget' }], entries, saved);
  assert(!refused.ok && refused.invalid.length === 1);
});

Deno.test('save: settles saved state before applying actions', () => {
  const saved = [row('a', { action: 'correct', before: 'PL', after: 'Nowe', state: 'pending' })];
  const plan = planSave([], [entry('a', 'EN', 'Nowe')], saved);
  assert(plan.ok);
  assertEquals(plan.upserts.map((r) => [r.action, r.state]), [['accept', 'accepted']]);
});

// --- export -----------------------------------------------------------------

Deno.test('export: only pending corrections, conflicts separate, no acceptances or entries gone from main', () => {
  const entries = [entry('a', 'EN', 'PL'), entry('b', 'EN', 'PL'), entry('c', 'EN2', 'PL')];
  const rows = [
    row('a', { action: 'correct', before: 'PL', after: 'Nowe\\n <b>x</b> ', state: 'pending' }),
    row('b', {}),
    row('c', { action: 'correct', before: 'PL', after: 'Y', state: 'conflict' }),
    row('gone', { action: 'correct', before: 'X', after: 'Y', state: 'pending', missing: true }),
  ];
  const result = buildExport({ game: 'g', mainSha: 'abc', exportedAt: 't', comment: 'uwaga', rows, entries });
  assertEquals(result.corrections, [{ namespace: '', key: 'a', english: 'EN', before: 'PL', after: 'Nowe\\n <b>x</b> ' }]);
  assertEquals(result.conflicts.map((c) => [c.key, c.main_english, c.main_polish]), [['c', 'EN2', 'PL']]);
  assertEquals(JSON.parse(JSON.stringify(result)), result);
});
