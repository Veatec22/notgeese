# QoL fixes

Research and test log. Published mods live in `games/<game>/mods/<mod>/` (`AGENTS.md`, Mods).

## Laika: Aged Through Blood: upstream ultrawide (2026-10-03, in-game test pending)

User chose the existing p1xel8ted fix instead of custom development:
https://github.com/p1xel8ted/UltrawideFixes/releases/tag/LaikaAgedThroughBlood .
Downloaded `01.LaikaAgedThroughBlood_v0.1.0_Windows.zip` to the game's ignored
`work/qol/`. Installed only `BepInEx/plugins/LaikaAgedThroughBlood.dll` and
`ConfigurationManager.dll` in `C:/Games/Laika Aged Through Blood`; retained the working
BepInEx 5.4.23.5 runtime/config and PL plugin. Both new DLL hashes verified against the
archive; translation hashes unchanged. Neither destination previously existed.
Receipt: `backups/laika-qol/p1xel8ted-v0.1.0/receipt.json`; undo by removing those two DLLs.
Upstream reports pillarbox removal and wider UI backgrounds, tested on Steam at 3440x1440.
Local GOG 1.0.13 at 5120x1440 remains untested. User should restart, check gameplay width,
HUD, menus and Polish text; F1 opens upstream configuration. No game launched by agent.

## Crypt Custodian: ultrawide (2026-10-05, in-game test pending)

No existing fix found: PCGamingWiki lists the game as 16:9-only; absent from
RoseTheFlower/UltrawideIndex and p1xel8ted/UltrawideFixes releases (checked 2026-10-05).
Own opt-in module `games/crypt-custodian/plugin/Ultrawide.h` in the PL `d3d11.dll`, active only
with `notgeese/ultrawide.ini` `Enabled=1` (created locally, not in the PL ZIP; `Enabled=0` +
restart disables it). Mechanism (from YYC analysis): `oCamera` builds a perspective projection
with aspect `view_width/view_height`; the image goes to `application_surface` at res_width x
res_height and GameMaker letterboxes it. Hooks by builtin name: `surface_resize` (16:9 → window
aspect), `matrix_build_projection_perspective_fov` aspect, `camera_set_view_size` width,
`view_set_wport` width; `display_set_gui_size` keeps the game's 1920x1080 GUI and adds
`display_set_gui_maximise` to scale it to full height and centre it (HUD stays in the middle
16:9, not at the edges). Harness: off / 32:9 / 16:9 cases and real-EXE discovery.
Open risks for the test: camera room clamps use the 16:9 `viewwidth`, so room edges may show
space outside rooms; lighting/effect surfaces sized from res_width may cover only the middle;
toggling fullscreen after start may leave the GUI offset stale until settings reload.

First in-game test FAILED (same mistake as DEADBOLT's first attempt): bars stayed and the
picture looked horizontally squeezed. Log: projection aspect, camera view and view port were
widened, but `surface_resize`/`display_set_gui_size` were never called — the runner sizes
`application_surface` from the game's options before the DLL loads, and the game resizes it
only when settings change. A wide port/projection inside a 16:9 surface squeezes the image.
Revision: on every `display_get_gui_width` call (the input library queries it each frame in
every room) and on `view_set_wport`, read `application_surface` through its read-only
builtin-variable getter; if it is still 16:9 and the window is wider, resize it to the window
aspect once and centre the original 1920x1080 GUI with `display_set_gui_maximise`
(re-applied when the window size changes). Harness replays this startup case. Retest pending;
rooms without the game's camera object (menus?) keep their room-defined port and may draw
in the left part of the wide surface — check the main menu specifically.

Second test: picture now fills 32:9 (no bars, not squeezed). Remaining: a darker 16:9-ish
rectangle in the middle and, in a dark room, the darkness/vignette overlay covering only part
of the screen; the player sits right of centre and the camera starts following sooner to the
left than to the right (room-edge clamp still computed from the 16:9 `viewwidth`; the player is
right of centre in the original 16:9 screenshot too). Static analysis: `o_Lighting` creates
`surface_create(1920*cam_scale, 1080*cam_scale2)` and draws it with `draw_surface_ext` around
the camera object's position; lights use constants 960/540. User asked for the UI across the
whole width: default GUI is now **stretched** (explicit 1920x1080 GUI size, runner stretches it);
`Gui=centered` in ultrawide.ini restores the centred 16:9 GUI. This build also logs (only) the
16:9 surfaces' creation/draw parameters with the owning object and the camera look-at point,
to fix lighting placement and the clamp from real numbers instead of guesses.

Third test (stretched GUI): pause overlay and a tint covered only the left ¾ of the screen.
Log: at 2560x1440 the runner's `application_surface` follows the window (2560x1440 → widened
to 5120x1440) while the game's GUI space is 1920x1080; the plugin had taken the surface size
as the GUI base, so 1920x1080 GUI content filled only 0.75 of it. The earlier "dark rectangle"
was the same GUI overlay (centred mode, wrong base). No 16:9 world-space effect surface was
logged, and the camera looks at its own x,y (`lookat` from == to), i.e. centred.
Revision: GUI base = the GUI size current before the surface is widened (read through the
original `display_get_gui_width/height`). Camera clamp: on each `camera_set_view_size` call
from `oCamera`, set its instance variable `viewwidth` (through `variable_instance_set(-1, …)`)
to view height × aspect, or to `room_width` when the room is narrower (camera centred there);
the camera view size passed to the runner is always the full wide view. Logged up to 12 times;
if the game rewrites `viewwidth` every step, the log shows repeated 1920 → wide lines.

Fourth test: rendering confirmed good by the user; pause/filters cover the screen; camera
centred (log: one clamp change 1920 → 3840 in a 5760-wide room, not rewritten by the game).
Remaining: stretched GUI distorts HUD sprites (health vase). Revision: in Draw GUI events
(`event_number` 64/74/75, read through its builtin-variable getter) and only when drawing to
the screen (`surface_get_target` = -1), `draw_sprite`, `draw_sprite_ext`, `draw_sprite_part`,
`draw_sprite_part_ext` get xscale × k (k = vertical/horizontal stretch, 0.5 at 32:9) and their
x anchored by thirds (left → left edge, right → right edge, middle → centre); sprites at least
3/4 of the GUI wide stay stretched. Scribble text is not changed (stays stretched). Gui=centered
disables this. Harness covers anchors, full-width, world-draw, surface-target and plain sprites.

Fifth test: HUD still stretched; log shows the sprite hooks never fired. The game's GML never
calls draw_sprite* (no symbol-table entries; wrapper has no callers): GUI text and HUD icons are
Scribble elements (inline sprites) submitted with `vertex_submit` under a world matrix
(Scribble 8.7.1 `__scribble_class_element`: `matrix_multiply(__update_matrix(model, x, y),
matrix_get(matrix_world))`; translation = the element's left edge after alignment).
Revision: in Draw GUI to the screen, `vertex_submit` runs under world' = world · T(−tx) ·
S(k,1) · T(Anchor(tx)) and the game's matrix is restored afterwards. Applies to all GUI
Scribble text too (pause menu no longer stretched). Harness checks the composed matrices with
row-vector arithmetic: left edge 30→15, centred 800..1120 → 880..1040, right 1700→1810..1910,
world (non-GUI) text untouched, matrix restored.

Sixth test: still stretched; no squash log line. The GML `vertex_submit` builtin wrapper is
never called by game code: YYC calls the runner's internal routine (RVA 0x148d5d0 in this
build: vertex buffer, primitive, texture RValue*, first, count) directly from Scribble's
`__submit` and the shockwave scripts. The hook now sits on that routine, found from the
`vertex_submit` builtin (wrapper → helper → tail jump) and verified by its prologue bytes;
the event check no longer requires an instance `self` (Scribble draws from struct methods;
the `event_number` getter reads a global anyway). Harness: discovery on the real EXE and the
internal-path matrix test.

Seventh test: user: "wystarczająco" — pause menu fixed; only the health vase still stretched.
`o_Game_Control` Draw GUI draws it through YYC's direct "fast" sprite routines (float args:
self, sprite, subimage, x, y[, xscale, yscale, angle, colour, alpha]); RVA 0x147f120 (ext) and
0x147f0a0 (plain) in this build, called 21 and 7 times there. Found by a unique prologue plus
≥3 call targets shared with the named `draw_sprite_ext`/`draw_sprite` builtin wrappers (sprite
lookup, subimage wrap, draw routine, error report). Same squash/anchor rule as the other GUI
sprites; plain draws become ext draws with the current draw alpha. Harness discovers both in
the real EXE and checks left/right anchoring and non-GUI pass-through.

Eighth test: the fast-sprite squash clipped two of the four cat-head health icons (that HUD
layout cannot be anchored per sprite this way). User judged further rounds not worth it and
asked to revert: fast-sprite hooks removed; the installed DLL is the previous build
(Scribble/internal vertex_submit squash, stretched GUI otherwise). **Accepted state:** wide
32:9 rendering, camera clamp fixed, pause menu and GUI text undistorted, health vase still
somewhat stretched. Personal QoL only; not in the PL package (`ultrawide.ini` stays local).

Minimap: none to build — the game already has one (settings `MINI MAP`, key 1592, PL
`MINIMAPA`; `o_Game_Control` Draw GUI draws `minimap_surf` at GUI 1650,900, bottom right).
The user's settings had it off; enabled by the user in game, visible bottom right.

Ninth test: speech bubbles mismatched — bubble background/name plate/key frame stretched,
their Scribble text squashed and anchored elsewhere. Fix: the six bubble Draw GUI events
(`oTextBox`, `oTextBox_noFreeze`, four `o_text_choice*`), hooked by YYC function name, run with
the squash suspended, so a bubble stays consistently stretched. Harness: names found in the
real EXE; text inside a bubble event keeps the stretch.

Tenth test: bubbles consistent, but the tail points away from the speaker. `oTextBox` stores
the speaker's world x (`x = follow.x + xoff`, Step) and Draw GUI places the bubble at
`960 + (x − camera x)·scale`, clamped to 300..1620 (constants in the event). With a stretched
GUI that offset is k times too large on screen. During the two `oTextBox` Draw GUI events the
instance's x is temporarily set to `camera x + (x − camera x)·k` (camera x from the observed
`matrix_build_lookat` target) and restored afterwards; choice bubbles unchanged.

## DEADBOLT: ultrawide checkpoint (confirmed 32:9, 2026-10-03)

Local opt-in extension to the PL d3d9 proxy; widens camera/viewport and scaling from 960x540
to 1920x540 for 5120x1440. Twelve static room views and the dynamic mission camera are patched
in memory; publisher files stay unchanged. No available online fix found.
Details: `games/deadbolt/docs/technical.md`; source `games/deadbolt/plugin/Ultrawide.h`.
Build `games/deadbolt/tools/build_qol.py`; local ZIP in `games/deadbolt/dist/`.
Installed via `games/deadbolt/tools/install_qol.py`; previous PL plugin saved in
`backups/deadbolt-qol/ultrawide-v1/`. Restore with that tool's `--restore`.
Set `Enabled=0` in the game's `notgeese/ultrawide.ini` and restart to disable only ultrawide.
Harness verifies actual DLL writes and PL regressions; install/restore/reinstall verified.
User must test lighting, aiming, HUD, pause, menus and room transitions. Small-room camera
clamp and fixed-coordinate menu artwork remain unverified. No launch by agent, no site release.

First in-game test FAILED: bars remained and graphics were compressed horizontally.
Revised DLL also updates cached default-window/application-surface widths, which the runner
copies from GEN8 before the DLL loads. Executable instruction signature matched uniquely;
writable destinations and current values checked before changes. Harness pre-scan replay
fails with the old DLL and passes with the revised DLL; disabled mode and PL checks pass.
Revised DLL installed with the original backup preserved. Fullscreen screenshot pending.

User confirms gameplay renders correctly at 32:9. Main menu left-aligned; load-save hover
displaced from its drawn list. Current revision restores original 960x540 view-space for eight
front-end rooms and centers their viewport within the wide output; mission/dock/apartment
cameras remain wide. Harness geometry and PL checks pass; final input/rendering still needs
user testing. Confirmed gameplay DLL saved separately before installing this menu revision.
Also corrected Charon's three untranslated texture headings via existing own mask recipes.

Centered-viewport revision FAILED in game: horizontal stretch and rightward clipping.
Removed viewport offsets; all cameras/ports retain confirmed wide dimensions. Current menu
fix shifts main-menu drawing and computed mouse rectangles through its own coordinate reads,
and shifts load-save's fixed hit-test center to match the already centered list. The harness
checks actual replacement bytecode and zero PortX, including disabled mode and PL labels.
Revised DLL installed. Main/load screenshots and live mouse confirmation still pending.

Latest revision confirmed by user: "idealnie"; accepted as a working checkpoint. Wide
gameplay, centered main menu and load-save interaction accepted; further gameplay testing
continues. Snapshot: `backups/deadbolt-qol/checkpoint-2026-10-03/` contains the exact installed
files, a separate checkpoint ZIP, implementation sources and a SHA-256 manifest. Installed
files verified byte-identical to ZIP. Preserve this checkpoint before later changes.
Full playthrough, other UI states and unusual maps remain open; no site release or ready-status
change. Earlier failures above are history, not the current checkpoint state.

Side findings outside the translation: ultrawide, FOV, UI. Personal use, tested by the user in
game; not part of any PL package or the site unless the user decides otherwise. Anything that
carries a game asset stays local (see Delivery in `AGENTS.md`).

## Possessor(s): ultrawide (confirmed 32:9, GOG 1.8.0)

Game cvar `pose.UseCamBlackBars` (found in the exe: "black bars will be added when the camera's
aspect ratio differs from the default (16:9)"). `%LOCALAPPDATA%\Pose\Saved\Config\Windows\Engine.ini`:

```ini
[SystemSettings]
pose.UseCamBlackBars=0
```

Hor+ by itself (UE5 default `MaintainYFOV`). Menus keep their bars. Rejected: exe hex of the
camera aspect/FOV constants (bars gone but zoomed in; gameplay FOV comes from data).
No earlier fix found online (2026-10-01).

2026-10-03: user reports widescreen was lost. Engine.ini is absent in the current Windows
config directory. Restored only `[SystemSettings] pose.UseCamBlackBars=0`, staged in
`games/possessors/dist/qol-config/Engine.ini`; absence recorded in
`backups/possessors-qol/widescreen-restore-v1/absence.txt`. No executable or save changes.
Previous in-game confirmation applies to the same cvar method; this restoration awaits
the next launch. Undo by removing the newly created Engine.ini if no other settings have
subsequently been added.

### Possessor(s): minimap feasibility and placement (2026-10-03)

User asks for a gameplay minimap based on TAB's map, excluding top right; bottom right is
the candidate, subject to later HUD elements. Read-only extraction of GOG 1.8.0 IoStore v8
directory and selected map/HUD packages. Decompressed blocks checked against original
20-byte BLAKE3 hashes. UE5 name batches/export offsets inspected against CUE4Parse:
https://github.com/FabianFG/CUE4Parse/blob/master/CUE4Parse/UE4/Assets/IoPackage.cs .
Scratch original packages/names/export slices stay in `games/possessors/work/qol/` (ignored).

- WBP_MapMenu contains MapManager, RoomCanvas, MarkerCanvas, MapBounds, MapLocation,
  GetCurrentMapLocation, MapToWorld, RebuildMap, MapLayoutReady and factories for rooms,
  regions, connections and markers. This is a composed map, not a single floor texture.
- WBP_MapRoom uses RoomVolume.GetMapLocation/GetMapExtent and RoomSizeBox. WBP_MapMarker
  uses GetMarkerMapLocation and display data. Native map-space coordinates provide a
  stronger seam than Labyrinth's fitted RoomID/world rectangles. Exact transform, zoom,
  visibility/discovery filters and lifecycle must still be confirmed at runtime.
- WBP_PlayerHUD includes three WBP_BossHealthBar instances, BossIntroScreen, QuestToast,
  ElevatorStatus, ChromaDisplay, health/healing and several energy/ammo widgets. HUD calls
  ShowBossBar/HideBossBar and room-enter/exit notifications. Canvas-slot exports resolve
  to boss bars, elevator status, HealBox and boss intro; serialized layout fragments include
  edge/centre alignments. Do not assert the lower-right corner stays permanently empty:
  complete unversioned layout and all runtime visibility states were not decoded.

Recommended first vertical: small own clipped map panel at bottom right during ordinary
exploration, same disclosed geometry/markers as TAB, player-centred and north-up. Hide it
for full map, pause/dialogue/cutscenes, boss encounters and overlapping notifications;
runtime screen-rectangle checks can refine the overlap rule. Keep original TAB interactive
behaviour. Reuse original data/assets in memory; do not reparent the active map menu or
copy complete publisher widgets into a package. Existing GetHUDVisible/InBoss/UI pause
signals are candidates for lifecycle gating, not yet tested API contracts.

No minimap or loader installed in Possessor(s) in this pass. It currently uses only a PL
localization overlay; a new UE4SS runtime is required for this proposed implementation.
Next: runtime map/HUD geometry probe, verify player map coordinates, current discovery
state and lower-right occupancy, then own read-only crop. Static file verification does
not prove live widget calls, input behaviour, or a collision-free screen location.

User confirms wide gameplay via screenshot but requests HUD at the full-width edges.
Native executable contains UConstraintBox.ClearMaxAspectRatio/SetMaxAspectRatio and
override flags. Added `games/possessors/qol/main.lua`: every second call ClearMaxAspectRatio
on WBP_PlayerHUD_C.RootConstraintBox, without changing icon/bar sizes or other menu roots.
Errors are caught/logged. Also read-only WBP_MapMenu probe on opening TAB: layout readiness,
MapManager class/path, current map location, room/marker counts and first five child slots.
This is preparation for the minimap, not a gameplay minimap implementation.

`tools/build_qol.py` stages the own script plus unchanged local UE4SS
v3.0.1-1140-gf58e8f84 runtime and MIT license to dist/qol-hud. Archive hash checked;
console windows disabled. Installed seven new files in Pose/Binaries/Win64; no game file
overwritten, new-file manifest in `backups/possessors-qol/hud-runtime-v1/new-files.json`.
Mock test exercises exact HUD class scope, invalid/recreated widgets and missing root.
Native runtime compatibility/layout unverified. Next: user launch, gameplay screenshot,
TAB open for at least two seconds then close, exit; inspect ue4ss/UE4SS.log.
To disable this new loader, remove its newly installed dwmapi.dll; full removal can use the
manifest, preserving any subsequently added mods or runtime settings.

Next user launch lost widescreen again. Engine.ini absent after the run; exact deletion
timing/actor not observed. UE4SS loads successfully, but log reports ClearMaxAspectRatio
is a TrivialObject: the custom Pose UConstraintBox lacks the reflected UMG SizeBox method.
Earlier method-name inference and mocked API were wrong. Replaced both approaches:
- Each second, read pose.UseCamBlackBars through KismetSystemLibrary; if nonzero, execute
  `pose.UseCamBlackBars 0` on the valid player controller. Does not rely on Engine.ini.
- Live in-viewport player HUD's constraint content moves to an own stretched canvas host.
  Original child widgets, owning HUD logic and sizes remain; own host mirrors original
  HUD visibility/opacity and hides when the original leaves the viewport. Other menu roots
  remain in place. This more invasive layout change needs native rendering/animation QA.

Updated mock models the missing method and checks cvar reset/reapplication, full-width
anchors, no repeated reparenting, opacity/visibility and recreated widgets. Passes; native
game test pending. Updated Lua installed with `backups/possessors-qol/hud-runtime-v2/` backup.
Next: restart, verify widescreen and edge HUD, pause/TAB hiding, then exit for runtime logs.

Latest user screenshot confirms full-width HUD, but gameplay still has black side bars.
Runtime log identifies a wrong Kismet getter name: GetConsoleVariableInt is unavailable;
the actual GetConsoleVariableIntValue name is present in the executable. Corrected the
call; the command previously never ran. Updated fixture reproduces the missing method:
fails before the fix, passes afterward. Script backed up as hud-runtime-v3; actual camera
result and repeat-launch persistence still require user testing.
TAB probe succeeds: layout ready, direct player map location and six marker widgets with
map-space positions. RoomCanvas has zero children; MapManager access is unavailable.
Room geometry source needs further runtime inspection before implementing the minimap.

User confirms restored widescreen with the corrected getter. Added a personal-use minimap
prototype in `games/possessors/qol/minimap.lua`: bottom-right 280x210 logical units, clipped,
player-centred, native map image brushes and passive visual widget copies. Does not move
the interactive map, execute its scripts or accept input. Source is the MapSizeBox content;
native marker anchors/positions supply the origin, GetCurrentMapLocation drives scrolling.
MapBackground export has the same native class reference as the menu's image backgrounds;
actual room rendering/brush copying still needs game QA. No publisher assets shipped.
Requires TAB once to prepare the native map. Rebuilds after closing TAB to refresh discovery;
copies live brush/visibility data and marker locations every 250 ms. New discovery may require
another TAB opening in this first prototype. Hidden with TAB, hidden gameplay HUD or visible
boss bars (including parent visibility). Quest/elevator notification overlap remains unverified.
Exceptions disable only this panel for the session and remove partial hosts; widescreen/HUD
continue independently. Mirror limits: 400 visual nodes, 18 levels, supported UMG image,
canvas, overlay, size/scale box, border and passive user-widget contents. Unsupported visual
classes logged once. A small cyan player point remains centred.
Lua fixture tests native-brush reuse, clipping, movement/centering, unchanged native UI,
TAB/HUD/boss hiding, hidden boss parents and refresh. Existing widescreen/HUD test passes.
Installed staged own scripts with backup `backups/possessors-qol/minimap-v1/` (main.lua),
new file minimap.lua. Native API calls, rendering and exact map placement are unconfirmed.
Next: user restart, TAB open briefly then close, move between rooms, screenshot bottom right;
also check TAB zoom/input and HUD hiding. Inspect UE4SS.log on any missing/wrong map.

First user run shows no minimap. Log records ready native TAB data but neither mirror-build
nor Lua-error lines: the panel is blocked before construction. Initial code required both
visible gameplay HUD and map layout readiness after TAB closed; readiness reset/hidden HUD
is a lifecycle hypothesis, not measured proof. Changed capture to run while TAB is visible,
before the gameplay-HUD gate; retain that mirror when the menu closes even if layout readiness
resets. Test now hides HUD during capture and clears map readiness after closing: fails with
old code, passes with fix. Added bounded state-change logging for capture, HUD/boss gating
and visible state to distinguish remaining causes. Module installed with minimap-v2 backup;
native minimap rendering still awaits user test. Widescreen/HUD continue independently.

Second user run reaches capture, then fails in the unsupported-visual logger: UObject
GetName is not a UE4SS Lua method. Replaced both class-name calls with GetFName():ToString(),
already used by the Labyrinth runtime. Fixture makes GetName non-callable and includes an
unsupported TextBlock; fails before the fix, passes afterward. An omitted decoration no
longer aborts the complete panel through its diagnostic message. Installed minimap-v3.
Read-only global.ucas script-object table now resolves the native class references: map
backgrounds are Image, the map root Overlay, containers CanvasPanel/ScaleBox/SizeBox. This
confirms the primitive types, not live struct marshalling or successful rendering.

Third minimap run confirms native construction: 81 visual nodes, native dimensions
13609.48x6979.96, marker origin at half size. No Lua/API error; panel then logs "hidden for
boss UI" during ordinary gameplay. Removed the generic boss-widget visibility gate:
instantiated inactive boss UI is not an encounter signal. Updated fixture keeps such a
Visible widget while asserting that the minimap shows; fails before fix, passes afterward.
TAB and gameplay-HUD hiding remain. Installed module with minimap-v4 backup. Automatic
boss/notification overlap handling deferred until a real activity signal is identified.
CommonButtonInternalBase visuals are currently omitted; native marker button icons may
be incomplete. Actual screen rendering still needs user confirmation.

User screenshot confirms a rendered panel, but only grid/dots and movement only after TAB.
Two incorrect assumptions addressed in minimap-v5:
- GetCurrentMapLocation is the menu view centre, not the pawn location. Read-only bytecode
  references SlotAsCanvasSlot/GetPosition and scale math; it stays fixed after menu close.
  Each update now samples PlayerController.K2_GetPawn/K2_GetActorLocation and native
  MapManager.WorldToMap. Function/class names resolved in global.ucas and present in exe;
  live conversion signature/offsets still need runtime QA. Logs compare live position/view
  centre at capture; the general TAB probe now labels the latter correctly.
- CommonButtonInternalBase was omitted by the mirror. Added passive Button-to-Border
  conversion, including WidgetStyle.Normal brush, BackgroundColor and child visuals.
  This preserves graphics carried by button styles without input or original scripts;
  whether it recovers all room geometry remains an in-game question.
Fixture now keeps TAB view centre fixed while the actual pawn moves, and includes a
CommonButtonInternalBase with a room brush/child image. Checks movement and brush copying,
plus existing lifecycle/unchanged-native-UI tests. Both Lua fixtures pass. Staged/installed
main.lua + minimap.lua with minimap-v5 backup. Next: TAB briefly, close, walk without TAB;
screenshot room outlines/icons and inspect log's live world-to-map/view centre values.

User confirms live movement and native icons; screenshot still lacks corridors/room fills
and movement is visibly stepped. IoStore inspection of WBP_MapTabRegion finds RegionImage,
RegionSizeBox/ScaleBox, MainRT/OverlayRT and layout/mapshot/mask textures; WBP_MapConnection
contains dash/end-dot images. These assets stay local and are not shipped.
Minimap-v6 removes the mirror's fixed UserWidget DesiredSize overrides: region allocation
comes from native canvas slots, while desired size can differ. Uses a fill Overlay wrapper.
Freezes the last visible native graphics outside TAB, instead of repeatedly copying hidden
menu visibility/opacity. While TAB is open, keeps syncing the captured visual state.
These address layout/visibility hypotheses; complete region rendering still needs game QA.
Movement is now a separate 33 ms loop: only live world-to-map, map translation and marker
positions, with no full brush/tree synchronization. Slow capture/visibility runs at 250 ms.
No claim of measured FPS. Fixture checks frozen native-hidden image, unconstrained wrapper,
and movement without a slow update; both Lua tests pass. Added native region allocation/image
resource diagnostics for the next run. Installed main/module with minimap-v6 backup.

## Labyrinth of the Demon King: ultrawide + HUD (confirmed 32:9, GOG 1.31)

1. Hidden AutoSettings cvar, `%LOCALAPPDATA%\Shinigami\Saved\Config\WindowsNoEditor\Settings.ini`:
   `Visual.EnableWidescreen=1` (menu offers only 4:3/16:9/16:10 aspect).
2. UE4 defaults to `MaintainXFOV` (zoomed in); same folder `Engine.ini`:
   `[/Script/Engine.LocalPlayer]` `AspectRatioAxisConstraint=AspectRatio_MaintainYFOV`.
3. HUD: `games/labyrinth-of-the-demon-king/tools/ultrawide.py --aspect 32:9` → copy
   `work/ultrawide/pakchunk98-ultrawideHUD_P.*` to `Shinigami/Content/Paks`; delete to undo.
   Widens UI_HUD's 16:9/16:10 box and UI_TutorialPopup's 640x480 box. Other menus are centered
   4:3 boxes, left as is. Carries two game widgets: local only.
4. In-engine cutscenes: `games/labyrinth-of-the-demon-king/qol/main.lua` as UE4SS mod
   `ue4ss/Mods/notgeeseQoL/Scripts/main.lua` + line `notgeeseQoL : 1` in `mods.txt` (UE4SS comes
   with PL 0.4; re-extracting the PL package resets `mods.txt`). Three switches:
   - cutscenes (CineCameraActor) set `LocalPlayer.AspectRatioAxisConstraint` to MaintainXFOV and
     never restore it, so gameplay stays zoomed after e.g. the first in-engine cutscene until a
     restart (seen in a camera-state log): put MaintainYFOV back;
   - cine cameras constrain to their filmback (~1.32, side bars): unconstrain and set sensor
     width = sensor height, so the lens FOV becomes the original vertical FOV (same framing
     height, wider sides);
   - `UI_CinematicBlackBars` letterbox: hide only the `BlackBars` images; the widget also shows
     cutscene subtitles.
   Confirmed in game 2026-10-02.

No earlier fix found online (2026-10-02). Ideas: a "Full screen" entry in the aspect dropdown
(same technique as Polski in the language list) instead of ini edits; HUD box override off
instead of fixed widths, so any aspect works. Weapon/hand viewmodel feels very close on 32:9
(vertical 90° + rectilinear stretch at the edges): candidates are the pawn's `Arms Mesh`
relative location/scale or a lower camera FOV, via the same QoL Lua.

### Player map marker (2026-10-02)

`qol/main.lua` pairs `BP_Map_RoomZone_C.RoomID` with `UI_Map_RoomHighlight_C.RoomID`.
An affine fit of room centres supplies orientation; inside a matching zone, position is
normalised from the zone box into the highlight rectangle. User reports the first
red diamond + yellow direction marker works well, with a small position error; precise placement remains
unverified without screenshots.

Local UE4SS log, session 23:32–23:43: T1F1 has 26 rectangles / 20 zones / 20 pairs,
maximum fit residual 31.6–54.8 map units; T1F2 has 30 / 19 / 19, residual 61.7–62.2.
No `map failed` line. Residual measures centre calibration, not the actual marker error:
the room-local branch replaces the global position. Log lacks per-room bounds and player
coordinates, so it cannot identify the small offset. No speculative correction applied.

Minimap feasibility from original asset name tables: `MapDataList` links `LevelFamily`
to `MapWidget`; `UI_Map` uses `AvailableMaps`, `HasAnyMapsForLevelFamily`,
`RetrieveMapLevelFamilyForLevelName` and `LoadCurrentMap`; floor widgets have `Image_Map`
and room highlights. Existing `T_Arrow_001` / `T_Arrow_002` appearance was not inspected.

First minimap vertical: opening M on the current floor captures numeric room rectangles,
the fitted orientation and the map texture path. After closing M, an own non-interactive
250x250 HUD canvas shows a player-centred crop (scale 1.35), 36 UI units from the top/right.
The map keeps its orientation; one muted-red `▲` glyph turns with view yaw, on both maps.
The crop uses the game's texture in memory, with a dark translucent backing; no game asset
is copied. Stretched `Image_Map` slots use cached canvas geometry, with capture retried
until layout is ready. Preferred highlighted RoomID wins when world zones overlap.

Ctrl+Alt+M toggles the minimap. Learned layouts last for the current run, keyed by actual
level name; an unlearned level or unrecognised room hides it. Opening M once per floor/run
is required. Menu, pause and ignored move/look input hide it; visible character/cutscene
widgets also hide it. Layout snapshots keep no menu object references. Per-opening room
logs now include player position, zone centre/extents, rectangle and marker coordinates.

`tools/test_qol.py`: six Lua 5.4 tests passed (actual Lua functions, mocked UE calls): affine
rotation, room position/direction, overlapping rooms, snapshot/HUD lifecycle after source
destruction, single marker and stretched slots. Native UE4SS marshalling, glyph appearance,
crop readability and hiding throughout cutscenes remain unverified in game. Installed only
the QoL script through `tools/install.py`; previous script preserved under
`backups/labyrinth-of-the-demon-king-qol/minimap-v1/`. No PL release change.
Next: user opens/closes M, walks/turns, changes floor and tests Ctrl+Alt+M; inspect the next
UE4SS log and screenshots before claiming the vertical passes.

2026-10-03: user reports the marker is too large and the minimap absent. Session 00:01–00:02
logs map calibration/room positions, but no capture success, HUD creation or capture exception.
The capture's silent early returns prevented identifying which field failed. Original T1F1
asset has a stretched Image_Map and a 300x300 SizeBox. Added fallback to ancestor SizeBox's
enabled width/height overrides when cached geometry has zero size, plus explicit logs for
missing texture, canvas size or asset path. The zero-geometry capture test failed before the
fix and passes after; all seven Lua tests pass. This reproduces a plausible failure path,
not proof of the runtime root cause. Marker font sizes reduced from 16 to 8 on M, 20 to 11
on the HUD. Updated script installed with backup in
`backups/labyrinth-of-the-demon-king-qol/minimap-v2/`. Next: user opens/closes M again;
verify `map canvas size from SizeBox`, `minimap learned`, `minimap HUD created` and
`minimap showing` in the next log, and actual minimap visibility.

Second user test still had no minimap. Session 00:04–00:05 explicitly reports
`Image_Map has no usable canvas size`; no capture success. All eight original floor
widgets have 300x300 SizeBox overrides. Added class-bound 300x300 image-rectangle fallback
when runtime geometry and ancestor traversal fail (widget roots can interrupt GetParent).
The missing-ancestor capture regression fails before this fallback and passes after;
all eight tests pass. Also removed idle CinematicBlackBars/subtitle-widget presence from
the hide conditions; cinematic input lock still hides the HUD. State-change logs now name
the exact reason for hiding, or report visibility. Installed with backup in
`backups/labyrinth-of-the-demon-king-qol/minimap-v3/`. Not yet verified in game.

User confirms v3 minimap appears; position mismatch in some areas and intermittent
disappearance remain. Do not call calibration or hiding finished. Next positioning/hiding
pass should use room and state-change logs from a matching session.

2026-10-03: user requests an image marker fitting the game, without red. Built-in ImageGen
produced `qol/assets/player-marker-v1.png` (original RGBA/alpha preserved); exact prompt in
the adjacent `.md`. Aged ivory/umber arrowhead, rough ink edge. Both map markers import
the PNG through KismetRenderingLibrary.ImportFileAsTexture2D and reuse the texture while
valid; render at 12.8/17.6 square UI units, with existing rotation. Failed import falls back
to a small ivory glyph and logs the reason. Nine Lua tests pass, including shared texture
and import failure. Script installed with backup `backups/labyrinth-of-the-demon-king-qol/marker-v1/`;
new PNG added beside the installed script under `assets/`. Native import/readability unverified.

### Enemy respawning: read-only investigation (2026-10-03)

Local GOG 1.31 IoStore inspection, not a runtime test. Findings from original Blueprint name
tables, exported function wrappers, bytecode call sites and CDO properties:

- `BP_WorldRandomiser` has `ReceiveBeginPlay` (wrapper calls its ubergraph),
  `CommonEnemySpawn`, `SpecialEncountersSpawn`, `SpawnHunter`, `SpawnNuribotoke`.
  Its graph calls CommonEnemySpawn/SpecialEncountersSpawn and spawn spots' SpawnNPCs;
  uses shuffled arrays, ActivationChance, LevelMinimumEnemies, MinimumEnemiesToSpawn,
  EnemySpawned and native MultiConditionCheck / HasMemory / IsInNewGamePlus.
- Class defaults: LevelMinimumEnemies = 5, ChanceToSpawnHunter = 0.5.
  Level instances may override them; these are not universal in-game counts/probabilities.
- `BP_NPCSpawnSpot`: defaults ActivationChance = 0.45, MinQuantity = 1, MaxQuantity = 2,
  SpawnRadius = 150 cm; PossibleNPCClasses / PossibleNPCClasses_NGP, RandomiseNPCs,
  SpawnConditions; graph creates actors with BeginDeferredActorSpawnFromClass /
  FinishSpawningActor and searches reachable points. No Tick/timer names found in this graph.
- `BP_NPCSpawnSpotTrigger`: overlap-driven, defaults chance 0.35, quantity 1–2,
  radius 200 cm; graph invokes SpawnNPCs and K2_DestroyActor. Other narrative triggers,
  boss-add spawns and Nuribotoke spawn spots are separate mechanisms.
- No respawn toggle found in extracted default ini files. Internet reports support enemies
  returning after area reload but conflict on exact triggers/timing; do not use them as code proof.

Inference: ordinary returning enemies are chiefly repopulation on level load, with shuffled
spots/classes, rather than every dead actor running a universal respawn timer. ReceiveBeginPlay
and common spawn functions provide a plausible UE4SS interception seam. Exact native memory
conditions and kill persistence were not decoded; full trigger coverage needs a runtime trace.

Candidate mod: remember deaths by level + spawn spot and suppress only replacement ordinary
enemies. Keep initial encounters, story triggers, bosses and boss adds. Globally blocking
SpawnActor, disabling the whole randomiser or zeroing spawn chance would also remove initial
enemies (and minimum-count logic may compensate), so none is an equivalent no-respawn fix.
Session-only tracking is simpler; persistence across restarts needs a per-save ledger and
new-game reset. Next if requested: read-only spawn/death trace on kill → leave → return, then
a vertical restricted to common encounters. No gameplay script, installation or save changed.
Scratch evidence: `games/labyrinth-of-the-demon-king/work/respawn/` (ignored).

### Quick-use inventory HUD (2026-10-03)

User shelved respawning and requested bottom-left quick-use slots: 1 healing, 2 stamina,
with the next item's original icon and quantity. Implemented two 76x76 slots, muted original
ItemFrame borders, Garamond labels and counts; empty categories retain a dimmed icon and zero.
Read-only inventory refresh every 300 ms, hidden with gameplay input lock, pause or menus;
own widget is recreated or reattached after removal. No key rebinding or inventory writes.

Local native disassembly of GOG 1.31 QuickHeal / QuickStamina proves priority:
Health_003_RefillableTea → Health_001_Sake → Health_002_Ginseng;
Stamina_001_Mushroom → Stamina_002_MushroomPouch. Each uses the first matching inventory
entry with AmountCarried >= 1. HUD follows that exact selection, showing the selected stack,
not an aggregate of different consumables. Uses reflected InventoryComponent.InventoryArray
(Blueprint property fallback: Inventory Component), ItemID and AmountCarried. Icon soft paths
verified from InventoryIcon in the original ItemList rows; textures loaded at runtime only.
Scratch native evidence: `games/labyrinth-of-the-demon-king/work/quickitems/` (ignored).

Eleven mocked Lua tests pass, including priority, duplicate/empty stacks, quantity updates,
icon switching, no consumption, pause hiding and widget recreation/reattachment. This verifies
script logic, not live UE4SS reflection or appearance. Installed with backup
`backups/labyrinth-of-the-demon-king-qol/quick-items-v1/`. Next: user restarts the game, compares
both counts with inventory, uses 1 and 2, checks depletion/fallback and bottom-left readability.

User screenshot confirms the first two quick-use slots render. Requested larger icons,
smaller map markers, matching frames and an equipped-talisman slot. Icons now 68 instead of
52 UI units; item cells 92 instead of 76. Both map markers reduced by about 25%; minimap
crop remains 250 square. Built-in ImageGen produced own transparent aged-paper frame
`qol/assets/hud-frame-v1.png`; exact prompt in adjacent Markdown. Shared by minimap,
three item slots and small input badges. Original alpha preserved, centre alpha verified zero.
Frame imports once and is cached, inventory falls back to original ItemFrame if unavailable.

Talisman selection uses SInventoryComponent.ReturnEquippedTalismanIndex (native accessor
returns its equipped index), matched to the zero-based InventoryArray entry. All eight
talisman InventoryIcon paths verified from original ItemList rows. No summed talisman stock
or selection of a different owned type. Empty/unequipped shows a dimmed talisman and zero.
DefaultInput.ini proves QuickHeal=One, QuickStamina=Two, ActivateTalisman=T. Badges under
icons try live PlayerInput.ActionMappings keyboard keys, falling back to those defaults;
live reflection and rebinding display require in-game confirmation. Keyboard labels only.

Twelve mocked Lua tests pass, including equipped-index selection, switching/depletion,
frame application, input defaults and remapping. Installed with backup
`backups/labyrinth-of-the-demon-king-qol/hud-v2/`; generated frame is a new file in Scripts/assets.
Next user test: talisman type/count and T use, frame readability, marker size, badge layout.

User clarified the marker request was enlargement, not reduction. Restored the pre-hud-v2
sizes and enlarged both by 25%: map 16 UI units (previously 12.8), minimap 22 (previously
17.6). Installed with `marker-larger-v1` backup; minimap crop and other HUD elements unchanged.

User reports equipped talisman stock 3 still displays 0. Runtime log confirms the accessor
does not error, but selection falls back to empty. Root cause: UE4SS TArray.ForEach passes
one-based indices; native ReturnEquippedTalismanIndex is zero-based. Earlier mock incorrectly
passed zero-based indices and hid the mismatch. Verified in upstream LuaTArray.cpp ForEach
(https://github.com/UE4SS-RE/RE-UE4SS/blob/main/UE4SS/src/LuaType/LuaTArray.cpp).
Corrected the mock and added the exact three-versus-zero regression; both selection tests
failed before normalising index - 1, then all thirteen passed. Fix installed with
`talisman-index-v1` backup. Actual user inventory not captured; live confirmation still needed.

User screenshot shows the minimap frame obscuring the map edges. Moved it out of the clipped
250x250 crop to the root canvas, enlarged to 290x290 with 20-unit outward padding on every
side. Crop size and screen position preserved. Existing lifecycle test checks the sibling
frame and unchanged crop; thirteen tests pass. Installed with `minimap-frame-outside-v1`
backup; visual confirmation pending.

### Settings menu and respawn diagnostics (2026-10-03)

User requests a native-looking separate settings section, and persistent suppression of
killed ordinary enemies in the current save, chiefly on floor return. Subsequent request:
first collect respawn traces across triggers, and correct/wrong minimap reports in game.

Read-only IoStore inspection of UI_SettingsMenu confirms CategorySwitcher (WidgetSwitcher),
Btn_General/Visual/Audio/Input/Language, SetCategory, NavigateCategoryLeft/Right and explicit
focus/navigation functions. Existing pages use ScrollBox, SettingRow, native AutoSettings
controls, CVarName, and SettingsManager.FlushAndSaveSettingsStatic. Reusable styled spinner,
slider and combo widgets exist in the original content. Current Lua already creates real
UMG widgets successfully. Earlier statement that a separate section necessarily needs the
Unreal editor was too strong: runtime insertion is a viable first prototype. Callback,
focus and gamepad integration remain unverified; adding a page alone does not extend the
hard-coded category navigation. Evidence in ignored `work/menu-respawn/`.

Recommended first menu vertical: one added section with a minimap checkbox, reopen/restart
persistence and native keyboard/mouse focus. Then add consumable HUD toggle/scale, marker
size, arms position/scale/reset and gameplay FOV. Keep a single settings state used by both
hotkeys and menu; current hard-coded booleans must not override changes. Visual preferences
can use an own versioned local config; do not assume AutoSettings saves unknown mod values.
Runtime widescreen/HUD control must account for the current fixed-width overlay and ini
axis constraint. Gameplay FOV should not overwrite cinematic lenses. An editor-built own
widget is a fallback if the runtime prototype cannot handle input cleanly, not a prerequisite.

New native findings: NPCID, bNPCKilledPermanently, StoredPermanentlyDeadNPCs and
SavedPermanentlyDeadNPCs exist in the executable. Nuppeppo, Warden and Kappa Blueprint name
tables reference permanent death/NPCID; inspected ordinary BP_Sinner_001 does not override
those properties in its name table. This suggests an existing boss/story persistence path,
not proof that ordinary random spawns have stable IDs. Do not globally set the permanent
flag, add arbitrary IDs to game memory, or disable the world randomiser. Stable common-spawn
identity, multiple actors per spot, rerolled classes, minimum-enemy replenishment, save rollback
and NG+ reset must be resolved before suppression. Native wrapper disassemblies are scratch
evidence only; death-storage code flow is not yet fully decoded.

Read-only diagnostic mode now in the local Lua mod:
- Every 500 ms: current level/save/death-load hints, randomiser count fields, common/special
  spot membership where reflected arrays expose it, NPC arrival/dead-state/removal with
  path, NPCID, permanent flag, position and owner. Missing fields log `?`. Actor removal is
  not treated as death. Polling can miss very short-lived actors/death states; source ownership
  and exact trigger classification are not established by proximity or class alone.
- Ctrl+Alt+F8: user marks a noticed respawn, with time in UE4SS.log.
- Ctrl+Alt+F9: correct minimap; F10: wrong position; F11: missing minimap. Reports include
  player world position/yaw, level, learned texture, visibility/input state, chosen room,
  marker coordinates, affine coefficients/error, and every room's bounds/yaw/map rectangle.
  No recalibration, position correction or gameplay change occurs when reporting.

Fifteen mocked Lua tests pass, including read-only NPC death/removal/level tracing and a
missing-layout map report. Actual property availability and capture overhead await user
testing. Installed with `backups/labyrinth-of-the-demon-king-qol/diagnostics-v1/` backup.
No enemy suppression or new menu installed. Capture protocol: report a correct position,
then the wrong one before reopening M; mark missing state separately. For enemies, kill one
recognisable ordinary NPC, change floor and return, mark reappearance; separately repeat
around rest/death if convenient. Do not combine all triggers in one unmarked sequence.

2026-10-03 crash diagnosis: identical native UE4SS property-lookup failures occur during
both minimap and quick-item HUD updates around level changes. Each panel previously checked
only its root before using cached child wrappers. Added child/slot validity guards and
panel rebuilding when the level changes or children are invalid; two regressions fail before
the change, all 17 mocked tests pass afterward. Installed locally with `crash-guard-v1`
backup and temporary per-operation/line probes. User stability test pending; this is not
yet proof that all native crashes are fixed. Full evidence and restoration chain in the
game's technical doc. Preserve probe logs before restarting after another crash.

2026-10-04: user reports zero crashes since the guarded panels were installed. Preserved
the stable session's diagnostic logs, then installed clean PL/QoL scripts while the game
was closed (`crash-probe-cleanup/` backup); guards and panel rebuilding retained. Removed
temporary runtime probes; all 17 QoL tests pass. Continue normal play to confirm stability
without instrumentation. No public release change.

2026-10-04: crash recurred after removing probes; the new dump starts in Lua closure access,
unlike the earlier property-lookup failures. Changed periodic PL and QoL work from
LoopAsync -> ExecuteInGameThread to the installed runtime's LoopInGameThreadWithDelay,
retaining the child guards. Eighteen QoL tests and one PL test pass; local backup
`game-thread-loops-v1/`. This scheduling hypothesis needs an in-game transition test.

2026-10-04 map reports: user reports no crash so far with game-thread loops. Archived 16
hotkey reports: six correct, four wrong, six missing (`work/minimap-reports-2026-10-04/`).
Wrong positions concentrate in T1F1 room 1102 and rotated T2F1 room 2106. Four gameplay
missing reports on T2F1 are caused by chosen=nil/outside-known-room hiding; two other
missing reports were paused. The native trigger zones leave traversable gaps, and a
trigger's extents cannot be assumed to match the full authored map corridor. Do not use
the high-error global fit as an accurate fallback or treat a report's calculated uv as
ground truth. Need full-map screenshots with expected position for corridor calibration.
No Lua edit or installation in this analysis pass; continue observing crash stability.

2026-10-04: crash recurred after 3619 seconds. Native property metadata access, immediately
after rebuilding the minimap when leaving the T2–T3 corridor. Exact property still unknown.
Installed targeted v3 operation breadcrumbs for both mods and specific minimap stages;
18 QoL tests pass. Direct game-thread scheduling and child checks retained. Backup
`targeted-probe-v3/`; preserve logs before restarting after failure. No further fix claimed.

Only expose separate respawn-policy switches after logs prove the corresponding triggers
can be identified reliably. Persist kill history per save/campaign with load rollback and
NG+ handling; a slot-name-only ledger can wrongly suppress enemies after loading an older
save or starting a new campaign. Initial/unvisited spawns and unclassified/story sources
remain enabled. Recommend a common-spawn-only vertical before broader coverage.

### Third-person camera: read-only investigation (2026-10-05)

Current arms setting (installed `arms.txt`): forward +60 cm, side/up 0, scale 1.00. Arms Mesh
sits on the FP `Camera` at base (-13.2, 0, -200).

GOG 1.31 IoStore, BP_PlayerPawn bytecode/defaults (own zen + Kismet disassembler, evidence in
ignored `work/tps/`). The developers left a complete, unbound third-person mode:
- `ViewChangeToggle()` flips `bInThirdPersonView`; ArmsMesh visible = !TP, HeadMesh visible =
  TP; `VisibleBoneToggle()` unhides/hides `ThirdPersonViewBones` (clavicle_l/r) on the body;
  torch/item actors re-attach to body `Mesh` (TP) or ArmsMesh (FP); `CameraComp` vs
  `ThirdPersonCamera` SetActive; AnimBP and item actors get `SAnimationInterface.ToggleView`.
- CDO `bInThirdPersonView = true`; BeginPlay calls `ViewChangeToggle()` once → FP. No input
  binding calls it. A new pawn (level load) therefore always starts in FP.
- `SpringArm_TP` on the capsule: length 364.8, Z +74.5, fixed pitch -18.6, no pawn control
  rotation (mouse pitch would not move the camera). `ThirdPersonCamera`: FOV 80,
  `bConstrainAspectRatio` true at 1.333 (4:3 bars; game's aspect callback only adjusts
  CameraComp/AnimCamera).
- Body `CharacterMesh0` runs AnimBP_Player_FullBody: state machine, 4-way idle/run, crouch,
  in-air, per-weapon blend spaces, montage slots. Head/Legs/Arms meshes use the body as
  MasterPoseComponent, so FP attacks are already full-body poses. In TP the AnimBP zeroes
  pitch aim offset. Body has CastShadow false.
- Weapons/torch use `M_MasterMaterial_Equipment` with static switch `RenderInFront`
  (MF_WeaponFOV, scalars `RIF`/`FOV`): likely drawn over walls/distorted in TP. Static switch
  cannot change at runtime; scalar MID override untested.

Unverified: native interaction/ranged trace origin (camera vs pawn; InteractDistance 280 vs
365 cm arm), AnimCamera cutscenes while TP camera active, Neck Mesh, armour head meshes.
TPS v1 in `qol/main.lua`: Ctrl+Alt+V calls the pawn's `ViewChangeToggle`. Then TP camera
unconstrained, SpringArm_TP `bUsePawnControlRotation`, length 250, SocketOffset.Y side,
TargetOffset.Z height, FOV 80 (vertical under MaintainYFOV). While on, the arms keys tune the
camera (I/K distance ±25, J/L side ±10, U/O height ±10, Y/H FOV ±5, R defaults); state in
`tps.txt`. Every 100 ms: re-enter TP on a pawn that is past BeginPlay (FP); never toggle a
pawn still at the class default or one not switched by the mod; leave TP while move/look
input is ignored, return after 500 ms unlocked. Five mocked Lua tests (23 total pass); the
ownership-guard mutation fails two of them. Installed into the probe-instrumented script
(targeted v3 breadcrumbs kept), backup `backups/labyrinth-of-the-demon-king-qol/tps-v1/`.
Native calls, rendering and gameplay effects untested. Next user test: toggle in a corridor,
walk/run/crouch/jump, attack with a melee weapon, torch, bow/firearm if owned, open a door
and pick up an item, talk to the merchant, trigger a cutscene, change floor, die/reload.
Screenshots: head/helmet, weapon over walls, side bars; UE4SS.log `third person` lines.

First user screenshot (2026-10-05): TP works (body, head, legs, camera), log one
`third person on`, no error. Katana appears enlarged and offset behind/away from the hand.
Cause: Weapon FOV reprojection for the FP view. MP_WeaponFOV defaults decoded: WeaponFov 90,
DepthScale 0.08, ClipDistance 50, BlendEffect 1, HitDistance 1000, WeaponOffset 0.
ImaginaryBlend docs: BlendEffect 1 = FOV space, 0 = world space. TPS v2 sets the collection's
BlendEffect to 0 via KismetMaterialLibrary while TP is active (re-checked each tick, values
are per world), restores the read value on leaving TP. Fallback if insufficient: swap to
the non-RIF `BasicMaterials/Unique/Weapons/MI_*` (no match for Tanto, hammers, knives,
Rifle, Flashlight, Metal_013, T002_Gunk). One mocked test added (24 pass); removing the call
fails it. Installed with backup `tps-v2/`. In-game weapon placement still unverified.

v2 user screenshot: katana normal size, in front of the body, still slightly beside the right
fist. Log: `BlendEffect 1.00 -> 0`, no error. Skeleton (shared by arms/body meshes) holds
the sockets: `WeaponSocket_RHand` on `u_WeaponBone_R`, which is a child of `hand_r`, so the
socket is not the cause. Remaining candidates: residual depth squash or FP-authored grip
pose. TPS v3 also sets DepthScale 1 while TP (restored with BlendEffect); backup `tps-v3/`.
Discriminator: offset that changes with camera distance/side = material; constant = pose.

v3 user test: little improvement; weapon position still follows camera pitch while the arm
is still, so the material reprojection persists despite the collection values (log confirms
BlendEffect 1->0, DepthScale 0.08->1). World pickup MIs (`BasicMaterials/Unique/Weapons/MI_*`)
use a separate `M_MasterMaterial_Base` with the same `BaseTexture` parameter; Tanto's RIF MI
has no switch override (master default). TPS v4: in TP, walks EquippedItemActor /
EquippedTorchActor components (RootComponent → AttachChildren, same owner); each material
whose parent chain reaches M_MasterMaterial_Equipment gets a MID of MI_Katanas_001_a with the
item's BaseTexture; re-swapped if the game reapplies; originals restored in FP. Particle
materials (torch flame) untouched. Collection override kept. One mocked test (25 pass);
removing the call fails it. Installed with backup `tps-v4/`. UE4SS marshalling of
AttachChildren/TextureParameterValues/CreateDynamicMaterialInstance unverified.

v4 user test: weapon equipped while in TP is offset and locked to the camera; FP→TP toggle
places it correctly; torch handle correct, flame offset in every variant. Log: every v4
swap failed (`CreateDynamicMaterialInstance` expects 4 parameters in 4.27, got 3), so the
correct placement came from the collection override plus ViewChangeToggle's re-attach.
Root cause of the camera lock: the game attaches newly equipped items to the hidden
ArmsMesh (at the FP camera); only the toggle moves them to the body. TPS v5: material
swap removed. While TP, items whose root is attached to ArmsMesh move to the body Mesh with
the socket the game chose (GetAttachSocketName; snap/snap/keep, weld) and get
ToggleView(true); items attached elsewhere are left. Torch flame `PS_TorchFlame_RIF` →
`PS_TorchFlame` (SetTemplate), restored in FP. Collection override kept. 26 mocked tests;
removing either call fails its test. Installed with backup `tps-v5/`.

v5 confirmed by user: items equipped in TP land in the hand (log `moved from arms to body`),
torch flame correct. Checkpoint. Next problems: centred camera makes picking table items
hard; attacks ignore view pitch in TP (small enemies unreachable).
- PDB public symbols (own MSF reader + capstone, scratch only): ASCharacter::InteractTick
  (0x140ece890) capsule-traces radius 5 from the component at this+0x630 (= ReturnCameraComp,
  the FP CameraComp) along its forward for this+0x6d8 (InteractDistance), ignoring the two
  held items; result in this+0x928. The FP camera stays in the head in TP, so the trace
  follows the head, not the TP crosshair.
- Body AnimBP uses InThirdPerson only in SelectFloat(0, PitchInput, InThirdPerson) for the
  RotationOffsetBlendSpace X (pitch aim offset).
TPS v6: while TP, CameraComp attaches to ThirdPersonCamera (snap) and InteractDistance =
original + |TP camera − head socket|, recomputed each tick; anim InThirdPerson kept false.
Restored (attach parent/socket/relative transform, distance) before ViewChangeToggle back to
FP. Defaults over the shoulder: distance 175, side 55, height 15; Ctrl+Alt+T in TP swaps the
shoulder. Installed `tps.txt` updated to the new defaults (TP off; old file in backup).
27 mocked tests; reversing restore order or dropping the pitch fix fails the aim test.
Installed with backup `tps-v6/`. Not verified: trace self-hit from behind the body,
reach feel, aim-offset look in TP, crosshair/attack parallax at melee range.

v6 user test: picking up works well. Melee no longer hits floor/ceiling when looking
down/up as in FP; body pitch only partial; swing trail offset from the blade.
ASCharacter::SetTraceStartAndEndPoints (0x140ee01b0): Start = CameraComp (this+0x630) world
location for every point type; End = socket `WeaponSocket_LH/RH` on this+0x548 (unarmed),
`TraceSocket_L/RFoot` on this+0x280 (body Mesh), the melee weapon's two trace components
(+0x4c8/+0x4d0) or ASBaseMeleeWeapon::ReturnOtherTraceStartAndEndPoints. v6 moved CameraComp
to the TP camera, so hit segments started behind the character. In FP the arms rig hangs
under CameraComp and copies the body pose (ArmsMesh.MasterPoseComponent = Mesh), so arms and
weapon pitch fully with the view; the TP body has only the aim offset.
TPS v7: CameraComp stays in the head. Rig "arms" (default): ArmsMesh visible at its original
place (personal arms.txt offset neutralised while TP), body clavicles hidden, held items
kept on/moved to ArmsMesh with ToggleView(false): hits, pitch and trails as in FP. Rig "body"
(Ctrl+Alt+B): v5 behaviour. Both: CameraComp turned (K2_SetWorldRotation each tick) from the
head towards the TP crosshair point (KismetSystemLibrary.LineTraceSingle from the TP camera,
ignore pawn, 30 m; hits nearer than the head ignored); relative rotation restored before
ViewChangeToggle back to FP. InteractDistance no longer changed. `tps.txt` gains a 6th
field (rig). 27 mocked tests; forcing the body rig or dropping the camera turn fails them.
Installed with backup `tps-v7/`. Unverified: UE4SS out-param HitResult (log
`crosshair trace hit without readable location` if not), look of FP arms seen from outside,
shoulder sliding at large pitch, 100 ms lag of the parallax correction.

v7 user test: aiming feels better, but the FP arms seen from outside swing around the head
(screenshot looking down: arms/weapon detached from the body). Log clean, no unreadable
trace warning. BP_Katana_001: ASBaseMeleeWeapon `AttackTraceStartPoint`/`EndPoint` =
components `Attack Trace Start` (Z 6.74) / `Attack Trace End` (Z 132.24) on `Weapon Mesh`;
these are the melee hit segment (+0x4c8/+0x4d0 in SetTraceStartAndEndPoints).
TPS v8: default rig "body" again (arms rig kept on Ctrl+Alt+B). In the body rig the
equipped item's two trace points are re-attached to the hidden ArmsMesh at the item's hand
socket: KeepWorld attach to the body socket yields their offset, KeepRelative attach to the
same ArmsMesh socket reproduces it; saved parent/socket/relative transform restored on FP or
rig switch. Fists already use ArmsMesh sockets. ArmsMesh neutral (no arms.txt offset) in
both TP rigs. Assumption: a hidden master-pose follower's socket transforms still come from
the master pose. Side note: arms.txt offset in FP also moves held weapons and therefore
the hit segment. 27 mocked tests; dropping the binding fails the body-rig test. Installed
with backup `tps-v8/`; installed `tps.txt` set to rig body.

v8 confirmed by user ("we are home"): body look, hits and aiming work. Checkpoint 2.
User wants the shoulder camera further back (legs not visible): default distance 175 → 240
(side 55, height 15, FOV 80 unchanged); installed `tps.txt` updated, backup `tps-v9/`.

User-tuned final config (installed `tps.txt`): distance 240, side 55, height 15, FOV 90,
rig body; FOV 90 is now also the default (backup `tps-v10/`). User calls TPS "excellent".

Before/after comparison: `games/labyrinth-of-the-demon-king/tools/vanilla.py --off` moves
dwmapi.dll (UE4SS: PL runtime + QoL) and pakchunk98/99 to
`backups/labyrinth-of-the-demon-king-vanilla/`, removes the MaintainYFOV axis and hidden
widescreen ini lines and sets Culture=en (original ini copies kept). `--on` restores; ini files
untouched by the game since `--off` come back byte for byte, otherwise only our lines are
re-applied. Dry-run on a fake game dir verified both paths. 2026-10-05: bare state active.
User still saw widescreen in the bare run. BP_LotDK_GameInstance registers
`Visual.EnableWidescreen` default false and `Visual.CameraAspectRatio` default "4:3"; the
remaining width came from the saved menu value 16:10. `--off` now also removes that line
(game default 4:3), applied to the active bare state. The bare game wrote
`[Internationalization] Culture=en` into Engine.ini, so `--on` now always restores the ini
copies taken by `--off` instead of re-adding single lines.
2026-10-05: `--on` run after the user's "before" captures; files, mods.txt, tps.txt and all
three ini files back to the pre-`--off` state (Engine.ini without the bare game's Culture).

Render-resolution check (user suspected missing pixels, in-game resolution 2560x1440): all
logged port sizes are 1920x1080 (→ 3840x1080 widened); `oCamera` sets the port to
1920·cam_scale × 1080·cam_scale only when its scale switch fires, and it never did with a
different scale. The rasterisation target is `application_surface`, 5120x1440 (from the
runner's window-sized 2560x1440): the port is the coordinate frame GameMaker scales onto that
surface (vanilla 16:9 at 1440p is the same: port 1920x1080 in a 2560x1440 surface), so the
world renders at native 5120x1440. GUI coordinates are 1920x1080, scaled ×1.33 vertically;
art and baked fonts are authored for 1080p in vanilla too. No change made.

## Silver Pines: minimap feasibility (2026-10-13, read-only)

Unity 6000.3.15f1 IL2CPP x64 (exe `Carpenter.exe`, data `Carpenter_Data`), metadata v39,
Addressables in StreamingAssets. Offline Cpp2IL from vendored BepInEx be.788 reads it
(157106 methods, 154 dummy assemblies); runtime BepInEx/Il2CppInterop on Unity 6000.3 unproven.

The game already has a gameplay quick map (hold/toggle `Player_QuickMap`, setting "Quick Map
Toggle"). Scene `scenes-utility`: `QuickMap` (QuickMapPanel) > `QuickMapMinimap` (CanvasGroup,
full stretch) > `Mask` (anchors 0.05–0.95) > `WorldMapView` (RawImage + UIMap3DPanel,
m_mapType 1), plus MenuButtonPrompts and MapFloorsInfo. The map is a separate 3D map scene
rendered by an orthographic camera into a screen-sized RenderTexture (MapSceneManager,
Map3D). ISIL: QuickMapPanel.OnQuickMapShowingStateChanged = UIMap3DPanel.set_MapViewActive +
PopulateMap + SetActive + DOFade + an input hook for "switch to main map". UIMap3DPanel.Update
calls PositionPlayer → Map3D.FocusCameraOnMapPosition every frame (player-centred, icons
rotated). Map3D.SetQuickMapZoomLevel sets orthographicSize. Player side (PlayerQuickMapControls,
PlayMaker InputQuickMap/IsQuickMapActive) is separate; showing the panel alone does not
need the player's map state.

Plan if pursued: BepInEx 6 IL2CPP plugin, show the panel without PlayerQuickMapControls and
without the main-map input hook, shrink `QuickMapMinimap` to a corner, hide prompts/floors,
crop RawImage uvRect, own zoom; hide in menus/cutscenes; restore full layout while the player
holds the native quick map. Risks: BepInEx on Unity 6000.3 (first gate, needs a launch test),
Unity base libraries for 6000.3.15 for interop, map UI inputs (scroll/zoom/hide icons) bound
while active, extra camera cost, menu map sharing MapSceneManager. Nothing built or installed.

BepInEx gate (2026-10-13): unchanged be.788 IL2CPP x64 extracted into the game dir (no file
collisions, nothing replaced), plus `BepInEx/config/BepInEx.cfg` with
`UnityLogListening = false`. File list in `backups/silver-pines-qol/installed-bepinex.txt`;
removal = delete those files. Awaiting first launch: `BepInEx/LogOutput.log`, interop
generation, game reaching the menu.
First launch (2026-10-14): BepInEx gate passed. LogOutput: Unity 6000.3.15f1, Cpp2IL metadata
v39 OK, interop generated (unity-libs 6000.3.15 downloaded), chainloader complete, ErrorLog
empty. Player.log: system menu reached, orderly shutdown, no exception. Gameplay not tried.

Minimap v0.1 (2026-10-14): `games/silver-pines/mods/minimap/plugin/Plugin.cs` (moved there at release), built by
`mods/minimap/tools/build.py --game <dir>` against the player's generated interop into
`games/silver-pines/dist/minimap` (own DLL only). Harmony prefix on QuickMapPanel.Update sets
m_shouldShow = native quick map || minimap wanted; minimap mode moves the QuickMapMinimap frame
to a 420x300 top-right box, scales the map view by 0.5 and zero-scales MenuButtonPrompts and
MapFloorsInfo; native quick map restores the captured layout. OpenFullMap blocked unless the
native quick map shows. Hidden when PlayerQuickMapControls.Update stops running, IsMapEnabled()
is false or timeScale is 0; F7 toggles. All values in BepInEx/config. Installed as a new file;
compiled only, untested in game. Unverified: icon alignment at scale 0.5, UI scroll/zoom inputs
during play, pause/cutscene detection, cost of the map camera.

User test v0.1 (2026-10-14): minimap visible top right, player arrow and labels aligned at
MapScale 0.5 (screenshot). Log: one Il2CppException NRE in MapSceneManager.SetMapActive on the
first show (static RenderTexture still null right after load); later shows fine. State flapped
between minimap and "player controls inactive"/"paused" during loads and menus.
v0.2: show only when MapSceneManager.RenderTexture exists and the conditions held 0.75 s;
hide immediately. Console window off: `[Logging.Console] Enabled = false` (disk log stays).
No existing Silver Pines minimap mod found (web search, Nexus).

v0.2 user run: clean log, no exception. Requests: hide outside free play, fades, framed look,
on/off key (F7 already existed, unused).
v0.3 (2026-10-14): QuickMap sits in `GamePlayElementsDisabledWhenPaused` (GameplayUIContainer)
next to Dialogue/CinematicBars/Examine panels. Hidden when any of: GameplayUIContainer.m_uiDisabled
(static), UIHideDuringCutscenes flags (cutscene, cutscene level, dialogue; the game's own HUD
hider), CinematicBarsUI m_isInDialogue (phone dialogue channel) / in-game or video cutscene,
DialoguePanel.m_isShown, ExaminationInfoDisplay.m_isActive, InventoryItemPickupPanel.m_isShowing,
GameNotesReaderPanel.m_isActive, InventoryInteractionPanel.m_isShowing; components found under
the panel's transform.root (GameUIContainer). Show after 0.5 s of free play. Minimap fades at
0.4 s via the panel's own speed-based fade fields (native speeds restored for the quick map);
leaving the native quick map fades it out full-size, then in small. Frame: the game's
`GrittyPanelDoubleSided` sprite (1024², 170 px 9-slice, ingamemenu bundle, used by GameUI prompt
backgrounds; taken from a loaded Image at runtime) as sliced Mask sprite (PPU ×5) plus a dark
sliced border Image (PPU ×4, alpha 0.8) behind the mask. All values configurable.

v0.3 user run: frame/fades/hiding OK (log: phone dialogue and cutscene hides, no errors), but
the dark border was too wide, bottom worst: it stretched over the whole frame while the mask is
inset (anchors 0.05–0.95, sizeDelta y −21, y +11 → gaps 21 sides, 15 top, 36 bottom).
v0.4: border copies the mask rect and grows by BorderWidth (7 units) on every side.

Release 1.0.0 (2026-10-14): user approves v0.4 look. `mods/minimap/tools/release.py` (after
`build.py`) writes `dist/SilverPines-Minimap-1.0.0.zip` (34 MB, 235 files): unmodified
BepInEx be.788 IL2CPP + LICENSE, .NET licenses, `BepInEx.cfg` (console off, disk log on,
UnityLogListening off), plugin + MIT license in `BepInEx/plugins/SilverPinesMinimap/`,
`README-Minimap.txt` (English, from `mods/minimap/docs/README.txt`). Checks: version match, fresh DLL,
no game files/interop, no local drive paths in own files. BepInEx source ZIP copied next to it
for Nexus "Optional files". Nexus page text: `mods/minimap/docs/nexus.txt` (BBCode).
Logo: `mods/minimap/tools/logo.py --art <1920x1080 key art>` adds a third red block "MINIMAP" under the
title, stitched from the letter-free bands of the PINES block (game's paint and torn edges),
Bahnschrift Bold with ink bleed; output `dist/minimap-logo.png` (key art not committed).

Site (2026-10-14): Silver Pines is the first game with catalog status `mods` (a Polish fan
translation exists, so we don't translate it). Minimap ZIP and BepInEx be.788 source in
`site/public/pobierz/`; mod listed in `game.yaml` `mods:`, Polish guide in
`mods/minimap/README.md`. Nexus URL pending publication.
