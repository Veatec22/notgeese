# The Hong Kong Massacre: technical

GOG `C:\Games\The Hong Kong Massacre`, game ID 1264181354, build 56046975430841034, changelog up to
1.0.3. Unity 2017.4.17 (Mono, x64), `THKM.exe`. English only (Steam lists English only). Full
`mscorlib` (`GetPEKind` present, 4 `AmbiguousMatchException` ctors): BepInEx 5 + Harmony viable.

Version: `bundleVersion` is "1.0"; GOG's changelog "1.0.3" lists what Steam released as patch 1.04
(2019-04-15: easy/hard, per-difficulty leaderboards, user rank, total kills on the results screen,
pause-menu controller fix), and the files contain those texts. Steam 1.04a (2019-04-21) only
tunes slow-motion depletion, no text; whether GOG has it is not verifiable from the files and
doesn't affect the translation.

Existing translations: none available found (2026-09-28). A 2021 gry-online.pl forum post names
NelsonPL as having made one; no download, page or release found. Russian fan translation exists
as a Steam guide (id 2977886354), not examined.

## Where texts live

No localization system in the game. Survey: `tools/inspect_game.py --game "<dir>"` →
`work/survey.json` (read-only).

- **Dialogue System (PixelCrushers) `DialogueDatabase`** "THKM" in `sharedassets50.assets`
  (path 367, Articy import): ~107 `Dialogue Text` lines, conversations `POLICE 01`–`05`
  (interrogation, level50) and `BAR c1`–`c5` (bar hub, level51). Second database
  "Level_Conversation" in `resources.assets` (4247): 27 older duplicate lines; which one is live
  is unverified. Actor names are displayed (`Name` label); `Menu Text` empty.
- **`UnityEngine.UI.Text`** in scenes/prefabs (legacy UGUI, no TMP text in use): 195 distinct
  `m_Text`, about 150 real labels (menus, options, pause, results, upgrades, tutorial prompts,
  chapter titles, dates); the rest is placeholders from asset-store samples.
- **`LevelItemData`** (`sharedassets0.assets`): ~30 levels with `LevelName` (chapter titles, film
  quotes/puns), `LevelNameLocation` (place + district), `LevelNameLocationChinesse` (keep),
  boss `SimpleName` (THE RAT, THE TIGER…).
- **`CutsceneTextIntroBase`** `_IntroTexts[].Text/DateText` (TODAY, FOUR DAYS EARLIER, "June 14,
  1992. HONG KONG"); `ConversationSettingBase.TimeDate`.
- **Rewired `LanguageData`** (`sharedassets1.assets`): ~55 control-mapper strings with `{0}`.
- **`LoadingScreenConfig.gameTips`**: 4 tips (the two `sceneInfos` are asset-store samples).
- **Hardcoded in `Assembly-CSharp`**: ~40 labels and prefixes (`BEST TIME: `, `DEATHS: `,
  `UNLOCK UPGRADE?`, `NO RECORD`, `SHOTS FIRED: `…) set via `Text.text`.
- Videos (`Cutscene01`–`08`, `IntroBusted`, `Intro_Logos`, H.264 + AAC): sampled every 2 s, no
  subtitles; only the title card and end credits ("MADE BY VRESKI", "MUSIC BY PROFESSOR KLIQ"),
  kept. Achievements are platform-side.

Estimate: ~450 entries.

## Fonts

| Font | Where | Missing Polish |
| --- | --- | --- |
| FjallaOne-Regular (dynamic, `sharedassets0` 108) | ~160 labels: menus, level titles, results | ą ć ę ś ź ż Ą Ć Ę Ś Ż |
| OstrichSans-Heavy (dynamic, `resources.assets` 876) | dialogue subtitles, name, HUD bits | ą ę Ą Ę „ … |
| Dosis-Medium (dynamic, `sharedassets2` 6) | loading-screen sample only | none |
| Arial (built-in) | Rewired control mapper | none (OS font) |

Unity fills missing glyphs of a dynamic font from a system font, so letters show but in another
face. Fix goes in the plugin (similar condensed font for the missing letters or whole labels);
decide from vertical screenshots. No font ships unless licensed and needed.

How code shows them (Cecil IL scan): level data, intro cards, weapon names and loading tips are
all assigned to `Text.text` as is (`LevelSelectionInfoDisplayBase.SetInfo`,
`CutsceneTextIntroBase.Start`, `WeaponItemDisplayInfoBase.UpdateDisplay`…), so data objects are
never modified (`ItemName` is also compared in `WeaponItemScreenLayoutBase`). Concatenations:
`LevelDataBaseUI.ShowLevelStats` ("DEATHS: " + n…), `WeaponItemUnlockConfirmBase.Show`
("UNLOCK " + name + "?"). `DOTweenAnimation` types text with `ShortcutExtensions46.DOText`.
The second database "Level_Conversation" is a prototype ("INSERTSOMETHING", other titles); not
translated. Two conversations are titled "Boss_5" with equal text: one key serves both.

## Plugin (`plugin/Plugin.cs`)

BepInEx 5.4.23.5 + Harmony, no game file replaced. `pl.tsv`: key, FNV-1a fingerprint of the
English letters/digits, text.

- `dlg/<conversation title>/<entry id>`: `Field` "Dialogue Text" set in every `DialogueDatabase`
  (prefix `DatabaseManager.Add` + pass after scene load); fingerprint mismatch keeps English and
  is counted in the log.
- `ui/<English>`: exact match in `Text.set_text` prefix, `Text.OnEnable` prefix (`m_Text`), a pass
  after scene load and the `DOText` end value. Surrounding whitespace is kept when only the
  trimmed text matches. Speaker labels (Police Officer…) go the same way.
- `fmt/<English with {0}>`: regex from the pattern; the inserted value is itself looked up
  (weapon names).
- `rewired/<field>`: `Rewired.UI.ControlMapper.LanguageData` fields set by reflection after
  scene load (format strings with `{0}` can't be matched at `set_text`).
- English-looking labels without a match are appended to `untranslated.txt` next to the DLL
  (diagnostics for the vertical).
- Fonts: `FjallaOne-Regular` and `OstrichSans-Heavy` get `fontNames` fallbacks "Bahnschrift
  SemiBold Condensed", "Bahnschrift Condensed", "Bahnschrift", "Arial Narrow", "Arial"; the log
  lists which of these Unity sees. Whether Unity takes only missing glyphs from them (intended)
  or the whole font is to be seen on screenshots.
- Logs game and Unity version and counts per scene.

## Build and test install

```powershell
.venv\Scripts\python.exe games\hong-kong-massacre\tools\extract.py --game "C:\Games\The Hong Kong Massacre"
.venv\Scripts\python.exe games\hong-kong-massacre\tools\build_plugin.py --game "C:\Games\The Hong Kong Massacre"
cd games\hong-kong-massacre\tools; ..\..\..\.venv\Scripts\python.exe install.py --game "C:\Games\The Hong Kong Massacre" [--restore]
```

`extract.py` merges into `translations/en-pl-review.json` keeping Polish by key. The build checks
placeholders and the tab count of `ui/` entries (tabs leave room for key icons) and refuses game
files in the ZIP. `install.py` keeps a manifest in `backups/hong-kong-massacre/plugin/` and removes
`BepInEx/` on restore if it wasn't there before.

## Tests

- 2026-09-28 vertical 0.1: 332/424 entries (all UI, patterns, control mapper, level titles,
  POLICE 01, BAR c1 01). Built, hook targets verified in the game assemblies with Cecil, installed
  locally. **Not tested in game yet.**
- 2026-09-28: user saw bad scaling on an ultrawide screen with the package installed; test install
  removed (`--restore`) to check whether the game does the same without it. The plugin touches
  no resolution, camera or canvas settings (only texts and font fallback names). User confirmed
  the same scaling without the package (game issue); package reinstalled. Cause in the files:
  `CanvasScaler`s are inconsistent: 1920×1080 `ScaleWithScreenSize` matched by width (0), height
  (1) or 0.5 side by side, plus `ConstantPixelSize` canvases (800×600 reference, no scaling) in
  the interrogation/bar scenes (level50/51) and some prefabs; one prefab uses 3000×1080. Anything
  but 1920×1080 moves canvases against each other. Known on Steam since 2019 (ultrawide cut off,
  3440×1440 unreadable; dev fix was deleting `HKCU\Software\VRESKI\The Hong Kong Massacre`).
  Test the translation at 1920×1080.
- 2026-09-28 full translation 424/424 at the user's request before the vertical was tested in
  game; report clean; built and installed locally. **Not tested in game yet.**
- Independent review done (see `docs/decisions.md`); `extract.py` now also reads Dropdown options
  → 429/429 entries. Rebuilt and reinstalled.
- 2026-09-28 published as 0.1 `testing` at the user's request (not yet played in game):
  `game.yaml` (`tested: structural`), cover and gallery from `tools/keyart.py`, ZIP in
  `site/public/pobierz/`. `translations/structure.yaml`: 7 groups by key prefix and context, 13
  sequences (conversations with more than one line) in Dialogue System link order, speakers from
  the Actor field; single-line boss taunts and street barks are a group, not sequences.
