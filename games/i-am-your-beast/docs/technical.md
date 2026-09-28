# I Am Your Beast: technical

GOG `C:\Games\I Am Your Beast`, game ID 1577997347, build 59479796167928060. Unity 2022.3.5f1,
Mono, x64; `bundleVersion` 0.1.0 (internal). Full `mscorlib` (`GetPEKind`, 4
`AmbiguousMatchException` ctors). `Assembly-CSharp.dll` and `AudioTextSynchronizer.dll` readable
with Cecil. Search for existing translations skipped at the user's request.

1581 entries: 684 Fleece, 853 scene segments, 44 TMP labels.

## Where texts live

- `resources.assets`: `Fleece.Story` "Sample" with 687 `Fleece.Passage` (684 with text): real UI,
  HUD, tutorial, enemy lines, names (the "Sample" name is misleading). Old Fleece CSV/JSON exports
  exist as TextAssets but the live `Passage` objects are the source.
- 44 `AudioTextSynchronizer.Core.PhraseAsset` with 870 `Timings` (story, tutorial, `CATCH`,
  `RELEASE`, `ENDING`, plus an unused `Example Cutscene No Text`). Each segment has its own `Text`,
  start/end, alignment, animation and color scheme. Support Group DLC scenes (`SCENE 1`–`9`,
  `FINAL CUTSCENE`, via `PLP_Cutscene_*`) have a full `Text` that looks like a buggy automatic
  transcript, but the game shows only segment texts, which are correct; those are translated.
  Speakers via color profiles BOB, IRIS, JODIE, KYLE, MARKUS, NATHAN, STEPHEN.
- TMP fields in scenes/prefabs: 1679 non-empty, 327 distinct; 44 are real fixed labels (`tmp/<en>`).

Survey: `tools/inspect_game.py --game "C:\Games\I Am Your Beast"` → `work/survey.json` (read-only;
resolve MonoScript from the standard MonoBehaviour header and explicitly loaded
`globalgamemanagers.assets`; the generated tree misreads `m_Script` endianness).

## Plugin

BepInEx 5 + Harmony, `plugin/Plugin.cs`. Three layers:

- **Fleece.** All reads go through `Passage.text` (`parsedText`, `Drawstring.Begin`,
  `Parser.InsertPassage`). The field is swapped once per object: prefixes on `get_parsedText` and
  `Drawstring.Begin`, postfixes on both `Story.Find`, plus a pass over
  `Resources.FindObjectsOfTypeAll<Passage>()` after scene load. Titles untouched
  (`Story.Find(string)` searches by title).
- **Dialogue scenes.** `CutsceneTextEffect` shows only `TextPart.Text` (= `Timing.Text`); the full
  `PhraseAsset.Text` is only used by `TimingsTextSplitConfig` (`IndexOf` after the previous segment)
  and word splitting. The plugin swaps segment texts and rebuilds `Text` from segments joined by
  `\n` so each is found in order (repeats included). Hooks: `TextSynchronizer.set_Timings`,
  `SplitWords`, `TextSplitConfigBase.Init`, `TextEffectBase.Init`. Growing sentences (short start,
  then repeated with more) are separate slides; the shared prefix is kept editorially. The original
  already has segments `IndexOf` misses ("Dear diary" vs "Dear Diary...") and the game copes.
- **Fixed TMP labels**: exact match in `TMP_Text.set_text` prefix, in both TMP classes' `Awake`
  (`m_text`) and after scene load.

Each Fleece entry and segment carries an FNV-1a fingerprint of the English letters/digits in
`pl.tsv`; a mismatch after a game update keeps English and is counted in the log. The plugin logs
game and Unity version and Polish-letter status per `TMP_FontAsset`
(`HasCharacters(..., tryAddCharacter: true)` adds them to the atlas immediately).

Fonts: source fonts in `sharedassets0.assets`, `octin college rg` and `LiberationSans`, both have
all Polish letters and „ ” — – … ’. Three dynamic Octin TMP variants (source font referenced,
no fallbacks) and LiberationSans (static + dynamic fallback) generate them at runtime.

Inserts to keep: `[KEY]`, `[WEAPON]`, `VALUE`, `[Quick Turn]` (HintManager replaces the bracket with
the action's key name, so the English action name stays), TMP tags. Build checks them.

## Build

```powershell
.venv\Scripts\python.exe games\i-am-your-beast\tools\build_plugin.py --game "C:\Games\I Am Your Beast"
.venv\Scripts\python.exe games\i-am-your-beast\tools\install_local.py --game "C:\Games\I Am Your Beast" [--restore]
```

Package ~680 KB: plugin, `pl.tsv`, readme, BepInEx + license (sources next to the package). The
build refuses archives with game files.

## Tests

- Vertical confirmed in game by the user (2026-09-25): "świetny efekt"; one note, I.T.O. with dots.
- Full translation after independent review, built and installed; full game not played.
