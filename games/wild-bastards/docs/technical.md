# Wild Bastards: technical

Steam app 1660840, buildid 16213058, `bundleVersion` 1.0.0.26658, Unity 2021.3.32f1 Mono. 4426/4426
entries. Delivered as a **BepInEx 5.4.23.5 plugin** adding Polish as another I2 language at runtime
plus a button in the language menu; no game file replaced.

## Existing translations

None available found (Polish and English searches). Steam lists EN, FR, IT, DE, ES, JA; no Polish.

## Game

- `mscorlib.dll` has `GetPEKind`: not stripped; BepInEx 5 starts.
- **I2 Localization** compiled into `Assembly-CSharp.dll`, plus the game's `Localize` helper. Table
  `I2Languages` in `resources.assets`, path_id 54563: 4543 terms, 4428 non-empty, 147 999 EN chars
  (twice Void Bastards). 10 languages (en, fr, it, de, es, zh, ko, ja, ru, pt); newer I2 layout
  without Description. The Russian table is empty.
- Tags, all kept 1:1: `<color=…>` (~210), own value parameters `<d>`, `<d2>`, `<d3>`, `<p>`, `<p2>`,
  `<n>`, `<s>` (numbers, percentages, planet name), `{0}`–`{2}` (outlaw names), `<sprite name=…>`,
  `[BLANK]`. Leading/trailing spaces matter (the game appends numbers).
- Categories: Dialog 723, UIMG 312, SME 270, TalentName/Desc 229/228, UIPM 220, ItemName/Description
  161, TraitName/Desc, Options, Hint, Location and others.
- Gendered key variants exist (`HUD/Dead`/`HUD/DeadFem`): "Ranny"/"Ranna".

## Plugin

- `plugin/Plugin.cs`: I2 as in Void Bastards: `AddLanguage("Polish", "pl")` on
  `AddSource`/`InitializeIfNeeded`, filled from `pl.tsv`.
- `plugin/LanguageButton.cs`: `UIMGMainMenu` shows a prefab `languagePanel`; `OnSetLanguage(string)`
  sets `LocalizationManager.CurrentLanguage`, saves `HydraOptions` and reloads the scene. The list
  isn't dynamic, so a postfix on `UIMGMainMenu.Start` clones the last button with a persistent
  `OnSetLanguage(...)`, labels it "Polski", removes the I2 `Localize` component, gives it a new
  `onClick` → `OnSetLanguage("Polish")` and a Polish flag if the button has a "flag" image. Logs every
  language button with its argument and texts, and the panel layout kind.
- `plugin/PolishFonts.cs`: the game's SDF atlases are static, without `m_SourceFontFile` and without
  ąćęłńśźż (typetree read). TTFs of the same families are in Resources (`Fonts/SouthbankSpurs`,
  `Fonts/GrindstoneDisplay`, `Fonts/JosefinSans-Regular`), so for each atlas the plugin makes
  `TMP_FontAsset.CreateFontAsset(TTF, …, Dynamic)` and puts it first as fallback. DroneRanger has no
  TTF with Polish letters: the game's dynamic LiberationSans fallback applies. No font shipped.

## Build

```powershell
.venv\Scripts\python.exe games\wild-bastards\tools\analyze.py --game "C:\SteamLibrary\steamapps\common\Wild Bastards"
.venv\Scripts\python.exe games\wild-bastards\tools\build_plugin.py --game "C:\SteamLibrary\steamapps\common\Wild Bastards"
.venv\Scripts\python.exe games\wild-bastards\tools\install_local.py --game "C:\SteamLibrary\steamapps\common\Wild Bastards" [--restore]
```

`analyze.py` refreshes the review file, `work/analysis.json` and `work/ref-<lang>.json`;
`tools/ref.py <regex> [fr,it]` shows other languages next to EN (how dialogue speaker gender was set:
French and Italian). `install_local.py` keeps a receipt in `backups/wild-bastards/`.
`translations/structure.yaml`: 9 groups by I2 term category.

## Tests

- Vertical 0.1.1 **confirmed in game**: Polski button, menus, fonts.
- Full translation built and installed; playthrough pending: outlaw screen (aces, items, traits),
  sector map events (SME), planet map descriptions, dialogue on the Drifter. More in
  `docs/decisions.md`.
