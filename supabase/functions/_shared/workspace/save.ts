import { describeRef, refId } from './ids.ts';
import { settle } from './settle.ts';
import type { DraftAction, Entry, EntryRef, JournalItem, WorkRow } from './types.ts';

export type SavePlan =
  | {
    ok: true;
    /** Full new state of rows to insert or overwrite. */
    upserts: WorkRow[];
    deletes: EntryRef[];
    journal: JournalItem[];
    rows: WorkRow[];
  }
  | {
    ok: false;
    /** Drafts whose base no longer matches main; the user decides. */
    stale: (EntryRef & { main: { english: string; polish: string } | null })[];
    invalid: string[];
  };

/**
 * Plans a game save: settle saved state against current main, then apply draft
 * actions. Each action's base is checked against main server-side; one stale
 * draft rejects the whole save, nothing is written partially.
 */
export function planSave(actions: DraftAction[], entries: Entry[], saved: WorkRow[]): SavePlan {
  const main = new Map(entries.map((entry) => [refId(entry), entry]));
  const settlement = settle(saved, entries);
  const rows = new Map(settlement.rows.map((row) => [refId(row), row]));
  const upserts = new Map(settlement.changed.map((row) => [refId(row), row]));
  const deletes = new Map<string, EntryRef>();
  const journal = [...settlement.journal];
  const stale: Extract<SavePlan, { ok: false }>['stale'] = [];
  const invalid: string[] = [];
  const seen = new Set<string>();

  for (const action of actions) {
    const ref = { namespace: action.namespace, key: action.key };
    const id = refId(ref);
    if (seen.has(id)) {
      invalid.push(`${describeRef(ref)}: więcej niż jedna akcja`);
      continue;
    }
    seen.add(id);
    const entry = main.get(id);
    const current = rows.get(id);

    if (action.kind === 'forget') {
      if (entry) invalid.push(`${describeRef(ref)}: wpis jest na main, nie można usunąć wyniku pracy`);
      else if (!current) invalid.push(`${describeRef(ref)}: brak wyniku pracy do usunięcia`);
      else {
        deletes.set(id, ref);
        upserts.delete(id);
        rows.delete(id);
        journal.push({ ...ref, kind: 'forget', detail: { state: current.state, english: current.english, before: current.before, after: current.after } });
      }
      continue;
    }

    if (!entry || entry.english !== action.base.english || entry.polish !== action.base.polish) {
      stale.push({ ...ref, main: entry ? { english: entry.english, polish: entry.polish } : null });
      continue;
    }

    if (action.kind === 'unset') {
      if (current) {
        deletes.set(id, ref);
        upserts.delete(id);
        rows.delete(id);
        journal.push({ ...ref, kind: 'unset', detail: { action: current.action, english: current.english, before: current.before, after: current.after } });
      }
      continue;
    }

    if (action.kind === 'correct' && typeof action.after !== 'string') {
      invalid.push(`${describeRef(ref)}: korekta bez tekstu`);
      continue;
    }
    // A correction equal to main's text is an acceptance.
    const next: WorkRow = action.kind === 'correct' && action.after !== entry.polish
      ? { ...ref, action: 'correct', english: entry.english, before: entry.polish, after: action.after, state: 'pending', missing: false }
      : { ...ref, action: 'accept', english: entry.english, before: null, after: entry.polish, state: 'accepted', missing: false };
    if (current && same(current, next)) continue;
    rows.set(id, next);
    upserts.set(id, next);
    deletes.delete(id);
    journal.push({
      ...ref,
      kind: next.action,
      detail: { english: next.english, before: next.before, after: next.after },
    });
  }

  if (stale.length || invalid.length) return { ok: false, stale, invalid };
  return { ok: true, upserts: [...upserts.values()], deletes: [...deletes.values()], journal, rows: [...rows.values()] };
}

function same(a: WorkRow, b: WorkRow): boolean {
  return a.action === b.action && a.english === b.english && a.before === b.before && a.after === b.after &&
    a.state === b.state && a.missing === b.missing;
}
