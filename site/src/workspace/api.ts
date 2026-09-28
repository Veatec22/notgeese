// Supabase connection: email-link login, workspace functions and reads via RLS.
// The browser holds only the publishable key; never a privileged key.
import { createClient, type Session, type SupabaseClient } from '@supabase/supabase-js';
import type { GameView, JournalItem, WorkspaceErrorBody } from '../../../supabase/functions/_shared/workspace/mod.ts';

/**
 * Publishable key of the Not Geese project. Public by design (like the project URL),
 * so it lives in the repo and goes into the GitHub Actions build. Empty = the panel shows
 * missing config. Fetch: `npx supabase projects api-keys --project-ref kulwhymoxgaiqpipwbav`
 * (klucz `sb_publishable_…`, nigdy `sb_secret_…`).
 */
const PROJECT_PUBLISHABLE_KEY = 'sb_publishable_tLou_pVQr_bzp9sJxLPoQQ_jhiy1YIS';

export const SUPABASE_URL: string = import.meta.env.PUBLIC_SUPABASE_URL ?? 'https://kulwhymoxgaiqpipwbav.supabase.co';
export const SUPABASE_PUBLISHABLE_KEY: string = import.meta.env.PUBLIC_SUPABASE_PUBLISHABLE_KEY || PROJECT_PUBLISHABLE_KEY;

if (SUPABASE_PUBLISHABLE_KEY.startsWith('sb_secret_')) throw new Error('Pracownia: w przeglądarce wolno użyć tylko klucza publishable.');

export class ApiError extends Error {
  constructor(readonly status: number, readonly body: WorkspaceErrorBody) {
    super(body.message);
  }
}

/** No server response: the save may or may not have gone through; drafts stay. */
export class NetworkError extends Error {}

export interface JournalRow extends JournalItem {
  at: string;
}

export class Api {
  readonly client: SupabaseClient;

  constructor() {
    this.client = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
      auth: { flowType: 'pkce', persistSession: true, detectSessionInUrl: true, autoRefreshToken: true },
    });
  }

  async session(): Promise<Session | null> {
    const { data } = await this.client.auth.getSession();
    return data.session;
  }

  async sendLink(email: string): Promise<void> {
    const { error } = await this.client.auth.signInWithOtp({
      email,
      // Sign-ups disabled: only an existing account gets a link.
      options: { shouldCreateUser: false, emailRedirectTo: new URL('/admin/', location.origin).href },
    });
    if (error) throw error;
  }

  async signOut(): Promise<void> {
    await this.client.auth.signOut();
  }

  async isAdmin(): Promise<boolean> {
    const { data, error } = await this.client.rpc('workspace_is_admin');
    if (error) throw error;
    return data === true;
  }

  /** Last open of games the user has opened before (no progress for the others). */
  async openedGames(): Promise<Map<string, string>> {
    const { data, error } = await this.client.from('workspace_games').select('game, refreshed_at');
    if (error) throw error;
    return new Map((data ?? []).map((row) => [row.game as string, row.refreshed_at as string]));
  }

  async journal(game: string): Promise<JournalRow[]> {
    const { data, error } = await this.client
      .from('workspace_journal')
      .select('at, kind, namespace, key, detail')
      .eq('game', game)
      .order('id', { ascending: false })
      .limit(300);
    if (error) throw error;
    return (data ?? []) as JournalRow[];
  }

  open(game: string): Promise<GameView> {
    return this.call('workspace-open', { game });
  }

  save(body: { game: string; expected_revision: number; request_id: string; actions: unknown[] }): Promise<GameView> {
    return this.call('workspace-save', body);
  }

  private async call(name: string, body: unknown): Promise<GameView> {
    const session = await this.session();
    if (!session) throw new ApiError(401, { error: 'forbidden', message: 'Sesja wygasła. Zaloguj się ponownie.' });
    let response: Response;
    try {
      response = await fetch(`${SUPABASE_URL}/functions/v1/${name}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          apikey: SUPABASE_PUBLISHABLE_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
    } catch {
      throw new NetworkError('Brak połączenia z serwerem. Szkice zostały w przeglądarce.');
    }
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      // below
    }
    if (response.ok && payload && typeof payload === 'object') return payload as GameView;
    const error = payload && typeof payload === 'object' && 'message' in payload
      ? payload as WorkspaceErrorBody
      : { error: 'internal', message: `Serwer odpowiedział błędem ${response.status}.` } as WorkspaceErrorBody;
    throw new ApiError(response.status, error);
  }
}
