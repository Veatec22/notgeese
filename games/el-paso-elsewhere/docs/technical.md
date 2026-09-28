# El Paso, Elsewhere: technical

GOG buildId 59616601088709653 (game id 1586317448), Unity 2021.3.21f1 **IL2CPP x64**, HDRP. Stage:
vertical confirmed in game; full translation 0.1 reviewed, packaged, in `testing`.

## Existing translations

No available Polish found (Polish and English searches). Steam lists English only
(`appdetails` 1546310, checked 2026-09-28); GOG `goggame-*.info` lists `en-US`. A search summary
claiming Polish on Steam was false. No fan translations or BepInEx/MelonLoader mods of this game
found. Inside the game: an I2 column "Portuguese (Brazil)" with 52 of 2708 entries filled (UI,
tutorial), credits mention LocalizeDirect; no language selector in the menus.

## Game

- `GameAssembly.dll` + `il2cpp_data/Metadata/global-metadata.dat` (metadata v29), no `Managed`:
  Mono stripping checks don't apply; same setup as Turbo Overkill (2021.3.11, v29), where
  BepInEx 6.0.0-pre.2 Unity.IL2CPP works.
- Serialized files have **no typetrees**. `UnityPy` `TypeTreeGenerator.load_local_game` reads
  IL2CPP; call `get_nodes('<assembly without .dll>', name)` directly: `get_nodes_up` adds `.dll`
  and fails with "Sequence contains no matching element". The generator lays out I2 `TermData`
  wrong (out-of-bounds read), so `tools/analyze.py` parses the I2 asset by hand with asserts.
- Other libraries in the build: Rewired, DOTween, Odin serializer, Sentry (native crash reporter),
  Quantum Console, Graphy, RuntimeInspector (debug UI present in every scene).

## Texts

1. **I2 Localization** `I2Languages` (`resources.assets`, `LanguageSourceAsset`, 362 KB): 2708
   terms, 2706 with English, ~117k EN chars. Languages: English/en, Portuguese (Brazil)/pt-BR,
   "FILE NAME" (spreadsheet leftover, empty). Term names carry category and speaker:
   `EPE Cutscene Subtitles/05_TruthOrDare - 5 - James`. Categories: Cutscene Subtitles 922,
   Ambient Subtitles (barks, hostages) 554, Level Subtitles 538, Optional Subtitles (radio,
   projectors, phones) 479, Chapters 51, Ticker Message 46, Quit Messages 18, Subtitles
   (tutorial) 14, Main Menu 8, Weapon Name 8, `VOSub_Luis_*` 55, credits. Some cutscenes exist
   in two namings (`02_BelieveMe` / `Believe_Me`); which one plays is unverified.
   Speaker tags inside text: `[Past James]`, `[Radio Cop]`, `[Hostage]`, `[???]`.
2. **Key references in assets:** `SubtitleTrackAsset.Text` (Timeline clips, sharedassets51+) holds
   I2 terms, not text; `LocalizeText.LocKey` (558 components) holds `Main Menu - *` etc.
   So dialogue goes through I2 lookups at runtime.
3. **Scene UI** (TextMeshProUGUI 10 046, legacy Text 1984 components; ~220 distinct strings,
   many are debug tools): settings, modifiers, pause, save slots, HUD. The in-game menu is
   duplicated in every level scene. Hardcoded, no I2.
4. **Code literals** (IL2CPP string table): e.g. `CHAPTER `, `CONTINUE`, `ENABLE SUBTITLES` /
   `DISABLE SUBTITLES`, `LOADING`, `ON`/`OFF`, `<voffset=0.6em><size=80%>Difficulty Preset:`,
   `Max Pills: `, `Stakes deal massive damage.`. Which reach the screen is unknown without runtime
   logging; not extracted yet.
5. Possible text in textures (logo, world signs): not surveyed.

Review file (2848 entries, ~135k EN chars): namespace `i2` 2706 (key = term), `ui` 132 (key =
exact English text, context = scene path of the first occurrence; ~17.7k chars, mostly the two
credits blocks), `subtitle` 10 (Timeline clips holding text instead of a term). 44 debug-tool and
placeholder strings skipped (listed in `work/analysis.json`). Dangling keys in assets (no I2
term): `EPE Cutscene Subtitles/05_TruthOrDare - 10 - Draculae`, `Main Menu - Reset`.

## Fonts

- TMP static atlases **without Polish**: SairaCondensed-Bold/Regular SDF,
  SairaExtraCondensed-Black/Bold SDF (sharedassets0, main UI/subtitle face), OfficeCodePro-Regular
  SDF, LiberationSans SDF, Consolas SDF. `LiberationSans SDF - Fallback` is dynamic
  (source LiberationSans TTF in resources.assets).
- TTF in the game: ARIAL, LiberationSans, PerfectDOSVGA437 (resources.assets), Roboto-Regular/Bold
  (sharedassets1). No Saira TTF.
- Options for the vertical, in order: compose Polish glyphs from the Saira atlas at runtime
  (Laika `PolishGlyphs.cs`, Mono → port to IL2CPP; needs readable atlas or GPU readback);
  dynamic fallback from a game TTF (different face); Saira is OFL, so shipping its TTF is legal
  but loading a TTF in TMP 3.0 at runtime needs a `Font` object (unverified).

## Plugin (`plugin/`)

BepInEx 6.0.0-pre.2 Unity.IL2CPP, Turbo Overkill model: interop generated offline only for
compiling (`tools/GenerateInterop.cs`, Cpp2IL + Il2CppInterop from the BepInEx build; Unity base
libraries of 2021.3.11 from Turbo Overkill are enough for compiling), the player's first start
generates their own.

- **I2** (`Terms`): after `LocalizationManager.InitializeIfNeeded` the plugin writes Polish over
  the English column (index 0, asserted `en`) of every loaded source's `TermData.Languages`. The
  game stays in English, nothing is persisted, removal restores the original. Applied before the
  first lookup: Harmony prefixes on `LocalizeText.Awake/Start` (called by Unity, can't be inlined)
  and `LocalizationHandler.GetLocalizedString`, plus every frame until done. Logs current I2
  language and counts.
- **Texts** (`Texts`): exact English → Polish (`ui`, `subtitle`, `code` namespaces) and
  `pattern` entries (`CHAPTER {0}`, `Use {0} and {1} to change weapons.`; inserted key names are
  translated too; an all-caps text matches its entry in capitals, "INTENDED") applied to `TMP_Text` and legacy `Text` on scene change and
  every second (scene-serialized texts never pass the setter), and in a `TMP_Text.text` setter
  prefix. Visible English without an entry (not a known I2 value) is logged once as
  `Untranslated text: "..."` (max 500): source for the code-literal list in `tools/analyze.py`.
- **Fonts** (`PolishGlyphs.cs`, Laika port): static atlases without Polish get a fallback;
  a same-face TTF if loaded (LiberationSans), else composed letters (base glyph from the atlas via
  GPU readback + SDF diacritic). Texts are re-dirtied after a font gets patched.
- On any exception: log, unpatch, game continues in English.

## Build

```powershell
.venv\Scripts\python.exe games\el-paso-elsewhere\tools\analyze.py --game "C:\Games\El Paso, Elsewhere" [--reuse]
.venv\Scripts\python.exe games\el-paso-elsewhere\tools\prepare_interop.py --game "C:\Games\El Paso, Elsewhere"
.venv\Scripts\python.exe games\el-paso-elsewhere\tools\build_plugin.py
.venv\Scripts\python.exe games\el-paso-elsewhere\tools\install_local.py --game "C:\Games\El Paso, Elsewhere" [--restore]
```

`analyze.py` keeps PL and notes; the scene scan (~10 min) is cached in `work/scan.json`.
`build_plugin.py` generates `pl.json` (maps `i2`, `text`, `pattern`) from the review file, checks
tags, `{n}`, newline and CR counts, strict ZIP allowlist, byte comparison of all 234 members.
`install_local.py` (from Turbo Overkill) records added files in
`backups/el-paso-elsewhere/install-receipt.json`; `--restore` removes only unchanged ones.

## Tests

- 0.1 vertical: first run showed dialogue in English (menu Polish); second run Polish with no
  fallback needed (handler/I2 lookups returned Polish, display fallback 0). Cause of the first
  run unknown (first start, interop generation); lookup postfixes, column watchdog and display
  fallback stay as safety nets. **Confirmed in game by the user** (menus, first dialogues).
- Code texts found through the log: key binding list, difficulty presets (Intended, Challenging,
  shown upper-cased), save slot texts, loading dots, tutorial prompts with key names
  (`Press {0} to reload`, `Use {0} and {1} to change weapons.`; key names translated inside).
- Full translation 0.1 (2910/2910 entries): built and installed 2026-09-28, **not yet played**.
  Independent review done (13 certain fixes applied, see docs/decisions.md); package rebuilt,
  copied to site/public/pobierz/, game in `testing`. `translations/structure.yaml` from
  `tools/structure.py` (10 groups, 52 sequences).
