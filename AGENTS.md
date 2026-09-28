# Not Geese: agent instructions

Public repo for machine-made Polish translations of games. User picks a game, installs it,
hands it over. Agent does technical analysis and translation; user judges in-game and does
final language review. **Talk to the user in Polish.**

## Language of the repo

English everywhere, except what Polish players or the Polish editor see:
site (`site/src` pages, components, UI strings), workspace panel UI, `games/<game>/README.md`,
`docs/INSTALL*.txt` (ships as `READ-ME.txt`), applier/plugin messages shown to players,
translations themselves, group/sequence names and sources in `structure.yaml`,
`approach`/`scope` in `game.yaml`, labels in `catalog.yaml`. Everything else (docs, code,
comments, tool output, bible prose, commit messages) is English. Terse: no filler, keep facts.

## Map

| Path | What |
| --- | --- |
| `AGENTS.md` | This file: workflow, delivery rules, conventions. |
| `docs/decisions.md` | Every settled project decision, one line each, with rejected options. Read before proposing process or delivery changes. |
| `docs/workspace.md` | Review workspace (`/admin/`, Supabase): model, states, export, `structure.yaml`, deploy. |
| `docs/design.md` | Site visual spec. Values live in `site/src/styles/tokens.css`. |
| `.claude/skills/localization*` | Translation direction, translation, independent review. |
| `.claude/skills/workspace-corrections` | Applying a workspace export. |
| `games/catalog.yaml` | Status (`ready` / `testing` / `in-progress`) and date added per game. |
| `games/<game>/` | One game, layout below. |
| `tools/` | Shared tools: `translations.py`, `patch.py` + `applier/`, `install.py`, `corrections.py`, `keyart.py`, `check_games.ts`. |
| `site/`, `supabase/` | Site + workspace frontend; workspace backend. |
| `vendor/bepinex/` | BepInEx builds shipped in plugin packages (LGPL, with sources in `site/public/pobierz/`). |

Game layout:

| Path | What |
| --- | --- |
| `README.md` | Player install guide, Polish, shown on the site. `# <Game> PL`, `## Instalacja` with numbered steps, one paragraph on removal/restore. Model: `games/shotgun-cop-man/README.md`. |
| `game.yaml` | Version, entry counts, `tested`, engine, `tested_on`, stores, download. Feeds the site. |
| `docs/technical.md` | Engine, where texts live, how build injects them, build commands, test state, what remains uncertain. |
| `docs/decisions.md` | Translation direction, terms, user-settled choices, review outcome, what to check in game. |
| `docs/INSTALL*.txt` | Player readme packed as `READ-ME.txt`. Polish. |
| `translations/en-pl-review.json` | The only translation file. |
| `translations/bible.yaml` | Characters, terms, style; format in the localization skill. |
| `translations/structure.yaml` | Groups and sequences for the workspace; format in `docs/workspace.md`. |
| `tools/`, `plugin/` | Game-specific extract/build tools, plugin source. |
| `work/` | Local scratch, git-ignored: extracted game data, reports, build dirs. |

`translations/en-pl-review.json`: list of `{key, namespace?, english, polish, context?, note?,
max_length?}`; `(namespace, key)` unique; key as the game uses it. Empty `polish` with non-empty
`english` = not translated yet, build keeps the original. Builds read it via
`tools/translations.py`; a flat map a package needs is generated into `dist/`, never committed.

## Workflow

1. **Existing translations.** Search the web. Found an available Polish translation or official
   PL support → give the download location, stop. Announcements, forum promises, dead pages
   don't count. Report absence as "no available translation found", not certainty.
2. **Other fan translations.** Useful for tools, formats, install method. Note links.
3. **Local game files.** Engine, text format and scope, extract/reinject, Polish glyphs,
   obstacles. Short verdict: go or not, how, what's uncertain.
4. **Direction before vertical.** After a go verdict: skill `localization-direction`.
   Sample real texts, propose tone, voices, key terms; settle significant options with the
   user on concrete EN/PL; decide ordinary ones yourself. Silence is not acceptance.
5. **Vertical.** Small representative slice through the whole pipe: extract → translate →
   build → install → in-game test. Must cover main menu, settings and the very start of play
   (first lines, tutorial, HUD) so the user sees Polish in the first minutes. Check visibility,
   glyphs, layout. A passing build proves nothing in-game; give the user concrete test steps.
6. **Full translation** only after the vertical works. Skill `localization`: bible with sourced
   facts, pitfalls list, check report (hints only). Keep tone, terms, placeholders, tags.
7. **Independent review.** Skill `localization-review` in a fresh-context subagent. Whole text
   plus re-evaluation of early decisions. Apply certain fixes; discuss stylistic options with the
   user; never override user choices. Not a substitute for in-game testing.
8. **Handoff.** Update translation file, scope, test status, install/restore guide,
   `docs/decisions.md`. Summarize to the user: what was chosen, why, source, what to check in game.
9. **Close the game.** Done only when the build leaves a ZIP in `dist/` (everything to extract into
   the game dir + `READ-ME.txt`), the ZIP is copied to `site/public/pobierz/` and referenced in
   `game.yaml` (`download`), `game.yaml` is current, and cover/gallery exist
   (`tools/keyart.py --game <game>`). New games go to `testing` or `in-progress` in
   `games/catalog.yaml`; only the user moves a game to `ready`, after a full playthrough.
10. **Workspace corrections.** User edits at `notgeese.cc/admin/`, exports one game, gives the
    file to a local session. Skill `workspace-corrections`. A game enters the workspace after
    step 7, with bible, decisions, review and `structure.yaml` (groups, conversations with
    speakers where keys allow). `tools/check_games.ts` shows what a game lacks.

## Versions

`0.N` while `testing`/`in-progress`; each package published to main bumps N. `1.0` when the user
moves the game to `ready`. Version is in the game's build, `game.yaml`, the ZIP name and the readme.

## Delivery

Default: **runtime plugin that adds the translation**, never replaced game files. Unity: BepInEx +
Harmony. Unreal: overlay pak. Replacing a file is last resort, after showing a plugin can't work.
Model: `games/my-friend-pedro` (`plugin/Plugin.cs`, `tools/build_plugin.py`).

Rules, no exceptions:

- **The package carries no game content.** No rewritten publisher assets where our text is a
  small add-on. The build checks and refuses to zip a game asset. Exception: **minimal carrier
  structures** the engine needs for a new language and that can't sensibly be made from scratch
  (language table, flag texture container, asset header): small vs our content and wholly
  localization-related. List each in the readme. Boundary: SPRAWL pak 240 KB, 182 KB ours,
  62 KB language table + repainted flag container = OK. My Friend Pedro `resources.assets`
  205 MB with ~40 KB ours = never.
- **No version pinning in plugins.** Bind by class names, not checksums. Game version is info in
  the readme ("tested on…"), never a startup condition. After a game update the plugin keeps
  working or disables itself quietly with a log line; never crashes or blocks the game.
- **Missing texts are not errors.** New lines stay English; plugin logs how many.
- **Plugin logs game and Unity version at startup.**
- **Bundled third-party software must be license-compliant.** BepInEx is LGPL-2.1: ship it
  whole with its LICENSE, publish that version's source archive next to the package, never
  modify or merge its code.

**No plugin possible → delta patch, never the file.** Package carries only the difference;
the player's own file supplies the rest; result is byte-identical to the full build.

```powershell
.venv\Scripts\python.exe tools\patch.py release --original <orig> --built <built> --readme <docs/INSTALL-patch.txt> --out-dir <dist> --game-name <slug> --relative "<path in game dir>" --package-name <Name> --version <version>
```

Text header with both checksums: applying refuses another game version or an already
patched file. Format is portable (copy/insert ops, DEFLATE, one patch per file); the package
ships the applier `<Name>-PL-<version>.exe` (`tools/applier/`, .NET Framework, ~85 KB), so the
player needs no Python. Two implementations (`patch.py`, applier): change one, change both.
Format 3 can **create a new file** from slices of game files (`sources`, `mode create`), e.g.
BPM's extra pak built from fonts inside the player's 3 GB pak (`games/bpm/tools/release.py`).
Scale: Skate Story 275 MB → 78 KB, Boomerang X 1.8 MB → 14 KB.

**Stripped managed code (known blocker).** Unity "managed stripping" removes unused `mscorlib`
methods, incl. `Module.GetPEKind`, which the BepInEx preloader calls in
`PlatformUtils.SetPlatform` → crash at start. Symptom: no `BepInEx/LogOutput.log`, a
`preloader_*.log` in the game dir. Engine-version independent (Skate Story 6000.0.45,
Boomerang X 2020.1.17); upstream calls it expected
([BepInEx#1312](https://github.com/BepInEx/BepInEx/issues/1312)). `dll_search_path_override`
with full libraries fails (game hangs before first screen). Own entry point
`tools/loader/notgeeseLoader.cs` skips the call but then hits `System.Linq.IGrouping`
(replaceable) and a missing `AmbiguousMatchException` ctor Harmony needs: the whole runtime is
cut. Before writing a plugin, check `<game>_Data/Managed/mscorlib.dll`, no game launch needed:

1. contains the string `GetPEKind`? Missing → stripped, preloader won't start.
2. `AmbiguousMatchException` has 4 constructors or 3? Three → Harmony won't start either,
   in every BepInEx from 5.4.17 to 6.0.0-be.788. Then only file replacement (delta patch) is left.

## Builds

- `ROOT = Path(__file__).resolve().parents[1]`; paths relative to the game dir.
- Output to `ROOT / 'dist'`, never the game dir. A build never installs, launches or writes
  outside its output dir.
- File-replacing builds pin originals by SHA-256 and refuse others (print expected hash, write
  nothing). A game update means re-inspecting the format, not just a new checksum.
- End with verification: entry counts in/out, other languages untouched, Polish present.
- Local test install: `tools/install.py` backs up originals to `backups/<game>/` (ignored) and
  never overwrites an existing backup; `--restore` brings them back. Close the game first.
- Environment: Python 3.11, `python -m venv .venv`, `pip install -r requirements.txt`.

## Practice

- Continuing a game: read its `docs/technical.md` and `docs/decisions.md` first, check existing
  texts and tools, resume from the current stage.
- Record findings and next step in `docs/technical.md`. Distinguish file verification from an
  actual in-game test.
- **Never launch a game.** Give concrete test steps and what should be visible on screenshots;
  wait for the user's screenshots before judging.
- Keep originals before replacing game files; build to `dist/`; test installs always with backup.
- Reuse existing tools and layout; don't grow conventions or infrastructure without need.
- Work directly on `main`. No branches, worktrees, PRs or commit conventions unless asked.

## Checks

```powershell
npx -y deno run --allow-read tools/check_games.ts                     # every game vs workspace rules
npx -y deno test --allow-read --allow-env=NOTGEESE_GITHUB_TOKEN supabase/functions/tests/
.venv\Scripts\python.exe -m unittest discover -s tools/tests
.venv\Scripts\python.exe .claude\skills\localization\scripts\l10n_report.py games\<game>
npm --prefix site run build; npm --prefix site test
```
