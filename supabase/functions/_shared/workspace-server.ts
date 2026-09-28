// Server side of open, refresh and save. Rules live in the shared `workspace/`
// module; here: fetch the game from main, read the database, call the RPC.
import { parse as parseYaml } from 'jsr:@std/yaml@1';
import type { SupabaseContext } from 'npm:@supabase/server@1.8.0';
import { GitHubError, mainSha, readFile } from './github.ts';
import {
  type DraftAction,
  type Entry,
  FormatError,
  type GameView,
  type JournalItem,
  parseReview,
  planSave,
  resolveLayout,
  settle,
  speakersFromBible,
  type WorkRow,
} from './workspace/mod.ts';

type Client = SupabaseContext['supabase'];

export type { GameView };

const SLUG = /^[a-z0-9][a-z0-9-]{0,63}$/;
const PAGE = 1000;

export class RequestError extends Error {
  constructor(public readonly status: number, public readonly body: Record<string, unknown>) {
    super(String(body.error));
  }
}

function githubToken(): string | undefined {
  return Deno.env.get('NOTGEESE_GITHUB_TOKEN') || undefined;
}

function parseYamlFile(file: string, text: string | null): unknown {
  if (text === null) return null;
  try {
    return parseYaml(text) ?? null;
  } catch (error) {
    throw new FormatError(file, [`błędny YAML: ${(error as Error).message.split('\n')[0]}`]);
  }
}

/** Game files from one main commit, validated (review format and structure format). */
async function loadGame(game: string) {
  const token = githubToken();
  const sha = await mainSha(token);
  const dir = `games/${game}/translations`;
  const [review, structure, bible] = await Promise.all([
    readFile(sha, `${dir}/en-pl-review.json`, token),
    readFile(sha, `${dir}/structure.yaml`, token),
    readFile(sha, `${dir}/bible.yaml`, token),
  ]);
  if (review === null) throw new RequestError(404, { error: 'not_found', message: `Na main nie ma ${dir}/en-pl-review.json.` });

  let reviewData: unknown;
  try {
    reviewData = JSON.parse(review);
  } catch (error) {
    throw new FormatError('en-pl-review.json', [`błędny JSON: ${(error as Error).message}`]);
  }
  const entries = parseReview(reviewData);
  const speakers = speakersFromBible(parseYamlFile('bible.yaml', bible));
  const layout = resolveLayout(
    parseYamlFile('structure.yaml', structure),
    entries,
    speakers ? new Set(speakers.keys()) : null,
  );
  return { sha, entries, layout, speakers: Object.fromEntries(speakers ?? []) };
}

async function assertAdmin(supabase: Client) {
  const { data, error } = await supabase.rpc('workspace_is_admin');
  if (error) throw error;
  if (data !== true) throw new RequestError(403, { error: 'forbidden', message: 'To konto nie ma dostępu do pracowni.' });
}

async function readSaved(supabase: Client, game: string): Promise<{ revision: number; rows: WorkRow[] }> {
  const { data: meta, error } = await supabase.from('workspace_games').select('revision').eq('game', game).maybeSingle();
  if (error) throw error;
  const rows: WorkRow[] = [];
  for (let from = 0;; from += PAGE) {
    const { data, error: pageError } = await supabase
      .from('workspace_work')
      .select('namespace, key, action, english, before, after, state, missing')
      .eq('game', game)
      .order('namespace')
      .order('key')
      .range(from, from + PAGE - 1);
    if (pageError) throw pageError;
    rows.push(...(data as WorkRow[]));
    if (data.length < PAGE) break;
  }
  return { revision: Number(meta?.revision ?? 0), rows };
}

type ApplyResult = { ok: true; revision: number; duplicate?: boolean } | { ok: false; reason: 'revision'; revision: number };

async function apply(
  supabase: Client,
  args: { game: string; revision: number; sha: string; upserts: WorkRow[]; deletes: { namespace: string; key: string }[]; journal: JournalItem[]; requestId?: string },
): Promise<ApplyResult> {
  const { data, error } = await supabase.rpc('workspace_apply', {
    p_game: args.game,
    p_expected_revision: args.revision,
    p_main_sha: args.sha,
    p_upserts: args.upserts,
    p_deletes: args.deletes,
    p_journal: args.journal,
    p_request_id: args.requestId ?? null,
  });
  if (error) throw error;
  return data as ApplyResult;
}

function view(game: string, loaded: Awaited<ReturnType<typeof loadGame>>, revision: number, rows: WorkRow[], changes: JournalItem[]): GameView {
  return {
    game,
    main_sha: loaded.sha,
    revision,
    entries: loaded.entries,
    layout: loaded.layout,
    speakers: loaded.speakers,
    work: rows.filter((row) => !row.missing),
    missing: rows.filter((row) => row.missing),
    changes,
  };
}

export function gameSlug(body: Record<string, unknown>): string {
  if (typeof body.game !== 'string' || !SLUG.test(body.game)) {
    throw new RequestError(400, { error: 'bad_request', message: 'Nieprawidłowy identyfikator gry.' });
  }
  return body.game;
}

/**
 * Open or refresh a game. A fetch or validation error leaves the database untouched.
 * Settle and journal go in one transaction; on a race with a save from another tab
 * the settle is retried once from fresh state.
 */
export async function openGame(supabase: Client, game: string): Promise<GameView> {
  await assertAdmin(supabase);
  const loaded = await loadGame(game);
  for (let attempt = 0; attempt < 2; attempt++) {
    const saved = await readSaved(supabase, game);
    const settlement = settle(saved.rows, loaded.entries);
    const result = await apply(supabase, {
      game,
      revision: saved.revision,
      sha: loaded.sha,
      upserts: settlement.changed,
      deletes: [],
      journal: settlement.journal,
    });
    if (result.ok) return view(game, loaded, result.revision, settlement.rows, settlement.journal);
  }
  throw new RequestError(409, { error: 'busy', message: 'Stan gry zmieniał się w trakcie odświeżania. Spróbuj ponownie.' });
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function draftActions(value: unknown): DraftAction[] {
  const bad = (message: string) => new RequestError(400, { error: 'bad_request', message });
  if (!Array.isArray(value) || value.length === 0 || value.length > 10000) throw bad('„actions” musi być niepustą listą.');
  return value.map((raw, index) => {
    const at = `actions[${index}]`;
    if (typeof raw !== 'object' || raw === null) throw bad(`${at}: nie jest obiektem.`);
    const a = raw as Record<string, unknown>;
    if (typeof a.key !== 'string' || a.key === '' || typeof a.namespace !== 'string') throw bad(`${at}: brak key/namespace.`);
    const ref = { namespace: a.namespace, key: a.key };
    if (a.kind === 'forget') return { ...ref, kind: 'forget' };
    const base = a.base as Record<string, unknown> | undefined;
    if (!base || typeof base.english !== 'string' || typeof base.polish !== 'string') throw bad(`${at}: brak bazy EN/PL szkicu.`);
    const baseTexts = { english: base.english, polish: base.polish };
    if (a.kind === 'accept' || a.kind === 'unset') return { ...ref, kind: a.kind, base: baseTexts };
    if (a.kind === 'correct' && typeof a.after === 'string') return { ...ref, kind: 'correct', base: baseTexts, after: a.after };
    throw bad(`${at}: nieznana akcja.`);
  });
}

/**
 * Save one game's drafts. The server checks draft bases against current main and
 * the revision; staleness is returned for resolution, never a partial save.
 */
export async function saveGame(supabase: Client, body: Record<string, unknown>): Promise<GameView> {
  const game = gameSlug(body);
  if (typeof body.request_id !== 'string' || !UUID.test(body.request_id)) {
    throw new RequestError(400, { error: 'bad_request', message: 'Brak identyfikatora żądania.' });
  }
  if (!Number.isSafeInteger(body.expected_revision)) {
    throw new RequestError(400, { error: 'bad_request', message: 'Brak oczekiwanej rewizji.' });
  }
  const actions = draftActions(body.actions);
  const requestId = body.request_id;
  const expected = body.expected_revision as number;
  await assertAdmin(supabase);

  // Retry of a save that already went through: no re-check of drafts against main.
  const { data: previous, error } = await supabase.from('workspace_requests').select('game').eq('request_id', requestId).maybeSingle();
  if (error) throw error;
  if (previous) return { ...(await openGame(supabase, game)), duplicate: true };

  const loaded = await loadGame(game);
  const saved = await readSaved(supabase, game);
  if (saved.revision !== expected) {
    throw new RequestError(409, { error: 'revision', revision: saved.revision, message: 'Gra została zapisana w innej karcie. Odśwież ją przed zapisem.' });
  }
  const plan = planSave(actions, loaded.entries, saved.rows);
  if (!plan.ok) {
    throw new RequestError(409, { error: 'stale', stale: plan.stale, invalid: plan.invalid, message: 'Część szkiców nie pasuje do aktualnego main.' });
  }
  const result = await apply(supabase, {
    game,
    revision: expected,
    sha: loaded.sha,
    upserts: plan.upserts,
    deletes: plan.deletes,
    journal: plan.journal,
    requestId,
  });
  if (!result.ok) {
    throw new RequestError(409, { error: 'revision', revision: result.revision, message: 'Gra została zapisana w innej karcie. Odśwież ją przed zapisem.' });
  }
  if (result.duplicate) return { ...(await openGame(supabase, game)), duplicate: true };
  return view(game, loaded, result.revision, plan.rows, plan.journal);
}

/** Shared error handling of both functions: readable JSON, never a partial response. */
export function errorResponse(error: unknown): Response {
  if (error instanceof RequestError) return Response.json(error.body, { status: error.status });
  if (error instanceof FormatError) {
    return Response.json({ error: 'format', file: error.file, issues: error.issues, message: error.message }, { status: 422 });
  }
  if (error instanceof GitHubError) {
    return Response.json({ error: 'github', retry_at: error.retryAt, message: error.message }, { status: 503 });
  }
  console.error(error);
  return Response.json({ error: 'internal', message: 'Nieoczekiwany błąd serwera.' }, { status: 500 });
}

export async function jsonBody(req: Request): Promise<Record<string, unknown>> {
  if (req.method !== 'POST') throw new RequestError(405, { error: 'method', message: 'Użyj POST.' });
  try {
    const body = await req.json();
    if (typeof body === 'object' && body !== null && !Array.isArray(body)) return body;
  } catch {
    // below
  }
  throw new RequestError(400, { error: 'bad_request', message: 'Treść żądania musi być obiektem JSON.' });
}
