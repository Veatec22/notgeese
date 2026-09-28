import type { EntryRef } from './types.ts';

/**
 * Map key for a (namespace, key) pair. A JSON array is unambiguous for any strings,
 * so no collisions like with a joined separator.
 * In-memory only: never an id in files or in the export.
 */
export function refId(ref: EntryRef): string {
  return JSON.stringify([ref.namespace, ref.key]);
}

export function sameRef(a: EntryRef, b: EntryRef): boolean {
  return a.namespace === b.namespace && a.key === b.key;
}

export function describeRef(ref: EntryRef): string {
  return ref.namespace ? `${ref.namespace} / ${ref.key}` : ref.key;
}
