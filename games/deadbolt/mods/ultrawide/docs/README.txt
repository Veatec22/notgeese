DEADBOLT - Ultrawide {version}
==============================

Fills 21:9 and 32:9 screens instead of black bars: the game draws a wider view (e.g. 1920x540
instead of 960x540 at 32:9) in missions, the dock and the apartment, and the main menu and
load screen are centred with working mouse input. No game files are changed: the plugin
adjusts the game's data in memory at start.

Tested at 32:9 (5120x1440) on Steam build 22449372. 21:9 is computed the same way but has not
been tested in game. 16:9 and narrower screens are left unchanged.


INSTALL
-------
1. Close the game.
2. Steam: DEADBOLT > Manage > Browse local files.
3. Extract the ZIP next to deadbolt_game.exe: d3d9.dll and the ultrawide folder.
4. Start the game normally.


SETTINGS
--------
ultrawide\settings.ini (restart the game after a change):
- Enabled=0 turns the widescreen off.
- VirtualWidth=0 matches your main display. Set a number (even, 961-3840) to force a width at
  540 px height, e.g. 1280 for 21:9 or 1920 for 32:9.


POLISH TRANSLATION
------------------
The same d3d9.dll also runs the Not Geese Polish translation (notgeese.cc). Both packages can
be extracted in any order; use the latest version of each. Another mod that ships its own
d3d9.dll cannot run alongside this one.


IF SOMETHING IS WRONG
---------------------
ultrawide\LogOutput.log shows the game version and each step (notgeese\LogOutput.log
if the Polish translation is installed too). If the game data looks different
from what the mod expects (e.g. after an update), the widescreen switches itself off with a line
in that log and the game runs normally.


UNINSTALL
---------
With the game closed, delete d3d9.dll and the ultrawide folder (if you also use the Polish
translation, keep d3d9.dll and delete only the ultrawide folder).


CREDITS AND LICENSES
--------------------
d3d9.dll: Not Geese plugin, MIT License (ultrawide\LICENSE.txt), source:
https://github.com/Veatec22/notgeese/tree/main/games/deadbolt
Includes MinHook 1.3.4 (BSD), see ultrawide\LICENSE-MINHOOK.txt;
source: https://github.com/TsudaKageyu/minhook/tree/v1.3.4
DEADBOLT belongs to Hopoo Games; this is an unofficial fan mod with no game files inside.
