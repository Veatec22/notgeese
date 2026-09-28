# Heat Signature: technical

Steam `C:\SteamLibrary\steamapps\common\Heat Signature`, appid 268130, buildid 6124596; EXE
version string 2021.1.20.1. `Heat_Signature.exe` 73 653 760 B, PE x86, GameMaker Studio **YYC**
(SHA-256 `a5f8befe…274d2`, documents the analysis input, never a startup condition). FORM at
offset 17 597 096 (54 608 170 B); CODE, VARI, FUNC empty: game code is native, no bytecode.
2566–2585 `gml_*` function names before FORM.

## Texts

1. `Dialog/*.txt`: 13 files (four faction bartenders, Fiasco, practice terminal, tutorial end).
   Syntax: `[Block]`, `#` replies, `{Target}` jumps, `=` continuation, `<Token>` substitutions.
2. Menus, tutorial, gear, objectives, messages: readable literals in the EXE outside FORM.
   `tools/extract_strings.py` reads the `{gml_* name, function address}` table from `.data`,
   finds each function's end (ret + `CC` padding to 16 B; runner code interleaves with GML) and
   assigns each literal to the function whose code loads its address → `work/strings.json`
   (9999 literals), `work/strings-by-function.txt`. Diagnostic logs (~2000 literals) skipped.
3. `Forenames.txt`, `Surnames.txt`: name lists (not translated). Text in graphics: HUD markers.

Scope: 2590 entries: EXE literals, 523 dialogue lines, templates for sentences the game glues
(`{0}`..`{9}`), and item-name grammar (`item-noun:*` with `gender`, `item-modifier:*` with forms
"m / ż / n", `item-tail:*`). Skipped: the `oProblem` repair minigame (random word combos).

## Fonts

All 19 game fonts have 96 glyphs (32–127), **no Polish letters, not even ó**; 18 use
`XoloniumCustom` (8–64 px, bold/italic/AA variants), `fDebugLarge` uses Arial.
First attempt: `font_add` with system Arial → fonts with zero metrics (a positive id was taken as
success; the constructor caps the last char at 255 and reads a file, not a Windows family): empty
text in HUD and menus. Now: `tools/font_assets.py` rasterizes **Xolonium 4.3** (OFL, `fonts/`) into
13 glyph strips + `.metrics` (char, frame, advance, offset, height) and a 120-char UTF-8 map; the
plugin loads them with `sprite_add` + `font_add_sprite_ext` (found by name) replacing the 19 game
fonts. Sprite fonts from `sprite_add` have no per-frame bounds, so proportional advance came out
as the full cell (huge letter gaps): the plugin overwrites glyph fields `[5]` advance and `[6]`
offset only in fonts it created, after checking the glyph map (char, frame, height, count), then
measures every char with `string_width` and requires "i" narrower than "W"; otherwise original
font and English stay. Italic is synthetic. `#` is skipped in measuring (GameMaker newline).

## Plugin (`d3d9.dll` proxy, `plugin/Plugin.cpp` + `plugin/Translate.h`)

Own code (HeatSignatureModLoader was read only to learn the ABI; it uses fixed offsets and is
CC BY-NC). Forwards to system D3D9; initializes at `Direct3DCreate9/Ex`, outside DllMain.
MinHook 1.3.4 (BSD) for trampolines. Finds `draw_set_font`, `string_width`, `font_add`,
`sprite_add`, `font_add_sprite_ext` registrations by name, checks wrapper instruction shape,
resolves relative calls; ambiguity → no hooks + log line. No fixed addresses or checksums.

- **Text**: hooks the shared line-wrapping function (takes UTF-8, builds UTF-16, used by measuring
  and drawing), so swapped text is measured and wrapped in Polish; logic ids untouched.
- **Translation engine** (`Translate.h`, pure C++): exact entry → CAPS version → item name (noun +
  agreeing adjectives) → template with holes `{0}`..`{9}` (holes translated recursively) →
  per-line (`#`, `\r\n`) → truncated names with "..." → word-boundary fragments. Results cached;
  untranslated strings logged unless they already look Polish. `pl.tsv` rows typed E, D (dialogue),
  T, N, A, P; dialogue `<PlayerName>` tokens become template holes.
- **Dialogue at load**: hooks `kernel32!CreateFileW/A`; opening `Dialog\<name>.txt` for reading gets
  `notgeese/cache/Dialog/<name>.txt` built from the player's file: only spoken text translated;
  `[Block]`, `#`, `=`, `{Target}`, `<Token>`, BOM and CRLF kept; replies fully in brackets
  (`[Continue]`) kept for game logic and translated at draw time. Copy error → original file.
  Log: "Dialog X.txt: n of m lines translated" (661 of 662 here; the rest is `<ProblemDescription>`).
- Log `notgeese/LogOutput.log` (shared read): plugin, PE version, engine, discovery, font creation,
  untranslated count.

## Build

Needs MSVC x86 and MinHook 1.3.4 in `work/minhook-1.3.4/`.

```powershell
.venv\Scripts\python.exe games\heat-signature\tools\gen_personal.py
.venv\Scripts\python.exe games\heat-signature\tools\assemble.py
.venv\Scripts\python.exe games\heat-signature\tools\build_plugin.py
.venv\Scripts\python.exe games\heat-signature\tools\test_translate.py --tsv --dialogs "C:\SteamLibrary\steamapps\common\Heat Signature\Dialog"
.venv\Scripts\python.exe games\heat-signature\tools\install.py --game "C:\SteamLibrary\steamapps\common\Heat Signature" [--restore]
```

`gen_personal.py` writes personal-mission templates (one set per relative, right case and gender)
to `work/batches/`; `assemble.py <batch.json>` merges batches into `en-pl-review.json` (plain keys
must be real literals or dialogue lines; template holes and `<Tokens>` preserved). `texts.py` splits
the file into game texts and item grammar. Package: `d3d9.dll`, `notgeese/pl.tsv`, fonts, MinHook
and Xolonium licenses, `READ-ME.txt` (explicit allow-list). Other tools: `verify_hooks.py` (static
ABI check of the EXE), `test_font_guard.py` (font loading safeguards with simulated engine
answers; not GPU rendering), `inspect_game.py` (survey to `work/`).

## Tests

- Vertical 1 (Arial): empty text; vertical 2: text back, huge letter gaps; vertical 3: pause menu
  with Polish letters and correct spacing, **confirmed by the user**.
- Full translation: engine test (incl. BOM/CRLF/token dialogue), preview of 194 strings from user
  session logs and composed examples, all `pl.tsv` rows accepted, font guard test; installed with a
  manifest; EXE and 13 dialogue files unchanged. Not checked in game: whether dialogue opens via
  CreateFile (log will tell), template coverage (log "Untranslated"), text length in tight UI.

## Other attempts found online

Russian project (transliterated dialogue, sprites; no full menu), Chinese LMAO 2.0 patch for build
20180323. Nothing downloaded.
