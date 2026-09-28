# Neon Abyss: technical

GOG 1.5.0.0 (`bundleVersion` "1.5.0.0sRC"), Unity 2018.4.21f1 Mono x64. 2639/2639 entries (menus,
600+ items, weapons, pets, sets, tips, lore, unlock tree, bosses, bar and office dialogue, seeds,
codes, achievements, death screen). Delivered as a **BepInEx 5.4.23.5 plugin**; no game file
replaced; Polish letters from the game's own fonts.

## Existing translations

None available found (2026-09-22). Steam 788100: EN, ZH-Hans/Hant, FR, IT, DE, ES, JA, RU. Neon Abyss
2 (2235200) has Polish; easy to confuse. GOG DLC Chrono Trap is only a license marker (same buildId);
its texts are in the base table and translated.

## Texts

- Full `mscorlib.dll` (has `GetPEKind`): BepInEx starts without workarounds.
- I2 Localization, one `LanguageSourceAsset` "I2Languages", object 3492 in
  `globalgamemanagers.assets`: 2784 terms, 10 languages (first column "Chinese (Mainland China)"
  without code, disabled). Binary layout: terms from byte 56 (key, type, description, 10 values,
  flags, empty `Languages_Touch`), then `CaseInsensitiveTerms`, `OnMissingTranslation`,
  `mTerm_AppName`, languages, Google settings (update Never).
- 2681 text terms, 2639 to translate (rest empty, `-----`, sprite names, one font path stored as
  text: `RESOURCE` in `tools/batch.py`). ~17.8k English words. Categories: PuName (items, 1307),
  UI, Tips, CheatCode, Boss, Tree, Dialogue, Achieve, Seed, Character, Dead.
- Tags: `{0}`, `{[k:Interact]}`, `{[UnlockCost]}`, `<br>`, platform variants
  `[i2s_PC]`/`[i2s_PS4]`/`[i2s_XBox]` (keep count and order). `[Active Item]`, `[Passive]` and
  `<...>` in seeds are plain text.

## Language switcher

Hardcoded in the game, not from I2; the plugin patches all four, found by class name (missing class
= log line, no `Assembly-CSharp` reference):

- `NEON.UI.Base.UIMenuSwitcherLanguageValueSource.Awake` fills labels "ENGLISH", "РУССКИЙ"…;
  plugin adds "POLSKI";
- `GamePlaySettingsHandler.LanguageReverseMapping(label)` → I2 language name, set in
  `LocalizationManager.CurrentLanguage` and saved; `LanguageMapping` similar from `UI/English`…;
- `SettingsHandlerBase.InitWithLanguge(switcher, name)` selects the saved language.

Prefixes return "Polish" for "POLSKI". First run: `SettingsService.Load` takes
`GetSupportedLanguage` from the system language, so Polish Windows may start in Polish.

## Fonts

I2 Font terms `UI/smallFont` and `UI/BigFont` (`Fonts & Materials/<atlas>` in Resources):

| Atlas | Mode | Polish | TTF in game |
| --- | --- | --- | --- |
| EN_12px_PixAntiqua (small, EN/FR/IT/DE/ES) | static | no | PixAntiqua: no |
| EN_70px_ModernBrush (big) | static | no | ModernBrush-Regular: full |
| RU_12px_tahoma, RU_70px_Terry | static | unchecked | tahomabd, Terry Junior Deluxe: full |
| CHT_12px_Zpix | dynamic | draws | Zpix: full |

For Polish `UI/smallFont` = Zpix, `UI/BigFont` = ModernBrush + our fallback; PixAntiqua gets a Zpix
fallback; `TMP_Settings.fallbackFontAssets` gets a global Zpix for hardcoded fonts. Nothing shipped.

- **Broken `CHT_12px_Zpix` atlas:** "i" drawn correctly but `m_FreeGlyphRects` overlaps 159 glyphs,
  so letters added on the fly land on others ("i" garbled in bubbles). `ClearFontAssetData` doesn't
  help (0.2.1–0.2.2). Fix (0.2.3): prefix on `TMP_Text.set_font` swaps it for Polish to a fresh
  atlas from `_TTF/Zpix` (`CreateFontAsset(font, 12, 5, RASTER_HINTED, 1024, 1024, Dynamic)`,
  Bitmap shader copied); Chinese keeps the original.
- **ModernBrush headers:** game atlases are hinted raster, Bitmap shader, Point filter;
  ModernBrush 70 pt, 1024×512 full to y=510. Failed: SDF fallback (Bitmap draws an empty outline),
  raster 70 pt fallbacks; `TryAddCharacters` on `CreateFontAsset` atlases throws NRE in
  `FontEngine.TryAddGlyphsToTexture` in this TMP version, so **dynamic fill doesn't work** and TMP
  silently took Zpix. 0.3.0: static fallback built by hand: glyphs "ĄĆĘŁŃÓŚŹŻąćęłńóśźż„”–—…"
  rendered one by one via internal `FontEngine.TryAddGlyphToTexture` (reflection) into our Alpha8
  texture, glyph/character tables filled manually. 0.3.1: fallback atlases, textures and materials
  get `HideFlags.DontUnloadUnusedAsset` and are reattached on every `TMP_Text.font` and
  `LoadFontAsset`: **confirmed in game** ("SZCZĘŚLIWA ZŁOTA MONETA" all ModernBrush).
  `UnloadUnusedAssets` was freeing our runtime objects; protection from unloading is key.
- Fresh Zpix and the global Zpix stay dynamic (+ filled lists + unload protection). If a foreign
  face shows up in small text, redo it like ModernBrush.

## Build

```powershell
.venv\Scripts\python.exe games\neon-abyss\tools\extract.py --game "C:\Games\Neon Abyss"
.venv\Scripts\python.exe games\neon-abyss\tools\batch.py stats
.venv\Scripts\python.exe games\neon-abyss\tools\build.py --game "C:\Games\Neon Abyss"
```

`extract.py` pins `globalgamemanagers.assets` SHA-256 (`d342ad45…f563`), writes `work/source.json`.
`batch.py show|put|stats` manages batches in `translations/en-pl-review.json`. `build.py` checks keys
and tags, compiles (csc, references from the game's `Managed` and BepInEx), zips
`dist/Neon-Abyss-PL-<version>.zip` with BepInEx and its source next to it. Plugin: texts from
`pl.tsv`; missing and non-text terms (sprites, pad buttons) from the English column.
`translations/structure.yaml`: 10 groups by key prefix.

## Tests

- Vertical (84 entries) **confirmed in game** 2026-09-22: POLSKI in options, Polish letters, system
  language picked Polish.
- Full translation built and installed; ModernBrush headers confirmed; full playthrough pending.
  What to check: `docs/decisions.md`.
