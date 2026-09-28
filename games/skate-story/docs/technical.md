# Skate Story: technical

GOG RC1, Unity 6000.0.45f1 Mono, I2 Localization. 2305/2305 entries (2302 by the agent, 3 existing
Polish: language name and health warning): all chapters and epilogue, dialogue, menus, tutorials,
items, goals, achievements, poems; also demo and debug texts. Not textures or letter models.
Delivered as a **delta patch** of `SkateStory_Data/resources.assets` (275 MB → ~78 KB): the game's
managed code is stripped, so no plugin.

## Source and format

- `resources.assets`, MonoBehaviour 785: 2314 records (2305 texts, 9 font references), 20 columns.
  Polish exists at index 15 (`Polish`, `pl`), originally disabled; we enable it in the existing
  selector. Other columns, metadata included, untouched.
- Columns TYPE (speaker, e.g. `Dialogue: Rabbie`), NOTES and 17 languages; `tools/ref_extract.py`
  dumps them to `work/ref-all.json`, `tools/gender_ru.py` compares RU gendered forms with PL (found
  Beea and the Square of Regret skeleton).
- Original SHA-256 `3e65be29272f5879bd907a0d0c7f8134f5b5bd35902263dc65381bb0c3a7a82c`.

## Fonts

Polish uses the existing dynamic `ru-serif-bigcaslon Regular` instead of BigCaslon/Cochin, existing
IMFell for its styles, LiberationSans instead of HelveticaRounded. Static LiberationSans SDF 791 uses
the existing dynamic fallback 789. Font 566 and TMP 791 added to the I2 asset list; all 9 PL font
references filled (`FONT_MAP` in `tools/build.py`). Other languages keep their fonts; no font object
or code modified. Accepted in the vertical test.

## Build

Needs UnityPy and TypeTreeGeneratorAPI (root `requirements.txt`); reads DLL metadata, never runs the
game.

```powershell
.venv\Scripts\python.exe games\skate-story\tools\build.py --original backups\skate-story\resources.assets --managed "C:\Games\Skate Story\SkateStory_Data\Managed" --extract
.venv\Scripts\python.exe games\skate-story\tools\build.py --original backups\skate-story\resources.assets --managed "C:\Games\Skate Story\SkateStory_Data\Managed"
.venv\Scripts\python.exe tools\patch.py release --original backups\skate-story\resources.assets --built games\skate-story\dist\SkateStory_Data\resources.assets --relative "SkateStory_Data\resources.assets" --readme games\skate-story\docs\INSTALL-patch.txt --out-dir games\skate-story\dist --game-name skate-story --package-name Skate-Story --version <version>
```

`--extract` refreshes `translations/en-pl-review.json` from the game table and
`translations/review-notes.json` (translator notes), keeping PL. The default build needs the review
file to match the table and cover all keys; checks source SHA, exact table round trip, tokens (incl.
`(S)`, `(C)`), newline counts, fonts, reads the output back, only object 785 changed, the other 19
columns intact. Output `dist/SkateStory_Data/resources.assets`. The patch was verified applied to a
copy of the original, byte-identical with the build.

Test install (repo root): `tools/install.py --game "C:\Games\Skate Story\SkateStory_Data" --built
games\skate-story\dist\SkateStory_Data --backup backups\skate-story` (`--restore` brings the
original back). Originals: `backups/skate-story/`, confirmed vertical:
`backups/skate-story-vertical/`; don't mix them.

`translations/structure.yaml`: 16 groups (chapters ch1–ch10, UI, items, tutorial, other).

## Why no plugin (2026-09-20/21)

The plugin itself worked (enabled slot 15, filled texts, repointed fonts) but the loader can't start:

- Doorstop enters fine; the BepInEx 5 and 6 preloader crashes with
  `MissingMethodException: System.Reflection.Module.GetPEKind` in `PlatformUtils.SetPlatform` (ARM
  detection). Unity 6 strips unused `mscorlib` methods.
  [BepInEx#1312](https://github.com/BepInEx/BepInEx/issues/1312): expected; use "BepInEx with
  corlibs".
- `dll_search_path_override` with only `mscorlib`, then with all 15 corlibs for 6000.0.45
  (`vendor/unity-corlibs/6000.0.45.zip`): the game hangs before the warning screen, no log.
- Own entry point (`tools/loader/notgeeseLoader.cs`) checked statically:

| element | Boomerang X | Skate Story | Anger Foot (works) |
| --- | --- | --- | --- |
| `Module.GetPEKind` in `mscorlib` | missing | missing | present |
| `System.Linq.IGrouping` in `System.Core` | missing | present | present |
| `AmbiguousMatchException..ctor(string, Exception)` | missing | missing | present |

  Harmony's `AccessTools` static ctor needs that constructor, in every BepInEx from 5.4.17 to
  6.0.0-be.788. Only a Harmony fork without it would do: a separate decision, not a workaround.
  Hence the delta patch.

## Tests

- Vertical confirmed by the user in game (selector, Polish letters, fonts).
- Full table verified structurally; full campaign not played. Review fixes (2026-09-26) enter with
  this build. What to check: `docs/decisions.md`.
