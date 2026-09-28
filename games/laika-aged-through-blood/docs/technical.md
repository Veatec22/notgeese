# Laika: Aged Through Blood: technical

GOG build 57119379309637473 (1.0.13), Unity 2021.3.29 Mono x64. 3470/3470 entries (UI 378,
characters 79, zones 83, items 265, quests 218, dialogue 2447). Delivered as a **BepInEx 5.4.23.5
plugin** adding a separate language "POLSKI"; no game file replaced.

## Existing translations

Steam: 8 languages, no Polish; no available Polish translation found (Steam, Nexus, search;
2026-09-23). Nexus has a Portuguese fan translation via BepInEx + XUnity AutoTranslator
(nexusmods.com/laikaagedthroughblood/mods/5): BepInEx runs in this game.

## Game

- Code in `Assembly-CSharp.dll`, localization in `Assembly-CSharp-firstpass.dll`.
- Full `mscorlib.dll` (4.6 MB, has `GetPEKind`): BepInEx and Harmony start.
- Assets in one `data.unity3d` (748 MB) + `resources.resource`; FMOD audio; voice is a made-up
  language, subtitles come from the sheets.

## Texts

- **M2H Localization** (`Language`, `LocalizationSettings`, `LanguageCode`). Sheets are TextAssets
  `Resources/Languages/<CODE>_<SHEET>` (`UI`, `CHARACTERS`, `ZONES`, `ITEMS`, `QUESTS`,
  `DIALOGUES`), XML `<entries><entry name="KEY">text</entry>`. Codes EN, ES, FR, DE, RU, JA, KO,
  ZH_CN (PT_UI, ZH_UI empty skeletons).
- Code-less sheets (`_UI` etc.) hold per-entry length limits (264); `extract.py` stores them as
  `limit`, build warns. Indicative only: many EN tutorial texts exceed them.
- `Language.DoSwitch`: per sheet `GetLanguageFileContents` → XmlReader → `Trim` → `\n` to newline
  → `UnescapeXML`. Choice saved in `PlayerPrefs["M2H_lastLanguage"]`, restored by `Language`'s
  static ctor.
- Available languages (`Language.LoadAvailableLanguages`) = `LanguageCode` values (includes `PL`)
  for which `HasLanguageFile(code, first sheet)` is true.
- Language menu (`Laika.UI.Settings.SettingsViewItem`): names from `get_LanguageNamesList`
  (8 hardcoded) + parallel `languageCodes`; selection → `LanguageManager.SwitchLanguage(code)`;
  current item highlighted by `UI_SETTINGS_LANGUAGE_<CODE>`.
- Dialogue: `D_*` TextAssets are scripts (`target LAIKA` / line key); speaker in the key
  `D_<scene>_<SPEAKER>_<n>`.
- Tags: TMP `<color=#…>`, `<sprite name=…>`, `<br>`, `{0}`, `{1}`.

## Plugin (`plugin/Plugin.cs`)

- Prefix `Language.HasLanguageFile`: true for `PL` if the `EN_…` sheet exists; the game adds PL
  to its list itself.
- Prefix `Language.GetLanguageFileContents`: with PL active, builds the sheet from the English XML
  with our texts; missing stay English, count per sheet logged. Adds
  `UI_SETTINGS_LANGUAGE_PL = POLSKI`.
- Postfix `SettingsViewItem.LanguageNamesList`, prefix `SetLayout`: "POLSKI" and `PL` at the end.
- Prefix `Language.SwitchLanguage(LanguageCode)` adds PL if the list was built without it (Harmony
  patching ran the static ctor before the `HasLanguageFile` patch; 0.1.0 bug). Saved
  `M2H_lastLanguage` read before patching; PL restored after the first scene loads.
- Fonts (`plugin/PolishGlyphs.cs`, from Cyber Hook): for each TMP font without Polish letters: the
  dynamic font draws them; else a fallback dynamic font from an already loaded TTF of the same
  face (Oswald, Like A Cave, FriendlyFire, SourceCodePro have Polish); else composed from base
  letters. **Never `Resources.LoadAll`**: loads scene prefabs and crashes (0.1.1); only
  `FindObjectsOfTypeAll<Font>`. Triggers: language switch, scene load, new `TMP_FontAsset` before
  the next `Language.Get`; only with PL active. `SDF_LikeACaveMinus` already lists ąćęłńśźż.
- Startup log: plugin, game and Unity versions.
- Uninstalling with `PL` saved: game falls back to the first language (M2H logs an error); readme
  says to switch to English first.

## Build

```powershell
.venv\Scripts\python.exe games\laika-aged-through-blood\tools\extract.py --game "C:\Games\Laika Aged Through Blood"
.venv\Scripts\python.exe games\laika-aged-through-blood\tools\review.py
.venv\Scripts\python.exe games\laika-aged-through-blood\tools\build_plugin.py --game "C:\Games\Laika Aged Through Blood"
.venv\Scripts\python.exe games\laika-aged-through-blood\tools\structure.py
.venv\Scripts\python.exe games\laika-aged-through-blood\tools\install_local.py --game "C:\Games\Laika Aged Through Blood" [--restore]
```

`extract.py` reads sheets from `data.unity3d` (UnityPy, ~2 min) into `work/source/en.json`;
`review.py` refreshes `translations/en-pl-review.json` (EN and context from the game, PL kept);
`build_plugin.py` checks keys, tags, limits, compiles (Roslyn `csc` from VS 2022), zips
`dist/Laika-Aged-Through-Blood-PL-<version>.zip`. It rejects archives containing
`Laika Aged through Blood_Data`, `.assets`, `.unity3d`, `.resource`, `.bank`. `structure.py`:
19 groups by key prefix, 368 linear scenes as sequences, speaker from the bible `key` regex;
branching scenes stay in group order.

## Tests

- 0.1.0: POLSKI listed, Apply did nothing ("Could not switch from language EN to PL"): list built
  without PL. 0.1.1: PL added, but `Resources.LoadAll<Font>` crashed the game. 0.1.2: **confirmed in
  game** (2026-09-24): Polish letters, menus, prologue, PL restored after restart; `FriendlyFire
  SDF`, `SDF_LikeACaveMinus` have own Polish letters, `LiberationSans` gets them from TTF, Asian
  fonts composed.
- Full translation after independent review: built, installed; later game not yet played. What to
  check: `docs/decisions.md`.
