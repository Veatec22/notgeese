import { getCollection, type CollectionEntry } from 'astro:content';
import { withBase } from './url';

export type Tone = 'ink' | 'red' | 'graphite';

/** Status from games/catalog.yaml, with its position in the file (drives filter order). */
export type Status = Omit<CollectionEntry<'statuses'>['data'], 'games'> & { id: string; order: number };

type Data = CollectionEntry<'games'>['data'];
export type Mod = Data['mods'][number];

export type Game = Data & {
  id: string;
  status: Status;
  added: Date;
  tone: Tone;
  href: string;
  /** False for catalog status `mods`: we don't translate the game, the page is about our mods. */
  translated: boolean;
};

/** Catalog status of games we don't translate (they have a Polish version) but made mods for. */
export const MODS_STATUS = 'mods';
const TRANSLATION_FIELDS = ['version', 'entries', 'tested', 'approach', 'scope', 'download'] as const;
export type TranslatedGame = Game & Required<Pick<Data, (typeof TRANSLATION_FIELDS)[number]>> & { translated: true };
export const isTranslated = (game: Game): game is TranslatedGame => game.translated;

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
      const { status, added } = catalog.get(entry.data.slug)!;
      const translated = status.id !== MODS_STATUS;
      // Same reasoning as the catalog check: a half-filled game.yaml must stop the build.
      if (translated) {
        const missing = TRANSLATION_FIELDS.filter((field) => entry.data[field] === undefined);
        if (missing.length > 0) throw new Error(`games/${entry.data.slug}/game.yaml: brak ${missing.join(', ')} (gra ma status tłumaczenia).`);
      } else if (entry.data.mods.length === 0) {
        throw new Error(`games/${entry.data.slug}/game.yaml: status „${MODS_STATUS}” bez żadnego moda.`);
      }
      return {
        ...entry.data,
        id: entry.id,
        status,
        added,
        translated,
        // The game's own page; on a page with this panel the tile opens it without reload.
        href: withBase(`/${entry.data.slug}/`),
        tone: 'ink' as Tone,
      };
    })
    // Newest first by default; same day falls back to title. The on-page sorter gives the same order.
    .sort((a, b) => b.added.getTime() - a.added.getTime() || a.title.localeCompare(b.title, 'pl'))
    .map((game, index) => ({ ...game, tone: TONES[index % TONES.length]! }));
}

/** Polish count noun: 1 mod, 2–4 mody, 5 modów (12–14 modów). */
function plural(n: number, one: string, few: string, many: string): string {
  if (n === 1) return one;
  const tens = n % 100;
  return n % 10 >= 2 && n % 10 <= 4 && (tens < 12 || tens > 14) ? few : many;
}

/** Translations lead; mods are one extra figure. */
export function stats(games: Game[]) {
  const translations = games.filter(isTranslated);
  const entries = translations.reduce((sum, game) => sum + game.entries.done, 0);
  const mods = games.reduce((sum, game) => sum + game.mods.length, 0);

  return [
    { value: String(translations.length), label: 'gier' },
    { value: entries.toLocaleString('pl-PL'), label: 'przetłumaczonych wpisów' },
    { value: String(translations.filter((game) => game.status.id === 'ready').length), label: 'gotowe' },
    { value: String(translations.filter((game) => game.tested !== 'structural').length), label: 'sprawdzonych w grze' },
    ...(mods > 0 ? [{ value: String(mods), label: plural(mods, 'mod', 'mody', 'modów') }] : []),
  ];
}

/** "485 wpisów" or "153 z 2305 wpisów": no repeated number when complete. */
export function entriesLabel(game: TranslatedGame): string {
  const { done, total } = game.entries;
  return done >= total ? `${done} wpisów` : `${done} z ${total} wpisów`;
}
