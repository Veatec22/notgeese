# Holy Shoot: technical

Steam app 2881660, build 24334618, `C:\SteamLibrary\steamapps\common\Holy Shoot`
(`DefaultGame.ini` says v.r.1.0.002). Unreal Engine 5.7 (`++UE5+Release-5.7` in the EXE).
Steam marks Polish unsupported; no available Polish or useful fan translation found.
1286/1286 entries (incl. placeholders and developer diagnostics).

## Format

`Windows/PVD/Content/Paks/PVD-Windows.pak`: format 12, unencrypted index, mount `../../../`,
4614 files, with IoStore `.utoc/.ucas` (texts don't need them). English
`PVD/Content/Localization/Game/en/Game.locres`: 108 883 B, format 3, 1286 entries.
`InternationalizationPreset=All`. Pak reader from SPRAWL (`games/sprawl/tools`) with format 12
allowed; decompression via a local FModel Oodle DLL (never shipped).

Fonts: BebasPro (Regular/Bold/BoldItalic) and Latin NotoSans (Regular/BoldItalic) all have
`ąćęłńóśźżĄĆĘŁŃÓŚŹŻ` (`.ufont` = 4-byte length header + OTF/TTF). Nothing to add; confirmed in game.

## Package (no game file replaced)

1. **`pakchunk99-notgeesePL_P.pak`** with one file `PVD/Content/Localization/Game/pl/Game.locres`
   (translated entries only; missing entries fall back to English, confirmed in game).
2. **Empty IoStore container** `pakchunk99-notgeesePL_P.utoc`/`.ucas` (202 and 64 B,
   `tools/iostore_empty.py`): without it UE 5.7 doesn't mount the pak (`FileExists` saw the game's
   `en/Game.locres` but not our `pl`). One chunk, empty container header (v5, zero packages); TOC v8
   layout copied from `PVD-Windows.utoc`; read back by the build. No compression, directory index,
   encryption or signature.
3. **UE4SS + `plugin/main.lua`** (+ `selector.lua`): adds Polski (code `pl`, index 10) to the
   templates menus are built from: the settings panel CDO `WB_T1_PVDSettingsMenu_C` ("Language
   Codes"), panel copies embedded in `WB_T1_PVDMainMenu` and `WB_T1_PVD_PauseMenu`, and the switcher
   template `WB_T1_OptionSwitcher_Language` ("Option Names"). Trigger: prehook on
   `UWidgetBlueprintLibrary::Create`; the later-loaded pause template is patched on a later call. The
   game itself saves the choice and switches culture (`SetCurrentLanguageAndLocale`, NiceSettings).

Lessons: `NotifyOnNewObject` on blueprint classes and `Construct`/`OnInitialized` hooks never fired;
patching a live menu is too late (the switcher sizes its indicator at creation, and a saved index 10
without a code gives "OPTION MISSING" and reverts to `en`); `-culture=pl` is not an install.

UE4SS **v3.0.1-1140-gf58e8f84**, MIT; runtime archive SHA-256
`b954f036b10e9abb0c0c41599311ab1accc53e30515aeed7e48ee22c5b3b1280`
([releases](https://github.com/UE4SS-RE/RE-UE4SS/releases),
[source](https://github.com/UE4SS-RE/RE-UE4SS/tree/f58e8f84)). Shipped: loader `dwmapi.dll` (the
game imports it), `UE4SS.dll`, settings with consoles off, license; no cheat/debug mods.

## Build

```powershell
.venv\Scripts\python.exe games\holy-shoot\tools\extract.py --pak "C:\SteamLibrary\steamapps\common\Holy Shoot\Windows\PVD\Content\Paks\PVD-Windows.pak" --oodle "<local oodle-data-shared.dll>"
.venv\Scripts\python.exe games\holy-shoot\tools\build.py
```

Checks the UE4SS runtime, locres, pak and IoStore round trips, review vs ids, placeholders, and a
12-file ZIP without game assets → `dist/Holy-Shoot-PL-<version>.zip`. `tools/test_selector.py`
(needs `lupa`) tests the Lua logic on stubs (not in game). `tools/batch.py` (`show`, `put`, `stats`)
handles translation batches in `work/tsv/`.

## Tests

- Vertical confirmed in game: Polski in the selector from start, kept after restart, pak texts
  shown; Polish letters in menus and settings. Full translation installed; full playthrough pending.
