// Drafts in localStorage, per account and game. This browser and this origin only;
// localhost has different drafts than notgeese.cc.
import { refId } from '../../../supabase/functions/_shared/workspace/mod.ts';
import type { Draft } from './model.ts';

const PREFIX = 'notgeese:workspace:v1';

const keyFor = (user: string, game: string) => `${PREFIX}:${user}:${game}`;

export class DraftStore {
  /** False when the browser refuses writes; the panel then shows a warning. */
  working = true;

  constructor(private readonly user: string) {}

  load(game: string): Map<string, Draft> {
    try {
      const raw = localStorage.getItem(keyFor(this.user, game));
      const drafts = raw ? (JSON.parse(raw) as { drafts?: Draft[] }).drafts ?? [] : [];
      return new Map(drafts.map((draft) => [refId(draft), draft]));
    } catch {
      this.working = false;
      return new Map();
    }
  }

  save(game: string, drafts: Map<string, Draft>): void {
    try {
      const key = keyFor(this.user, game);
      if (drafts.size === 0) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify({ drafts: [...drafts.values()] }));
      this.working = true;
    } catch {
      this.working = false;
    }
  }

  /** Draft count per game for the list tiles. */
  counts(): Map<string, number> {
    const result = new Map<string, number>();
    try {
      const prefix = `${PREFIX}:${this.user}:`;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (!key?.startsWith(prefix)) continue;
        const drafts = (JSON.parse(localStorage.getItem(key) ?? '{}') as { drafts?: unknown[] }).drafts ?? [];
        if (drafts.length) result.set(key.slice(prefix.length), drafts.length);
      }
    } catch {
      this.working = false;
    }
    return result;
  }
}

/** View preferences (page size, edit mode), shared by accounts in this browser. */
export function preference<T extends string | number>(name: string, allowed: readonly T[], fallback: T): T {
  try {
    const raw = localStorage.getItem(`${PREFIX}:pref:${name}`);
    const value = (typeof fallback === 'number' ? Number(raw) : raw) as T;
    return allowed.includes(value) ? value : fallback;
  } catch {
    return fallback;
  }
}

export function setPreference(name: string, value: string | number): void {
  try {
    localStorage.setItem(`${PREFIX}:pref:${name}`, String(value));
  } catch {
    // Preference for this tab only.
  }
}
