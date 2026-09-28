/**
 * Page titles and descriptions for search. Each game has its own /<slug>/ URL and its title
 * starts with what people type: „<gra> spolszczenie". The panel script sets the same
 * title when the panel opens without reload.
 */
export const HOME_TITLE = 'Not Geese — spolszczenia do gier';
export const HOME_DESCRIPTION =
  'Nieoficjalne polskie tłumaczenia gier indie. Teksty, narzędzia i instrukcje instalacji dla każdego tytułu osobno.';

export function gameTitle(title: string): string {
  return `${title} spolszczenie — polska wersja do pobrania | Not Geese`;
}

/** Description under the title in results: Google cuts around 155–160 chars, so scope gets shortened. */
export function gameDescription(game: { title: string; version: string; scope: string }): string {
  const lead = `Spolszczenie ${game.title} (wersja ${game.version}) do pobrania za darmo, z instrukcją instalacji.`;
  const room = 158 - lead.length - 1;
  const scope = game.scope.length > room ? `${game.scope.slice(0, room - 1).replace(/[\s,;—-]+\S*$/, '')}…` : game.scope;
  return `${lead} ${scope}`;
}
