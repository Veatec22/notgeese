// Game request tests: parsing, store lookups and the submit flow with stubbed fetch and DB.
import { assert, assertEquals, assertThrows } from 'jsr:@std/assert@1';
import { normalizeTitle, parseTarget, TargetError } from '../_shared/game-request.ts';
import {
  LIMIT_PER_IP,
  lookupGog,
  lookupSteam,
  type RequestRow,
  type RequestStore,
  submitRequest,
} from '../_shared/game-request-server.ts';

Deno.test('parseTarget: Steam links reduce to the appid', () => {
  for (const link of [
    'https://store.steampowered.com/app/1978590/Anger_Foot/',
    'store.steampowered.com/app/1978590',
    'http://store.steampowered.com/app/01978590?l=polish',
    'https://steamcommunity.com/app/1978590',
  ]) {
    assertEquals(parseTarget(link), {
      store: 'steam',
      id: '1978590',
      key: 'steam:1978590',
      url: 'https://store.steampowered.com/app/1978590/',
    });
  }
});

Deno.test('parseTarget: GOG links reduce to the slug, with or without a locale', () => {
  for (const link of ['https://www.gog.com/en/game/anger_foot', 'https://www.gog.com/pl/game/Anger_Foot?x=1', 'gog.com/game/anger_foot']) {
    assertEquals(parseTarget(link).key, 'gog:anger_foot');
  }
});

Deno.test('parseTarget: titles dedupe on case, diacritics and punctuation', () => {
  assertEquals(parseTarget('  Hades II ').key, 'title:hadesii');
  assertEquals(parseTarget('hades: ii').key, 'title:hadesii');
  assertEquals(normalizeTitle('Pokémon'), 'pokemon');
  assertEquals(parseTarget('Hades II'), { store: null, key: 'title:hadesii', title: 'Hades II' });
});

Deno.test('parseTarget: other links, empty and too long input are refused', () => {
  for (const input of ['https://store.epicgames.com/p/hades', 'www.example.com', 'itch.io/game/x', '', '  ?! ', 'x'.repeat(121)]) {
    assertThrows(() => parseTarget(input), TargetError);
  }
});

function json(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), { ...init, headers: { 'Content-Type': 'application/json' } });
}

function stubFetch(routes: Record<string, () => Response>): typeof fetch {
  return ((input: string | URL | Request) => {
    const url = String(input instanceof Request ? input.url : input);
    const route = Object.entries(routes).find(([prefix]) => url.startsWith(prefix));
    return Promise.resolve(route ? route[1]() : new Response('not found', { status: 404 }));
  }) as typeof fetch;
}

const STEAM_API = 'https://store.steampowered.com/api/appdetails?appids=';

Deno.test('lookupSteam: name, Polish flag, missing app, failure', async () => {
  const fetcher = stubFetch({
    [`${STEAM_API}10&`]: () => json({ 10: { success: true, data: { name: 'Gra', supported_languages: 'English, Polish<strong>*</strong>' } } }),
    [`${STEAM_API}11&`]: () => json({ 11: { success: true, data: { name: 'Game', supported_languages: 'English' } } }),
    [`${STEAM_API}12&`]: () => json({ 12: { success: false } }),
    [`${STEAM_API}13&`]: () => new Response('busy', { status: 503 }),
  });
  assertEquals(await lookupSteam('10', fetcher), { status: 'found', title: 'Gra', polish: true });
  assertEquals(await lookupSteam('11', fetcher), { status: 'found', title: 'Game', polish: false });
  assertEquals(await lookupSteam('12', fetcher), { status: 'missing' });
  assertEquals(await lookupSteam('13', fetcher), { status: 'unknown' });
});

Deno.test('lookupGog: product id from the page, then title and languages', async () => {
  const fetcher = stubFetch({
    'https://www.gog.com/en/game/anger_foot': () => new Response('<div card-product="1983918143"></div>'),
    'https://api.gog.com/products/1983918143': () => json({ title: 'Anger Foot', languages: { en: 'English', pl: 'polski' } }),
  });
  assertEquals(await lookupGog('anger_foot', fetcher), { status: 'found', title: 'Anger Foot', polish: true });
  assertEquals(await lookupGog('nothing_here', fetcher), { status: 'missing' });
});

function memoryStore(rows: (RequestRow & { created_at: string })[] = []) {
  const store: RequestStore & { rows: typeof rows } = {
    rows,
    count: (since, ipHash) => Promise.resolve(rows.filter((row) => row.created_at >= since && (!ipHash || row.ip_hash === ipHash)).length),
    insert: (row) => {
      rows.push({ ...row, created_at: '2026-10-13T12:00:00Z' });
      return Promise.resolve();
    },
  };
  return store;
}

const now = new Date('2026-10-13T12:00:00Z');
const noFetch = stubFetch({});

Deno.test('submitRequest: Steam link stores the store title and the Polish flag', async () => {
  const store = memoryStore();
  const fetcher = stubFetch({ [`${STEAM_API}10&`]: () => json({ 10: { success: true, data: { name: 'Gra', supported_languages: 'Polish' } } }) });
  const reply = await submitRequest({ target: 'https://store.steampowered.com/app/10/', comment: '  bardzo proszę ' }, '1.2.3.4', {
    store,
    fetch: fetcher,
    secret: 's',
    now,
  });
  assertEquals(reply, { status: 200, body: { ok: true, title: 'Gra', polish: true } });
  assertEquals(store.rows.length, 1);
  const row = store.rows[0]!;
  assertEquals([row.game_key, row.store, row.url, row.comment, row.polish], ['steam:10', 'steam', 'https://store.steampowered.com/app/10/', 'bardzo proszę', true]);
  assert(/^[0-9a-f]{32}$/.test(row.ip_hash) && !row.ip_hash.includes('1.2.3.4'));
});

Deno.test('submitRequest: plain title, unknown store data, missing game', async () => {
  const store = memoryStore();
  const title = await submitRequest({ target: 'Hades II' }, 'ip', { store, fetch: noFetch, secret: 's', now });
  assertEquals(title.body, { ok: true, title: 'Hades II', polish: null });
  const gog = await submitRequest({ target: 'https://www.gog.com/en/game/some_game' }, 'ip', {
    store,
    fetch: stubFetch({ 'https://www.gog.com/': () => new Response('down', { status: 503 }) }),
    secret: 's',
    now,
  });
  assertEquals(gog.body, { ok: true, title: 'some game', polish: null });
  const missing = await submitRequest({ target: 'https://www.gog.com/en/game/nothing' }, 'ip', { store, fetch: noFetch, secret: 's', now });
  assertEquals(missing.status, 404);
  assertEquals(store.rows.length, 2);
});

Deno.test('submitRequest: honeypot, bad input and the per-IP daily limit', async () => {
  const store = memoryStore();
  const deps = { store, fetch: noFetch, secret: 's', now };
  assertEquals((await submitRequest({ target: 'Gra', website: 'spam' }, 'ip', deps)).body, { ok: true });
  assertEquals(store.rows.length, 0);
  assertEquals((await submitRequest({}, 'ip', deps)).status, 400);
  assertEquals((await submitRequest({ target: 'Gra', comment: 'x'.repeat(501) }, 'ip', deps)).status, 400);
  assertEquals((await submitRequest({ target: 'https://example.com/' }, 'ip', deps)).status, 400);

  for (let i = 0; i < LIMIT_PER_IP; i++) assertEquals((await submitRequest({ target: `Gra ${i}` }, 'ip', deps)).status, 200);
  assertEquals((await submitRequest({ target: 'Jeszcze jedna' }, 'ip', deps)).status, 429);
  assertEquals((await submitRequest({ target: 'Inny adres' }, 'other', deps)).status, 200);
  // Next UTC day: a new hash, a new limit.
  const tomorrow = { ...deps, now: new Date('2026-10-14T00:10:00Z') };
  assertEquals((await submitRequest({ target: 'Jutro' }, 'ip', tomorrow)).status, 200);
});
