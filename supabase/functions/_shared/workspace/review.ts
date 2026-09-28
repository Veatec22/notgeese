import { describeRef, refId } from './ids.ts';
import { type Entry, FormatError } from './types.ts';

export const REVIEW_FILE = 'en-pl-review.json';

/**
 * Validates en-pl-review.json. Returns entries in file order or throws FormatError
 * with every problem found; never a partially loaded game.
 */
export function parseReview(data: unknown): Entry[] {
  const issues: string[] = [];
  if (!Array.isArray(data)) throw new FormatError(REVIEW_FILE, ['plik musi być listą obiektów']);

  const seen = new Set<string>();
  const entries: Entry[] = [];
  data.forEach((raw, index) => {
    const at = `wpis ${index + 1}`;
    if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) {
      issues.push(`${at}: nie jest obiektem`);
      return;
    }
    const item = raw as Record<string, unknown>;
    for (const field of ['key', 'english', 'polish'] as const) {
      if (typeof item[field] !== 'string') issues.push(`${at}: brak tekstowego pola „${field}”`);
    }
    if (item.namespace !== undefined && typeof item.namespace !== 'string') {
      issues.push(`${at}: „namespace” musi być tekstem`);
    }
    for (const field of ['context', 'note'] as const) {
      if (item[field] !== undefined && typeof item[field] !== 'string') issues.push(`${at}: „${field}” musi być tekstem`);
    }
    if (item.max_length !== undefined && !(Number.isInteger(item.max_length) && (item.max_length as number) > 0)) {
      issues.push(`${at}: „max_length” musi być dodatnią liczbą całkowitą`);
    }
    if (typeof item.key !== 'string' || typeof item.english !== 'string' || typeof item.polish !== 'string') return;
    if (item.key === '') {
      issues.push(`${at}: pusty „key”`);
      return;
    }

    const entry: Entry = {
      namespace: typeof item.namespace === 'string' ? item.namespace : '',
      key: item.key,
      english: item.english,
      polish: item.polish,
    };
    if (typeof item.context === 'string') entry.context = item.context;
    if (typeof item.note === 'string') entry.note = item.note;
    if (Number.isInteger(item.max_length)) entry.max_length = item.max_length as number;

    const id = refId(entry);
    if (seen.has(id)) issues.push(`${at}: zdublowany wpis ${describeRef(entry)}`);
    seen.add(id);
    entries.push(entry);
  });

  if (issues.length) throw new FormatError(REVIEW_FILE, issues);
  return entries;
}
