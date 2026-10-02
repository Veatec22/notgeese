# Journey to the Savage Planet: technical

GOG build 54102244257232737 with the Hot Garbage DLC (`C:\Games\Journey to the Savage Planet`). No official or
available fan translation found (Steam language table: 12 languages, no Polish; GrajPoPolsku
has only a 2025 request thread).

## Engine and pak

Unreal Engine 4.21 (`++UE4+Release-4.21` in the exe), project `Towers`. One
`Towers/Content/Paks/Towers-WindowsNoEditor.pak`, 4.3 GB, **pak v7, index not encrypted**,
no `.sig`, entries zlib (method 1, relative block offsets) or raw. `tools/game_pak.py` reads
the index and extracts. The exe ships with its full `.pdb` (686 MB), so C++ functions can be
read by name (capstone + public symbols).

## Texts

`Towers/Content/Localization/Game/<culture>/Game.locres`, **locres v1**, English 5374 entries,
4002 unique strings, ~52k words (unique). Cultures: en, de-DE, es-ES, fr-CA, it-IT, ja, ko,
pt-BR, ru, zh-CN, zh-TW. `tools/locres.py` (from BPM, plus: empty strings written bare) re-dumps
every culture byte for byte.

Namespaces: unnamed (2780, UI and blueprint texts, many debug/placeholder), `ScannableInfoDataTable`
(1188, scan encyclopedia), `VoiceOverDataTable` (637, subtitles incl. timed video subtitles
`<00:04.337>line`), `CreditsDataTable` (439), `QuestInfosDataTable`, `AchievementsDataTable`,
spawn point names, network/profile messages. Markup: `<mm:ss.fff>` timing, `{name}` arguments,
`<action id="Jump"/>` input icons. `Localization/Untold` (2 strings, store login messages).
Engine.locres has no Polish (engine strings fall back to English).

## Fonts

UI font `UI/Fonts/TacticSans` (composite; Reg, Med, ExtExd-Blk faces, ©2016 Richard Miller) has
all 18 Polish letters. CJK faces (SourceHanSansJP, NanumGothic) are per-culture fallbacks.

## Language selection

C++ `UTowersGameUserSettings` (read from the exe):

- `GetCultures` returns a static array of 11 `FTowersCulture {Code, NativeDisplayName}`
  (en, fr-CA, es-ES, de-DE, it-IT, pt-BR, ru, ja, ko, zh-TW, zh-CN), wide literals in the exe.
  The options menu (`BPW_Menu_Options_Gameplay`: Spoken Language, Subtitles Language) lists these.
- `FTowersSaveProfileSettings` ctor: `SubtitlesLanguageOverride` = first of the current culture's
  prioritized names that is in the list, **else empty**. Spoken = fr-CA if culture is fr, else en-US
  (voice is only English/French).
- `ApplyProfileSettings` calls `FInternationalization::SetCurrentLanguageAndLocale(SubtitlesLanguageOverride)`;
  with an empty string no culture exists, so the engine keeps the startup culture.

- `BPW_Menu_Options_Gameplay` (the only blueprint calling `SetSubtitlesLanguageOverride`;
  bytecode read with a 4.21 variant of BPM's `kismet.py`): `UpdateSettingsHandler` does
  `Slider_SubtitlesLanguage.SetValue(GetCultureIndex(override))`; the slider's OnValueChanged
  sets `override = GetCultures()[floor(value)].Code`. An unknown culture gives -1, the slider
  lands on 0 and saves `en`. This runs at startup without opening the options.
- The profile lives in `%LOCALAPPDATA%\Towers\Saved\SaveGames\PlayerProfile.sav` (GVAS,
  `SubtitlesLanguageOverride` StrProperty).
- Menu labels are `Conv_StringToText(NativeDisplayName)` from exe literals; no string table.

**Consequence:** a new `pl` culture works only until the options widget initializes (probe 1:
title screen Polish, then English; saved `en`). Polish must take one of the 11 slots, and the
label "Polski" needs the exe literal changed. User choice: a less popular Latin slot, not English;
selector must read "Polski". Italian: Latin, TacticSans, no Engine.locres of its own.
`"Italiano"` occurs once in the exe (UTF-16 at file offset `0x296F810`), 8 chars → "Polski"
fits in place.

## Probes (diagnostic, 2026-09-29)

1. `pl/Game.locres` with 2519 plain UI strings prefixed `ĄŁ `: **user test**: "ĄŁ Press ... ĄŁ to
   start" on the title screen with correct glyphs, English everywhere after. Explained above.
2. `tools/build_probe.py <game>` → `dist/probe/`: same marked strings in `it-IT/Game.locres`
   (overlay pak shadows the game's Italian file) + GOG exe (SHA-256 `b0ee2d93…bc1a`) with
   "Italiano" → "Polski". Installed with `tools/install.py` (exe backup in
   `backups/journey-to-the-savage-planet/`), pak copied. **User test 2026-09-29: passed**
   ("Polski" in the selector, marked strings, kept after restart).

## Delivery

Polish is a **12th culture** (`pl`), all game languages stay:

- Overlay pak with a new `Localization/Game/pl/Game.locres` (ours only; no game file shadowed).
- Delta patch of the exe (`tools/exe_patch.py`, 166 own bytes): the culture list initializer
  (RVA `0xF3FF0`, 11 unrolled `{Code, NativeDisplayName}` pairs) gets `Num`/`ResizeForCopy` 11 → 12;
  the instruction after its copy loop (`0xF44F5`) jumps to a cave in int3 padding (`0x9C710`,
  148 bytes, no .pdata entry) that fills slot 12 with `{"pl", "Polski"}` (FMemory::Malloc +
  memcpy, freed by the array's own destructor at exit), replays the displaced `lea r9` and jumps
  back. RIP-relative only, no relocations. Verified by disassembly of the built exe.
- With `pl` in the list, the profile default (current culture's prioritized names) resolves to
  `pl` on a Polish Windows, so a new profile starts in Polish.

The exe patch is required: without it the options widget resets any non-listed culture to `en`.
Rejected: Polish in the Italian slot (earlier build; pak worked alone under "Italiano", exe patch
only renamed the label). The user preferred that the exe change buy a separate language.

## Tools and build

```powershell
.venv\Scripts\python.exe games\journey-to-the-savage-planet\tools\extract.py "C:\Games\Journey to the Savage Planet"
.venv\Scripts\python.exe games\journey-to-the-savage-planet\tools\key_sources.py "C:\Games\Journey to the Savage Planet"
.venv\Scripts\python.exe games\journey-to-the-savage-planet\tools\build.py "C:\Games\Journey to the Savage Planet" [version]
```

- `game_pak.py` pak v7 reader; `pak.py` v7 writer (uncompressed, read-back check); `locres.py` v1.
- `extract.py`: all cultures' locres to `work/extract`, `work/ref-<culture>.json`, creates or checks
  `translations/en-pl-review.json` (context = defining assets from `work/key-sources.json`).
- `key_sources.py`: scans all 26k assets for GUID keys (2499 located) → `work/key-sources.json`.
- `apply_batch.py`: writes `{"<namespace>|<key>": pl}` batches into the review file; `--by-english`
  fills every untranslated entry with a given English text.
- `build.py`: pins en locres (`71b0a06c…`) and GOG exe (`b0ee2d93…`); checks `<action…/>`,
  `{args}` and timecodes; locres read-back with the English hashes; pak read-back; exe patch
  (`exe_patch.py`, checks every original byte it touches) rebuilt and verified by `patch.build`;
  ZIP refuses game assets.
  Output `dist/Journey-to-the-Savage-Planet-PL-<v>.zip`: pak at `Towers/Content/Paks/`, `.patch`,
  applier `.exe`, `READ-ME.txt`.
- `build_probe.py`: the diagnostic Italian-slot probe (not a release).

## Vertical (2026-09-29)

1186 entries (897 translated, 289 kept: debug, placeholders, numbers, key names): main menu,
save slots and game modes, options (all tabs), pause menu, HUD, journal, crafting UI, KindredOS
desktop, intro computer report, quests 100–105, tutorials and hints, all craftable items,
interactions, resources, first EKO lines (intro, Javelin scan, first scans, respawn), Tweed welcome
videos, first Kindred email, Pufferbird scan. Installed like a player: ZIP contents + applier
(backup `Towers-Win64-Shipping.exe.przed-spolszczeniem`). **User test 2026-09-29 (12th-language
build): works** ("Polski" as a separate language, vertical texts in game). Next: full translation.

## Full translation and release (2026-09-29, packaged 2026-10-02)

All 5374 entries settled (see `docs/decisions.md`). Package 0.1 rebuilt from the final file
(ZIP 359 235 B), published to `site/public/pobierz/`, catalog status `testing`. File
verification only for the full text; in game only the vertical is confirmed.
Next: in-game test of the full text, independent review (`localization-review`).
