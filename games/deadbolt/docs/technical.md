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

## Local ultrawide prototype (2026-10-03)

User requests 32:9 support (5120x1440 screenshot). No available ultrawide fix found online.
`plugin/Ultrawide.h` is opt-in via `notgeese/ultrawide.ini`; ordinary PL builds stay disabled.
Entry point is the existing pre-parse memory patch. Camera/viewport widths in 12 enabled ROOM
views become 1920; heights remain 540. The dynamic mission camera is created by
`gml_Object_oLoadRoom_Other_10`: two 960 constants in `room_set_view` become 1920.
`gml_Script_init_screen` has fixed `iw=960, ih=540`; iw also becomes 1920 so the magnification
surface and final scaling retain the new aspect ratio. Named entries and instruction patterns
are checked; the complete plan is validated before any QoL write. No file checksum or runner
address is used. Changed layouts/operands disable QoL with a log line.

ROOM/View serialization source:
https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Models/UndertaleRoom.cs

Lighting creates its surface from view_wview/view_hview; mouse mapping also reads those
variables. Their bytecode is unchanged. Not yet verified: runtime surface drawing, aim,
menus (some artwork/positions use fixed coordinates), small-room framing. Camera clamp uses
room_width - view_wview; a room narrower than the widened view can produce a negative upper
bound. First prototype leaves that code unchanged; inspect small maps before accepting it.

Build: `.venv/Scripts/python.exe games/deadbolt/tools/build_qol.py`.
Test: `.venv/Scripts/python.exe games/deadbolt/tools/test_plugin.py --game
C:/SteamLibrary/steamapps/common/DEADBOLT --dist games/deadbolt/dist/ultrawide --ultrawide-width 1920`.
Install/restore: `games/deadbolt/tools/install_qol.py [--restore]` with repo Python.
ZIP: `dist/Deadbolt-ultrawide-prototype-1.zip`, local only; own plugin/text/config, no game assets.

Harness passes with QoL disabled and at 1920: all 12 room views and 3 constants verified;
other ROOM bytes, lighting creation/recreation and mouse mapping unchanged; PL checks pass.
Installed locally with `backups/deadbolt-qol/ultrawide-v1/`; restore then reinstall passed.
Publisher exe, data.win and dia JSON hashes unchanged. Old local translation lives in NieGesi;
the prototype uses current notgeese files and leaves the old folder intact for restoration.
No game launched. Next: user screenshot of the same mission, aiming near both edges, pause,
menu, and a room transition at fullscreen 5120x1440. In-game outcome pending.

User test of the first prototype: FAILED. Side bars remained; world and HUD were compressed
horizontally. Runtime log confirms all 12 views and 3 code constants were applied.
Earlier memory-only verification missed the runner's cached output dimensions.

Runner disassembly shows GEN8 pre-scan copies DefaultWindowWidth/Height (+0x3c/+0x40)
into default window and application-surface globals before Direct3DCreate9 loads our DLL.
Later surface creation and presentation read those globals. Evidence addresses (not bindings):
stores at 0x45a756; default width 0x74e68c, application width 0x750918; reads at 0x4563bf
(surface creation), 0x42fcdf (presentation) and 0x454fc5 (coordinate scaling).

Revised prototype: locate the five GEN8 store instructions in executable PE sections, require
one match, require destinations in writable image sections and original width/height/flags;
then update the two cached widths plus GEN8 width alongside the previous plan. Heights and
aspect flags remain unchanged. Unknown code/state disables the complete QoL plan.
The real installed executable has exactly one valid signature; no hard-coded addresses.

Harness now replays the actual pre-scan instruction sequence with relocated globals before
DLL loading. Old DLL fails: `Runner output still has old aspect: [960, 540, 960, 540]`.
Revised DLL passes at 1920 and disabled at 960, including all PL checks. This validates cached
dimensions and memory writes, not actual D3D presentation. Revised DLL installed; original
pre-QoL backup preserved, publisher files unchanged. Next: user fullscreen screenshot;
confirm proportions and side bars before claiming the issue fixed.

User confirms revised gameplay renders correctly at 32:9. Main menu artwork remained at
the left; load-save drawing centered but hover activation was displaced left.
`oLoadGame_Draw_0` places the list using view_wview/2, while its hit test uses hard-coded
x=530. Widening that menu camera broke the shared drawing/input coordinate system.

Current revision keeps eight front-end room cameras/viewport sizes at original 960x540
and shifts their viewport PortX to (outputWidth-960)/2. Their view-space drawing and input
coordinates remain original. rInit, rm_apt, rm_dock and rm_pause retain wide cameras;
dynamic mission camera remains wide. Application output/scaling remains 1920x540.
This avoids changing individual menu drawing and hit-test constants. Native mouse mapping
and manual scaling-surface rendering through the offset viewport require user confirmation;
the harness checks stored viewport geometry, not live input or final presentation.

Charon headings are `sUpgradeWeapon` frames 0/1/2, texture text omitted from earlier labels.
Added color erase/mask recipes in `tools/labels.py`: ULEPSZ BROŃ, GŁÓWNA, DODATKOWA.
All three before/after previews inspected; masks fit the plates and game pixels are not shipped.
Harness: enabled and disabled pass, 18 labels, all 10 affected sprite frames match recipes,
PL regression checks pass. Installed with original pre-QoL backup preserved; previously
confirmed gameplay DLL/config/label recipe additionally saved in
`backups/deadbolt-qol/ultrawide-gameplay-confirmed/` before this revision.
Next user checks: centered main menu, load-save hover/click under the pointer, settings/back,
pause/resume, Charon's three headings and a gameplay screenshot after returning from menus.

User test of centered viewport revision: FAILED. Menu image became horizontally stretched
and moved to the right; load title/list clipped off screen. The custom scaling/presentation
path does not preserve the assumed viewport offset. Geometry-only test was insufficient.

Current fix removes all PortX edits and restores the confirmed 1920x540 camera/viewport path
in every room. Main menu Draw reads of view_xview become the centered artwork origin
(outputWidth-960)/2; its view_wview reads become 960. This moves drawing and the computed tx
used for mouse rectangles together. Each 16-byte array read becomes push.double + conv to
variant, preserving bytecode size and stack effect. Disk VARI chains identify sites; runner
reference operands may already be rewritten, but the three original instruction headers are
validated. Exactly nine main-menu reads must match before the complete plan is applied.
Load-save Draw keeps its already correct wide-camera drawing; the sole hard-coded mouse
hit center 530 becomes 530+(outputWidth-960)/2. Exactly one pattern must match.

Harness verifies actual replacement double/conversion instructions, original zero PortX,
wide views, load draw/hit relative geometry, cached output sizes and all 18 labels.
Enabled and disabled tests pass. Revised DLL installed; gameplay and Charon label corrections
retained. Next: user screenshots and hover/click tests of main and load-save menus. No live
D3D presentation or input verification by the harness; do not claim in-game confirmation.

## Confirmed checkpoint (2026-10-03)

User confirms the latest revision works "idealnie" and accepts it as a working checkpoint.
32:9 gameplay, main-menu placement and load-save interaction accepted in game. Further
gameplay testing remains pending; this is not a full-playthrough verdict or a ready release.
Checkpoint at `backups/deadbolt-qol/checkpoint-2026-10-03/`: exact installed files, separate
`Deadbolt-ultrawide-checkpoint-2026-10-03.zip`, implementation sources, SHA-256 manifest.
Installed files verified byte-identical to the built ZIP before snapshotting. Preserve this
checkpoint before further changes. No runtime change in this checkpoint-recording pass.
Next: user continues gameplay; investigate only reported regressions (other screens,
small-room camera bounds, lighting, aiming, transitions). Previous pending menu checks above
are superseded by this user confirmation. Full translation playthrough remains pending.

2026-10-04: user reports untranslated purchase notification "NEW WEAPON". Confirmed texture
in `sNewWeapon` frame 0 (170x96 source rect). Added NOWA BROŃ erase/mask recipe; only the
upper heading changes, lower dynamic-name plate untouched. Before/after preview inspected.
Rebuilt label recipe and local QoL ZIP using the unchanged checkpoint DLL; all other package
files verified identical to installed files. Harness passes: 19 labels, 11 sprite frames,
PL and camera checks. Installed with existing backup; publisher files unchanged. Checkpoint
snapshot preserved. Next in-game check: buy a weapon and confirm NOWA BROŃ appears and the
weapon name still displays below it. No game launched; purchase rendering confirmation pending.

## Translation release 0.2 (2026-10-04)

Added texture-label recipes for Charon's sUpgradeWeapon frames 0/1/2:
ULEPSZ BROŃ, GŁÓWNA, DODATKOWA; sNewWeapon frame 0: NOWA BROŃ.
The lower dynamic weapon-name plate is unchanged. Recipes erase matching colors and
draw our masks in memory; no publisher textures are shipped. Source frames and previews
were inspected during local correction work. The release contains translation only.
Build and no-game harness verification cover all 19 label recipes and 11 sprite frames,
STRG, Polish glyphs and redirected dialogue. ZIP published in site/public/pobierz.
These are file/memory checks; purchase notification rendering and full playthrough remain
pending. Next: buy a weapon, confirm NOWA BROŃ and the weapon name below; check Charon's
three headings. No game was launched or installed for this release.

## PL 0.3 + Ultrawide mod 1.0.0 (2026-10-14)

One d3d9.dll (plugin 0.3), two independent features switched on by their files:
translation needs `notgeese/pl.tsv` + `fonts.txt`, ultrawide needs `ultrawide/settings.ini`
with `Enabled=1` (user: mod files must not live in a folder named notgeese). Log goes to
`notgeese/LogOutput.log` when PL files exist, else `ultrawide/LogOutput.log`; no folder or log
when neither feature is on. Without translation files the DLL finds data.win, applies ultrawide and
returns ("translation off, ultrawide only"); with neither it does nothing. Init order and the
ultrawide code (`plugin/Ultrawide.h`, the user-confirmed 2026-10-03 checkpoint) are unchanged.
`mods/ultrawide/tools/release.py` runs `tools/build_plugin.py` (PL 0.3 ZIP, unchanged
translation) and builds `Deadbolt-Ultrawide-1.0.0.zip` (d3d9.dll, `ultrawide/settings.ini` with
`VirtualWidth=0` = main display aspect, MIT and MinHook licenses, English readme); asserts
identical DLLs, no `ultrawide/` in the PL ZIP and no `notgeese/` in the mod ZIP; copies both to site/public/pobierz. Either ZIP can
be extracted alone or over the other. PL 0.2 DLL had no ultrawide, hence the 0.3 bump.
No-game harness (`tools/test_plugin.py`, new `--no-translation`): PL only, PL + 1920,
ultrawide-only 1920 and 1280 all pass; ultrawide-only leaves every string, font and label
untouched. User confirmed the mod in game (32:9, before the folder rename). 21:9 untested in game.
`tools/build_qol.py` (prototype ZIP) removed; `tools/install_qol.py` still restores the
2026-10-03 local install from `backups/deadbolt-qol/`.
Nexus images: `mods/ultrawide/tools/art.py --art <16:9 key art>` brings the art back to native
320x180 (box filter), scales by whole numbers only and sets "ULTRAWIDE" in the game's
fontSmall from data.win (bone fill, shirt-brown shadow): `dist/ultrawide-header.png`
(1300x372 = 650x186 x2, ULTRA / peephole / WIDE) and `dist/ultrawide-gallery.png`
(1920x1080 = 384x216 x5). Key art and font stay out of the repo.
