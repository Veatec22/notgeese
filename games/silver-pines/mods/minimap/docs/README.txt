Silver Pines - Minimap {version}
================================

Shows the game's own quick map as a small minimap in the top-right corner while you explore,
fight and sneak. It fades out for dialogue, phone calls, cutscenes, examining and picking up
items, notes and inventory interactions, and fades back in when you are in control again.
Holding the quick map key still opens the full quick map as usual.

F7 turns the minimap on and off (the choice is remembered).

Tested on game version 610_173504 (Windows). No game files are changed or replaced.


INSTALL
-------
1. Close the game.
2. Extract everything from this ZIP into the game folder, the one with Carpenter.exe.
   (Steam: right-click Silver Pines > Manage > Browse local files.)
3. Start the game. The FIRST start takes 1-3 minutes with nothing on screen while BepInEx
   prepares itself (it needs an internet connection once). Later starts are normal.

Steam Deck / Linux (Proton): set the game's launch options to
    WINEDLLOVERRIDES="winhttp=n,b" %command%


SETTINGS
--------
After the first start, edit BepInEx\config\pl.notgeese.silverpines.minimap.cfg
(restart the game afterwards):
- ToggleKey      key that turns the minimap on/off (default F7)
- Top / Right    which screen corner
- Width, Height, MarginX, MarginY   size and position (1920x1080 UI units)
- MapScale       lower shows more of the map (default 0.5)
- FadeSeconds, SettleSeconds        fade time and delay after interactions
- BorderOpacity, BorderWidth        the dark torn border


UNINSTALL
---------
Delete from the game folder: winhttp.dll, doorstop_config.ini, .doorstop_version,
changelog.txt and the folders BepInEx and dotnet.
To remove only the minimap, delete BepInEx\plugins\SilverPinesMinimap.


TROUBLESHOOTING
---------------
The log is in BepInEx\LogOutput.log. If a game update changes the map code, the mod switches
itself off with a line in that log and the game keeps working without it.


CREDITS AND LICENSES
--------------------
Minimap plugin: MIT License, see BepInEx\plugins\SilverPinesMinimap\LICENSE.txt.
Includes the unmodified BepInEx 6.0.0-be.788 (Unity IL2CPP, win-x64), LGPL-2.1, see
BepInEx-LICENSE.txt. Source code of this exact version:
https://github.com/BepInEx/BepInEx/tree/5b766a3b7f6c164d4798924a93f3acf4db769d06
BepInEx ships the .NET 6 runtime in the dotnet folder (MIT, see dotnet\LICENSE.TXT).
Silver Pines belongs to its developers and publisher; this is an unofficial fan mod.
