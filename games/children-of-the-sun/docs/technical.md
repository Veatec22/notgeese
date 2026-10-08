# Children of the Sun: technical

Steam (app 1309950), install `C:\SteamLibrary\steamapps\common\ChildrenOfTheSun`, Unity
2021.3.20f1 **Mono** x64, URP. Stage: full translation (170/170), independent review done (3 fixes
applied); 0.2 published as testing (language choice persists, Polish splash screens).

## Existing translations

No available Polish translation found (Polish and English searches). Steam lists EN, FR, DE, ES,
JA, KO, PT-BR, RU, ZH-Hans, ZH-Hant; no PL. gry-online.pl at launch: "Gra nie oferuje polskiej
wersji językowej". No fan translations found for other languages that would help.

## Game

- `ChildrenOfTheSun_Data/Managed/Assembly-CSharp.dll` (Mono). `mscorlib.dll` contains `GetPEKind`:
  not stripped, BepInEx Mono preloader should start.
- Unity Localization + Addressables; TextMeshPro; `Unity.InputSystem`.

## Texts

One string table `LOL` in `StreamingAssets/aa/StandaloneWindows64/`:
`localization-string-tables-english(en)_assets_all.bundle` (6671 B), shared data in
`localization-assets-shared_assets_all.bundle` (171 keys). **170 EN entries, 3939 chars**: menu,
options, pause, tutorial, death reasons, score categories, 22 level names, ~20 challenge hints,
dream poem (10 lines), endless mode, photosensitivity warning. Tags `<color=#...>` in tutorial lines.

Story is told without words (cutscene art); no subtitles or dialogue.

Code (`LocalisationSystem.GetLocalisedValue(key, TextMeshProUGUI, big)`): reads table `LOL` via
`LocalizationSettings.StringDatabase.GetLocalizedString`, then swaps the TMP font by locale code
from `GameManager.gm.localizedFonts` (`LocalizedFonts`: `normalBig/Small`, `jp*`, `ru*`, `ko*`,
`zh*`, `zhHant*`). 158 `LocalizeText` components in scenes. Language: TMP dropdown in
`OptionsMenu` (English … Chinese (Traditional)), PlayerPrefs `languageNEW`.

Scene TMP texts without `LocalizeText` (survey `tools/inspect_game.py` → `work/survey.json`): credits
(names, role headings), some debug/placeholder texts never shown. To verify in the vertical which
visible texts bypass the table (e.g. score lines `HEAD X2 ..... 500`, `RATING A` from
`Grading.GetGrade`, `START` countdown in endless).

## Fonts

All 19 TMP font assets are **static** atlases (mode 0) without Polish: Avara-Black/Bold,
GermaniaOne, Plain_Black, LiberationSans have `ó` only, missing `ąćęłńśźż` + caps; Reey,
PermanentMarker, TungusFont, Noto*/Vollkorn RU and CJK lack all. Source TTFs are not in the build.
Vertical: Polish letters composed at runtime from each font's own atlas (base letter + drawn
diacritic, `PolishGlyphs.cs`), nothing shipped. If a face looks wrong in game, fallback option:
ship the OFL original (Avara, Germania One) as a dynamic fallback. Which face is
`normalBig/Small` and where Reey/PermanentMarker/Tungus show: check in the vertical.

## Plugin (`plugin/Plugin.cs`)

BepInEx 5.4.23.5 x64 + Harmony; build/install scripts and `PolishGlyphs.cs` from Laika (Unity
2021.3.29 Mono, same TMP). `mscorlib` has `GetPEKind` and 4 `AmbiguousMatchException` ctors.

- Polish is a layer over English: the game stays on locale `en` (its `normal*` fonts, layout,
  saved `languageNEW`); postfix on `LocalisationSystem.GetLocalisedValue` swaps the result and the
  TMP field text for keys in `pl.tsv`. Missing keys stay EN, logged once each.
- Options → Language: `OptionsMenu.Start` postfix appends "Polski" (index = locale count).
  Prefix on `OptionsMenu.ChangeLanguage`: Polski index → choose Polish, pass the English index;
  another index from the player → Polish off. The game itself calls `ChangeLanguage` twice in
  `OptionsMenu.Start`: `languageDropdown.value = <current locale>` (set_value notifies) and
  `LoadAndSetPlayerPrefs` (saved locale). A counter around both `Start` and
  `LoadAndSetPlayerPrefs` keeps these from turning Polish off; the dropdown is set back to Polski
  after them. Own PlayerPrefs key `notgeese.ChildrenOfTheSun.Polish`.
- **0.1 bug:** the guard covered only `LoadAndSetPlayerPrefs`, so the `set_value` in `Start` turned
  Polish off at every launch (log: "Polish chosen" then "Polish off"); the choice did not persist.
  Fixed in 0.2.
- English → Polski fires no locale event; the plugin calls `LocalizeText.UpdateText` on all
  active `LocalizeText` objects after each change.
- Fonts: `PolishGlyphs.PatchLoadedFonts` (only with Polish on) on scene load, language change and
  before the next lookup after a new `TMP_FontAsset.Awake`. No font shipped.
- Uninstall: game simply returns to English (our key is ignored).
- **Splash logos** (`plugin/SplashLogos.cs`, `tools/splash.py`): the Unity splash screen shows
  three 1024×1024 DXT5 logo textures in `globalgamemanagers.assets` with baked English text:
  `logowarning` (yellow "warning" + the whole photosensitivity paragraph), `logodevolver`
  ("presented by DEVOLVER DIGITAL"), `agameby_logo` ("a game by RENÉ ROTHER"). The table entries
  `photowarning_head/_body` are never used by the game. `splash.py` redraws all three from scratch
  (UnifrakturMaguntia for the headline, "ż" composed; Vollkorn for the rest, the original body face;
  both OFL, not shipped) with PL from `photowarning_*`, "wydawca", "gra autorstwa"; the build ships
  the PNGs. In `Awake` (Polish chosen) the plugin `LoadImage`s them into the textures by name
  (fallback: RGBA → Compress → `Graphics.CopyTexture`) and logs whether the splash had finished.
  First test: textures replaced before the splash finished (log), but only fragments showed: the
  logo sprites have a **tight mesh** around the English letters (warning 499 verts). Now each logo
  sprite gets `Sprite.OverrideGeometry` with a full 1024×1024 quad.

## Build

```powershell
.venv\Scripts\python.exe games\children-of-the-sun\tools\extract.py --game "C:\SteamLibrary\steamapps\common\ChildrenOfTheSun"
.venv\Scripts\python.exe games\children-of-the-sun\tools\build_plugin.py --game "C:\SteamLibrary\steamapps\common\ChildrenOfTheSun"
.venv\Scripts\python.exe games\children-of-the-sun\tools\install_local.py --game "C:\SteamLibrary\steamapps\common\ChildrenOfTheSun" [--restore]
```

`extract.py` reads the EN table (+ DE, RU for context) into `work/source/en.json` and refreshes
`translations/en-pl-review.json` keeping PL. `build_plugin.py` checks keys, TMP tags and line
break counts, compiles (Roslyn csc from VS 2022), zips `dist/Children-of-the-Sun-PL-<version>.zip`,
refuses game files. `install_local.py` adds files with a receipt in `backups/children-of-the-sun/`.
`tools/inspect_game.py`: TMP fonts (PL coverage), scene TMP texts → `work/survey.json`.
IL inspection: Mono.Cecil dumper compiled ad hoc (not kept).

## Tests

- Vertical 0.1 (107/170 entries) **confirmed in game** 2026-10-08: language list, Polish menus, Polish letters OK.
- Full 0.1 (170/170) built and installed locally 2026-10-08; not yet tested in game.
- 0.2 confirmed in game 2026-10-08: language choice persists across restarts; splash logos in Polish (full quads).
