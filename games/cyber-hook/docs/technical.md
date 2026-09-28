# Cyber Hook: technical

GOG 1.2.1, build `55931336877424935`, `C:\Games\CyberHook_GOG`. Unity 2019.4.28f1, Mono, x64.
Game code in `GlobalAssembly.dll` (asmdef), not `Assembly-CSharp.dll`. Full `mscorlib`
(`GetPEKind`, 4 `AmbiguousMatchException` ctors): BepInEx 5 + Harmony start. Officially EN, FR,
DE, ES, RU, PT-BR, ZH (JP in files); no available Polish or other fan translation (2026-09-23).
Assets: `data.unity3d` (whole build, 104 MB) + `Assetbundles/` (fonts, dialogue, UI, levels).
Audio FMOD, no voice acting.

702 entries: 686 CSV + 16 tutorial lines whose key is English text
(`translations/raw-keys.json`). Three DLC keys (`dialog_dlc_boss_intro_01_00`, `01_01`, `02_00`)
have no CSV row in any language: the game shows the key even in English; not translated.

## How the game stores text

- Each language is a `Language_SO` with a TextAsset CSV `CyberHook <Language>` in `data.unity3d`
  (`sharedassets1.assets`): `KEY,VALUE,DETAILS`, CRLF. DETAILS is usually the French equivalent.
- `Language_SO.ParseLanguageFile`: split on `Environment.NewLine`, commas outside quotes, strip edge
  `"`, `""` → `"`, `Trim()`, lower-case keys. An unquoted comma truncates text (the game shows just
  "Hey" for `dialog_ending_credits_00_00`). Our texts bypass the CSV, so these get fixed.
- Everything goes through `Language_SO.GetTranslatedKey`/`KeyExists`: `StringParser` (UI),
  `TranslatedString` (dialogue, `{0}`), `SO_Level` (level names), `OptionField_Enum`
  (`option_<enum value>`). Almost nothing hard-coded.
- Dialogue: `DialogLine.LineTextKeys[].TextKey` in bundles `dialogs/*`, `story/*`.
  `Tutorial_Line_04_00` and `_04_01` carry English text (with trailing spaces) instead of a key.
- Tags: TMP (`<color>`, `<size>`, `<sprite name="Jump">`, `<br>`) and own `<link="Pause(1)">`,
  `<link="EventTrigger(...)">` driving dialogue. The build compares them with the original.
- Language choice: enum `OptionEnums.AvailableLanguages` (en, fr, es, de, ru, zh, pt, jp) saved in
  `GameData`; no new value without code changes.

## Plugin

BepInEx 5.4.23.5, `plugin/Plugin.cs`:

- `Language_SO.GetTranslatedKey` prefix, `KeyExists` postfix: when the English `Language_SO` is asked
  and `en` is active, answer from `pl.tsv` (other languages ask English as fallback → English stays).
  Raw-text keys we translated count as existing.
- `option_en` → "Polski": Polish takes English's place in the language list.
- `ParseLanguageFile` postfix logs untranslated game keys; startup logs plugin, game, Unity versions.
- `DialogTextDisplay.Init` gets a top margin of 0.25 font size so the window's `Mask` doesn't clip
  marks over Ś, Ć, Ż.

Fonts (`plugin/PolishGlyphs.cs`, ported from Void Bastards to TMP 2.x): game SDF atlases have only
ó/Ó (some); source TTFs in the `fonts` bundle don't help (Equalize, Neon Overdrive, Square: none;
Blockletter: no ś/Ś). For each `TMP_FontAsset` lacking letters the plugin builds a small fallback
atlas from the font's own base letter + a drawn mark and puts it first in
`fallbackFontAssetTable`. Triggers: `TMP_FontAsset.Awake` flags a font; composing happens before
the next text translation, after a language change and after scene load; only while `en` is active.
Before composing, `characterLookupTable` is touched (fills glyphs of fonts not yet shown); dynamic
fonts first add base letters (`TryAddCharacters`); fonts without an atlas yet are retried. Marks fit
under `faceInfo.ascentLine`, compressed when short (min 1.3 stroke), max 1/5 of letter height.
English `CustomFonts`: Equalize SDF, Lucida console SDF, Blockletter SDF Squared, Neon Overdrive SDF.

## Build

```powershell
.venv\Scripts\python.exe games\cyber-hook\tools\extract.py --game "C:\Games\CyberHook_GOG"
.venv\Scripts\python.exe games\cyber-hook\tools\build_plugin.py --game "C:\Games\CyberHook_GOG"
.venv\Scripts\python.exe games\cyber-hook\tools\review.py
.venv\Scripts\python.exe games\cyber-hook\tools\install_local.py --game "C:\Games\CyberHook_GOG" [--restore]
```

`extract.py` reads raw TextAsset bytes (UnityPy drops `\r`) → `work/source/<lang>.json` (reference
for translator and build). `build_plugin.py` checks keys and inserts, compiles (Roslyn `csc` from
VS 2022), writes `dist/Cyber-Hook-PL-<version>.zip` (~660 KB, ~40 KB ours); refuses archives with
`CyberHook_Data`, `.assets`, `.unity3d`, `.bank`. `install_local.py` installs with a receipt in
`backups/cyber-hook` and removes exactly those files.

## Tests

- First vertical: boxes in the intro terminal (`Fixedsys SDF`: a font not yet shown has empty
  glyphs, the plugin gave up on it) and Dron's acute clipped by the dialogue mask. Fixed (see above);
  second vertical confirmed in game: menu, options, intro and tutorial.
- Full translation built and installed; later worlds, ending and DLC not played.
