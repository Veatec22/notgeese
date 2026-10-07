// Data for the read-only workspace copy on the home page (Workshop.astro): one game laid out
// exactly as /admin/ shows it, by the same shared code the Edge Function uses. Fetched only
// when the section comes near, so the home page itself stays light.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';
import {
  parseReview,
  refId,
  resolveLayout,
  speakersFromBible,
} from '../../../supabase/functions/_shared/workspace/mod.ts';

const SLUG = 'shotgun-cop-man';
const TITLE = 'Shotgun Cop Man';

const dir = fileURLToPath(new URL(`../../../games/${SLUG}/translations/`, import.meta.url));
const read = (name: string) => readFileSync(dir + name, 'utf8');

export function GET() {
  const entries = parseReview(JSON.parse(read('en-pl-review.json')));
  const speakers = speakersFromBible(yaml.load(read('bible.yaml')));
  const layout = resolveLayout(yaml.load(read('structure.yaml')), entries, new Set(speakers?.keys() ?? []));

  const data = {
    slug: SLUG,
    title: TITLE,
    entries: entries.map((entry) => ({
      id: refId(entry),
      key: entry.key,
      english: entry.english,
      polish: entry.polish,
      ...(entry.max_length ? { max_length: entry.max_length } : {}),
    })),
    groups: layout.groups.map((group) => ({ id: group.id, name: group.name, entries: group.entries.map(refId) })),
    sequences: layout.sequences.map((sequence) => ({
      id: sequence.id,
      name: sequence.name,
      order: sequence.order,
      speakers: sequence.speakers,
      lines: sequence.lines.map((line) => ({
        id: refId(line),
        ...(line.speaker ? { speaker: speakers?.get(line.speaker) ?? line.speaker } : {}),
      })),
    })),
  };
  return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
}
