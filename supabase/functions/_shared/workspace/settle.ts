import { refId } from './ids.ts';
import type { Entry, JournalItem, WorkRow, WorkState } from './types.ts';

/**
 * State of saved work vs current EN/PL on main (settle table in docs/workspace.md).
 * An EN change wins over a PL match.
 */
export function stateAgainst(row: Pick<WorkRow, 'action' | 'english' | 'before' | 'after'>, main: Entry): {
  action: WorkRow['action'];
  before: string | null;
  state: WorkState;
} {
  if (row.action === 'accept') {
    const same = row.english === main.english && row.after === main.polish;
    return { action: 'accept', before: null, state: same ? 'accepted' : 'review' };
  }
  if (row.english !== main.english) return { action: 'correct', before: row.before, state: 'conflict' };
  // A correction that landed on main becomes an acceptance of its wording.
  if (main.polish === row.after) return { action: 'accept', before: null, state: 'accepted' };
  if (main.polish === row.before) return { action: 'correct', before: row.before, state: 'pending' };
  return { action: 'correct', before: row.before, state: 'conflict' };
}

export interface Settlement {
  /** Rows changed by this settle (full new state). */
  changed: WorkRow[];
  /** All rows after the settle. */
  rows: WorkRow[];
  journal: JournalItem[];
}

/**
 * Settles a game's saved work against main entries. A row without a main entry stays
 * untouched except for the `missing` flag. No change, no journal item.
 */
export function settle(rows: WorkRow[], entries: Entry[]): Settlement {
  const main = new Map(entries.map((entry) => [refId(entry), entry]));
  const changed: WorkRow[] = [];
  const journal: JournalItem[] = [];
  const result = rows.map((row) => {
    const ref = { namespace: row.namespace, key: row.key };
    const entry = main.get(refId(row));
    if (!entry) {
      if (row.missing) return row;
      const next = { ...row, missing: true };
      changed.push(next);
      journal.push({ ...ref, kind: 'missing', detail: { state: row.state, english: row.english, before: row.before, after: row.after } });
      return next;
    }

    const settled = stateAgainst(row, entry);
    const next: WorkRow = { ...row, ...settled, missing: false };
    if (row.missing) journal.push({ ...ref, kind: 'returned', detail: { state: settled.state } });
    if (row.state !== next.state || row.action !== next.action || row.before !== next.before) {
      journal.push({
        ...ref,
        kind: 'settle',
        detail: {
          from: row.state,
          to: next.state,
          action: next.action,
          saved: { english: row.english, before: row.before, after: row.after },
          main: { english: entry.english, polish: entry.polish },
        },
      });
    }
    if (differs(row, next)) changed.push(next);
    return differs(row, next) ? next : row;
  });
  return { changed, rows: result, journal };
}

function differs(a: WorkRow, b: WorkRow): boolean {
  return a.state !== b.state || a.action !== b.action || a.before !== b.before || a.missing !== b.missing;
}
