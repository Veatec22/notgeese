// Supabase project address and publishable key: public by design, shared by the workspace
// and the game request form. Never a privileged key in the browser.

/**
 * Publishable key of the Not Geese project. Public by design (like the project URL),
 * so it lives in the repo and goes into the GitHub Actions build. Empty = the panel shows
 * missing config. Fetch: `npx supabase projects api-keys --project-ref kulwhymoxgaiqpipwbav`
 * (klucz `sb_publishable_…`, nigdy `sb_secret_…`).
 */
const PROJECT_PUBLISHABLE_KEY = 'sb_publishable_tLou_pVQr_bzp9sJxLPoQQ_jhiy1YIS';

export const SUPABASE_URL: string = import.meta.env.PUBLIC_SUPABASE_URL ?? 'https://kulwhymoxgaiqpipwbav.supabase.co';
export const SUPABASE_PUBLISHABLE_KEY: string = import.meta.env.PUBLIC_SUPABASE_PUBLISHABLE_KEY || PROJECT_PUBLISHABLE_KEY;

if (SUPABASE_PUBLISHABLE_KEY.startsWith('sb_secret_')) throw new Error('W przeglądarce wolno użyć tylko klucza publishable Supabase.');
