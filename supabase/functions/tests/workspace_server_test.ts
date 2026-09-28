// Edge Function orchestration without network or Supabase: a stubbed fetch serves SCM
// files as "main", and a client stub mimics the migration's RLS/RPC in memory.
// Transactions, RLS and permissions are covered by supabase/tests/workspace.sql on real Postgres.
import { assert, assertEquals, assertRejects } from 'jsr:@std/assert@1';
import { openGame, RequestError, saveGame } from '../_shared/workspace-server.ts';
import { GitHubError } from '../_shared/github.ts';
import { FormatError, type WorkRow } from '../_shared/workspace/mod.ts';

const SCM = new URL('../../../games/shotgun-cop-man/translations/', import.meta.url);
const SHA = 'a'.repeat(40);

type Files = Record<string, string | null>;

function scmFiles(): Files {
  const read = (name: string) => Deno.readTextFileSync(new URL(name, SCM));
  const dir = 'games/shotgun-cop-man/translations';
  return {
    [`${dir}/en-pl-review.json`]: read('en-pl-review.json'),
    [`${dir}/structure.yaml`]: read('structure.yaml'),
    [`${dir}/bible.yaml`]: read('bible.yaml'),
  };
}

function withMain(files: Files, run: () => Promise<void>, opts: { rateLimited?: boolean } = {}) {
  return async () => {
    const original = globalThis.fetch;
    let calls = 0;
    globalThis.fetch = (input: string | URL | Request) => {
      calls++;
      const url = String(input instanceof Request ? input.url : input);
      if (opts.rateLimited) {
        return Promise.resolve(new Response('', { status: 403, headers: { 'x-ratelimit-reset': '2000000000' } }));
      }
      if (url.endsWith('/commits/main')) return Promise.resolve(new Response(SHA));
      const path = url.split(`/${SHA}/`)[1];
      const text = path === undefined ? undefined : files[path];
      return Promise.resolve(text == null ? new Response('404', { status: 404 }) : new Response(text));
    };
    try {
      await run();
      assert(calls > 0);
    } finally {
      globalThis.fetch = original;
    }
  };
}

/** Minimal supabase-js client stub for the queries workspace-server uses. */
function fakeDb(opts: { admin?: boolean } = {}) {
  const state = {
    revision: null as number | null,
    rows: new Map<string, WorkRow>(),
    journal: [] as unknown[],
    requests: new Map<string, unknown>(),
    applies: 0,
  };
  const id = (r: { namespace: string; key: string }) => JSON.stringify([r.namespace, r.key]);
  const query = (table: string) => {
    const filters: Record<string, unknown> = {};
    let range: [number, number] = [0, Infinity];
    const rows = () => {
      if (table === 'workspace_games') return state.revision === null ? [] : [{ revision: state.revision }];
      if (table === 'workspace_requests') return state.requests.has(filters.request_id as string) ? [{ game: 'shotgun-cop-man' }] : [];
      return [...state.rows.values()].slice(range[0], range[1] + 1);
    };
    const builder = {
      select: () => builder,
      eq: (column: string, value: unknown) => ((filters[column] = value), builder),
      order: () => builder,
      range: (from: number, to: number) => ((range = [from, to]), Promise.resolve({ data: rows(), error: null })),
      maybeSingle: () => Promise.resolve({ data: rows()[0] ?? null, error: null }),
    };
    return builder;
  };
  const rpc = (name: string, args: Record<string, unknown>) => {
    if (name === 'workspace_is_admin') return Promise.resolve({ data: opts.admin ?? true, error: null });
    state.applies++;
    const requestId = args.p_request_id as string | null;
    if (requestId && state.requests.has(requestId)) return Promise.resolve({ data: { ...state.requests.get(requestId) as object, duplicate: true }, error: null });
    const current = state.revision ?? 0;
    if (current !== args.p_expected_revision) return Promise.resolve({ data: { ok: false, reason: 'revision', revision: current }, error: null });
    for (const d of args.p_deletes as WorkRow[]) state.rows.delete(id(d));
    for (const u of args.p_upserts as WorkRow[]) state.rows.set(id(u), u);
    state.journal.push(...(args.p_journal as unknown[]));
    const changed = (args.p_upserts as unknown[]).length + (args.p_deletes as unknown[]).length > 0;
    state.revision = current + (changed ? 1 : 0);
    const result = { ok: true, revision: state.revision };
    if (requestId) state.requests.set(requestId, result);
    return Promise.resolve({ data: result, error: null });
  };
  // deno-lint-ignore no-explicit-any
  return { client: { from: query, rpc } as any, state };
}

const uuid = () => crypto.randomUUID();

Deno.test('open: SCM from main, 9 groups, first open changes nothing', withMain(scmFiles(), async () => {
  const { client, state } = fakeDb();
  const view = await openGame(client, 'shotgun-cop-man');
  assertEquals(view.main_sha, SHA);
  assertEquals(view.entries.length, 485);
  assertEquals(view.layout.groups.length, 9);
  assertEquals(view.speakers.pedro, 'Pedro');
  assertEquals([view.revision, view.work.length, view.changes.length, state.journal.length], [0, 0, 0, 0]);
}));

Deno.test('save → open: pending correction, landing on main makes it accepted', withMain(scmFiles(), async () => {
  const { client, state } = fakeDb();
  const opened = await openGame(client, 'shotgun-cop-man');
  const play = opened.entries.find((e) => e.key === 'mPlay')!;
  const saved = await saveGame(client, {
    game: 'shotgun-cop-man',
    expected_revision: opened.revision,
    request_id: uuid(),
    actions: [{ namespace: '', key: 'mPlay', kind: 'correct', base: { english: play.english, polish: play.polish }, after: 'Zagraj  ' }],
  });
  assertEquals(saved.revision, 1);
  assertEquals(saved.work.map((r) => [r.key, r.state, r.after]), [['mPlay', 'pending', 'Zagraj  ']]);

  // The agent applied the correction on main.
  const files = scmFiles();
  const path = 'games/shotgun-cop-man/translations/en-pl-review.json';
  files[path] = JSON.stringify(JSON.parse(files[path]!).map((e: { key: string }) => e.key === 'mPlay' ? { ...e, polish: 'Zagraj  ' } : e));
  await withMain(files, async () => {
    const refreshed = await openGame(client, 'shotgun-cop-man');
    assertEquals(refreshed.work.map((r) => [r.key, r.action, r.state]), [['mPlay', 'accept', 'accepted']]);
    assertEquals(refreshed.changes.map((c) => c.kind), ['settle']);
    assertEquals(state.revision, 2);
  })();
}));

Deno.test('save: stale draft and foreign revision save nothing', withMain(scmFiles(), async () => {
  const { client, state } = fakeDb();
  await openGame(client, 'shotgun-cop-man');
  const stale = await assertRejects(() =>
    saveGame(client, {
      game: 'shotgun-cop-man',
      expected_revision: 0,
      request_id: uuid(),
      actions: [{ namespace: '', key: 'mPlay', kind: 'accept', base: { english: 'Play', polish: 'nie to' } }],
    }), RequestError);
  assertEquals([stale.status, stale.body.error], [409, 'stale']);
  const revision = await assertRejects(() =>
    saveGame(client, {
      game: 'shotgun-cop-man',
      expected_revision: 7,
      request_id: uuid(),
      actions: [{ namespace: '', key: 'mPlay', kind: 'forget' }],
    }), RequestError);
  assertEquals(revision.body.error, 'revision');
  assertEquals([state.rows.size, state.journal.length], [0, 0]);
}));

Deno.test('save: retrying the same request does not duplicate changes', withMain(scmFiles(), async () => {
  const { client, state } = fakeDb();
  const opened = await openGame(client, 'shotgun-cop-man');
  const play = opened.entries.find((e) => e.key === 'mPlay')!;
  const body = {
    game: 'shotgun-cop-man',
    expected_revision: 0,
    request_id: uuid(),
    actions: [{ namespace: '', key: 'mPlay', kind: 'accept', base: { english: play.english, polish: play.polish } }],
  };
  await saveGame(client, body);
  const again = await saveGame(client, body);
  assert(again.duplicate);
  assertEquals([state.revision, state.journal.length], [1, 1]);
}));

Deno.test('open: broken file, missing game, foreign account and GitHub limit leave the database untouched', async () => {
  const broken = scmFiles();
  broken['games/shotgun-cop-man/translations/structure.yaml'] = 'format: 1\ngroups: [{id: A}]\n';
  const { client, state } = fakeDb();
  await withMain(broken, async () => {
    await assertRejects(() => openGame(client, 'shotgun-cop-man'), FormatError);
    const missing = await assertRejects(() => openGame(client, 'nie-ma-takiej'), RequestError);
    assertEquals(missing.status, 404);
  })();
  await withMain(scmFiles(), async () => {
    const forbidden = await assertRejects(() => openGame(fakeDb({ admin: false }).client, 'shotgun-cop-man'), RequestError);
    assertEquals(forbidden.status, 403);
    await assertRejects(() => openGame(client, '../etc'), RequestError);
    await assertRejects(() => saveGame(client, { game: 'shotgun-cop-man', expected_revision: 0, request_id: 'x', actions: [] }), RequestError);
  })();
  await withMain({}, async () => {
    const limited = await assertRejects(() => openGame(client, 'shotgun-cop-man'), GitHubError);
    assertEquals(limited.retryAt, new Date(2000000000 * 1000).toISOString());
  }, { rateLimited: true })();
  assertEquals(state.applies, 0);
});

Deno.test('open: entry removed from main goes to the missing list', withMain(scmFiles(), async () => {
  const { client } = fakeDb();
  const opened = await openGame(client, 'shotgun-cop-man');
  const quit = opened.entries.find((e) => e.key === 'mQuit')!;
  await saveGame(client, {
    game: 'shotgun-cop-man',
    expected_revision: 0,
    request_id: uuid(),
    actions: [{ namespace: '', key: 'mQuit', kind: 'accept', base: { english: quit.english, polish: quit.polish } }],
  });
  const files = scmFiles();
  const path = 'games/shotgun-cop-man/translations/en-pl-review.json';
  files[path] = JSON.stringify(JSON.parse(files[path]!).filter((e: { key: string }) => e.key !== 'mQuit'));
  await withMain(files, async () => {
    const refreshed = await openGame(client, 'shotgun-cop-man');
    assertEquals(refreshed.missing.map((r) => r.key), ['mQuit']);
    assertEquals(refreshed.work.length, 0);
    const forgotten = await saveGame(client, {
      game: 'shotgun-cop-man',
      expected_revision: refreshed.revision,
      request_id: uuid(),
      actions: [{ namespace: '', key: 'mQuit', kind: 'forget' }],
    });
    assertEquals(forgotten.missing.length, 0);
  })();
}));
