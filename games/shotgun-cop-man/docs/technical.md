# Shotgun Cop Man: technical

## How it works

Unity 2022.3.47f1 (Mono, x64). Texts in I2 Localization compiled into `Assembly-CSharp.dll`,
source asset in `resources.assets` (path ID 4903), 485 terms × 10 languages. BepInEx 5 plugin
(`plugin/Plugin.cs`) adds Polish as the 11th I2 language at runtime; the menu lists languages
dynamically, so it appears in **Options → Language**. No game file replaced.

- Hooks I2 source registration in the manager (the source can be an asset whose `Awake` never runs).
- Binds by class names; logs game + Unity version; missing texts stay English, count logged.
  Healthy start: `Polish added as language 11 of 11` in `BepInEx/LogOutput.log`.
- Old GUID from before the project rename: if that plugin folder remains, BepInEx skips ours
  instead of loading two translations. Readme tells players to delete `NieGesiShotgunCopMan`.
- `pl.tsv` must be written with LF: CRLF left `\r` at the end of every text; TextMeshPro moves the
  pen back on `\r`, so the rating screen ("Otrzymane trafienia:" + `"  "` + number, glued in
  `RatingScreenScript.TriggerRatingScreen`) drew the number over the text. Plugin also trims `\r`.

## Files

| File | Purpose |
| --- | --- |
| `translations/en-pl-review.json` | 485 entries, key = I2 term. |
| `translations/structure.yaml` | 9 groups + Pedro conversation for the workspace. |
| `plugin/Plugin.cs` | BepInEx plugin. |
| `tools/build_plugin.py` | Compiles plugin, writes `pl.tsv`, assembles package. |
| `tools/other_languages.py` | Dumps the other 10 languages to `work/ref-<code>.json` (bible evidence). |
| `docs/INSTALL-plugin.txt` | Player readme (`READ-ME.txt`). |

## Build

Needs `csc.exe` (VS 2022 or .NET Framework 4) and the installed game (references from `Managed`).

```powershell
.venv\Scripts\python.exe games\shotgun-cop-man\tools\build_plugin.py --game "C:\SteamLibrary\steamapps\common\Shotgun Cop Man"
```

Output: `dist/Shotgun-Cop-Man-PL-<version>.zip` (BepInEx 5.4.23.5 + LICENSE, plugin, `pl.tsv`,
`READ-ME.txt`) and the BepInEx source archive next to it (LGPL-2.1).

## Tests

- Steam 1.0.4 (`bundleVersion`, build 20572164): language selection and texts confirmed in game.
  Full playthrough done; user moved the game to `ready` on 2026-09-28 (version 1.0).
- Out of scope: recorded voices; achievement descriptions shown by the Steam client (not in I2).

## Game material

Repo holds only translation text and tools. *Shotgun Cop Man*, its text and characters belong to
its authors; unaffiliated. Works only with a legal copy.
