import { describeRef, refId } from './ids.ts';
import {
  type Certainty,
  type Entry,
  type EntryRef,
  FormatError,
  type Group,
  type Layout,
  type Sequence,
  SINGLE_GROUP,
  UNSORTED_GROUP,
} from './types.ts';

export const STRUCTURE_FILE = 'structure.yaml';

const CERTAINTIES: Certainty[] = ['certain', 'reconstructed'];
const ID = /^[a-z0-9][a-z0-9-]*$/;

type Obj = Record<string, unknown>;

function isObj(value: unknown): value is Obj {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Splits entries into groups and sequences per structure.yaml (format in docs/workspace.md).
 * `data === null` = no file: one group in review order. A broken file is a
 * FormatError, not a missing file. `speakers` = character ids from bible.yaml, or null
 * when the game has no bible; speakers are then not checked.
 */
export function resolveLayout(data: unknown, entries: Entry[], speakers: Set<string> | null): Layout {
  if (data === null) {
    return { groups: [{ ...SINGLE_GROUP, entries: entries.map(refOf) }], sequences: [] };
  }

  const issues: string[] = [];
  const byId = new Map(entries.map((entry) => [refId(entry), entry]));

  if (!isObj(data)) throw new FormatError(STRUCTURE_FILE, ['plik musi być mapą']);
  unknownFields(data, ['format', 'groups', 'assign', 'rules', 'sequences'], 'plik', issues);
  if (data.format !== 1) issues.push('„format” musi mieć wartość 1');

  // Groups in display order.
  const groupIds: string[] = [];
  const groupNames = new Map<string, string>();
  if (!Array.isArray(data.groups) || data.groups.length === 0) issues.push('„groups” musi być niepustą listą');
  else {
    data.groups.forEach((raw, index) => {
      const at = `groups[${index}]`;
      if (!isObj(raw)) return void issues.push(`${at}: nie jest mapą`);
      unknownFields(raw, ['id', 'name'], at, issues);
      if (typeof raw.id !== 'string' || !ID.test(raw.id)) return void issues.push(`${at}: „id” musi pasować do ${ID}`);
      if (typeof raw.name !== 'string' || !raw.name.trim()) issues.push(`${at}: brak „name”`);
      if (groupNames.has(raw.id)) issues.push(`${at}: zdublowane id „${raw.id}”`);
      groupIds.push(raw.id);
      groupNames.set(raw.id, typeof raw.name === 'string' ? raw.name : raw.id);
    });
  }
  const knownGroup = (id: unknown, at: string): id is string => {
    if (typeof id === 'string' && groupNames.has(id)) return true;
    issues.push(`${at}: nieznana grupa „${String(id)}”`);
    return false;
  };

  // Manual assignments.
  const assigned = new Map<string, string>();
  listOf(data.assign, 'assign', issues).forEach((raw, index) => {
    const at = `assign[${index}]`;
    if (!isObj(raw)) return void issues.push(`${at}: nie jest mapą`);
    unknownFields(raw, ['key', 'namespace', 'group'], at, issues);
    const ref = entryRef(raw, at, byId, issues);
    if (!knownGroup(raw.group, at) || !ref) return;
    if (assigned.has(refId(ref))) issues.push(`${at}: ${describeRef(ref)} ma już przypisanie`);
    assigned.set(refId(ref), raw.group);
  });

  // Rules, in order.
  // `match` tests the key, `context` the entry context; if both are given both must match.
  const rules: { group: string; match: RegExp | null; context: RegExp | null; namespace: string }[] = [];
  listOf(data.rules, 'rules', issues).forEach((raw, index) => {
    const at = `rules[${index}]`;
    if (!isObj(raw)) return void issues.push(`${at}: nie jest mapą`);
    unknownFields(raw, ['group', 'match', 'context', 'namespace'], at, issues);
    if (raw.namespace !== undefined && typeof raw.namespace !== 'string') issues.push(`${at}: „namespace” musi być tekstem`);
    if (raw.match === undefined && raw.context === undefined) return void issues.push(`${at}: brak „match” ani „context”`);
    const pattern = (field: 'match' | 'context'): RegExp | null | undefined => {
      const value = raw[field];
      if (value === undefined) return null;
      if (typeof value !== 'string' || value === '') return void issues.push(`${at}: „${field}” musi być niepustym tekstem`);
      try {
        return new RegExp(value);
      } catch {
        return void issues.push(`${at}: błędne wyrażenie „${value}”`);
      }
    };
    const match = pattern('match');
    const context = pattern('context');
    if (match === undefined || context === undefined) return;
    if (knownGroup(raw.group, at)) {
      rules.push({ group: raw.group, match, context, namespace: typeof raw.namespace === 'string' ? raw.namespace : '' });
    }
  });

  if (issues.length) throw new FormatError(STRUCTURE_FILE, issues);

  const groupOf = (entry: Entry): string =>
    assigned.get(refId(entry)) ??
      rules.find((rule) =>
        rule.namespace === entry.namespace &&
        (rule.match === null || rule.match.test(entry.key)) &&
        (rule.context === null || rule.context.test(entry.context ?? ''))
      )?.group ??
      UNSORTED_GROUP.id;

  const members = new Map<string, EntryRef[]>([...groupIds, UNSORTED_GROUP.id].map((id) => [id, []]));
  const entryGroup = new Map<string, string>();
  for (const entry of entries) {
    const group = groupOf(entry);
    members.get(group)!.push(refOf(entry));
    entryGroup.set(refId(entry), group);
  }

  // Sekwencje.
  const sequences: Sequence[] = [];
  const sequenceIds = new Set<string>();
  listOf(data.sequences, 'sequences', issues).forEach((raw, index) => {
    const at = `sequences[${index}]`;
    if (!isObj(raw)) return void issues.push(`${at}: nie jest mapą`);
    unknownFields(raw, ['id', 'name', 'group', 'order', 'speakers', 'lines'], at, issues);
    if (typeof raw.id !== 'string' || !ID.test(raw.id)) issues.push(`${at}: „id” musi pasować do ${ID}`);
    else if (sequenceIds.has(raw.id)) issues.push(`${at}: zdublowane id „${raw.id}”`);
    else sequenceIds.add(raw.id);
    if (typeof raw.name !== 'string' || !raw.name.trim()) issues.push(`${at}: brak „name”`);
    const group = knownGroup(raw.group, at) ? raw.group : null;
    const order = certainty(raw.order, `${at}.order`, issues);
    const speakerInfo = certainty(raw.speakers, `${at}.speakers`, issues);

    const lines: Sequence['lines'] = [];
    if (!Array.isArray(raw.lines) || raw.lines.length === 0) issues.push(`${at}: „lines” musi być niepustą listą`);
    else {
      raw.lines.forEach((line, lineIndex) => {
        const lineAt = `${at}.lines[${lineIndex}]`;
        if (!isObj(line)) return void issues.push(`${lineAt}: nie jest mapą`);
        unknownFields(line, ['key', 'namespace', 'speaker'], lineAt, issues);
        const ref = entryRef(line, lineAt, byId, issues);
        if (!ref) return;
        if (group && entryGroup.get(refId(ref)) !== group) {
          issues.push(`${lineAt}: ${describeRef(ref)} nie należy do grupy „${group}”`);
        }
        if (line.speaker === undefined) return void lines.push(ref);
        if (typeof line.speaker !== 'string' || (speakers && !speakers.has(line.speaker))) {
          return void issues.push(`${lineAt}: nieznany mówca „${String(line.speaker)}”`);
        }
        lines.push({ ...ref, speaker: line.speaker });
      });
    }
    if (typeof raw.id === 'string' && typeof raw.name === 'string' && group && order && speakerInfo) {
      sequences.push({ id: raw.id, name: raw.name, group, order, speakers: speakerInfo, lines });
    }
  });

  if (issues.length) throw new FormatError(STRUCTURE_FILE, issues);

  const groups: Group[] = groupIds.map((id) => ({ id, name: groupNames.get(id)!, entries: members.get(id)! }));
  const unsorted = members.get(UNSORTED_GROUP.id)!;
  if (unsorted.length) groups.push({ ...UNSORTED_GROUP, entries: unsorted });
  return { groups, sequences };
}

function refOf(entry: Entry): EntryRef {
  return { namespace: entry.namespace, key: entry.key };
}

function listOf(value: unknown, name: string, issues: string[]): unknown[] {
  if (value === undefined) return [];
  if (Array.isArray(value)) return value;
  issues.push(`„${name}” musi być listą`);
  return [];
}

function unknownFields(obj: Obj, allowed: string[], at: string, issues: string[]) {
  for (const field of Object.keys(obj)) {
    if (!allowed.includes(field)) issues.push(`${at}: nieznane pole „${field}”`);
  }
}

function entryRef(raw: Obj, at: string, byId: Map<string, Entry>, issues: string[]): EntryRef | null {
  if (typeof raw.key !== 'string' || raw.key === '') return void issues.push(`${at}: brak „key”`), null;
  if (raw.namespace !== undefined && typeof raw.namespace !== 'string') {
    return void issues.push(`${at}: „namespace” musi być tekstem`), null;
  }
  const ref = { namespace: typeof raw.namespace === 'string' ? raw.namespace : '', key: raw.key };
  if (!byId.has(refId(ref))) return void issues.push(`${at}: nie ma wpisu ${describeRef(ref)}`), null;
  return ref;
}

function certainty(value: unknown, at: string, issues: string[]): { certainty: Certainty; source: string } | null {
  if (!isObj(value)) return void issues.push(`${at}: brak mapy {certainty, source}`), null;
  unknownFields(value, ['certainty', 'source'], at, issues);
  if (!CERTAINTIES.includes(value.certainty as Certainty)) {
    return void issues.push(`${at}: „certainty” musi być jednym z: ${CERTAINTIES.join(', ')}`), null;
  }
  if (typeof value.source !== 'string' || !value.source.trim()) return void issues.push(`${at}: brak „source”`), null;
  return { certainty: value.certainty as Certainty, source: value.source };
}

/** Character ids and names from bible.yaml (`characters[].id`, `name`). */
export function speakersFromBible(data: unknown): Map<string, string> | null {
  if (data === null) return null;
  if (!isObj(data) || !Array.isArray(data.characters)) throw new FormatError('bible.yaml', ['brak listy „characters”']);
  const result = new Map<string, string>();
  for (const raw of data.characters) {
    if (isObj(raw) && typeof raw.id === 'string') result.set(raw.id, typeof raw.name === 'string' ? raw.name : raw.id);
  }
  return result;
}
