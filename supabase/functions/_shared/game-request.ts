// Game requests from the site form: what a player typed, reduced to one key per game.
// Pure TS, shared by the `game-request` function and the form on the home page.

export const TITLE_MAX = 120;
export const COMMENT_MAX = 500;

export type Target =
  | { store: 'steam'; id: string; key: string; url: string }
  | { store: 'gog'; id: string; key: string; url: string }
  | { store: null; key: string; title: string };

export class TargetError extends Error {}

const STEAM = /^(?:https?:\/\/)?(?:store\.steampowered\.com|steamcommunity\.com)\/app\/(\d{1,10})(?:[/?#]|$)/i;
const GOG = /^(?:https?:\/\/)?(?:www\.)?gog\.com\/(?:[a-z]{2}(?:-[a-z]{2})?\/)?game\/([a-z0-9_]{1,100})(?:[/?#]|$)/i;
const LINK = /^(?:https?:\/\/|www\.)|^[a-z0-9-]+(?:\.[a-z0-9-]+)+\//i;

/** Title for deduplication: no case, diacritics, spaces or punctuation. */
export function normalizeTitle(title: string): string {
  return title.normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase('en').replace(/[^\p{L}\p{N}]+/gu, '');
}

/** Steam or GOG link, or a plain title. Throws TargetError with a message for the player. */
export function parseTarget(input: string): Target {
  const text = input.trim();
  const steam = STEAM.exec(text);
  if (steam) {
    const id = String(Number(steam[1]));
    return { store: 'steam', id, key: `steam:${id}`, url: `https://store.steampowered.com/app/${id}/` };
  }
  const gog = GOG.exec(text);
  if (gog) {
    const id = gog[1]!.toLowerCase();
    return { store: 'gog', id, key: `gog:${id}`, url: `https://www.gog.com/en/game/${id}` };
  }
  if (LINK.test(text)) throw new TargetError('Przyjmuję tylko linki do sklepu Steam albo GOG. Możesz też wpisać sam tytuł.');
  const normalized = normalizeTitle(text);
  if (!normalized) throw new TargetError('Wpisz tytuł gry albo wklej link do Steam lub GOG.');
  if ([...text].length > TITLE_MAX) throw new TargetError(`Tytuł może mieć najwyżej ${TITLE_MAX} znaków.`);
  return { store: null, key: `title:${normalized}`, title: text };
}
