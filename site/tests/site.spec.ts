import { expect, test, type Page } from '@playwright/test';

// Tests do not know the game list: counts come from the page itself, so nothing needs
// updating per new game. Only the page size must match Search.astro.
const PAGE_SIZE = 12;

const allCards = (page: Page) => page.locator('[data-card]');
const visibleCards = (page: Page) => page.locator('[data-card]:visible');
const pager = (page: Page) => page.locator('[data-pager]');

async function choose(page: Page, root: string, value: string) {
  await page.locator(`${root} [data-dropdown-trigger]`).click();
  await page.locator(`${root} [role="option"][data-value="${value}"]`).click();
}

test.describe('game list', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('first page shows at most one page of tiles', async ({ page }) => {
    const total = await allCards(page).count();
    expect(total).toBeGreaterThan(0);
    await expect(visibleCards(page)).toHaveCount(Math.min(PAGE_SIZE, total));
    await expect(pager(page)).toBeVisible({ visible: total > PAGE_SIZE });
  });

  test('pagination moves between pages without changing the URL', async ({ page }) => {
    const total = await allCards(page).count();
    test.skip(total <= PAGE_SIZE, 'all games fit on one page');

    const prev = page.locator('[data-pager-prev]');
    const next = page.locator('[data-pager-next]');
    await expect(prev).toBeDisabled();
    await expect(pager(page).getByRole('button', { name: 'Strona 1' })).toHaveAttribute('aria-current', 'page');
    const firstPage = await visibleCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.card));

    await next.click();
    await expect(pager(page).getByRole('button', { name: 'Strona 2' })).toHaveAttribute('aria-current', 'page');
    await expect(visibleCards(page)).toHaveCount(Math.min(PAGE_SIZE, total - PAGE_SIZE));
    const secondPage = await visibleCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.card));
    expect(secondPage.filter((slug) => firstPage.includes(slug))).toEqual([]);
    await expect(prev).toBeEnabled();
    expect(new URL(page.url()).pathname + new URL(page.url()).hash).toBe('/');

    await pager(page).getByRole('button', { name: 'Strona 1' }).click();
    await expect(visibleCards(page)).toHaveCount(PAGE_SIZE);
    await expect(prev).toBeDisabled();
  });

  test('search narrows the list and Escape clears it', async ({ page }) => {
    const input = page.locator('[data-search-input]');
    const title = (await allCards(page).first().getAttribute('data-title')) ?? '';
    const word = title.split(/\s+/)[0]!.toLowerCase();

    await input.fill(word);
    const shown = await visibleCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.search ?? ''));
    expect(shown.length).toBeGreaterThan(0);
    for (const haystack of shown) expect(haystack).toContain(word);

    await input.fill('zzzz nie ma takiej gry');
    await expect(visibleCards(page)).toHaveCount(0);
    await expect(page.locator('[data-search-empty]')).toBeVisible();
    await expect(pager(page)).toBeHidden();

    await input.press('Escape');
    await expect(input).toHaveValue('');
    await expect(page.locator('[data-search-empty]')).toBeHidden();
    await expect(visibleCards(page)).toHaveCount(Math.min(PAGE_SIZE, await allCards(page).count()));
  });

  test('status filter shows only games with that status and returns to page one', async ({ page }) => {
    const statuses = await page
      .locator('[data-status-filter] [role="option"]')
      .evaluateAll((options) => options.map((option) => option.getAttribute('data-value') ?? '').filter(Boolean));
    expect(statuses.length).toBeGreaterThan(0);

    for (const status of statuses) {
      const expected = await page.locator(`[data-card][data-status="${status}"]`).count();
      await choose(page, '[data-status-filter]', status);
      await expect(visibleCards(page)).toHaveCount(Math.min(PAGE_SIZE, expected));
      const shown = await visibleCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.status));
      expect(new Set(shown)).toEqual(new Set([status]));
      await expect(pager(page)).toBeVisible({ visible: expected > PAGE_SIZE });
    }
  });

  test('A–Z sort orders titles alphabetically', async ({ page }) => {
    await choose(page, '[data-sort]', 'az');
    const expected = await allCards(page).evaluateAll((cards) =>
      cards
        .map((card) => card.dataset.title ?? '')
        .sort((a, b) => a.localeCompare(b, 'pl')),
    );
    const shown = await visibleCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.title ?? ''));
    expect(shown).toEqual(expected.slice(0, PAGE_SIZE));
  });
});

test.describe('game panel', () => {
  test('a tile opens the panel at the game URL, Back closes it', async ({ page }) => {
    await page.goto('/');
    const card = visibleCards(page).first();
    const slug = await card.getAttribute('data-card');
    const panel = page.locator('[data-panel]');

    await card.click();
    await expect(page).toHaveURL(`/${slug}/`);
    await expect(panel).toHaveAttribute('data-open', 'true');
    await expect(panel.locator(`[data-game="${slug}"]`)).toBeVisible();

    await page.goBack();
    await expect(page).toHaveURL('/');
    await expect(panel).toBeHidden();
  });

  test('every game page opens with that game panel', async ({ page }) => {
    await page.goto('/');
    const slugs = await allCards(page).evaluateAll((cards) => cards.map((card) => card.dataset.card ?? ''));

    for (const slug of slugs) {
      const response = await page.goto(`/${slug}/`);
      expect(response?.status(), slug).toBe(200);
      await expect(page.locator(`[data-panel] [data-game="${slug}"]`), slug).toBeVisible();
    }
  });

  test('closing the panel on a game page returns home', async ({ page }) => {
    await page.goto('/');
    const slug = await allCards(page).first().getAttribute('data-card');
    await page.goto(`/${slug}/`);

    await page.locator('[data-panel-close]').click();
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-panel]')).toBeHidden();
  });

  test('every download button points to an existing file', async ({ page, request }) => {
    await page.goto('/');
    const hrefs = await page.locator('a[download]').evaluateAll((links) => links.map((link) => link.getAttribute('href') ?? ''));
    expect(hrefs.length).toBeGreaterThan(0);

    for (const href of hrefs) {
      const response = await request.fetch(href, { method: 'HEAD' });
      expect(response.ok(), href).toBe(true);
    }
  });
});

test.describe('header and FAQ', () => {
  test('theme button cycles system → light → dark and remembers', async ({ page }) => {
    await page.goto('/');
    const html = page.locator('html');
    const toggle = page.locator('[data-theme-toggle]');

    await expect(html).not.toHaveAttribute('data-theme');
    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'light');
    await toggle.click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    await expect(toggle).toHaveAttribute('aria-label', 'Motyw strony: ciemny');

    await page.reload();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    await page.locator('[data-theme-toggle]').click();
    await expect(html).not.toHaveAttribute('data-theme');
  });

  test('FAQ icon scrolls to the section without adding #faq', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#faq')).not.toBeInViewport();

    await page.locator('[data-faq-link]').click();
    await expect(page.locator('#faq')).toBeInViewport();
    expect(new URL(page.url()).hash).toBe('');
  });

  test('FAQ question expands and collapses', async ({ page }) => {
    await page.goto('/');
    const item = page.locator('.ng-faq-item').first();

    await item.locator('summary').click();
    await expect(item).toHaveAttribute('open', '');
    await expect(item.locator('.ng-faq-answer')).toBeVisible();

    await item.locator('summary').click();
    await expect(item).not.toHaveAttribute('open');
  });
});
