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

No earlier fix found online (2026-10-02). Ideas: a "Full screen" entry in the aspect dropdown
(same technique as Polski in the language list) instead of ini edits; HUD box override off
instead of fixed widths, so any aspect works.
