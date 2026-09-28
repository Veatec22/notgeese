// State of every game vs the workspace, using the same rules as the Edge Functions.
//
//   npx -y deno run --allow-read tools/check_games.ts
//
// Checks the translation file, structure and bible, that the game has exactly one
// translation file (no pl.json) and its docs. Prints a status table. Exit code 1 on any error.
import { parse as parseYaml } from 'jsr:@std/yaml@1';
import {
  FormatError,
  parseReview,
  resolveLayout,
  speakersFromBible,
} from '../supabase/functions/_shared/workspace/mod.ts';

const root = new URL('../games/', import.meta.url);
const exists = (path: URL) => {
  try {
    Deno.statSync(path);
    return true;
  } catch {
    return false;
  }
};
const read = (path: URL) => (exists(path) ? Deno.readTextFileSync(path) : null);
const issue = (error: unknown) =>
  error instanceof FormatError ? `${error.file}: ${error.issues[0]}` : (error as Error).message;

type Row = { game: string; entries: string; layout: string; bible: string; decisions: string; review: string };
const rows: Row[] = [];
const failures: string[] = [];

const games = [...Deno.readDirSync(root)]
  .filter((d) => d.isDirectory && exists(new URL(`${d.name}/game.yaml`, root)))
  .map((d) => d.name)
  .sort();

for (const game of games) {
  const dir = new URL(`${game}/`, root);
  const t = (name: string) => new URL(`translations/${name}`, dir);
  const row: Row = { game, entries: '', layout: '—', bible: '—', decisions: '—', review: '—' };
  let entries: ReturnType<typeof parseReview> | null = null;

  const reviewText = read(t('en-pl-review.json'));
  try {
    if (reviewText === null) throw new Error('missing translations/en-pl-review.json');
    entries = parseReview(JSON.parse(reviewText));
    row.entries = String(entries.length);
  } catch (error) {
    row.entries = `error: ${issue(error)}`;
    failures.push(`${game}: ${issue(error)}`);
  }

  let speakers: Set<string> | null = null;
  const bibleText = read(t('bible.yaml'));
  if (bibleText !== null) {
    try {
      const found = speakersFromBible(parseYaml(bibleText));
      speakers = found ? new Set(found.keys()) : null;
      row.bible = speakers ? `${speakers.size} characters` : 'yes';
    } catch (error) {
      row.bible = `error: ${issue(error)}`;
      failures.push(`${game}: bible.yaml: ${issue(error)}`);
    }
  }

  const structureText = read(t('structure.yaml'));
  if (structureText !== null && entries) {
    try {
      const layout = resolveLayout(parseYaml(structureText), entries, speakers);
      row.layout = `${layout.groups.length} groups, ${layout.sequences.length} sequences`;
    } catch (error) {
      row.layout = `error: ${issue(error)}`;
      failures.push(`${game}: structure.yaml: ${issue(error)}`);
    }
  }

  if (exists(t('pl.json'))) failures.push(`${game}: pl.json is back; en-pl-review.json is the only translation file`);
  for (const doc of ['README.md', 'docs/technical.md']) {
    if (!exists(new URL(doc, dir))) failures.push(`${game}: missing ${doc}`);
  }

  const decisions = read(new URL('docs/decisions.md', dir));
  if (decisions !== null) row.decisions = 'yes';
  // A `## Review` section starting with "No independent" records only the check report.
  const review = decisions?.match(/^## Review\b[^\n]*\n(?:\r?\n)*([^\r\n]*)/m);
  if (review && !/^No independent/.test(review[1])) row.review = 'yes';
  rows.push(row);
}

const header = ['Game', 'Entries', 'Structure', 'Bible', 'Decisions', 'Review'];
console.log(`| ${header.join(' | ')} |\n| ${header.map(() => '---').join(' | ')} |`);
for (const r of rows) {
  console.log(`| ${[r.game, r.entries, r.layout, r.bible, r.decisions, r.review].join(' | ')} |`);
}
const ready = rows.filter((r) => /^\d+$/.test(r.entries)).length;
const count = (pick: (r: Row) => boolean) => `${rows.filter(pick).length}/${rows.length}`;
console.log(`\nOpens in workspace: ${ready}/${rows.length}. Structure: ${count((r) => r.layout !== '—')}. Bible: ${count((r) => r.bible !== '—')}. Decisions: ${count((r) => r.decisions === 'yes')}. Review: ${count((r) => r.review === 'yes')}.`);

if (failures.length) {
  console.error(`\nErrors (${failures.length}):\n- ${failures.join('\n- ')}`);
  Deno.exit(1);
}
