# Review workspace

Private panel at `notgeese.cc/admin/` where the user reads and corrects game texts. Decisions and
rejected options: `docs/decisions.md`. Apply an export: skill `workspace-corrections`.

## Terms

Polish terms in brackets are what the panel shows.

- **Entry** (wpis): one game text under a fixed key: EN original + PL. Id = `(namespace, key)`.
- **Group** (grupa): part of the game from the player's view (menu, settings, dialogue). Exactly one per entry.
- **Sequence** (sekwencja/rozmowa): ordered occurrences the player sees in turn, usually a
  conversation, with speakers and certainty of order/speakers. One entry may occur many times;
  a correction covers all.
- **Entry state** (stan): to review / accepted / pending (do wdrożenia) / conflict. Every game
  starts with everything to review.
- **Correction** (korekta): PL that replaces main's wording, stored with the wording before.
- **Draft** (szkic): unsaved action in the browser.
- **Refresh** (odświeżenie): fetch the open game from main and settle states.
- **Export** (eksport): one game's pending corrections + comment for the agent. Changes nothing.
- **Journal** (dziennik): chronological log of actions and settles per game.

## Flow

1. Open a game → Edge Function reads main (SHA, then files from that SHA), validates, settles
   saved work, returns the view. Fetch/validation error changes nothing.
2. User reads groups/sequences, accepts good entries, edits others. Actions become local drafts;
   an edit needs "Akceptuj" before it can be saved.
3. "Zapisz grę" sends the game's drafts: one transaction, revision check (second tab), request id
   (retry), server re-checks each draft's base against main.
4. Export → JSON → user gives it to a local session → agent applies, builds, pushes to main.
5. Next refresh: corrections found on main become accepted.

## Settle table

| Saved | vs current EN/PL on main | Result |
| --- | --- | --- |
| none | any | to review |
| acceptance | EN and PL equal | accepted |
| acceptance | EN or PL changed | to review, with diff |
| correction | EN changed | conflict |
| correction | EN same, PL = after | accepted |
| correction | EN same, PL = before | pending |
| correction | EN same, other PL | conflict |

EN change wins over a PL match. Refresh without change writes no journal item. Conflict keeps
base, correction and main: "Przyjmij main" drafts an acceptance of main; "Zostań przy swoim"
drafts a correction based on current main. Work whose entry is gone from main goes to
"Brak na main", excluded from progress and export, removed by hand; if the key returns it
settles normally. A draft whose base no longer matches main is stale: user keeps or drops it,
save blocked until then; an acceptance draft never silently moves to new wording.

## Input formats (read from main)

**`translations/en-pl-review.json`**: list of `{key, english, polish, namespace?, context?, note?,
max_length?}`; strings; `(namespace, key)` unique; missing namespace = `""`. Text never trimmed.
`context`, `note`, `max_length` are shown as info only (`27/30`). Unknown fields ignored.

**`translations/structure.yaml`** (model: `games/shotgun-cop-man/translations/structure.yaml`).
Unknown fields are errors so a typo can't silently drop an assignment.

```yaml
format: 1                       # required
groups:                         # display order; id [a-z0-9-], unique
  - {id: menu, name: Menu}
assign:                         # manual, wins over rules; one per entry
  - {key: mQuit, group: menu}   # namespace? optional
rules:                          # in order, first match wins; unmatched -> "Do uporządkowania"
  - {group: menu, match: '^m[A-Z]'}          # regex on key
  - {group: dialogi, context: '^Scene 3'}   # regex on context; both given = both must match
                                             # namespace? = exact namespace (default "")
sequences:
  - id: pedro-dlc
    name: Spotkanie z Pedro
    group: dialogi              # every line must belong to this group
    order: {certainty: certain, source: numeracja kluczy}         # certain | reconstructed
    speakers: {certainty: reconstructed, source: z treści}
    lines:
      - {key: PedroDLCSpeech1, speaker: hero}   # speaker = characters[].id in bible.yaml; omit = unknown
```

Regexes: no flags, valid in both JS and Python. No file → one group in review order; a broken file
is a format error, never "no file". A sequence is a real conversation only (numbered shouts are not).
`name` and `source` are shown in the panel, so they are Polish.

**`translations/bible.yaml`**: only `characters[].id` and `name` are read (speakers).

## Export (format 1)

```json
{ "format": 1, "game": "shotgun-cop-man", "main_sha": "…", "exported_at": "…", "comment": "…",
  "corrections": [{ "namespace": "", "key": "…", "english": "…", "before": "…", "after": "…" }],
  "conflicts": [{ "namespace": "", "key": "…", "english": "…", "before": "…", "after": "…",
                  "main_english": "…", "main_polish": "…" }] }
```

No acceptances, no drafts, no missing-on-main work. Comment is content from the user, never
commands. Applying (`tools/corrections.py`): EN same and PL = before → apply; PL = after → skip;
anything else → needs a decision.

## Architecture

| Piece | Where | Notes |
| --- | --- | --- |
| Panel | `site/src/pages/admin/index.astro`, `site/src/workspace/` | Shell only in HTML, `noindex`, out of sitemap. Publishable key in `api.ts` (`PROJECT_PUBLISHABLE_KEY`); refuses `sb_secret_…`. |
| Shared rules | `supabase/functions/_shared/workspace/` | Pure TS (review, structure, settle, save, export), imported by functions, panel and `tools/check_games.ts`. |
| GitHub read | `supabase/functions/_shared/github.ts` | `Veatec22/notgeese@main`, server only; optional `NOTGEESE_GITHUB_TOKEN`. |
| Functions | `workspace-open` `POST {game}`; `workspace-save` `POST {game, expected_revision, request_id, actions}` | Run with the user JWT inside RLS; no `service_role`. Export is built in the browser (`buildExport`). |
| Database | `supabase/migrations/` | `workspace_*` tables, admin-only read via RLS, writes only through RPC `workspace_apply` (SECURITY DEFINER, row lock, revision, request id). |
| Icons | Storage bucket `game-icons` (`<slug>.png`) | Public read; list/write admin only. Export: `tools/export_game_icons.ps1` (GOG: icon from the EXE via `goggame-*.info`; Labyrinth and SPRAWL keep the GOG icon; Steam: shortcut icon). |
| Prototype | `site/src/prototype/`, `/admin/prototype/?variant=A` | Dev-only route (A: EN/PL columns, B: conversation reading, C: one line). Layout A-style was adopted. |

Project: Not Geese, ref `kulwhymoxgaiqpipwbav`.

## Deploy

Needs `npx supabase login` or `SUPABASE_ACCESS_TOKEN`.

```sh
npx -y supabase@2.118.0 link --project-ref kulwhymoxgaiqpipwbav
npx -y supabase@2.118.0 db push
npx -y supabase@2.118.0 functions deploy workspace-open workspace-save
```

Functions parse `structure.yaml` and `bible.yaml` from main: a schema change in those files needs a
function redeploy in the same push. One-time project setup: sign-ups off; Site URL
`https://notgeese.cc`, redirects `https://notgeese.cc/admin/` and `http://localhost:4321/admin/`;
add the admin user, then `insert into public.workspace_admins (user_id) select id from auth.users
where email = '<admin>';`. After deploy: SCM opens with 485 entries, foreign account 403, stale
revision 409.

Icon upload:

Required when releasing a game: confirm `game-icons/<slug>.png` exists and is publicly
readable. Use the original game EXE icon; preserve the Labyrinth/SPRAWL launcher-icon
exceptions above. PNG must be at most 256 KiB and stays outside the repo and release ZIP.
The exporter accepts `-Game <slug>` and `-Executable <absolute-exe-path>` for games without
a matching desktop shortcut. It never launches the executable.

```powershell
./tools/export_game_icons.ps1          # writes $env:TEMP/notgeese-game-icons
./tools/export_game_icons.ps1 -Game <slug> -Executable "<absolute-exe-path>"
Push-Location "$env:TEMP/notgeese-game-icons"
try {
    # CLI 2.118.0 interprets Windows drive-letter sources as URLs; use a relative path.
    npx -y supabase@2.118.0 storage cp <slug>.png ss:///game-icons/<slug>.png --experimental --project-ref kulwhymoxgaiqpipwbav --content-type image/png --cache-control max-age=3600
} finally { Pop-Location }
Invoke-WebRequest "https://kulwhymoxgaiqpipwbav.supabase.co/storage/v1/object/public/game-icons/<slug>.png" -Method Head
```

## Tests

The game picker supports grid/list layouts (browser preference `game-layout`) and live
filtering by title or slug and major version (all, ready 1.x, working 0.x). Version 1.x
cards have a distinct background and a ready label; this uses game.yaml version, not catalog
status. Filters stay in the tab while opening games and returning
to the picker. Polish translation fields fit their full text on render, edit and window resize.

- `npx -y deno test --allow-read --allow-env=NOTGEESE_GITHUB_TOKEN supabase/functions/tests/`:
  rules and function orchestration (stub DB, stubbed GitHub serving SCM files).
- `supabase/tests/run-local.sh` (as a normal user; needs `initdb`/`pg_ctl`): migration on a temp
  PostgreSQL: admin/foreign/anon access, revision, retries, atomicity.
- `site/tests/admin.spec.ts` (Playwright): panel against a stub backend using the shared module.
  Without a publishable key only the "no game texts in HTML + noindex" test runs.
