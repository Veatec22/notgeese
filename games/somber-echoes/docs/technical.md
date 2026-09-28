# Somber Echoes: technical

GOG gameId 1448685189, buildId 59160173690323092, Unreal Engine 5.4 (XeSS plugin), pak v11.
1507/1507 entries in eight tables. Delivered as an **overlay pak with culture `pl`** plus a
**UE4SS Lua mod** adding "Polski" to the language selector; no original file replaced.

## Existing translations

No available Polish found; GOG lists no Polish. Fan translations found: Czech (DickzillaTranslator,
[lokalizace.net](https://lokalizace.net/localizations/somber-echoes), public 92 KB ZIP; not used),
Turkish (SinnerClown, page didn't load), Russian (Wulf84; Russian is now official too).

## Texts

Paks v11, unencrypted index, no compression, no IoStore. Texts in `pakchunk0-Windows.pak`,
`SomberEchoes/Content/Localization`:

| Table | EN entries |
| --- | ---: |
| Challenges | 80 |
| Dialog | 326 |
| Journal | 101 |
| StringTables | 798 |
| Updated1 | 28 |
| Updated2 | 36 |
| Updated3 | 18 |
| Updated4 | 120 |
| Total | 1507 |

Counts include shop and achievement entries. Some English sources already contain U+FFFD; compare
with other languages for context. `DefaultGame.ini` lists SupportedCultures and all eight
LocalizationPaths; English cultures are `en` and `en-001`. Keys: `table/namespace/key`.

## Language selector

The menu language list is hardcoded in blueprints (`Settings_BP` "Get Languages",
`UI_Settings-Text_BP` "LanguageHack"). `plugin/main.lua` (UE4SS v3.0.1-1140-gf58e8f84, as in Holy
Shoot) appends `pl` to the returned list and sets the label "Polski"; other cultures untouched, no
game version check. `tools/test_selector.py` tests the hooks on a model of UE4SS parameters (not a
substitute for the game).

## Fonts

cmap of fonts extracted from the paks (fontTools): Cinzel Regular/Medium, Maitree-Cinzel (main),
Minion Pro, Montserrat, Yanone Kaffeesatz have the Polish alphabet; Maitree-Cinzel Medium lacks
capital Ą (U+0104); Merienda and Paestum lack many; numeric Maitree has none. No fonts added.

## Build

```powershell
.venv\Scripts\python.exe games\somber-echoes\tools\extract.py
.venv\Scripts\python.exe games\somber-echoes\tools\build.py
```

Reuses the pak and locres reader from BPM and the pak writer from SPRAWL. Extraction writes assets
and full EN only to `work/`. The build keeps only our translations per table, carries original key
and source hashes, checks tags, EN/PL agreement, locres and pak read-back. ZIP (9 files): pak with
eight `pl` locres, loader `dwmapi.dll`, UE4SS with license, `mods.txt`/`mods.json`, the script and
READ-ME. Checks the UE4SS archive SHA-256 and rejects game assets (`.uasset`, `.uexp`, `.ufont`,
`.ubulk`). No version pinning. Batches: `tools/batch.py`. `translations/structure.yaml`: 9 groups by
locres table; no sequences (dialogue is mostly narration).

## Tests

- Vertical (111 entries under `en`) **confirmed in game**; installed as a new
  `SomberEchoes/Content/Paks/pakchunk99-notgeese-PL_P.pak` (nothing replaced).
- Full translation as separate `pl`: preliminary check in game; open question whether the engine
  loads `pl` tables outside SupportedCultures. Full playthrough pending; review fixes (2026-09-25/26)
  enter with this build. What to check: `docs/decisions.md`.
