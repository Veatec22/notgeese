// State of the open game: server response plus local drafts.
// The browser settles nothing; saved states come from the server. Here we only
// overlay drafts and check whether their base still matches the text on main.
import {
  type DraftAction,
  type Entry,
  type EntryRef,
  type GameView,
  refId,
  type WorkRow,
  type WorkState,
} from '../../../supabase/functions/_shared/workspace/mod.ts';

export type DraftKind = 'accept' | 'correct' | 'unset' | 'forget';

export interface Draft extends EntryRef {
  kind: DraftKind;
  /** EN/PL on main when the draft was made; null only when removing work without an entry. */
  base: { english: string; polish: string } | null;
  after?: string;
  /** A textarea edit waits for "Akceptuj" before it can be saved. */
  confirmed: boolean;
}

export const STATE_LABELS: Record<WorkState, string> = {
  review: 'Do przejrzenia',
  accepted: 'Zaakceptowane',
  pending: 'Do wdrożenia',
  conflict: 'Konflikt',
};

export class GameModel {
  readonly entries = new Map<string, Entry>();
  readonly work = new Map<string, WorkRow>();
  readonly missing = new Map<string, WorkRow>();
  readonly groupOf = new Map<string, string>();
  /** Occurrences of the entry in sequences (scope of a correction). */
  readonly occurrences = new Map<string, number>();

  constructor(readonly view: GameView, readonly drafts: Map<string, Draft>) {
    for (const entry of view.entries) this.entries.set(refId(entry), entry);
    for (const row of view.work) this.work.set(refId(row), row);
    for (const row of view.missing) this.missing.set(refId(row), row);
    for (const group of view.layout.groups) for (const ref of group.entries) this.groupOf.set(refId(ref), group.id);
    for (const sequence of view.layout.sequences) {
      for (const line of sequence.lines) this.occurrences.set(refId(line), (this.occurrences.get(refId(line)) ?? 0) + 1);
    }
  }

  savedState(id: string): WorkState {
    return this.work.get(id)?.state ?? 'review';
  }

  /** A draft whose base no longer matches main cannot be saved. */
  isStale(draft: Draft): boolean {
    const id = refId(draft);
    if (draft.kind === 'forget') return !this.missing.has(id) || this.entries.has(id);
    const entry = this.entries.get(id);
    return !entry || !draft.base || entry.english !== draft.base.english || entry.polish !== draft.base.polish;
  }

  /** State shown on the entry: a confirmed, current draft overrides the saved state. */
  shownState(id: string): WorkState {
    const draft = this.drafts.get(id);
    if (draft && draft.confirmed && !this.isStale(draft)) {
      if (draft.kind === 'accept') return 'accepted';
      if (draft.kind === 'correct') return 'pending';
      if (draft.kind === 'unset') return 'review';
    }
    return this.savedState(id);
  }

  /** Text in the edit field: draft, saved correction, or PL from main. */
  text(id: string): string {
    const draft = this.drafts.get(id);
    if (draft?.after !== undefined) return draft.after;
    const row = this.work.get(id);
    if (row?.action === 'correct') return row.after;
    return this.entries.get(id)?.polish ?? '';
  }

  base(id: string): { english: string; polish: string } {
    const entry = this.entries.get(id)!;
    return { english: entry.english, polish: entry.polish };
  }

  counts(): Record<WorkState, number> {
    const counts: Record<WorkState, number> = { review: 0, accepted: 0, pending: 0, conflict: 0 };
    for (const id of this.entries.keys()) counts[this.shownState(id)]++;
    return counts;
  }

  blockers(): { stale: number; unconfirmed: number } {
    let stale = 0;
    let unconfirmed = 0;
    for (const draft of this.drafts.values()) {
      if (this.isStale(draft)) stale++;
      else if (!draft.confirmed) unconfirmed++;
    }
    return { stale, unconfirmed };
  }

  /** Actions for workspace-save. The caller checks `blockers()` first. */
  actions(): DraftAction[] {
    return [...this.drafts.values()].map((draft): DraftAction => {
      const ref = { namespace: draft.namespace, key: draft.key };
      if (draft.kind === 'forget') return { ...ref, kind: 'forget' };
      const base = draft.base!;
      if (draft.kind === 'correct') return { ...ref, kind: 'correct', base, after: draft.after ?? base.polish };
      return { ...ref, kind: draft.kind, base };
    });
  }

  /** Group entries or sequence lines in order; an entry may appear in a sequence more than once. */
  itemsOf(scope: string): { id: string; speaker?: string }[] {
    const sequence = this.view.layout.sequences.find((s) => `seq:${s.id}` === scope);
    if (sequence) return sequence.lines.map((line) => ({ id: refId(line), speaker: line.speaker }));
    const group = this.view.layout.groups.find((g) => g.id === scope);
    return group ? group.entries.map((ref) => ({ id: refId(ref) })) : [];
  }

  /** Group or sequence where an entry found by game-wide search can be shown. */
  scopeOf(id: string): string {
    return this.groupOf.get(id) ?? this.view.layout.groups[0]?.id ?? '';
  }
}
