import { readFileSync } from 'node:fs';
import { expect, test, type Page, type Route } from '@playwright/test';
import { load as parseYaml } from 'js-yaml';
// Module files directly, not via mod.ts: Playwright loads code outside the site package as
// CommonJS, and `export *` re-exports then do not reach named imports.
import { planSave } from '../../supabase/functions/_shared/workspace/save.ts';
import { parseReview } from '../../supabase/functions/_shared/workspace/review.ts';
import { resolveLayout, speakersFromBible } from '../../supabase/functions/_shared/workspace/structure.ts';
import type { DraftAction, GameView, WorkRow } from '../../supabase/functions/_shared/workspace/types.ts';

// Workspace /admin/ on the built site, without real Supabase: a session planted in
// localStorage, and function responses computed by the same shared module on SCM files.
// Access, RLS and transactions are covered by the tests in supabase/.

const PROJECT = 'kulwhymoxgaiqpipwbav';
const SESSION_KEY = `sb-${PROJECT}-auth-token`;
const SHA = 'a'.repeat(40);
const USER = { id: '00000000-0000-0000-0000-00000000000a', email: 'admin@example.test' };
const scm = (name: string) => readFileSync(new URL(`../../games/shotgun-cop-man/translations/${name}`, import.meta.url), 'utf8');

function scmView(rows: WorkRow[], revision: number): GameView {
  const entries = parseReview(JSON.parse(scm('en-pl-review.json')));
  const speakers = speakersFromBible(parseYaml(scm('bible.yaml')))!;
  return {
    game: 'shotgun-cop-man',
    main_sha: SHA,
    revision,
    entries,
    layout: resolveLayout(parseYaml(scm('structure.yaml')), entries, new Set(speakers.keys())),
    speakers: Object.fromEntries(speakers),
    work: rows.filter((r) => !r.missing),
    missing: rows.filter((r) => r.missing),
    changes: [],
  };
}

/** Backend stub: work state in test memory, saves via planSave like the Edge Function. */
async function fakeBackend(page: Page, opts: { admin?: boolean } = {}) {
  const state = { rows: [] as WorkRow[], revision: 0, saves: [] as { actions: DraftAction[] }[] };
  const entries = parseReview(JSON.parse(scm('en-pl-review.json')));
  const json = (route: Route, body: unknown, status = 200) =>
    route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body), headers: { 'access-control-allow-origin': '*' } });
  await page.route(`https://${PROJECT}.supabase.co/**`, async (route) => {
    const url = new URL(route.request().url());
    if (route.request().method() === 'OPTIONS') {
      return route.fulfill({ status: 200, headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': '*' } });
    }
    if (url.pathname === '/rest/v1/rpc/workspace_is_admin') return json(route, opts.admin ?? true);
    if (url.pathname === '/rest/v1/workspace_games') return json(route, []);
    if (url.pathname === '/rest/v1/workspace_journal') return json(route, []);
    if (url.pathname === '/functions/v1/workspace-open') return json(route, scmView(state.rows, state.revision));
    if (url.pathname === '/functions/v1/workspace-save') {
      const body = route.request().postDataJSON() as { expected_revision: number; actions: DraftAction[] };
      state.saves.push(body);
      if (body.expected_revision !== state.revision) return json(route, { error: 'revision', message: 'Rewizja.' }, 409);
      const plan = planSave(body.actions, entries, state.rows);
      if (!plan.ok) return json(route, { error: 'stale', message: 'Nieaktualne.', stale: plan.stale }, 409);
      state.rows = plan.rows;
      state.revision++;
      return json(route, scmView(state.rows, state.revision));
    }
    return json(route, { message: `unhandled ${url.pathname}` }, 404);
  });
  return state;
}

async function signIn(page: Page) {
  await page.addInitScript(([key, user]) => {
    const now = Math.floor(Date.now() / 1000);
    localStorage.setItem(key as string, JSON.stringify({
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
      expires_in: 3600,
      expires_at: now + 3600,
      user: { ...(user as object), aud: 'authenticated', role: 'authenticated', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' },
    }));
  }, [SESSION_KEY, USER] as const);
}

async function configured(page: Page) {
  await page.goto('/admin/');
  const missing = page.getByRole('heading', { name: 'Pracownia nie jest skonfigurowana' });
  const ready = page.locator('h1');
  await expect(ready).not.toHaveText('');
  return !(await missing.isVisible());
}

test.describe('workspace', () => {
  test('/admin/ has no game texts and is not indexed', async ({ page, request }) => {
    const html = await (await request.get('/admin/')).text();
    expect(html).toContain('noindex');
    expect(html).not.toContain('Who goes there');
    const sitemap = await (await request.get('/sitemap-0.xml')).text();
    expect(sitemap).not.toContain('/admin/');
    await page.goto('/admin/');
    await expect(page.locator('#workspace h1')).toBeVisible();
  });

  test('without a session shows login', async ({ page }) => {
    await fakeBackend(page);
    test.skip(!(await configured(page)), 'build without Supabase publishable key');
    await expect(page.getByRole('heading', { name: 'Zaloguj się' })).toBeVisible();
    await expect(page.getByLabel('Adres e-mail')).toBeVisible();
  });

  test('an account without access sees no games', async ({ page }) => {
    await fakeBackend(page, { admin: false });
    await signIn(page);
    test.skip(!(await configured(page)), 'build without Supabase publishable key');
    await expect(page.getByRole('heading', { name: 'Brak dostępu' })).toBeVisible();
    await expect(page.locator('.ws-game')).toHaveCount(0);
  });

  test('correction: draft, confirm, persistence, save and export', async ({ page }) => {
    const backend = await fakeBackend(page);
    await signIn(page);
    test.skip(!(await configured(page)), 'build without Supabase publishable key');

    await page.locator('[data-action=open][data-game=shotgun-cop-man]').click();
    await expect(page.getByRole('heading', { name: 'Shotgun Cop Man', level: 1 })).toBeVisible();
    await expect(page.locator('.ws-sidebar [data-action=scope]')).toHaveCount(11); // Wszystkie + 9 grup + sekwencja Pedro
    await expect(page).toHaveURL(/\?gra=shotgun-cop-man$/);

    const play = page.locator('article.ws-entry', { has: page.locator('.ws-key', { hasText: /^mPlay$/ }) });
    await play.locator('textarea').fill('Zagraj  ');
    await expect(play.locator('.ws-draft-badge')).toHaveText('Szkic');
    await expect(page.locator('[data-action=save]')).toHaveText('Zapisz zmiany (1)');

    // An unconfirmed edit blocks saving.
    await page.locator('[data-action=save]').click();
    await expect(page.locator('#ws-toast')).toContainText('zatwierdź poprawki');
    expect(backend.saves).toHaveLength(0);

    await play.getByRole('button', { name: 'Akceptuj', exact: true }).click();
    await expect(play.locator('.ws-status')).toHaveText('Do wdrożenia');

    // The draft survives a reload and shows on the game list.
    await page.reload();
    await expect(play.locator('textarea')).toHaveValue('Zagraj  ');
    await page.locator('[data-action=home]').first().click();
    await expect(page.locator('.ws-game[data-game=shotgun-cop-man] .ws-draft-badge')).toHaveText('Niezapisane szkice: 1');
    await page.locator('[data-action=open][data-game=shotgun-cop-man]').click();

    // Accepting the page does not overwrite the correction draft.
    const eligible = Number((await page.locator('[data-action=accept-page]').textContent())!.match(/\d+/)![0]);
    await page.locator('[data-action=accept-page]').click();
    await expect(page.locator('[data-action=save]')).toHaveText(`Zapisz zmiany (${eligible + 1})`);
    await expect(play.locator('.ws-status')).toHaveText('Do wdrożenia');

    await page.locator('[data-action=save]').click();
    await expect(page.locator('#ws-toast')).toContainText(`Zmiany: ${eligible + 1}.`);
    expect(backend.saves[0].actions).toContainEqual({
      namespace: '', key: 'mPlay', kind: 'correct', base: { english: 'Play', polish: 'Graj' }, after: 'Zagraj  ',
    });
    await expect(page.locator('[data-action=save]')).toHaveText('Zapisz zmiany (0)');
    await expect(play.locator('.ws-status')).toHaveText('Do wdrożenia');
    await expect(play.locator('.ws-draft-badge')).toHaveCount(0);

    // Export: only the correction, spaces kept, state unchanged.
    await page.locator('[data-action=export]').click();
    await page.locator('#ws-comment').fill('Sprawdź długość w menu.');
    const [download] = await Promise.all([page.waitForEvent('download'), page.locator('[data-action=download]').click()]);
    expect(download.suggestedFilename()).toMatch(/^shotgun-cop-man-korekty-\d{4}-\d{2}-\d{2}\.json$/);
    const exported = JSON.parse(readFileSync((await download.path())!, 'utf8'));
    expect(exported.main_sha).toBe(SHA);
    expect(exported.comment).toBe('Sprawdź długość w menu.');
    expect(exported.corrections).toEqual([{ namespace: '', key: 'mPlay', english: 'Play', before: 'Graj', after: 'Zagraj  ' }]);
    expect(exported.conflicts).toEqual([]);
    expect(backend.saves).toHaveLength(1);
  });

  test('Pedro sequence shows speakers in order', async ({ page }) => {
    await fakeBackend(page);
    await signIn(page);
    test.skip(!(await configured(page)), 'build without Supabase publishable key');
    await page.goto('/admin/?gra=shotgun-cop-man');
    await page.locator('[data-action=scope][data-scope="seq:pedro-dlc"]').click();
    const speakers = page.locator('.ws-entry .ws-speaker');
    await expect(speakers).toHaveCount(15);
    await expect(speakers.nth(0)).toHaveText('Shotgun Cop Man');
    await expect(speakers.nth(1)).toHaveText('Pedro');
    await expect(speakers.nth(14)).toHaveText('Mówca nieustalony');
  });

  test('a stale draft blocks saving until decided', async ({ page }) => {
    const backend = await fakeBackend(page);
    await signIn(page);
    await page.addInitScript(([user]) => {
      localStorage.setItem(`notgeese:workspace:v1:${user}:shotgun-cop-man`, JSON.stringify({
        drafts: [{ namespace: '', key: 'mQuit', kind: 'correct', base: { english: 'Quit', polish: 'stare brzmienie' }, after: 'Zakończ', confirmed: true }],
      }));
    }, [USER.id]);
    test.skip(!(await configured(page)), 'build without Supabase publishable key');
    await page.goto('/admin/?gra=shotgun-cop-man');
    const quit = page.locator('article.ws-entry', { has: page.locator('.ws-key', { hasText: /^mQuit$/ }) });
    await expect(quit.getByRole('heading', { name: 'Nieaktualny szkic' })).toBeVisible();
    await page.locator('[data-action=save]').click();
    await expect(page.locator('#ws-toast')).toContainText('nieaktualne szkice');
    expect(backend.saves).toHaveLength(0);
    await quit.getByRole('button', { name: 'Zachowaj na nowej bazie' }).click();
    await page.locator('[data-action=save]').click();
    await expect(page.locator('#ws-toast')).toContainText('Zmiany: 1.');
    expect(backend.saves[0].actions[0]).toMatchObject({ key: 'mQuit', kind: 'correct', after: 'Zakończ' });
  });
});
