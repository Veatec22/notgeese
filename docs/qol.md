# QoL fixes

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
