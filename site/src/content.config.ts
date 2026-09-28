import { defineCollection, z } from 'astro:content';
import { file, glob } from 'astro/loaders';

const slugFromPath = ({ entry }: { entry: string }) => entry.split('/')[0];

/**
 * Game metadata from game.yaml: only the fields the site uses. The file also has fields for
 * tools (steam_appid, year from tools/keyart.py, test_notes); the schema skips them.
 */
const games = defineCollection({
  loader: glob({ pattern: '*/game.yaml', base: '../games', generateId: slugFromPath }),
  schema: z.object({
    slug: z.string(),
    title: z.string(),
    version: z.string(),
    entries: z.object({ done: z.number(), total: z.number() }),
    tested: z.enum(['confirmed', 'partial', 'structural']),
    engine: z.string(),
    approach: z.string(),
    scope: z.string(),
    // What the translation was tested on: store (key as in `stores`) and game version from its
    // menu or PlayerSettings.bundleVersion. Info for the player, never a runtime condition.
    tested_on: z.array(z.object({ store: z.string(), version: z.string() })).default([]),
    stores: z.record(z.string()).default({}),
    // Steam screenshot numbers in the panel carousel, in slide order (tools/keyart.py).
    gallery: z.array(z.number()).default([]),
    quote: z
      .object({ text: z.string().nullable().default(null), source: z.string().nullable().default(null) })
      .default({ text: null, source: null }),
    download: z.object({
      kind: z.enum(['zip', 'patch', 'none']),
      file: z.string().nullable().default(null),
      bytes: z.number().nullable().default(null),
    }),
  }),
});

/** Game README: player install guide, rendered in the game panel. */
const gameDocs = defineCollection({
  loader: glob({ pattern: '*/README.md', base: '../games', generateId: slugFromPath }),
});

/** Catalog: translation statuses, each with games and date added. Status order in the file = filter order. */
const statuses = defineCollection({
  loader: file('../games/catalog.yaml'),
  schema: z.object({
    label: z.string(),
    description: z.string(),
    tone: z.enum(['ink', 'outline', 'accent']),
    games: z.record(z.coerce.date()).default({}),
  }),
});

export const collections = { games, gameDocs, statuses };
