# SPRAWL: technical

GOG 1.7 (title screen 2024.12.09), Unreal Engine 4.27. 717/717 entries of the English `Game.locres`:
menus, HUD, tutorials, dialogue, codex, interactions, level, enemy and weapon names and descriptions.
Not voice-over or text in images. Delivered as an **overlay pak** with a separate Polish language
and flag; no game file replaced or removed; uninstall = delete one file. The model for overlay paks.

## Language selector

`Marketplace/UltimateMenu/UserInterface/Examples/WB_MainMenuPanel` builds languages from the
`LocaleInfo_PC` map; extending the map and adding a flag texture is enough. Blueprint bytecode
untouched. A v11 archive needs the 221-byte footer (16-byte GUID) and parent directories in the
index, or the game won't detect cultures. An earlier English-slot swap was diagnosis only, removed.

## Pak content

Five files, 240 KB:

| File | Origin | Size |
| --- | --- | --- |
| `Content/Localization/Game/pl/Game.locres` | ours, 717 entries | 182 KB |
| `Content/StringTables/LocaleInfo_PC.uasset` + `.uexp` | game's language table plus one row | 3.7 KB |
| `Content/Textures/UI/Flags/polska_.uasset` + `.uexp` | flag texture container with repainted pixels | 59 KB |

The flag comes from the game's Ukrainian flag: its alpha mask and native 120×120 BGRA layer kept,
pixels painted white-red. These 62 KB are minimal carrier structures (see AGENTS.md): without the
language table and a flag texture Unreal won't take a new language.

## Reproducibility

The build needs files from your own game copy: `translations/en.locres` and four assets in
`work/assets` (git-ignored; all pinned by SHA-256). **The package can't be built from a clean
clone.**

```powershell
.venv\Scripts\python.exe games\sprawl\tools\prepare_selector_assets.py --game-pak "<game>\Sprawl\Content\Paks\Sprawl-WindowsNoEditor.pak" --oodle "<FModel>\Output\.data\oodle-data-shared.dll"
```

## Build

```powershell
.venv\Scripts\python.exe games\sprawl\tools\validate_translations.py
.venv\Scripts\python.exe games\sprawl\tools\build.py
.venv\Scripts\python.exe -m unittest discover -s games/sprawl/tools -p "test_*.py"
```

Validation: completeness, EN/PL agreement, tags, icons, placeholders, entities, no test markers.
Then locres read-back, key and source hashes, pak read-back, original selector rows preserved, flag
alpha channel. Writes only to `dist/`: `Sprawl-WindowsNoEditor_pl_P.pak` and
`SPRAWL-PL-<version>.zip` (pak + `READ-ME.txt`). `translations/structure.yaml`: 6 groups by
namespace and prefix. Vertical kept in `backups/sprawl/gameplay-vertical-before-full.pak`.

## Tests

- **Confirmed in game** by the user: selector, back to English, choice saved after restart, sample
  dialogue, tutorials and interactions.
- Full campaign pending; review fixes (2026-09-26) enter with this build. What to check:
  `docs/decisions.md`.
