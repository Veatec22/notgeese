# DEADBOLT: technical

Steam buildid 22449372, `C:\SteamLibrary\steamapps\common\DEADBOLT`. `deadbolt_game.exe`
3 832 320 B, FileVersion 1.0.0.87: standard GameMaker Studio 1.4 runner (imports `d3d9.dll`,
`dsound.dll`, `xinput1_3.dll`). `data.win` 4 130 572 B: GEN8 `deadbolt_game` 1.0.0.1749,
**bytecode 15, VM** (CODE 1543 entries), not YYC. `deadbolt_map_editor.exe`: out of scope.
Steam lists English only; no available Polish translation found (GrajPoPolsku 0 hits;
spolszczeniepl.com is a game repack). Russian: ZoG Forum Team 1.2 (replaces game files, incl.
textures, confirming text in graphics); older DiSTiNCT; no tools documented.

619 entries: STRG, 8 `dia_*.json`, 34 label operations on graphics (main menu, tutorial, "Back",
mission folder).

## Texts

1. **`dia_*.json` next to the exe** (8 files, ~26 KB): notes and conversations at folders, the
   fireplace (`dia_fp.json`: missions, verses) and safes. Read with `json_decode`.
2. **STRG in `data.win`**: 6329 strings, ~595 player-facing (menus, settings, controls, hints
   "E: OTWÓRZ DRZWI", objectives, mission names and descriptions, enemy nicknames, shouts,
   death tips, weapons, tape stories, credits).
3. `Stages/*.nc` headers repeat level names ("Noisy Neighbours" vs STRG "Noisy Neighbors");
   probably custom maps only.
4. **Text in graphics**: main menu (`sMain`, one 960×540 image), tutorial (`sTutorial`),
   mission folder (`sMissionFolder`), "Back".

Tags: `#` newline (GMS 1.x), `&y&`, `&r&`, `&b&`, `&w&`, `&dk&` color, `&!&` reset. Many
strings are glued in code (`"&y&'" + key + "'&!&: OPEN DOOR"`, `"You have died " + n + "
times..."`), so Polish must fit the pieces.

Keys in `en-pl-review.json`: `s<index>` (STRG string everywhere), `s<index>@<CODE entry>`
(only in that entry: the plugin moves that `push.s` operand to a free slot at the end of the
STRG list), `j:<file>/<path>` (dialogue; translated by text, so repeats get the same text).

Findings:
- `tools/strings_usage.py`: 177 logic-only strings, 52 mixed; among player-facing ones only
  "Controls" is mixed (Prefs.ini section and pause menu), hence `s222@gml_Object_oPause_Create_0`.
- `global.quest == "Stage cleared"` (oChangeRoom) compares with a separate string never shown;
  don't translate it.
- The interpreter computes a string on each `push.s` (`0x51a767`): base + entry + 4.

## Fonts

| font | face | size | range | Polish |
|---|---|---|---|---|
| fontTiny | NBP Informa FiveSix | 12 | 32–127 | none |
| fontSmall | Windows Command Prompt | 12 | 32–127 | none |
| fontMedium | Windows Command Prompt | 24 | 32–220 | only Ó (without acute) |

18 letters (fontMedium 16) composed from game glyphs + our pixel marks (`tools/fonts.py` →
`notgeese/fonts.txt`, preview `work/font-preview.png`). fontMedium = fontSmall ×2. New cells go
in free rows below the glyphs inside each font's atlas rect (46 / 28 / 96 px; fontSmall cells
1 px apart). Fonts have no „ ” or en dash.

## Plugin: `d3d9.dll` proxy patching `data.win` in memory

Game files on disk untouched. Proxy DLL like Heat Signature (MinHook, MSVC x86), but it patches
data before the runner parses it instead of hooking drawing.

Runner disassembly (1.0.0.87, no ASLR; addresses are evidence, **not used by the plugin**):
start (`0x5594c0`) reads the whole file into a heap buffer (`0x43f450`), pre-scans it
(`0x45a4b0`: requires `FORM.len == size − 8`, remembers base, GEN8, CODE and the STRG list),
then initializes graphics (`Direct3DCreate9`; `d3d9.dll` is a **delayed** import, so the proxy
loads only here), then parses chunks (`0x45a950`: FONT, TXTR, CODE, SPRT…). **The gap between
pre-scan and parse is our entry point.** All file pointers become `base + offset` in 32 bits,
so new data can live in our memory (offset = address − base mod 2³²). TXTR: PNG read to IEND.
FONT: glyph pointer list, **binary search** by char (`0x41b030`), miss = U+25AF; list must be
sorted; 512-byte tail untouched.

What the plugin does (`plugin/Plugin.cpp`):

1. At `Direct3DCreate9`, finds the buffer: scans all writable private regions for `FORM` +
   `GEN8` `deadbolt_game` with `FORM.len` = file length; STRG/FONT/TXTR/TPAG must equal the file,
   other chunk differences only logged. In game the runner has already rewritten **CODE (70 616
   bytes)**, so code (slots, `push.s` operands) is read from the file on disk and an operand in the
   buffer is changed only if it still points to the same string.
2. Fonts: new structures with Polish glyphs (sorted), texture pages decoded/re-encoded via WIC.
3. Labels on graphics (`tools/labels.py` → `notgeese/labels.txt`): erase old text pixels by color,
   fill, draw our 1-bit masks (rendered from similar faces, no font files shipped). A group draws
   only if the old pixel count matches the build (±10%); a changed graphic stays English.
4. Strings: STRG entries matched by English text point to our strings.
5. Dialogue: MinHook on `kernel32!CreateFileW` redirects `dia_*.json` to Polish copies generated
   into `notgeese/cache/`.
6. Log `notgeese/LogOutput.log`: plugin, PE and GEN8 versions, counts per step. Fonts first,
   strings only after fonts succeed; any error leaves the game English. No fixed addresses or checksums.

Rejected: `data.win` delta patch with applier (user doesn't want to give players an exe; fallback
only); redirecting `data.win` to a rebuilt file (needs a proxy loaded at process start;
`d3d9.dll` comes too late); swapping text at draw time (strings are glued from colored pieces).

## Build and test

```powershell
.venv\Scripts\python.exe games\deadbolt\tools\review.py --game "C:\SteamLibrary\steamapps\common\DEADBOLT"
.venv\Scripts\python.exe games\deadbolt\tools\build_plugin.py
.venv\Scripts\python.exe games\deadbolt\tools\test_plugin.py --game "C:\SteamLibrary\steamapps\common\DEADBOLT"
.venv\Scripts\python.exe games\deadbolt\tools\install.py --game "C:\SteamLibrary\steamapps\common\DEADBOLT" [--restore]
```

Needs MSVC x86 and MinHook 1.3.4 sources in `work/minhook-1.3.4`. `review.py` refreshes EN and
context and checks tags (tag parity, trailing spaces of appended strings, characters missing from
fonts, one translation per JSON value). `test_plugin.py` runs `tools/harness.cpp` (does what the
runner does: `data.win` in a heap buffer, then `Direct3DCreate9` from our DLL) and checks the dumped
state; `work/harness/render.png` is a render from dumped structures, not proof of in-game rendering.
`install.py` keeps a manifest in `backups/deadbolt/plugin/manifest.json`.
`inspect_game.py` re-creates the survey in `work/`.

## Tests

- First vertical in game: nothing translated (buffer search looked at the first 64 KB of a region
  and required the whole file byte-exact). Fixed; second vertical **works** (user, 2026-09-25):
  one candidate, buffer 0x30 after region start, only CODE differs.
- Full translation: `review.py` 0 problems, plugin test OK (460 STRG strings, all dialogue, 253 ms);
  installed locally. Full playthrough pending (see `docs/decisions.md`, Check in game).
