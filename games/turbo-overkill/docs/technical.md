# Turbo Overkill: technical

GOG buildId 58328218944594138 (menu 1.0), Unity 2021.3.11f1 **IL2CPP x64**. 2316/2316 entries
translated (17 more of the game's 2333 have an empty original and are skipped, the game shows empty text as in
EN). Delivered as a **BepInEx 6.0.0-pre.2 Unity.IL2CPP plugin** adding a separate "Polski" language
and flag; tables are built in memory, no game asset replaced.

## Existing translations

No available Polish found (Polish and English searches, Graj po polsku); Steam lists Polish as
unsupported. No useful fan pipeline (Portuguese, Turkish, Korean searched; local Turkish tables are
part of the install). Existing mods of this game confirm BepInEx 6 IL2CPP x64 works:
[Enhanced Graphics and UI](https://www.nexusmods.com/turbooverkill/mods/3),
[Ammo regen](https://www.nexusmods.com/turbooverkill/mods/4); developer thread on localization and
`-language=en`: [Steam](https://steamcommunity.com/app/1328350/discussions/0/5590708606426106672/).

## Game

- `GameAssembly.dll` + `il2cpp_data/Metadata/global-metadata.dat` (metadata v29), no `Managed`: the
  Mono stripping checks don't apply; the Unity.IL2CPP BepInEx build is needed.
- Unity Localization + Addressables 1.19.19, Unity.TextMeshPro. `data.unity3d` ~5.35 GB, never
  rewritten or shipped.

## Texts

In `Turbo Overkill_Data/StreamingAssets/aa/StandaloneWindows64/`: English bundle 90 120 B, shared data
30 933 B, locales 2800 B. Tables en, fr, de, ru, zh, es, tr; no pl.

| Table | Entries | EN chars |
| --- | ---: | ---: |
| TurboVoices | 606 | 37 943 |
| TurboGame | 195 | 2849 |
| TurboStrings | 682 | 17 033 |
| TurboCodex | 66 | 8672 |
| TurboBestiary | 79 | 4323 |
| TurboItems | 261 | 10 023 |
| TurboEx1 | 339 | 7227 |
| TurboIndodex2 | 105 | 49 089 |
| **Total** | **2333** | **137 159** |

Review key = collection GUID + entry ID, with `table`, `term`, `entry_id` fields (no cross-table
collisions); `context` = "table: term". Don't normalize text keys (e.g. `menu_campaign` has a tab).
All eight tables round-trip through typetree byte-identically. Keep `[input:...]`, `{val}`, TMP tags,
formatting. The Superior Maw entry in TurboStrings has a literal `\n` as text; PL does the same.

## Plugin (`plugin/Plugin.cs`)

- Interop generated offline from the local GameAssembly and metadata (Cpp2IL +
  Il2CppInteropGenerator shipped with this BepInEx; reads PE files, runs no game code). The player's
  first start generates their own interop; ours isn't shipped.
- After init the plugin loads the eight English tables async and makes in-memory copies with
  LocaleIdentifier `pl`, changing only entries in `pl.json` (built from
  `translations/en-pl-review.json`); missing stay English, count logged. Native SmartString format and
  metadata kept; checks the copy doesn't share modified entry data with EN; keeps EN operations
  referenced (SharedTableData must stay loaded).
- `RegisterTableOperation` registers copies by name and GUID; Harmony prefix on
  `LocalizationSettings.GetInitializationOperation` rebuilds the cache after a language change before
  UI is notified; locale falls back to EN. On mismatch: log, remove own patches, try EN. No checksums.
- **Crash 0.1:** two WER dumps read offline (ClrMD 2.2.332302 with runtime 6.0.7 DAC): access
  violation in coreclr +0x1d1fdd, `ExecutionEngineException` in
  `Il2CppSystem.Collections.Generic.Dictionary<...>.ContainsKey` on a
  `ValueTuple<LocaleIdentifier,string>` key through the IL2CPP generic wrapper. Fix: no dictionary read
  in the plugin; native `RegisterTableOperation` makes and checks keys; re-registration guarded by a
  flag reset before `SendLocaleChangedEvents`.
- **Selector:** `UiLanguageSelector` with `SetLanguage_English/Chinese/French/German/Spanish/Russian/
  Turkish`; level1 has seven UGUI Buttons with persistent SetLanguage_* listeners in an 800-unit
  vertical panel. The plugin clones the English button, gives it a **new** onClick (drops the copied
  persistent listener), label "Polski" and its own 32×20 generated flag, lays out eight buttons in the
  panel with automatic navigation. No original language taken. Click runs native English first (panel
  closing, safe state if the plugin is removed), then selects `pl`. Own PlayerPrefs
  `notgeese.TurboOverkill.Locale` stores the choice. 0.1.1 bug: `GetPersistentMethodName` →
  `NotSupportedException: Method unstripping failed`; now reads
  `m_PersistentCalls.m_Calls[i].m_MethodName` directly (Mono.Cecil call-chain check: zero stubs in 150
  methods).
- **Fonts:** Oxanium, Russo One, Roboto, TheNeue have full Polish; Disket Mono, ZeF RAVE, part of
  TapeFont don't. Menus use UGUI Text (Legacy). `HasCharacter` may count system fonts and miss gaps,
  so for Polish whole texts in the limited fonts (Disket, ZeF RAVE, TapeFont High/LowQuality) switch
  to the game's Oxanium-Regular (Arial fallback), also texts without diacritics for consistency;
  Disket keeps caps via `ToUpperInvariant` (skipping tags, bracket tokens, placeholders). Restored on
  leaving Polish. No font shipped.
- Package: the whole official BepInEx (files byte-identical to the official archive) with LICENSE,
  source next to the ZIP, .NET runtime license and third-party notices (commit
  `0ec02c8c96e2eda06dc5b5edfdbdba0f36415082`, from coreclr.dll); `BepInEx/config/BepInEx.cfg` with
  the console off and file log on. No assets, interop, dummy assemblies or Unity base libraries.

## Build

```powershell
.venv\Scripts\python.exe games\turbo-overkill\tools\analyze.py --game "C:\Games\Turbo Overkill"
.venv\Scripts\python.exe games\turbo-overkill\tools\prepare_interop.py
.venv\Scripts\python.exe games\turbo-overkill\tools\build_plugin.py
.venv\Scripts\python.exe games\turbo-overkill\tools\install_local.py --game "C:\Games\Turbo Overkill" [--restore]
```

`analyze.py` keeps existing PL on re-extraction. Interop needs unpacked
`vendor/bepinex/il2cpp-pre2` and Unity base libraries from
`https://unity.bepinex.dev/libraries/2021.3.11.zip` in `work/unity-libs`; compiler Roslyn from VS
2022, the offline generator uses the installed dotnet host (`tools/GenerateInterop.cs`). The build
checks review sync, `[input:...]`, `{val}`, tags and newline counts; exception: four
dialogue-recordings in TurboIndodex2 (Jazz, Exec/Jazz, Ripper/Exec, Exec/Doc) where the source breaks
lines by hand with an indent and PL joins them (the field wraps). Strict ZIP allowlist, CRC and all
234 members compared. `install_local.py` records added files in
`backups/turbo-overkill/install-receipt.json`, refuses to overwrite a foreign loader, and on
`--restore` removes only files still matching their hashes. `translations/structure.yaml`: 12 groups
by "table: term".

## Tests

- Vertical 0.1.3 **confirmed in game**: selector, Polish menu, fonts (Oxanium replacing Disket).
- Full translation built and installed; campaign subtitles (length), infodex recordings and bestiary
  (paragraphs, scrolling), augment and weapon shop await the test. On problems: `BepInEx/LogOutput.log`
  and a screenshot.
