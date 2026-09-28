# Void Bastards: technical

Steam app 857980, buildid 4269398, `bundleVersion` 2.0.24, Unity 2017.4.21f1 Mono. 2480/2480
entries. Delivered as a **BepInEx 5.4.23.5 plugin** adding Polish as another I2 language at
runtime; no game file replaced.

## Existing translations

None available found (Polish and English searches, Graj po polsku, Steam, ModDB). Steam lists EN, FR,
DE, ES, JA, KO, PT-BR, RU, ZH-Hans; no Polish.

## Game

- `mscorlib.dll` has `GetPEKind`: not stripped; BepInEx 5 starts.
- **I2 Localization** compiled into `Assembly-CSharp.dll` (like Shotgun Cop Man). Table `I2Languages`
  in `resources.assets`, path_id 14623: 2483 terms, 2479 non-empty, 69 674 EN chars; 9 languages
  (en-US, de-DE, fr-FR, es-ES, zh-CN, ko, ja, ru, pt-BR).
- Older I2 layout with a **Description** field: 227 terms have developer notes (e.g. about plurals),
  stored as `context`.
- Tags: `{[x]}` (I2 parameters), `<b>`, `<size>`, `%d`. Some sentences get a number appended in code:
  numeral trap.
- Categories: Dialog 174, Key 141, Part 122, Star Map 112, CS 103, Interact 94, UpgradeDescription
  93×2, Star Map Event 92, Achievement 72, Junk 72, others.
- Language menu: `LanguageScreen.onEnter` takes `LocalizationManager.GetAllLanguages()`, `draw`
  shows the `Language/<name>` term; a new I2 language appears by itself once `Language/Polish` exists.
- `SwitchFontByLanguage` switches objects by `CurrentLanguage.Contains(...)`; Polish gets the default
  Latin object.

## Plugin

- `plugin/Plugin.cs` (pattern from Shotgun Cop Man): Harmony on `LocalizationManager.AddSource` and
  `InitializeIfNeeded`, `AddLanguage("Polish", "pl")`, filled from `pl.tsv`; adds the missing term
  `Language/Polish` = "Polski".
- **Fonts:** the custom `FUI` UI draws through TextMeshPro components; the old TMP compiled into the
  game has only static SDF atlases without Polish letters and no dynamic glyphs. `FUI` also draws
  `subMeshes` (fallback glyphs). `plugin/PolishGlyphs.cs`: for each `TMP_FontAsset` lacking Polish
  letters, copy its atlas via RenderTexture, take the base glyph (E, Z, L, a…) and draw the diacritic
  as a distance field (ogonek, acute, dot, stroke; thickness measured from "I"/"l"); build a small
  atlas and `TMP_FontAsset`, first in the original's `fallbackFontAssets`. Also „ from ” (and ‚ from ’)
  moved to the baseline. Same face; no font or atlas shipped. Triggered by the
  `LocalizationManager.CurrentLanguage` setter, after adding the language and on every `sceneLoaded`
  (the BepInEx object gets no `Update` in this game). Log: `TMP font "…": composed …`.
- **CRLF bug (fixed):** `pl.tsv` written with `Path.write_text` on Windows got CRLF; the plugin split
  on `\n`, leaving U+000D at the end of every text. TMP moves the pen back to line start on `\r`, so
  text the game appends (key name for `KEY`, ": 5 Jedzenie") overlapped. Now written with
  `newline='\n'` and `TrimEnd('\r')` on load; `pl.tsv` has no `\r`.

## Build

```powershell
.venv\Scripts\python.exe games\void-bastards\tools\analyze.py --game "C:\SteamLibrary\steamapps\common\Void Bastards"
.venv\Scripts\python.exe games\void-bastards\tools\build_plugin.py --game "C:\SteamLibrary\steamapps\common\Void Bastards"
.venv\Scripts\python.exe games\void-bastards\tools\install_local.py --game "C:\SteamLibrary\steamapps\common\Void Bastards" [--restore]
```

`analyze.py` refreshes the review file, `work/analysis.json` and other languages'
`work/ref-<code>.json`. `build_plugin.py` compiles against the game's libraries (.NET 3.5 profile),
zips `dist/Void-Bastards-PL-<version>.zip` with BepInEx 5.4.23.5; trailing spaces preserved.
`install_local.py` keeps a receipt in `backups/void-bastards/`; `--restore` removes exactly the added
files. `translations/structure.yaml`: 10 groups by I2 term category.

## Tests

- Vertical 0.1.1 **confirmed in game**: selector, menus, comic with Polish letters composed at
  runtime; the missing „ fixed after.
- Full translation tested in game partly (overlapping texts found and fixed, two action-log entries
  shortened); review fixes (2026-09-26) enter with this build. Full playthrough pending; what to
  check: `docs/decisions.md`.
