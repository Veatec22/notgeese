// Server side of a game request: store lookup, rate limit, insert. The database
// and fetch are injected so tests run without network or Supabase.
import { COMMENT_MAX, parseTarget, type Target, TargetError } from './game-request.ts';

/** Per hashed IP per UTC day, and for everyone per UTC day. */
export const LIMIT_PER_IP = 5;
export const LIMIT_PER_DAY = 500;
const TIMEOUT_MS = 5000;

export type Lookup =
  | { status: 'found'; title: string; polish: boolean }
  | { status: 'missing' }
  | { status: 'unknown' };

export interface RequestRow {
  game_key: string;
  store: 'steam' | 'gog' | null;
  title: string;
  url: string | null;
  comment: string | null;
  polish: boolean | null;
  ip_hash: string;
}

export interface RequestStore {
  /** Rows since `since`, only for `ipHash` when given. */
  count(since: string, ipHash?: string): Promise<number>;
  insert(row: RequestRow): Promise<void>;
}

export interface Deps {
  store: RequestStore;
  fetch: typeof fetch;
  /** HMAC key for the IP hash; never stored. */
  secret: string;
  now?: Date;
}

export interface Reply {
  status: number;
  body: Record<string, unknown>;
}

async function getJson(fetcher: typeof fetch, url: string): Promise<unknown> {
  const response = await fetcher(url, { signal: AbortSignal.timeout(TIMEOUT_MS), headers: { 'User-Agent': 'notgeese-requests' } });
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  return response.json();
}

/** Steam store API: name and whether Polish is among supported languages. */
export async function lookupSteam(id: string, fetcher: typeof fetch): Promise<Lookup> {
  try {
    const data = await getJson(fetcher, `https://store.steampowered.com/api/appdetails?appids=${id}&l=english&filters=basic`) as
      Record<string, { success?: boolean; data?: { name?: string; supported_languages?: string } }>;
    const app = data?.[id];
    if (app?.success === false) return { status: 'missing' };
    if (!app?.data?.name) return { status: 'unknown' };
    return { status: 'found', title: app.data.name, polish: /\bPolish\b/.test(app.data.supported_languages ?? '') };
  } catch {
    return { status: 'unknown' };
  }
}

/** GOG: product id from the store page, then name and languages from the products API. */
export async function lookupGog(slug: string, fetcher: typeof fetch): Promise<Lookup> {
  try {
    const page = await fetcher(`https://www.gog.com/en/game/${slug}`, { signal: AbortSignal.timeout(TIMEOUT_MS) });
    if (!page.ok) return page.status === 404 ? { status: 'missing' } : { status: 'unknown' };
    // An unknown slug redirects to the catalog with 200.
    if (page.url && !page.url.includes('/game/')) return { status: 'missing' };
    const id = /card-product="(\d+)"/.exec(await page.text())?.[1];
    if (!id) return { status: 'unknown' };
    const product = await getJson(fetcher, `https://api.gog.com/products/${id}`) as { title?: string; languages?: Record<string, string> };
    if (!product?.title) return { status: 'unknown' };
    return { status: 'found', title: product.title, polish: Boolean(product.languages && 'pl' in product.languages) };
  } catch {
    return { status: 'unknown' };
  }
}

/** Hex HMAC of IP and UTC day: counts a day's requests from one address, links nothing across days. */
export async function ipHash(secret: string, ip: string, day: string): Promise<string> {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signature = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`${day}|${ip}`));
  return [...new Uint8Array(signature)].slice(0, 16).map((b) => b.toString(16).padStart(2, '0')).join('');
}

function fail(status: number, error: string, message: string): Reply {
  return { status, body: { error, message } };
}

function fallbackTitle(target: Target): string {
  if (target.store === 'steam') return `Steam ${target.id}`;
  if (target.store === 'gog') return target.id.replace(/_/g, ' ');
  return target.title;
}

/** Body `{target, comment?, website?}`; `website` is a honeypot real players never fill. */
export async function submitRequest(body: Record<string, unknown>, ip: string, deps: Deps): Promise<Reply> {
  if (typeof body.website === 'string' && body.website !== '') return { status: 200, body: { ok: true } };
  if (typeof body.target !== 'string') return fail(400, 'bad_request', 'Wpisz tytuł gry albo wklej link do Steam lub GOG.');
  const commentText = typeof body.comment === 'string' ? body.comment.trim() : '';
  if ([...commentText].length > COMMENT_MAX) return fail(400, 'bad_request', `Komentarz może mieć najwyżej ${COMMENT_MAX} znaków.`);

  let target: Target;
  try {
    target = parseTarget(body.target);
  } catch (error) {
    if (error instanceof TargetError) return fail(400, 'bad_request', error.message);
    throw error;
  }

  const now = deps.now ?? new Date();
  const day = now.toISOString().slice(0, 10);
  const since = `${day}T00:00:00Z`;
  const hash = await ipHash(deps.secret, ip, day);
  if (await deps.store.count(since, hash) >= LIMIT_PER_IP) {
    return fail(429, 'limit', 'Na dziś wystarczy zgłoszeń z tego adresu. Wróć jutro.');
  }
  if (await deps.store.count(since) >= LIMIT_PER_DAY) {
    return fail(429, 'limit', 'Dzienny limit zgłoszeń się wyczerpał. Spróbuj jutro.');
  }

  const lookup: Lookup = target.store === 'steam'
    ? await lookupSteam(target.id, deps.fetch)
    : target.store === 'gog'
    ? await lookupGog(target.id, deps.fetch)
    : { status: 'unknown' };
  if (lookup.status === 'missing') {
    return fail(404, 'not_found', `Nie znalazłem tej gry na ${target.store === 'steam' ? 'Steamie' : 'GOG-u'}. Sprawdź link.`);
  }

  const title = lookup.status === 'found' ? lookup.title : fallbackTitle(target);
  const polish = lookup.status === 'found' ? lookup.polish : null;
  await deps.store.insert({
    game_key: target.key,
    store: target.store,
    title,
    url: target.store ? target.url : null,
    comment: commentText || null,
    polish,
    ip_hash: hash,
  });
  return { status: 200, body: { ok: true, title, polish } };
}
