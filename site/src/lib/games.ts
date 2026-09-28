import { getCollection, type CollectionEntry } from 'astro:content';
import { withBase } from './url';

export type Tone = 'ink' | 'red' | 'graphite';

/** Status from games/catalog.yaml, with its position in the file (drives filter order). */
export type Status = Omit<CollectionEntry<'statuses'>['data'], 'games'> & { id: string; order: number };

export type Game = CollectionEntry<'games'>['data'] & {
  id: string;
  status: Status;
  added: Date;
  tone: Tone;
  href: string;
};

const TONES: Tone[] = ['ink', 'red', 'graphite'];

export async function getStatuses(): Promise<Status[]> {
  const entries = await getCollection('statuses');
  return entries.map(({ id, data: { games: _, ...rest } }, order) => ({ ...rest, id, order }));
}

/**
 * Game -> status and date added from games/catalog.yaml. The build must fail when a game
 * has no status, has two, or the file lists a slug missing from games/; a silent mistake
 * would be worse.
 */
async function catalogBySlug(slugs: string[]): Promise<Map<string, { status: Status; added: Date }>> {
  const [entries, statuses] = await Promise.all([getCollection('statuses'), getStatuses()]);
  if (entries.length === 0) throw new Error('games/catalog.yaml: brak pliku albo statusów.');
  const assigned = new Map<string, { status: Status; added: Date }>();

  entries.forEach((entry, index) => {
    for (const [slug, added] of Object.entries(entry.data.games)) {
      const previous = assigned.get(slug);
      if (previous) throw new Error(`games/catalog.yaml: „${slug}" stoi i w „${previous.status.id}", i w „${entry.id}".`);
      if (!slugs.includes(slug)) throw new Error(`games/catalog.yaml: „${slug}" nie ma w games/.`);
      assigned.set(slug, { status: statuses[index]!, added });
    }
  });

  const missing = slugs.filter((slug) => !assigned.has(slug));
  if (missing.length > 0) throw new Error(`games/catalog.yaml: brak statusu dla ${missing.join(', ')}.`);

  return assigned;
}

export async function getGames(): Promise<Game[]> {
  const entries = await getCollection('games');
  const catalog = await catalogBySlug(entries.map((entry) => entry.data.slug));

  return entries
    .map((entry) => {
      return {
        ...entry.data,
        id: entry.id,
        ...catalog.get(entry.data.slug)!,
        // The game's own page; on a page with this panel the tile opens it without reload.
        href: withBase(`/${entry.data.slug}/`),
        tone: 'ink' as Tone,
      };
    })
    // Newest first by default; same day falls back to title. The on-page sorter gives the same order.
    .sort((a, b) => b.added.getTime() - a.added.getTime() || a.title.localeCompare(b.title, 'pl'))
    .map((game, index) => ({ ...game, tone: TONES[index % TONES.length]! }));
}

export function stats(games: Game[]) {
  const translated = games.reduce((sum, game) => sum + game.entries.done, 0);

  return [
    { value: String(games.length), label: 'gier' },
    { value: translated.toLocaleString('pl-PL'), label: 'przetłumaczonych wpisów' },
    { value: String(games.filter((game) => game.status.id === 'ready').length), label: 'gotowe' },
    { value: String(games.filter((game) => game.tested !== 'structural').length), label: 'sprawdzonych w grze' },
  ];
}

/** "485 wpisów" or "153 z 2305 wpisów": no repeated number when complete. */
export function entriesLabel(game: Game): string {
  const { done, total } = game.entries;
  return done >= total ? `${done} wpisów` : `${done} z ${total} wpisów`;
}
