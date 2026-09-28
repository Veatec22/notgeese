// Workspace contracts. Plain TypeScript: no Deno, Node, DOM or secrets, so the
// Edge Functions and the site import the same module.

/** Validated en-pl-review.json entry. Text is never trimmed. */
export interface Entry {
  namespace: string;
  key: string;
  english: string;
  polish: string;
  context?: string;
  note?: string;
  max_length?: number;
}

export interface EntryRef {
  namespace: string;
  key: string;
}

/** Saved review work for one entry. */
export type WorkAction = 'accept' | 'correct';

/**
 * State after settling against main. `review` = an acceptance whose text changed on main:
 * back to review, the saved row stays so the diff can be shown.
 */
export type WorkState = 'accepted' | 'review' | 'pending' | 'conflict';

export interface WorkRow extends EntryRef {
  action: WorkAction;
  english: string;
  /** PL before the correction; null for an acceptance. */
  before: string | null;
  /** Accepted PL, or PL after the correction. */
  after: string;
  state: WorkState;
  /** Entry gone from main. State kept from the last settle. */
  missing: boolean;
}

export interface Group {
  id: string;
  name: string;
  entries: EntryRef[];
}

export type Certainty = 'certain' | 'reconstructed';

export interface Sequence {
  id: string;
  name: string;
  group: string;
  order: { certainty: Certainty; source: string };
  speakers: { certainty: Certainty; source: string };
  lines: (EntryRef & { speaker?: string })[];
}

export interface Layout {
  groups: Group[];
  sequences: Sequence[];
}

export const UNSORTED_GROUP = { id: '_unsorted', name: 'Do uporządkowania' } as const;
export const SINGLE_GROUP = { id: '_all', name: 'Wszystkie wpisy' } as const;

/** Journal item. `detail` carries the texts needed to replay the change. */
export interface JournalItem extends Partial<EntryRef> {
  kind:
    | 'accept' | 'correct' | 'unset' | 'forget'
    | 'settle' | 'missing' | 'returned';
  detail: Record<string, unknown>;
}

/** Draft action sent on save. `base` = EN/PL on main when the draft was made. */
export type DraftAction =
  | (EntryRef & { kind: 'accept'; base: { english: string; polish: string } })
  | (EntryRef & { kind: 'correct'; base: { english: string; polish: string }; after: string })
  | (EntryRef & { kind: 'unset'; base: { english: string; polish: string } })
  | (EntryRef & { kind: 'forget' });

/** workspace-open / workspace-save response: game from main plus settled work. */
export interface GameView {
  game: string;
  main_sha: string;
  revision: number;
  entries: Entry[];
  layout: Layout;
  /** bible.yaml character id → display name. */
  speakers: Record<string, string>;
  /** Work for entries present on main. */
  work: WorkRow[];
  /** Work whose entry is gone from main. */
  missing: WorkRow[];
  /** State changes from this settle. */
  changes: JournalItem[];
  /** Retry of a save that already went through. */
  duplicate?: boolean;
}

/** Error body of both functions. */
export interface WorkspaceErrorBody {
  error: 'bad_request' | 'method' | 'not_found' | 'forbidden' | 'format' | 'github' | 'revision' | 'stale' | 'busy' | 'internal';
  message: string;
  file?: string;
  issues?: string[];
  retry_at?: string | null;
  revision?: number;
  stale?: (EntryRef & { main: { english: string; polish: string } | null })[];
  invalid?: string[];
}

export class FormatError extends Error {
  constructor(public readonly file: string, public readonly issues: string[]) {
    super(`${file}: ${issues.slice(0, 5).join('; ')}${issues.length > 5 ? ` (i ${issues.length - 5} więcej)` : ''}`);
    this.name = 'FormatError';
  }
}
