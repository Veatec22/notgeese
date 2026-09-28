# Boomerang X: technical

## Summary

GOG build, Unity 2020.1.17f1. Delivered as a **delta patch** (plugin impossible, see below).
359 of 360 table rows (one key is duplicated). Two patches, both required:
`BOOMERANG X_Data/Managed/Assembly-CSharp.dll` (~14 KB) and `BOOMERANG X_Data/resources.assets`
fonts (<1 KB). Pinned originals:
`Assembly-CSharp.dll` `1c0ac29aad888faa7439ec57ea7da4976a74c6936aefd7b388a3e9fe904e0b40`,
`resources.assets` `f663c3c3ba23f7534572f35cf5e8e38fa30846a5d7203aba04b8eb69418dd247`.

## How the game stores text

No data file. All 360 rows are IL inside `SheetData.Init`, building an array of `Data` objects;
every row is the same instruction sequence, so `tools/table.py` reads the table by walking IL.
`Data` has `id`, `description`, `max_char_limit`, `asian_char_limit` and 11 language columns
(EN, EN source for Asian languages, FR, DE, ES, RU, PT-BR, JA, KO, ZH-T, ZH-S). The `language`
enum has 10 values + `LENGTH = 10`. Row `difficulty_select_prompt` appears twice with different
EN; both get the same Polish.

## Where Polish lives

A 12th column would mean inserting a field and renumbering metadata. Replacing French was
rejected (we want an 11th language). So Polish goes into **`description`**, the developer note:
written by `Data..ctor`, read by nothing (every method body scanned). Notes hold 55 843 chars vs
~18 000 needed; each is its own `#US` literal. A row that outgrows its note swaps notes with a
roomier row by swapping `ldstr` operands in `Init` (4 bytes each); `lend_room` does it (42 rows).
Every write is same-length over existing bytes: **file size never changes** (1 806 336 B).

Three code patches:

| Method | Change |
| --- | --- |
| `localization_manager.get_translation` | default arm returned `"LOCALIZATION ERROR"` (16 bytes at 383710) → `ldarg.1; ldfld Data::description; ret` + nops. Index 10 = Polish. |
| `font_manager.get_font` | default arm returned `null`; one `br.s` byte (270235) now points to the **Latin set** (same as English). |
| `options_screen.on_reading_save_complete` | two literal `10`s bounding the dropdown loops (372734, 372783) → 11. |

`menu_option` stores the choice as a plain int `language` with no clamp; those two loops are the
only literal-ten language counts in the assembly.

## Fonts

`font_set` slots: menu button, menu text, trick notification, arena title + background; loaded
by name via `Resources.Load`. Only the `beer money SDF` family has all Polish letters; `Sure Shot`
and `Dead Stock` have only `ł ó Ł Ó`; `Abys-Regular` (Russian buttons) has none and is caps-only.
The first attempt used the Russian set: Polish letters came out half-size from the `beer money`
fallback ("WYBóR"). Now Polish uses the Latin set (Dead Stock caps + small caps, own `ó ł`) and
`tools/fonts.py` adds `beer money SDF` (and the title layers) as TMP fallback to Dead Stock and
Sure Shot - title in `resources.assets`. A fallback is consulted only for missing glyphs, so
other languages don't change. If ą ę ś on buttons still look small: a separate beer-money copy
at ~1.5 scale for Dead Stock (can't scale the shared one).

## Why no plugin

Managed stripping: BepInEx preloader dies on `Module.GetPEKind`; `dll_search_path_override` with
full Unity 2020.1.17 libs hangs before the first screen. Our entry point (`tools/loader/`) got
past `GetPEKind` and past `System.Linq.IGrouping` (one library substituted), then hit the missing
`AmbiguousMatchException(string, Exception)` ctor that `HarmonyLib.AccessTools` needs. Whole
runtime is cut; see `AGENTS.md`.

## Build

```powershell
.venv\Scripts\python.exe games\boomerang-x\tools\build.py --source "backups\boomerang-x\BOOMERANG X_Data\Managed\Assembly-CSharp.dll"
.venv\Scripts\python.exe games\boomerang-x\tools\fonts.py --source backups\boomerang-x --managed "C:\Games\Boomerang X\BOOMERANG X_Data\Managed"
.venv\Scripts\python.exe tools\patch.py release --original "backups\boomerang-x\BOOMERANG X_Data\Managed\Assembly-CSharp.dll" --built "games\boomerang-x\dist\BOOMERANG X_Data\Managed\Assembly-CSharp.dll" --relative "BOOMERANG X_Data/Managed/Assembly-CSharp.dll" --original "backups\boomerang-x\BOOMERANG X_Data\resources.assets" --built "games\boomerang-x\dist\BOOMERANG X_Data\resources.assets" --relative "BOOMERANG X_Data/resources.assets" --readme games\boomerang-x\docs\INSTALL-patch.txt --out-dir games\boomerang-x\dist --game-name boomerang-x --package-name Boomerang-X --version <version>
```

`build.py` refuses anything but the original (use the backup of a patched game), asserts
unchanged size and reads every string back. `fonts.py` rewrites the 836 MB file once and checks
only the two fallback lists grew. `tools/review.py --source <original DLL>` refreshes EN and
context in `en-pl-review.json`, keeping Polish.

## Tests

- Vertical (38 rows) seen in game: 11th entry "Polski", Polish letters after the font fix.
- First full release on a clean game showed boxes: earlier tests ran on an already font-patched
  `resources.assets`. Hence two patches.
- Applier updates an older translation from the backed-up original (checked on 1.0 → 1.1).
- Full translation not played.

## Game material

Repo holds only translation text and tools. *Boomerang X* belongs to its authors; unaffiliated.
