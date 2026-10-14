/**
 * Page titles and descriptions for search. Each game has its own /<slug>/ URL and its title
 * starts with what people type: „<gra> spolszczenie", then „PL" and „po polsku". Titles stay
 * short (Google cuts around 60 chars). The panel script sets the same title when the panel
 * opens without reload. Avoid „polska wersja" alone: it reads as an official or pirated game.
 * Games we only made mods for (no translation) never promise a translation.
 */
import type { Game } from './games';

export const HOME_TITLE = 'Not Geese — spolszczenia gier indie, gry po polsku';
export const HOME_DESCRIPTION =
  'Darmowe spolszczenia gier indie do pobrania: polskie napisy, polskie znaki i instrukcja instalacji. Gry po polsku, które nie dostały polskiej wersji językowej.';

export function gameTitle(game: Pick<Game, 'title' | 'translated' | 'mods'>): string {
  const core = game.translated
    ? `${game.title} spolszczenie PL — gra po polsku`
    : `${game.title} mod — ${game.mods.map((mod) => mod.title).join(', ')}`;
  const full = `${core} | Not Geese`;
  return full.length <= 60 ? full : core;
}

/** Shortens to the room left, at a word boundary. */
function fit(text: string, room: number): string {
  return text.length > room ? `${text.slice(0, room - 1).replace(/[\s,;—-]+\S*$/, '')}…` : text;
}

/** Description under the title in results: Google cuts around 155–160 chars, so the tail gets shortened. */
export function gameDescription(game: Game): string {
  const lead = game.translated
    ? `Zagraj w ${game.title} po polsku. Darmowe spolszczenie z polskimi napisami i instrukcją instalacji (v${game.version}).`
    : `${game.mods.length > 1 ? 'Darmowe mody' : 'Darmowy mod'} do ${game.title}: ${game.mods.map((mod) => mod.title.toLowerCase()).join(', ')}. Pobieranie i instrukcja instalacji.`;
  const tail = game.translated ? game.scope! : game.mods[0]!.summary;
  const room = 158 - lead.length - 1;
  return room < 20 ? lead : `${lead} ${fit(tail, room)}`;
}
