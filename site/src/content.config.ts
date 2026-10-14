import { defineCollection, z } from 'astro:content';
import { file, glob } from 'astro/loaders';

const slugFromPath = ({ entry }: { entry: string }) => entry.split('/')[0];

/** Tested store and game version: info for the player, never a runtime condition. */
const testedOn = z.array(z.object({ store: z.string(), version: z.string() })).default([]);

/**
 * A mod we made for the game (QoL, HUD...): our own ZIP in public/pobierz, optional Nexus page.
 * Source lives in games/<game>/mods/<slug>/, its Polish install guide in README.md there.
 */
const mod = z.object({
  slug: z.string(),
  title: z.string(),
  version: z.string(),
  summary: z.string(),
  approach: z.string(),
  tested_on: testedOn,
  download: z.object({ file: z.string().nullable().default(null), bytes: z.number().nullable().default(null) }),
  nexus: z.string().url().nullable().default(null),
});

/**
 * Game metadata from game.yaml: only the fields the site uses. The file also has fields for
 * tools (steam_appid, year from tools/keyart.py, test_notes); the schema skips them.
 * Translation fields are optional only for games with the catalog status `mods` (we don't
 * translate them, there are only our mods); lib/games.ts enforces that.
 */
const games = defineCollection({
  loader: glob({ pattern: '*/game.yaml', base: '../games', generateId: slugFromPath }),
  schema: z.object({
    slug: z.string(),
    title: z.string(),
    version: z.string().optional(),
    entries: z.object({ done: z.number(), total: z.number() }).optional(),
    tested: z.enum(['confirmed', 'partial', 'structural']).optional(),
    engine: z.string(),
    approach: z.string().optional(),
    scope: z.string().optional(),
    // What the translation was tested on: store (key as in `stores`) and game version from its
    // menu or PlayerSettings.bundleVersion.
    tested_on: testedOn,
    stores: z.record(z.string()).default({}),
    // Steam screenshot numbers in the panel carousel, in slide order (tools/keyart.py).
    gallery: z.array(z.number()).default([]),
    quote: z
      .object({ text: z.string().nullable().default(null), source: z.string().nullable().default(null) })
      .default({ text: null, source: null }),
    download: z
      .object({
        kind: z.enum(['zip', 'patch', 'none']),
        file: z.string().nullable().default(null),
        bytes: z.number().nullable().default(null),
      })
      .optional(),
    mods: z.array(mod).default([]),
  }),
});

/** Game README: player install guide, rendered in the game panel. */
const gameDocs = defineCollection({
  loader: glob({ pattern: '*/README.md', base: '../games', generateId: slugFromPath }),
});

/** Mod README: Polish install guide of one mod, rendered under the mod in the game panel. */
const modDocs = defineCollection({
  loader: glob({
    pattern: '*/mods/*/README.md',
    base: '../games',
    generateId: ({ entry }) => entry.split('/').filter((_, i) => i === 0 || i === 2).join('/'),
  }),
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

export const collections = { games, gameDocs, modDocs, statuses };
