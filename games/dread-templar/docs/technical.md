# Dread Templar: technical

GOG 1.0.2b fix, Unity 2019.4.40f1, x64. 636 text entries, 791 translated fields (`name`/`text`; 6 empty names skipped): menus, settings, controls,
tutorial, in-game messages, dialogue, cutscenes, level and boss names, weapons, runes.

## How the game stores text

One TextAsset in `resources.assets` (path ID 393): pretty-printed JSON keyed by language code →
category → entry id → `name` / `text`:

```json
{ "eng": { "menu": { "mnt_004": { "text": "Options" } } } }
```

Nine languages plus **an empty `"pol"` block** between `"rus"` and `"por"`. Not strict JSON: one
German entry has a trailing comma (Newtonsoft accepts it). Categories: gametext, cutscene, menu,
emblem, add01, add02. Some `name` fields are numbers (speaker ids).

Polish is half-built in code: `GlobalVars.SetLanguage`, `SaveLanguageStr` and
`InitialGameLanguage` already handle `pol` (a Polish Windows picks it up once the block has
content). Missing: the menu. The options menu has language buttons `LanguagePick_eng_00` …
`jan_08` under `Language_ToggleGroup` (a `GridLayoutGroup`) plus `LanguagePick_ita_03`, a
complete Italian button the developers disabled and parked in the sibling
`Language_Toggle_Panel`. `LanguageToggleGroup.filterToggle` is a serialized array of exactly nine,
and `LoadCurLanguage` maps the saved code to an index with a switch over the original nine
(unknown → 0 = English, which then overwrites the saved language).

## Plugin

BepInEx 5, `plugin/Plugin.cs`: fills the `pol` block from `pl.tsv` (kind `t` text / `n` speaker
name, `category/key`, text) and revives the parked Italian button in every scene: moves it into
the grid, appends it to `filterToggle` as index 9, code `pol`, label "Polski" (label reached via a
child object's `text` property, no TextMeshPro binding). Disabled objects are found without
`GameObject.Find`. Healthy log: "Polish button revived and put into the language grid", "First
Polish text served to the game". Earlier the translation shipped as 35 replaced files (789 MB:
`resources.assets`, a same-length IL rewrite of `LoadCurLanguage`, 33 scenes); the plugin package
is < 1 MB.

Polish letters render (`Dźwięk`, `Zarządzanie danymi`, `Zatwierdź` confirmed in game) although
`LiberationSans SDF` stops at Latin-1: something deeper in the fallback chain covers them, likely
the serif `SourceHanSerifTC` atlas (Latin Extended-A).

## Files and build

| File | Purpose |
| --- | --- |
| `translations/en-pl-review.json` | One entry per text field: `namespace` = category, `key` = `<key>/<field>`. |
| `translations/structure.yaml` | 6 groups by category. |
| `tools/game.py` | Reads the language JSON from `resources.assets`. |
| `tools/texts.py` | Review → Polish tree; `polish_tree(english)` gives a full `"pol"` block for developers. |
| `tools/extract.py` | Dumps English and refreshes the review file. |
| `tools/build_plugin.py` | `pl.tsv`, plugin, package. |

```powershell
.venv\Scripts\python.exe games\dread-templar\tools\build_plugin.py --game "C:\Games\Dread Templar"
```

## Tests

- Polish text and diacritics in menus confirmed in game.
- Not confirmed: button placement in the grid, choice surviving a restart, pause menu like the
  title screen. Nothing beyond menus read in place; long strings may overflow.
