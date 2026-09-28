# Decisions

Settled project decisions. Format: **decision.** Why. *Rejected:* option (why).
Don't reopen a rejected option without a new argument; say what changed.
Per-game translation decisions live in `games/<game>/docs/decisions.md`.

## Repo

- **Repo is English; only what Polish players/editor see is Polish** (list in `AGENTS.md`).
  GitHub stays readable for anyone; presentation and editing stay Polish. (2026-09-27)
- **Docs are terse and few:** `AGENTS.md`, this file, `docs/workspace.md`, `docs/design.md`,
  skills, two docs per game. Former ADRs, specs, research notes and reading notes were folded
  in here. (2026-09-27)
- **History squashed into one `init` commit; every game reset to 0.1, status `testing`.**
  Earlier versions were pseudo-versions from fast iteration. (2026-09-27)
- **Versions: `0.N` while testing, bump N per published package, `1.0` when the user marks the
  game `ready`.** One visible rule instead of ad-hoc numbering.
- **Status is set only in `games/catalog.yaml`; only the user moves a game to `ready`**, after a
  full playthrough.
- **Work directly on `main`.** One maintainer; branches/PRs add ceremony only.
- **Scratch (`games/*/work/`) is never committed.** Extracted game data is third-party content;
  batches and reports are reproducible.

## Delivery

- **Runtime plugin before any file replacement.** Package stays small and ours, survives game
  updates. My Friend Pedro went from a 142 MB rewritten asset to 660 KB (43 KB ours).
  *Rejected:* shipping rewritten publisher assets (distributes their content).
- **No plugin possible → delta patch.** Only our difference ships; byte-identical result.
  *Rejected:* shipping the whole file.
- **Patch format 2: copy/insert ops + raw DEFLATE** (2026-09-21). Every runtime has DEFLATE;
  patches got smaller (Skate Story 2.4 MB → 78 KB, Boomerang X 18.4 → 14.3 KB) because offset
  guessing catches shifted files. *Rejected:* format 1 zstd with dictionary (no .NET/browser
  support; removed with the `zstandard` dependency).
- **Delta packages ship `<Name>-PL-<version>.exe` applier** (C# 5, .NET Framework 4). Extract,
  double-click. Checks checksum, backs up original as `<file>.przed-spolszczeniem`, writes via
  temp file; run again on a patched game → offers restore. CLI: `<game dir> [patch]`,
  `--przywroc`. *Rejected:* NSIS/Inno installer (opaque exe poking the game dir, disliked by
  modders, another tool); `.bat` wrapper (less friendly).
- **No in-browser "Install" button** (File System Access API), built and withdrawn 2026-09-21.
  Chromium refuses `.dll .ini .cfg .manifest .lnk .scf .url` (Safe Browsing "dangerous"; BepInEx
  is `winhttp.dll` + `doorstop_config.ini`), blocks all of `Program Files` (Steam/GOG default),
  Firefox/Safari have no API. Worked for 3 of 9 games. Don't revisit without browser changes.
- **Package = ZIP extracted into the game dir, published in `site/public/pobierz/`.** Site shows a
  download only if the file exists there.
- **Stripped Unity runtime → delta patch.** Own BepInEx entry point (`tools/loader/`) tried and
  exhausted: the whole runtime is cut, not one method. Details in `AGENTS.md`.

## Translation process

- **Direction before vertical, independent review after full** (2026-09-24). Regex report can't
  judge meaning, subtext, rhythm or voice; a vertical proves the sample works, not the whole text.
- **Reviewer: fresh-context subagent, read-only, three outputs:** certain fixes (key, before/after,
  reason), topics to discuss (usually top 5–10), in-game checks. No quota of findings; never
  override the user. Same model ≠ independent errors; still worth it.
- **Every game gets bible, decisions and review before entering the workspace.** User: always one
  step less at final correction.
- **Adaptation freedom depends on audio** (user, 2026-09-27): audible dialogue, esp. English →
  stay close (content, register, profanity strength); text-only or mumbling → freer, keep facts,
  mechanics, character.
- **Reading conditions are a second axis** (user, 2026-09-27; from Mangiron 2013): click-through vs
  auto-dismiss, divided attention during play. Drives concision; no invented char limits.
- **Keep what characters know** (from Gacek 2019): certainty, scope, source of information,
  emotion and its cause; don't cut foreshadowing details.
- **Adapt linked lines together** (from O'Hagan & Mangiron 2006): a deliberately wrong line that the
  next line corrects stays wrong in Polish.
- **Strategy per problem, not per game** (from Fernández Costales 2012): precise, domesticate,
  foreignize, keep, transcreate, compensate, canon loyalty.
- *Not adopted:* player-reception checks from Mangiron 2016 (user declined); a corpus of cases
  from published Polish localizations and a before/after pilot metric (recommended, not built).

## Workspace

Details and formats in `docs/workspace.md`.

- **Workspace is for review, not translation.** Agent translates in the repo. No MT/LLM in the
  panel, no multi-language/multi-user, no translation memory, no QA checks (agent validates on
  apply). *Rejected:* light TMS like Weblate (duplicates the repo process; user relies on the agent).
- **Repo is the source of releases; Supabase holds only review work.** Builds never depend on the
  database; losing it loses at most unapplied corrections. *Rejected:* Supabase as source of truth
  (every build/agent change needs sync, two copies drift).
- **Weblate: ideas, not code.** Weblate is GPL-3.0+, repo is MIT; porting would be a derivative work.
- **Panel is `/admin/` of the static Astro site on GitHub Pages;** texts arrive from Supabase only
  after login; access via Supabase Auth + RLS, not a hidden URL. *Rejected:* separate app (second
  deploy), local-only (user wants it at the site address).
- **Workspace reads main straight from GitHub,** no token (repo is public), SHA first then all files
  from that SHA, never writes. Sees only what is pushed. *Rejected:* uploading an import file
  (manual step per change); GitHub Action pushing to Supabase (needs a secret).
  Optional fine-grained read-only token as a function secret if rate limits bite (60 req/h per IP).
- **Entry state settles against main** (table in `docs/workspace.md`). *Rejected:* "taken by
  agent" state and frozen export sets (only main proves application); separate "applied" state
  (text on main in the user's wording = accepted); per-entry comments (a comment goes into the export).
- **Groups and sequences live in the repo** (`structure.yaml`), prepared by the agent. Survive DB
  loss; agent knows where a new line belongs. *Rejected:* groups only in Supabase.
- **Supabase stores only work; a game is fetched on open.** No progress for unopened games, search
  within the open game only, no cross-game similar lines. *Rejected:* full copy of every game on refresh.
- **Settling runs in an Edge Function, one DB transaction.** *Rejected:* in the browser (client
  rules, non-atomic).
- **One review file format, no per-game adapters.** Non-conforming games are fixed in the repo;
  panel shows a clear format error meanwhile. *Rejected:* adapter per file shape.
- **One translation file per game: `en-pl-review.json`; `pl.json` removed** (2026-09-25, all 26
  games, build input proven equal). Two files drifted (Laika: 3 lines). *Rejected:* keep both
  unified; generate review from `pl.json` (review needs EN, context, notes).
- **One admin account, email magic link,** sign-ups off, RLS + function check on `user_id`.
  *Rejected:* GitHub OAuth (own OAuth app for one person).
- **Work whose entry vanished from main is kept** in a "Brak na main" list, outside progress and
  export, removed by hand (journaled). A renamed key = removal + new entry. *Rejected:* auto-delete
  (loses unapplied corrections); blocking save/export (one key stalls the game).
- **No moving entries between groups in v1.** Deferred, not rejected; change goes to the agent.
- **Drafts are saved/discarded only inside a game.** Game list only shows draft counts. *Rejected:*
  "save all" per game or atomic (no context; one stale game blocks the rest; GitHub limits).
- **Export skips conflicts and lists them separately.** *Rejected:* blocking export on conflicts.
- **"Zaakceptuj na stronie" covers the visible page only** (after search/filter), entries to review
  without drafts. No whole-game accept. "Cofnij wszystko" drops only unsaved changes of the open game.
- **Export is JSON** (exact spaces, `\r\n`, tags), unversioned, one game, with main SHA and a free
  comment. Package version changes only on release to main.
- **Sequences without branching graph in v1.** Branching dialogue (DEADBOLT, Heat Signature, Laika)
  stays in file order inside its group.
- **Drafts live in localStorage per account, game and origin** (localhost ≠ notgeese.cc).
- **Prototype stays** in `site/src/prototype/` (dev-only route), user's call.
- **Game icons: public Storage bucket `game-icons`, PNG ≤ 256 KiB, not in the repo.**
