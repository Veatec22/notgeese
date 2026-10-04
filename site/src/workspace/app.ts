// Workspace /admin/ (docs/workspace.md).
// The view is rendered from text templates with event delegation, like the prototype
// whose layout the user approved; the code is new and state comes from the server.
import {
  buildExport,
  type GameView,
  refId,
  UNSORTED_GROUP,
  type WorkRow,
  type WorkState,
} from '../../../supabase/functions/_shared/workspace/mod.ts';
import { Api, ApiError, type JournalRow, NetworkError, SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from './api.ts';
import { DraftStore, preference, setPreference } from './drafts.ts';
import { type Draft, GameModel, STATE_LABELS } from './model.ts';
import { icon } from './icons.ts';

interface GameMeta {
  slug: string;
  title: string;
  version: string;
  entries: number;
}

type Mode = 'A' | 'B' | 'C';
const MODES: Record<Mode, string> = { A: 'EN i PL obok siebie', B: 'Czytanie rozmowy', C: 'Jedna kwestia' };
const PAGE_SIZES = [50, 100, 200] as const;
const MISSING_SCOPE = '_missing';
const ALL_SCOPE = '_all';
const STATES: WorkState[] = ['review', 'accepted', 'pending', 'conflict'];

const root = document.getElementById('workspace')!;
const dialog = document.getElementById('ws-dialog') as HTMLDialogElement;
const toastBox = document.getElementById('ws-toast')!;
const games = JSON.parse(document.getElementById('ws-games')!.textContent!) as GameMeta[];

const api = SUPABASE_PUBLISHABLE_KEY ? new Api() : null;
let store: DraftStore | null = null;
let email = '';
let opened = new Map<string, string>();
let model: GameModel | null = null;
let gameMeta: GameMeta | null = null;

let scope = '';
let query = '';
let stateFilter: WorkState | '' = '';
let onlyDrafts = false;
let page = 0;
let focusId: string | null = null;
let pageSize = preference('page-size', PAGE_SIZES, 50);
let mode = preference<Mode>('mode', ['A', 'B', 'C'], 'A');
let onlyPl = preference('only-pl', ['1', '0'], '0') === '1';
let gameLayout = preference('game-layout', ['grid', 'list'], 'grid');
let gameQuery = '';
let gameVersionFilter = 'all';
let busy = false;
let pendingSave: { requestId: string; fingerprint: string } | null = null;
let toastTimer: number | undefined;

// --- pomocnicze -----------------------------------------------------------------------

function esc(value: unknown = ''): string {
  return String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
}

function toast(message: string) {
  window.clearTimeout(toastTimer);
  toastBox.textContent = message;
  toastTimer = window.setTimeout(() => (toastBox.textContent = ''), 7000);
}

function notice(message: string, tone: 'info' | 'warn' = 'info') {
  return `<div class="ws-callout" data-tone="${tone}"><p>${esc(message)}</p></div>`;
}

function modal(title: string, body: string, actions = '') {
  dialog.innerHTML = `<h2 id="ws-dialog-title">${esc(title)}</h2>${body}<div class="ws-actions">${actions}<button type="button" data-action="close">${icon('close')} Zamknij</button></div>`;
  if (!dialog.open) dialog.showModal();
}

function labelOf(id: string): string {
  const [namespace, key] = JSON.parse(id) as [string, string];
  return namespace ? `${namespace} / ${key}` : key;
}

function shortSha(sha: string) {
  return sha.slice(0, 7);
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('pl-PL', { dateStyle: 'medium', timeStyle: 'short' });
}

function flag(language: 'en' | 'pl') {
  const label = language === 'en' ? 'Oryginał angielski' : 'Polskie tłumaczenie';
  const shapes = language === 'en'
    ? '<path fill="#012169" d="M0 0h60v30H0z"/><path stroke="#fff" stroke-width="6" d="m0 0 60 30M60 0 0 30"/><path stroke="#c8102e" stroke-width="2" d="m0 0 60 30M60 0 0 30"/><path stroke="#fff" stroke-width="10" d="M30 0v30M0 15h60"/><path stroke="#c8102e" stroke-width="6" d="M30 0v30M0 15h60"/>'
    : '<path fill="#fff" d="M0 0h60v30H0z"/><path fill="#dc143c" d="M0 15h60v15H0z"/>';
  return `<svg class="ws-flag" viewBox="0 0 60 30" role="img" aria-label="${label}"><title>${label}</title>${shapes}</svg>`;
}

function stateBadge(state: WorkState, count?: number) {
  return `<span class="ws-status" data-state="${state}">${icon(state === 'accepted' ? 'check' : state === 'review' ? 'search' : state)} ${STATE_LABELS[state]}${count === undefined ? '' : ` <b>${count}</b>`}</span>`;
}

function persistDrafts() {
  if (!store || !model || !gameMeta) return;
  store.save(gameMeta.slug, model.drafts);
  if (!store.working) toast('Nie udało się utrwalić szkiców w przeglądarce. Są tylko w pamięci tej karty.');
}

function setUrl(slug: string | null) {
  const url = new URL(location.href);
  if (slug) url.searchParams.set('gra', slug);
  else url.searchParams.delete('gra');
  history.pushState({}, '', url);
}

// --- screens without a game -----------------------------------------------------------

function renderMessage(title: string, body: string) {
  root.className = '';
  root.innerHTML = `<div class="ws-narrow"><h1>${esc(title)}</h1>${body}</div>`;
}

function renderConfigMissing() {
  renderMessage(
    'Pracownia nie jest skonfigurowana',
    '<p>Brak klucza publishable Supabase w buildzie strony (<code>PUBLIC_SUPABASE_PUBLISHABLE_KEY</code>). Szczegóły w <code>supabase/README.md</code>.</p>',
  );
}

function renderLogin(message = '') {
  renderMessage(
    'Zaloguj się',
    `<p class="ws-muted">Pracownia jest prywatna. Link do logowania przyjdzie na e-mail administratora.</p>
    ${message}
    <form class="ws-login" data-form="login">
      <label for="ws-email">Adres e-mail</label>
      <input id="ws-email" name="email" type="email" autocomplete="email" required />
      <button class="ws-primary" type="submit">Wyślij link</button>
    </form>`,
  );
}

function renderForbidden() {
  renderMessage(
    'Brak dostępu',
    `<p>Konto <b>${esc(email)}</b> nie ma dostępu do pracowni.</p><button type="button" data-action="sign-out">${icon('logout')} Wyloguj</button>`,
  );
}

function renderList() {
  const counts = store?.counts() ?? new Map<string, number>();
  root.className = '';
  root.innerHTML = `<div class="ws-top"><div><h1>Pracownia</h1></div>
    <div class="ws-actions"><span class="ws-muted">${esc(email)}</span><button type="button" data-action="sign-out">${icon('logout')} Wyloguj</button></div></div>
    ${store && !store.working ? notice('Przeglądarka nie pozwala zapisać szkiców. Będą tylko w pamięci karty.', 'warn') : ''}
    <div class="ws-game-controls"><label class="ws-game-search">${icon('search')}<span class="ng-visually-hidden">Szukaj gry</span>
      <input id="ws-game-search" type="search" placeholder="Szukaj gry…" value="${esc(gameQuery)}"></label>
      <label><span class="ng-visually-hidden">Filtr wersji</span><select id="ws-game-version">
        ${[['all', 'Wszystkie wersje'], ['1', 'Gotowe (1.x)'], ['0', 'Robocze (0.x)']].map(([value, label]) => `<option value="${value}" ${gameVersionFilter === value ? 'selected' : ''}>${label}</option>`).join('')}
      </select></label>
      <span id="ws-game-count" class="ws-muted" role="status"></span>
      <div class="ws-actions" role="group" aria-label="Układ gier">
        <button type="button" data-action="game-layout" data-layout="grid" aria-pressed="${gameLayout === 'grid'}">${icon('grid')} Kafelki</button>
        <button type="button" data-action="game-layout" data-layout="list" aria-pressed="${gameLayout === 'list'}">${icon('list')} Lista</button>
      </div></div>
    <div class="ws-game-list" data-layout="${gameLayout}">${
    games.map((game) => {
      const drafts = counts.get(game.slug) ?? 0;
      const last = opened.get(game.slug);
      const majorVersion = game.version.split('.')[0];
      return `<a class="ws-game ng-card" href="?gra=${encodeURIComponent(game.slug)}" data-action="open" data-game="${esc(game.slug)}" data-version-major="${esc(majorVersion)}"><div class="ws-overline">${esc(game.version)} · ${game.entries} wpisów${majorVersion === '1' ? ' · gotowe' : ''}</div>
        <div class="ws-game-heading"><img class="ws-game-icon" src="${esc(SUPABASE_URL)}/storage/v1/object/public/game-icons/${encodeURIComponent(game.slug)}.png?v=3" width="48" height="48" alt="" loading="lazy" decoding="async"><h2>${esc(game.title)}</h2></div>
        ${drafts ? `<span class="ws-draft-badge">Niezapisane szkice: ${drafts}</span>` : ''}
        <p class="ws-muted">${last ? `Ostatnio otwarta ${esc(formatDate(last))}` : 'Jeszcze nie otwierana'}</p></a>`;
    }).join('')
  }</div><p class="ws-empty" id="ws-game-empty" hidden>Brak gier pasujących do wyszukiwania.</p>`;
  filterGames();
}

function filterGames() {
  const search = gameQuery.trim().toLocaleLowerCase('pl');
  let count = 0;
  for (const card of root.querySelectorAll<HTMLElement>('.ws-game')) {
    const title = card.querySelector('h2')?.textContent ?? '';
    card.hidden = !`${title} ${card.dataset.game}`.toLocaleLowerCase('pl').includes(search) ||
      (gameVersionFilter !== 'all' && card.dataset.versionMajor !== gameVersionFilter);
    if (!card.hidden) count++;
  }
  const summary = root.querySelector('#ws-game-count');
  if (summary) summary.textContent = `${count} z ${games.length} gier`;
  const empty = root.querySelector<HTMLElement>('#ws-game-empty');
  if (empty) empty.hidden = count > 0;
}

function renderLoading(title: string) {
  root.innerHTML = `<div class="ws-narrow"><button class="ws-link" type="button" data-action="home">${icon('back')} Wszystkie gry</button><h1>${esc(title)}</h1>
    <p class="ws-muted" role="status">Pobieranie tekstów z main i rozliczanie wyniku pracy…</p></div>`;
}

function renderGameError(title: string, error: unknown) {
  let body = `<p>${esc(error instanceof Error ? error.message : String(error))}</p>`;
  if (error instanceof ApiError && error.body.error === 'format') {
    body = `<p>Plik <code>${esc(error.body.file)}</code> na main nie jest zgodny z formatem pracowni. Gra nie została wczytana częściowo.</p>
      <ul>${(error.body.issues ?? []).slice(0, 30).map((issue) => `<li>${esc(issue)}</li>`).join('')}</ul>`;
  } else if (error instanceof ApiError && error.body.error === 'github' && error.body.retry_at) {
    body += `<p>Spróbuj po ${esc(formatDate(error.body.retry_at))}.</p>`;
  }
  root.innerHTML = `<div class="ws-narrow"><button class="ws-link" type="button" data-action="home">${icon('back')} Wszystkie gry</button><h1>${esc(title)}</h1>
    ${body}<button type="button" data-action="retry-open">Spróbuj ponownie</button></div>`;
}

// --- game view ------------------------------------------------------------------------

function scopeName(): string {
  if (!model) return '';
  if (scope === ALL_SCOPE) return 'Wszystkie';
  if (scope === MISSING_SCOPE) return 'Brak na main';
  const sequence = model.view.layout.sequences.find((s) => `seq:${s.id}` === scope);
  if (sequence) return sequence.name;
  return model.view.layout.groups.find((g) => g.id === scope)?.name ?? '';
}

function scopeItems() {
  if (scope === ALL_SCOPE && model) return [...model.entries.keys()].map((id) => ({ id }));
  return model ? model.itemsOf(scope) : [];
}

function matches(id: string): boolean {
  const m = model!;
  if (onlyDrafts && !m.drafts.has(id)) return false;
  if (stateFilter && m.shownState(id) !== stateFilter) return false;
  if (!query) return true;
  const entry = m.entries.get(id)!;
  const q = query.toLocaleLowerCase('pl');
  return `${labelOf(id)} ${entry.english} ${m.text(id)}`.toLocaleLowerCase('pl').includes(q);
}

function pageItems() {
  const items = scopeItems().filter((item) => matches(item.id));
  const size = mode === 'C' ? 1 : pageSize;
  const pages = Math.max(1, Math.ceil(items.length / size));
  if (focusId) {
    const index = items.findIndex((item) => item.id === focusId);
    if (index >= 0) page = Math.floor(index / size);
  }
  page = Math.max(0, Math.min(page, pages - 1));
  return { items, size, visible: items.slice(page * size, page * size + size) };
}

function draftBadge(draft: Draft | undefined) {
  if (!draft || !model) return '';
  if (model.isStale(draft)) return '<span class="ws-draft-badge" data-stale="true">Nieaktualny szkic</span>';
  return `<span class="ws-draft-badge">${icon('draft')} ${draft.confirmed ? 'Niezapisane' : 'Szkic'}</span>`;
}

function compare(left: [string, string], right: [string, string], extra?: [string, string]) {
  const cell = ([label, text]: [string, string]) => `<div><small>${esc(label)}</small><p>${esc(text)}</p></div>`;
  return `<div class="ws-compare">${cell(left)}${cell(right)}${extra ? cell(extra) : ''}</div>`;
}

function callout(id: string): string {
  const m = model!;
  const entry = m.entries.get(id)!;
  const draft = m.drafts.get(id);
  const row = m.work.get(id);
  if (draft && m.isStale(draft)) {
    return `<div class="ws-callout" data-tone="warn"><h3>Nieaktualny szkic</h3><p>Tekst na main zmienił się od powstania szkicu. Zapis gry jest zablokowany do decyzji.</p>
      ${compare(['Baza szkicu', draft.base?.polish ?? ''], ['Teraz na main', entry.polish], ['Twój szkic', draft.after ?? draft.base?.polish ?? ''])}
      <div class="ws-actions"><button type="button" data-action="rebase" data-id="${esc(id)}">Zachowaj na nowej bazie</button><button type="button" data-action="discard" data-id="${esc(id)}">${icon('undo')} Porzuć szkic</button></div></div>`;
  }
  if (row?.state === 'conflict' && !draft) {
    return `<div class="ws-callout" data-tone="warn"><h3>Konflikt</h3><p>${
      row.english !== entry.english ? 'Na main zmienił się tekst angielski.' : 'Na main jest inne brzmienie niż przed i po korekcie.'
    }</p>
      ${compare(['Przed korektą', row.before ?? ''], ['Twoja korekta', row.after], ['Teraz na main', entry.polish])}
      <div class="ws-actions"><button type="button" data-action="accept" data-id="${esc(id)}">${icon('check')} Przyjmij main</button><button type="button" data-action="keep-own" data-id="${esc(id)}">${icon('draft')} Zostań przy swoim</button></div></div>`;
  }
  if (row?.action === 'accept' && row.state === 'review' && !draft) {
    return `<div class="ws-callout"><h3>Zaakceptowany tekst zmienił się na main</h3>
      ${compare(['Zaakceptowane wcześniej', row.after], ['Teraz na main', entry.polish])}
      ${row.english !== entry.english ? compare(['EN wcześniej', row.english], ['EN teraz', entry.english]) : ''}</div>`;
  }
  return '';
}

function entryActions(id: string): string {
  const m = model!;
  const draft = m.drafts.get(id);
  if (draft && m.isStale(draft)) return '';
  const state = m.shownState(id);
  if (state === 'conflict' && !draft) return '';
  const editing = draft?.confirmed === false;
  const settled = state === 'accepted' || state === 'pending';
  return `${editing || !settled ? `<button type="button" data-action="approve" data-id="${esc(id)}">${icon('check')} Akceptuj</button>` : ''}
    ${draft || settled ? `<button type="button" data-action="undo" data-id="${esc(id)}">${icon('undo')} Cofnij</button>` : ''}`;
}

function entryCard(item: { id: string; speaker?: string }, index: number): string {
  const m = model!;
  const { id } = item;
  const entry = m.entries.get(id)!;
  const draft = m.drafts.get(id);
  const row = m.work.get(id);
  const state = m.shownState(id);
  const stale = draft ? m.isStale(draft) : false;
  const text = m.text(id);
  const speaker = item.speaker ? m.view.speakers[item.speaker] ?? item.speaker : undefined;
  const occurrences = m.occurrences.get(id) ?? 0;
  const conflict = row?.state === 'conflict' && !draft;
  const field = `ws-entry-${page}-${index}`;
  return `<article class="ws-entry" data-id="${esc(id)}">
    <div class="ws-meta"><div><h3 class="ws-key">${esc(labelOf(id))}</h3>
      ${item.speaker !== undefined || scope.startsWith('seq:') ? `<span class="ws-speaker">${esc(speaker ?? 'Mówca nieustalony')}</span>` : ''}</div>
      <span class="ws-badges">${stateBadge(state)}${draftBadge(draft)}</span></div>
    ${callout(id)}
    <div class="ws-pair"><div class="ws-source"><div class="ws-language">${flag('en')}</div><div class="ws-en">${esc(entry.english)}</div></div>
      <div><label class="ws-language" for="${field}">${flag('pl')}<span class="ng-visually-hidden">Polskie tłumaczenie — ${esc(labelOf(id))}</span></label>
      <textarea id="${field}" data-edit="${esc(id)}" ${stale || conflict || busy ? 'disabled' : ''}>${esc(text)}</textarea>
      ${entry.max_length ? `<small class="ws-muted" data-length="${esc(id)}">${[...text].length}/${entry.max_length}</small>` : ''}</div></div>
    ${entry.context ? `<p class="ws-muted">${esc(entry.context)}</p>` : ''}
    ${entry.note ? `<p class="ws-muted"><b>Uwaga tłumacza:</b> ${esc(entry.note)}</p>` : ''}
    ${occurrences > 1 ? `<p class="ws-muted">Ten wpis występuje w sekwencjach ${occurrences} razy — poprawka obejmie wszystkie wystąpienia.</p>` : ''}
    <div class="ws-actions" data-entry-actions>${entryActions(id)}</div></article>`;
}

function missingCard(row: WorkRow): string {
  const id = refId(row);
  const draft = model!.drafts.get(id);
  return `<article class="ws-entry" data-id="${esc(id)}">
    <div class="ws-meta"><div><h3 class="ws-key">${esc(labelOf(id))}</h3></div>
      <span class="ws-badges">${stateBadge(row.state)}${draft ? '<span class="ws-draft-badge">Do usunięcia</span>' : ''}</span></div>
    <p class="ws-muted">Tego wpisu nie ma na main. Wynik pracy czeka na ręczne usunięcie; nie trafia do eksportu.</p>
    ${row.action === 'correct'
      ? compare(['EN', row.english], ['Przed korektą', row.before ?? ''], ['Twoja korekta', row.after])
      : compare(['EN', row.english], ['Zaakceptowane', row.after])}
    <div class="ws-actions">${draft
      ? `<button type="button" data-action="discard" data-id="${esc(id)}">${icon('undo')} Porzuć szkic</button>`
      : `<button type="button" data-action="forget" data-id="${esc(id)}">Usuń wynik pracy</button>`}</div></article>`;
}

function stats() {
  const counts = model!.counts();
  return `<div class="ws-stats">${
    (['accepted', 'pending', 'review', 'conflict'] as const).map((state) => stateBadge(state, counts[state])).join('')
  }<span class="ws-draft-badge">${icon('draft')} Szkice <b>${model!.drafts.size}</b></span></div>`;
}

function stateDropdown() {
  return `<details class="ws-filter"><summary aria-label="Filtr stanu">${stateFilter ? stateBadge(stateFilter) : `${icon('filter')} Wszystkie stany`} ▾</summary>
    <div class="ws-filter-options"><button type="button" data-action="filter" data-state="">Wszystkie stany</button>${
    STATES.map((state) => `<button type="button" data-action="filter" data-state="${state}" aria-pressed="${stateFilter === state}">${stateBadge(state)}</button>`).join('')
  }</div></details>`;
}

function scopeCounts(ids: string[]): string {
  const counts: Record<WorkState, number> = { accepted: 0, pending: 0, review: 0, conflict: 0 };
  for (const id of ids) counts[model!.shownState(id)]++;
  return `<span class="ws-scope-counts">${(['accepted', 'pending', 'review', 'conflict'] as const)
    .filter((state) => state !== 'conflict' || counts.conflict > 0)
    .map((state) => `<span class="ws-count" data-state="${state}" title="${STATE_LABELS[state]}: ${counts[state]}" aria-label="${STATE_LABELS[state]}: ${counts[state]}">${icon(state === 'accepted' ? 'check' : state === 'review' ? 'search' : state)}${counts[state]}</span>`).join('')}</span>`;
}

function sidebar() {
  const m = model!;
  const groupButtons = m.view.layout.groups.map((group) =>
    `<button type="button" data-action="scope" data-scope="${esc(group.id)}" aria-current="${scope === group.id}"><span>${esc(group.name)}</span>${scopeCounts(group.entries.map(refId))}</button>`
  ).join('');
  const sequences = m.view.layout.sequences.map((sequence) =>
    `<button type="button" data-action="scope" data-scope="seq:${esc(sequence.id)}" aria-current="${scope === `seq:${sequence.id}`}"><span>${esc(sequence.name)}</span>${scopeCounts(sequence.lines.map(refId))}</button>`
  ).join('');
  return `<aside class="ws-sidebar"><button type="button" data-action="scope" data-scope="${ALL_SCOPE}" aria-current="${scope === ALL_SCOPE}"><span>${icon('all')} Wszystkie</span>${scopeCounts([...m.entries.keys()])}</button><h3>Grupy</h3>${groupButtons}
    ${sequences ? `<hr><h3>Sekwencje</h3>${sequences}` : ''}
    ${m.missing.size ? `<hr><button type="button" data-action="scope" data-scope="${MISSING_SCOPE}" aria-current="${scope === MISSING_SCOPE}"><span>Brak na main</span><small>${m.missing.size}</small></button>` : ''}
    <hr><button type="button" data-action="journal">${icon('journal')} Dziennik gry</button>
    <p class="ws-muted">Szkice tylko w tej przeglądarce${location.hostname === 'localhost' ? ' (localhost ma inne szkice niż notgeese.cc)' : ''}.</p>
    ${store && !store.working ? notice('Brak trwałego zapisu lokalnego.', 'warn') : ''}</aside>`;
}

function changesNotice() {
  const changes = model!.view.changes.filter((c) => c.kind === 'settle' || c.kind === 'missing' || c.kind === 'returned');
  if (!changes.length) return '';
  const kinds: Record<string, string> = { settle: 'zmiana stanu', missing: 'zniknął z main', returned: 'wrócił na main' };
  return `<details class="ws-callout"><summary>Zmiany od ostatniego rozliczenia: ${changes.length}</summary><ul>${
    changes.slice(0, 50).map((c) => {
      const detail = c.detail as { from?: WorkState; to?: WorkState };
      const states = detail.from && detail.to ? `: ${STATE_LABELS[detail.from]} → ${STATE_LABELS[detail.to]}` : '';
      return `<li>${esc(labelOf(refId({ namespace: c.namespace ?? '', key: c.key ?? '' })))} — ${kinds[c.kind]}${esc(states)}</li>`;
    }).join('')
  }</ul></details>`;
}

function fitTranslation(field: HTMLTextAreaElement) {
  field.style.height = 'auto';
  const border = field.offsetHeight - field.clientHeight;
  field.style.height = `${field.scrollHeight + border}px`;
}

function fitTranslations() {
  for (const field of root.querySelectorAll<HTMLTextAreaElement>('textarea[data-edit]')) {
    fitTranslation(field);
  }
}

function renderGame() {
  const m = model!;
  const game = gameMeta!;
  root.className = `ws-layout-${mode}${onlyPl ? ' ws-only-pl' : ''}`;
  const blockers = m.blockers();
  let content: string;
  let toolbar: string;
  if (scope === MISSING_SCOPE) {
    toolbar = `<div class="ws-toolbar"><h2>Brak na main</h2><p class="ws-muted">Wyniki pracy wpisów usuniętych z main.</p></div>`;
    content = [...m.missing.values()].map(missingCard).join('') || '<p class="ws-empty">Brak takich wpisów.</p>';
  } else {
    const { items, size, visible } = pageItems();
    const eligible = visible.filter((item) => m.shownState(item.id) === 'review' && !m.drafts.has(item.id));
    toolbar = `<div class="ws-toolbar"><div class="ws-top"><div><h2>${esc(scopeName())}</h2><p class="ws-muted">Widoczne: ${items.length} z ${scopeItems().length}</p></div>
      <label>Tryb redakcji <select id="ws-mode">${Object.entries(MODES).map(([id, name]) => `<option value="${id}" ${id === mode ? 'selected' : ''}>${name}</option>`).join('')}</select></label>
      <button type="button" data-action="only-pl" aria-pressed="${onlyPl}">${icon('languages')} ${onlyPl ? 'Pokaż EN i PL' : 'Czytaj tylko PL'}</button></div>
      ${scope.startsWith('seq:') ? sequenceNotice() : ''}
      <div class="ws-actions"><input id="ws-search" type="search" value="${esc(query)}" aria-label="Szukaj w grupie" placeholder="Szukaj: tekst lub klucz, Enter">${stateDropdown()}
        <button type="button" data-action="only-drafts" aria-pressed="${onlyDrafts}">${icon('draft')} Tylko szkice</button>
        <button type="button" data-action="search-game">${icon('search')} Szukaj w całej grze</button></div>
      <div class="ws-actions"><button type="button" data-action="accept-page" ${!eligible.length || busy ? 'disabled' : ''}>${icon('check')} Zaakceptuj na stronie (${eligible.length})</button>
        <small class="ws-muted">Tylko widoczne wpisy do przejrzenia, bez szkiców.</small></div></div>`;
    content = (visible.map(entryCard).join('') || '<p class="ws-empty">Brak wpisów w tym widoku.</p>') +
      `<div class="ws-pagination"><label>Wpisów na stronie <select id="ws-page-size" ${mode === 'C' ? 'disabled' : ''}>${
        PAGE_SIZES.map((n) => `<option ${n === pageSize ? 'selected' : ''}>${n}</option>`).join('')
      }</select></label>
      <button type="button" data-action="page" data-delta="-1" ${page === 0 ? 'disabled' : ''}>${icon('back')} Poprzednie</button>
      <span class="ws-muted">${items.length ? page * size + 1 : 0}–${Math.min((page + 1) * size, items.length)} / ${items.length}</span>
      <button type="button" data-action="page" data-delta="1" ${(page + 1) * size >= items.length ? 'disabled' : ''}>${icon('next')} Następne</button></div>`;
  }
  root.innerHTML = `<div class="ws-top"><div><button class="ws-link" type="button" data-action="home">${icon('back')} Wszystkie gry</button><h1>${esc(game.title)}</h1>
      <p class="ws-muted">${m.view.entries.length} wpisów · main <code>${shortSha(m.view.main_sha)}</code> · rewizja ${m.view.revision}</p></div>
      <div class="ws-actions"><button type="button" data-action="refresh" ${busy ? 'disabled' : ''}>${icon('refresh')} Odśwież</button>
      <button class="ws-primary" type="button" data-action="save" ${busy || !m.drafts.size ? 'disabled' : ''}>${icon('save')} Zapisz zmiany (${m.drafts.size})</button>
      <button type="button" data-action="discard-all" ${busy || !m.drafts.size ? 'disabled' : ''}>${icon('undo')} Cofnij wszystko</button>
      <button type="button" data-action="export">${icon('download')} Eksportuj korekty</button></div></div>
    ${busy ? notice('Trwa zapis…') : ''}
    ${blockers.stale ? notice(`Nieaktualne szkice blokują zapis (${blockers.stale}). Zachowaj je na nowej bazie albo porzuć.`, 'warn') : ''}
    ${blockers.unconfirmed ? notice(`Edycje czekające na „Akceptuj” blokują zapis (${blockers.unconfirmed}).`, 'warn') : ''}
    ${changesNotice()}${stats()}
    <div class="ws-shell">${sidebar()}<section class="ws-content">${toolbar}<div>${content}</div></section></div>`;
  fitTranslations();
  if (focusId) {
    const target = root.querySelector(`[data-id="${CSS.escape(focusId)}"]`);
    target?.scrollIntoView({ block: 'center' });
    target?.querySelector('textarea')?.focus({ preventScroll: true });
    focusId = null;
  }
}

const CERTAINTY_LABEL = { certain: 'pewna', reconstructed: 'odtworzona' } as const;

function sequenceNotice() {
  const sequence = model!.view.layout.sequences.find((s) => `seq:${s.id}` === scope)!;
  const { order, speakers } = sequence;
  return notice(`Kolejność: ${CERTAINTY_LABEL[order.certainty]} (${order.source}). Mówcy: ${CERTAINTY_LABEL[speakers.certainty]} (${speakers.source}).`);
}

// --- akcje ----------------------------------------------------------------------------

function setView(view: GameView) {
  const drafts = model && gameMeta?.slug === view.game ? model.drafts : store!.load(view.game);
  model = new GameModel(view, drafts);
  const scopes = [ALL_SCOPE, ...view.layout.groups.map((g) => g.id), ...view.layout.sequences.map((s) => `seq:${s.id}`), MISSING_SCOPE];
  if (!scopes.includes(scope) || (scope === MISSING_SCOPE && !model.missing.size)) scope = view.layout.groups[0]?.id ?? UNSORTED_GROUP.id;
}

async function openGame(slug: string, push = true) {
  const game = games.find((g) => g.slug === slug);
  if (!game || !api) return renderList();
  if (push) setUrl(slug);
  if (gameMeta?.slug !== slug) {
    model = null;
    scope = '';
    query = '';
    stateFilter = '';
    onlyDrafts = false;
    page = 0;
  }
  gameMeta = game;
  renderLoading(game.title);
  try {
    setView(await api.open(slug));
    opened.set(slug, new Date().toISOString());
    renderGame();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return renderLogin(notice(error.message, 'warn'));
    renderGameError(game.title, error);
  }
}

async function refresh() {
  if (!api || !gameMeta || !model) return;
  busy = true;
  renderGame();
  try {
    setView(await api.open(gameMeta.slug));
    const changes = model.view.changes.length;
    toast(changes ? `Odświeżono. Zmiany w rozliczeniu: ${changes}.` : 'Odświeżono, bez zmian od ostatniego rozliczenia.');
  } catch (error) {
    toast(error instanceof Error ? error.message : 'Nie udało się odświeżyć gry.');
  } finally {
    busy = false;
    renderGame();
  }
}

function stage(id: string, draft: Omit<Draft, 'namespace' | 'key'>) {
  const [namespace, key] = JSON.parse(id) as [string, string];
  model!.drafts.set(id, { namespace, key, ...draft });
  persistDrafts();
}

async function save() {
  if (!api || !model || !gameMeta || busy) return;
  const blockers = model.blockers();
  if (blockers.stale) return toast('Najpierw rozstrzygnij nieaktualne szkice. Nic nie zostało zapisane.');
  if (blockers.unconfirmed) return toast('Najpierw zatwierdź poprawki przy wpisach albo porzuć szkice.');
  const actions = model.actions();
  if (!actions.length) return;
  const fingerprint = JSON.stringify([gameMeta.slug, model.view.revision, actions]);
  // A retry after a network error sends the same id, so the server will not double the save.
  if (pendingSave?.fingerprint !== fingerprint) pendingSave = { requestId: crypto.randomUUID(), fingerprint };
  const sent = new Map([...model.drafts].map(([id, draft]) => [id, JSON.stringify(draft)]));
  busy = true;
  renderGame();
  try {
    const view = await api.save({ game: gameMeta.slug, expected_revision: model.view.revision, request_id: pendingSave.requestId, actions });
    pendingSave = null;
    for (const [id, snapshot] of sent) if (JSON.stringify(model.drafts.get(id)) === snapshot) model.drafts.delete(id);
    persistDrafts();
    setView(view);
    toast(view.duplicate ? 'Ten zapis przeszedł już wcześniej. Stan gry jest aktualny.' : `Zapisano. Zmiany: ${sent.size}.`);
  } catch (error) {
    if (error instanceof NetworkError) {
      toast(`${error.message} Spróbuj ponownie — ponowienie nie zdubluje zmian.`);
    } else if (error instanceof ApiError && (error.body.error === 'stale' || error.body.error === 'revision')) {
      pendingSave = null;
      toast(`${error.message} Pobieram aktualny stan; szkice zostają.`);
      try {
        setView(await api.open(gameMeta.slug));
      } catch {
        // Message already shown; drafts untouched.
      }
    } else {
      pendingSave = null;
      toast(error instanceof Error ? error.message : 'Zapis nie powiódł się. Szkice zostały.');
    }
  } finally {
    busy = false;
    renderGame();
  }
}

const JOURNAL_KINDS: Record<string, string> = {
  accept: 'akceptacja',
  correct: 'korekta',
  unset: 'cofnięcie',
  forget: 'usunięcie wyniku pracy',
  settle: 'rozliczenie z main',
  missing: 'zniknął z main',
  returned: 'wrócił na main',
};

function journalLine(row: JournalRow) {
  const detail = row.detail as { from?: WorkState; to?: WorkState; after?: string };
  const states = detail.from && detail.to ? ` ${STATE_LABELS[detail.from]} → ${STATE_LABELS[detail.to]}` : '';
  const text = row.kind === 'correct' && typeof detail.after === 'string' ? ` „${detail.after}”` : '';
  const key = row.key !== null && row.key !== undefined ? labelOf(refId({ namespace: row.namespace ?? '', key: row.key })) : '';
  return `<li><small>${esc(formatDate(row.at))}</small> <b>${esc(key)}</b> ${esc(JOURNAL_KINDS[row.kind] ?? row.kind)}${esc(states)}${esc(text)}</li>`;
}

async function showJournal() {
  if (!api || !gameMeta) return;
  modal('Dziennik gry', '<p class="ws-muted" role="status">Wczytywanie…</p>');
  try {
    const rows = await api.journal(gameMeta.slug);
    modal('Dziennik gry', rows.length ? `<p class="ws-muted">Ostatnie wpisy: ${rows.length}. Szkice nie trafiają do dziennika.</p><ol class="ws-journal">${rows.map(journalLine).join('')}</ol>` : '<p>Brak zapisanych akcji.</p>');
  } catch (error) {
    modal('Dziennik gry', notice(error instanceof Error ? error.message : 'Nie udało się wczytać dziennika.', 'warn'));
  }
}

function exportPayload(comment: string) {
  const m = model!;
  return buildExport({
    game: gameMeta!.slug,
    mainSha: m.view.main_sha,
    exportedAt: new Date().toISOString(),
    comment,
    rows: [...m.work.values(), ...m.missing.values()],
    entries: m.view.entries,
  });
}

function showExport() {
  const preview = exportPayload('');
  const drafts = model!.drafts.size;
  const empty = !preview.corrections.length && !preview.conflicts.length;
  modal(
    `Eksport korekt · ${gameMeta!.title}`,
    `<p>Korekty do wdrożenia: ${preview.corrections.length}, według stanu z main <code>${shortSha(model!.view.main_sha)}</code>. Eksport obejmuje wyłącznie zapisany wynik pracy i niczego nie zmienia.</p>
    ${drafts ? notice(`Niezapisane szkice (${drafts}) nie trafią do eksportu. Zapisz zmiany, jeśli mają być uwzględnione.`, 'warn') : ''}
    ${preview.conflicts.length ? notice(`Wpisy w konflikcie (${preview.conflicts.length}) nie trafią do korekt; eksport wypisze je osobno.`, 'warn') : ''}
    <label for="ws-comment">Komentarz dla agenta</label>
    <textarea id="ws-comment" placeholder="Co agent powinien wiedzieć przy nanoszeniu korekt?"></textarea>
    <details><summary>Pokaż JSON</summary><pre>${esc(JSON.stringify(preview, null, 2))}</pre></details>`,
    `<button type="button" data-action="copy-export" ${empty ? 'disabled' : ''}>${icon('copy')} Kopiuj JSON</button>
    <button class="ws-primary" type="button" data-action="download" ${empty ? 'disabled' : ''}>${icon('download')} Pobierz JSON</button>`,
  );
}

function exportWithComment() {
  const comment = (document.getElementById('ws-comment') as HTMLTextAreaElement | null)?.value ?? '';
  const payload = exportPayload(comment);
  return { payload, text: `${JSON.stringify(payload, null, 2)}\n` };
}

async function copyExport() {
  try {
    await navigator.clipboard.writeText(exportWithComment().text);
    toast('Skopiowano eksport do schowka. Stan wpisów nie zmienił się.');
  } catch {
    toast('Przeglądarka nie pozwoliła skopiować. Użyj „Pobierz JSON”.');
  }
}

function download() {
  const { payload, text } = exportWithComment();
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `${payload.game}-korekty-${payload.exported_at.slice(0, 10)}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('Pobrano eksport. Stan wpisów nie zmienił się.');
}

function searchGame() {
  const m = model!;
  const q = query.toLocaleLowerCase('pl');
  if (!q) return toast('Wpisz szukany tekst w polu wyszukiwania.');
  const hits = [...m.entries.keys()].filter((id) => {
    const entry = m.entries.get(id)!;
    return `${labelOf(id)} ${entry.english} ${m.text(id)}`.toLocaleLowerCase('pl').includes(q);
  });
  modal(
    'Wyniki w całej grze',
    `<p>Trafienia dla „${esc(query)}”: ${hits.length}.</p><ul class="ws-hits">${
      hits.slice(0, 80).map((id) => `<li><button type="button" data-action="jump" data-id="${esc(id)}">${esc(labelOf(id))}</button> ${esc(m.text(id).slice(0, 100))}</li>`).join('')
    }</ul>${hits.length > 80 ? '<p class="ws-muted">Pokazano pierwsze 80 trafień — doprecyzuj wyszukiwanie.</p>' : ''}`,
  );
}

function handleEntryAction(action: string, id: string) {
  const m = model!;
  const entry = m.entries.get(id);
  const row = m.work.get(id);
  const draft = m.drafts.get(id);
  switch (action) {
    case 'approve': {
      if (!entry || (draft && m.isStale(draft))) return;
      const text = m.text(id);
      stage(id, { kind: text === entry.polish ? 'accept' : 'correct', base: m.base(id), after: text, confirmed: true });
      break;
    }
    case 'accept':
      if (!entry) return;
      stage(id, { kind: 'accept', base: m.base(id), after: entry.polish, confirmed: true });
      break;
    case 'undo':
      if (!entry) return;
      if ((draft && (!draft.confirmed || draft.kind === 'unset')) || !row) {
        m.drafts.delete(id);
        persistDrafts();
      } else {
        stage(id, { kind: 'unset', base: m.base(id), after: entry.polish, confirmed: true });
      }
      break;
    case 'keep-own':
      if (!entry || !row) return;
      stage(id, { kind: 'correct', base: m.base(id), after: row.after, confirmed: true });
      break;
    case 'rebase':
      if (!entry || !draft) return;
      // The user saw both texts; an acceptance draft never moves to the new wording by itself.
      stage(id, { ...draft, base: m.base(id), after: draft.kind === 'accept' ? entry.polish : draft.after, confirmed: draft.kind !== 'correct' || draft.confirmed });
      break;
    case 'discard':
      m.drafts.delete(id);
      persistDrafts();
      break;
    case 'forget':
      stage(id, { kind: 'forget', base: null, confirmed: true });
      break;
    default:
      return;
  }
  renderGame();
}

async function handleClick(event: Event) {
  const button = (event.target as HTMLElement).closest<HTMLButtonElement | HTMLAnchorElement>('button[data-action], a[data-action]');
  if (!button || (button instanceof HTMLButtonElement && button.disabled)) return;
  if (button instanceof HTMLAnchorElement) {
    if (event instanceof MouseEvent && (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0)) return;
    event.preventDefault();
  }
  const { action, id } = button.dataset;
  switch (action) {
    case 'game-layout':
      gameLayout = button.dataset.layout === 'list' ? 'list' : 'grid';
      setPreference('game-layout', gameLayout);
      return renderList();
    case 'close':
      return dialog.close();
    case 'sign-out':
      await api?.signOut();
      store = null;
      model = null;
      gameMeta = null;
      setUrl(null);
      return renderLogin();
    case 'open':
      return openGame(button.dataset.game!);
    case 'restart':
      store = null;
      return start();
    case 'retry-open':
      return gameMeta && openGame(gameMeta.slug, false);
    case 'home':
      setUrl(null);
      gameMeta = null;
      model = null;
      root.className = '';
      return renderList();
  }
  if (!model) return;
  switch (action) {
    case 'scope':
      scope = button.dataset.scope!;
      page = 0;
      query = '';
      return renderGame();
    case 'only-drafts':
      onlyDrafts = !onlyDrafts;
      page = 0;
      return renderGame();
    case 'filter':
      stateFilter = (button.dataset.state ?? '') as WorkState | '';
      page = 0;
      return renderGame();
    case 'page':
      page += Number(button.dataset.delta);
      renderGame();
      return root.querySelector('.ws-content')?.scrollIntoView({ block: 'start' });
    case 'only-pl':
      onlyPl = !onlyPl;
      setPreference('only-pl', onlyPl ? '1' : '0');
      return renderGame();
    case 'accept-page': {
      const { visible } = pageItems();
      const eligible = visible.filter((item) => model!.shownState(item.id) === 'review' && !model!.drafts.has(item.id));
      for (const item of eligible) {
        stage(item.id, { kind: 'accept', base: model.base(item.id), after: model.entries.get(item.id)!.polish, confirmed: true });
      }
      toast(`Akceptacje na tej stronie: ${eligible.length}. Zapisz zmiany, aby je utrwalić.`);
      return renderGame();
    }
    case 'discard-all':
      return modal(
        'Cofnąć wszystkie niezapisane zmiany?',
        `<p>Szkice do porzucenia: ${model.drafts.size}. Zapisane akceptacje i korekty zostają bez zmian.</p>`,
        `<button class="ws-primary" type="button" data-action="discard-all-confirm">${icon('undo')} Cofnij wszystko</button>`,
      );
    case 'discard-all-confirm':
      model.drafts.clear();
      persistDrafts();
      dialog.close();
      toast('Cofnięto niezapisane zmiany w tej grze.');
      return renderGame();
    case 'save':
      return save();
    case 'refresh':
      return refresh();
    case 'journal':
      return showJournal();
    case 'export':
      return showExport();
    case 'download':
      return download();
    case 'copy-export':
      return copyExport();
    case 'search-game':
      query = (document.getElementById('ws-search') as HTMLInputElement | null)?.value ?? query;
      return searchGame();
    case 'jump':
      scope = model.scopeOf(id!);
      query = '';
      stateFilter = '';
      onlyDrafts = false;
      focusId = id!;
      dialog.close();
      return renderGame();
  }
  if (id) handleEntryAction(action!, id);
}

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement | HTMLInputElement;
  if (target.id === 'ws-game-search') {
    gameQuery = target.value;
    filterGames();
    return;
  }
  if (target.id === 'ws-search') {
    query = target.value;
    return;
  }
  const id = target.dataset.edit;
  if (!id || !model) return;
  const entry = model.entries.get(id)!;
  const row = model.work.get(id);
  const value = target.value;
  const savedText = row?.action === 'correct' ? row.after : entry.polish;
  const existing = model.drafts.get(id);
  if (value === savedText && (!existing || existing.kind === 'correct')) {
    model.drafts.delete(id);
  } else {
    stage(id, { kind: value === entry.polish ? 'accept' : 'correct', base: model.base(id), after: value, confirmed: false });
  }
  persistDrafts();
  // Update in place so the cursor is not lost; other occurrences of this entry too.
  for (const field of root.querySelectorAll<HTMLTextAreaElement>(`textarea[data-edit="${CSS.escape(id)}"]`)) {
    if (field !== target) field.value = value;
    fitTranslation(field);
  }
  for (const card of root.querySelectorAll<HTMLElement>(`article[data-id="${CSS.escape(id)}"]`)) {
    const badges = card.querySelector('.ws-badges');
    if (badges) badges.innerHTML = stateBadge(model.shownState(id)) + draftBadge(model.drafts.get(id));
    const actions = card.querySelector('[data-entry-actions]');
    if (actions) actions.innerHTML = entryActions(id);
    const length = card.querySelector('[data-length]');
    if (length && entry.max_length) length.textContent = `${[...value].length}/${entry.max_length}`;
  }
  const count = model.drafts.size;
  const saveButton = root.querySelector<HTMLButtonElement>('[data-action=save]');
  if (saveButton) {
    saveButton.innerHTML = `${icon('save')} Zapisz zmiany (${count})`;
    saveButton.disabled = !count;
  }
  const discardAll = root.querySelector<HTMLButtonElement>('[data-action=discard-all]');
  if (discardAll) discardAll.disabled = !count;
  const sidebarElement = root.querySelector('.ws-sidebar');
  if (sidebarElement) sidebarElement.outerHTML = sidebar();
  const statsElement = root.querySelector('.ws-stats');
  if (statsElement) statsElement.outerHTML = stats();
}

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  if (target.id === 'ws-game-version') {
    gameVersionFilter = target.value;
    filterGames();
    return;
  }
  if (target.id === 'ws-page-size') {
    pageSize = Number(target.value) as (typeof PAGE_SIZES)[number];
    setPreference('page-size', pageSize);
    page = 0;
    renderGame();
  } else if (target.id === 'ws-mode') {
    const firstVisible = pageItems().visible[0]?.id;
    mode = target.value as Mode;
    setPreference('mode', mode);
    if (firstVisible) {
      const items = scopeItems().filter((item) => matches(item.id));
      const index = items.findIndex((item) => item.id === firstVisible);
      page = Math.max(0, Math.floor(index / (mode === 'C' ? 1 : pageSize)));
    }
    renderGame();
  }
}

async function handleSubmit(event: SubmitEvent) {
  const form = event.target as HTMLFormElement;
  if (form.dataset.form !== 'login' || !api) return;
  event.preventDefault();
  const address = String(new FormData(form).get('email') ?? '').trim();
  const button = form.querySelector('button')!;
  button.disabled = true;
  try {
    await api.sendLink(address);
    renderMessage('Sprawdź skrzynkę', `<p>Jeśli <b>${esc(address)}</b> ma konto w pracowni, przyjdzie na nie link do logowania. Otwórz go w tej przeglądarce.</p>`);
  } catch (error) {
    renderLogin(notice(error instanceof Error ? error.message : 'Nie udało się wysłać linku.', 'warn'));
  }
}

// --- start ----------------------------------------------------------------------------

let starting: Promise<void> | null = null;

/** One start at a time: the login event from the link arrives while the page is starting. */
function start(): Promise<void> {
  starting ??= boot().finally(() => (starting = null));
  return starting;
}

async function boot() {
  if (!api) return renderConfigMissing();
  const session = await api.session();
  if (!session) return renderLogin();
  email = session.user.email ?? '';
  store = new DraftStore(session.user.id);
  try {
    if (!(await api.isAdmin())) return renderForbidden();
    opened = await api.openedGames();
  } catch (error) {
    return renderMessage('Nie udało się połączyć', `<p>${esc(error instanceof Error ? error.message : String(error))}</p><button type="button" data-action="restart">Spróbuj ponownie</button>`);
  }
  const slug = new URL(location.href).searchParams.get('gra');
  if (slug && games.some((g) => g.slug === slug)) return openGame(slug, false);
  renderList();
}

root.addEventListener('click', handleClick);
root.addEventListener('error', (event) => {
  const target = event.target;
  if (target instanceof HTMLImageElement && target.classList.contains('ws-game-icon')) target.hidden = true;
}, true);
dialog.addEventListener('click', handleClick);
root.addEventListener('input', handleInput);
root.addEventListener('change', handleChange);
root.addEventListener('submit', handleSubmit);
root.addEventListener('keydown', (event) => {
  const target = event.target as HTMLElement;
  if (target.id === 'ws-search' && event.key === 'Enter') {
    page = 0;
    renderGame();
    (document.getElementById('ws-search') as HTMLInputElement | null)?.focus();
  }
});
root.addEventListener('search', (event) => {
  if ((event.target as HTMLElement).id === 'ws-game-search') {
    handleInput(event);
    return;
  }
  if ((event.target as HTMLElement).id === 'ws-search' && !(event.target as HTMLInputElement).value) {
    query = '';
    page = 0;
    renderGame();
  }
});
window.addEventListener('popstate', () => {
  const slug = new URL(location.href).searchParams.get('gra');
  if (slug) openGame(slug, false);
  else {
    gameMeta = null;
    model = null;
    root.className = '';
    renderList();
  }
});
api?.client.auth.onAuthStateChange((event) => {
  if (event === 'SIGNED_IN' && !store) void start();
  if (event === 'SIGNED_OUT') {
    store = null;
    model = null;
  }
});

window.addEventListener('resize', fitTranslations);
void document.fonts.ready.then(fitTranslations);
void start();
