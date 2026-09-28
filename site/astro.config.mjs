// @ts-check
import { defineConfig } from 'astro/config';

import sitemap from '@astrojs/sitemap';

// GitHub Pages with custom domain https://notgeese.cc/ (DNS on Cloudflare), so the site
// lives at / both locally and in production. In-site paths go through withBase()
// from src/lib/url.ts in case it ever moves back under a subdirectory.
export default defineConfig({
  site: 'https://notgeese.cc',
  base: '/',
  devToolbar: { enabled: false },
  build: { format: 'directory' },
  // The workspace is private: out of the sitemap (the page also has noindex).
  integrations: [sitemap({ filter: (page) => !new URL(page).pathname.startsWith('/admin/') })],
});