# My Friend Pedro: technical

GOG 1.03, Unity 2017.4.19f1 (Mono). 721/721 I2 entries: dialogue (incl. ending), menus,
tutorials, HUD, results, modifiers, barks, achievements, credits. Delivered as a **BepInEx 5.4.23.5
plugin** adding an eleventh language "Polski"; no game file replaced. This is the model plugin
for the repo.

## Texts

- I2 Localization `LanguageSource` is `resources.assets` object 2279 (205 MB file;
  original SHA-256 `4a81ed99cd1e8e5e4665bde87b80d4bd551bf95c088c1b3a80ed2ecfbb9764fd`).
  Languages precede terms (unlike Shotgun Cop Man). `OptionsMenuScript` builds the selector from
  `GetAllLanguages`, so a new language shows up by itself.
- Tokens: icons `<SHOOT2>` etc., `<color>`, `<i>`, `<shake>`, animation commands
  `[Butcher_Shout?Butcher_Idle]`, segment separator `|`. `[Not mapped]` is a label, translated
  `[Nieprzypisane]`.
- Basic Noto fonts have all Polish glyphs; confirmed in game.

## Plugin (`plugin/Plugin.cs`)

- The game can register several sources; `LocalizationManager.AddSource` is the reliable hook
  (plus `InitializeIfNeeded`). The source with our keys gets language `pl` "Polski" appended and
  filled from `pl.tsv` next to the DLL; the other ten languages untouched. Idempotent (a source
  may wake more than once).
- Keys not in `pl.tsv` stay English; count logged. Startup log: plugin, game, Unity versions.
- History: until 0.2 the package replaced the rewritten `resources.assets` (142 MB); replaced by
  the plugin (660 KB package, 43 KB ours).

## Build

```powershell
.venv\Scripts\python.exe games\my-friend-pedro\tools\build_plugin.py --game "C:\Games\My Friend Pedro"
```

Compiles the plugin, writes `pl.tsv` from `translations/en-pl-review.json`, zips the full
unmodified BepInEx, plugin, texts, licenses and `docs/INSTALL-plugin.txt` as `READ-ME.txt`.
BepInEx source zip goes next to the package. `translations/structure.yaml`: 9 groups by key prefix
(`w…` dialogue, menu, keys, hints, results, achievements, GIF/Twitter, credits); no sequences.

## Tests

- Vertical (then asset-replacing build) confirmed by the user in game: selector, saved choice,
  Polish letters, opening.
- Plugin package and the full translation after review: built and verified from files (721/721 TSV
  = JSON, BepInEx files = official ZIP); full campaign not played. What to check:
  `docs/decisions.md`.
