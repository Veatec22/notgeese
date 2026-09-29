# Lovers in a Dangerous Spacetime: technical

## Existing translations

No available Polish translation found (2026-09-29). Official: EN, FR, IT, DE, ES, PT-BR, RU, JA,
KO, ZH-Hans, ZH-Hant (Steam store table, game code). GOG lists "polski" only in its site/review
language switcher, not as a game language. No fan translation on GrajPoPolsku or elsewhere.

## Game

GOG build, `version` TextAsset `1.4.5-83666ded3`. Unity **5.0.2f1**, Mono, **x86** (PE machine
0x14C). `mscorlib.dll` not stripped (`GetPEKind` present). Needs BepInEx 5 **win_x86**; vendor has
only x64 builds so far.

## Texts

- 11 `LocalizationSet` ScriptableObjects in `resources.assets` (path IDs 3–13), loaded by
  `Resources.Load("Localization/Localization-<code>")`. 325 key/value pairs per language, ~1600
  English words. No typetree; raw layout: name, `Language {name, code, systemLanguage}`,
  `StringKeyValuePair[] {key, value}` (aligned strings). `work/<code>.json` holds all 11.
- `Localizer` (singleton, created lazily): ctor takes `Language.SupportedLanguages()` (static
  array of 11), drops those `PlatformLocalizationSupport.PlatformSupportsLanguage(systemLanguage)`
  rejects, then picks from `Application.systemLanguage` via `languageFromSystemLanguage`.
  `SetCurrentLanguage(Language)` loads the set, builds a dictionary, raises `LanguageChangedEvent`.
  `GetStringValue(key)` returns the key itself if missing. Saved setting stores the code;
  `languageFromCode` falls back to `en_us` for unknown codes (removing the plugin → English).
- Scene/prefab texts go through `LocalizeText` (205), `LocalizeTextMesh` (30),
  `LocalizeTextByPlatform` (3). Unlocalized visible strings in all languages: credits (level13),
  ending scene TextMeshes `♥ LOVE HAS PREVAILED ♥` / `Thanks for playing!` (level10),
  `ThanksForPlayingController` (`Better love next time!`, `Thanks for playing!`, demo only?).
  Rest are placeholders overwritten at runtime or debug markers.
- No texture with baked text except logos (title logo stays).

## Fonts

`TorontoSubwayBold` (dynamic, fallbacks Noto Sans + CJK) and `NotoSans-Regular` both contain all
of `ąćęłńóśźżĄĆĘŁŃÓŚŹŻ`. No font work expected.

## Plugin

BepInEx 5.4.23.5 **win_x86** + Harmony (`plugin/Plugin.cs`), no game file replaced:

- Postfix `Language.SupportedLanguages` → append `Language("Polski", "pl-pl", SystemLanguage.Polish)`
  (one instance, compared by reference).
- Postfix `PlatformLocalizationSupport.PlatformSupportsLanguage` → true for Polish.
- Postfix `Localizer.languageFromSystemLanguage` → Polish system → Polish.
- `Localizer.SetCurrentLanguage(Language)` prefix/finalizer set a flag while Polish loads;
  `localizationPath(Language)` returns the English path for Polish; `LocalizationSet.
  GenerateDictionaryRepresentation` postfix overlays `pl.tsv` while the flag is set. The original
  method then sets `currentLanguage` and raises `LanguageChangedEvent` itself.
- If `Localizer` already exists when the plugin loads, Polish is appended to its `supportedLanguages`.
- Logs game + Unity version; `Polish active: N of 325 texts` on every switch to Polish.
- Texts outside the tables: `Static.*` entries in the review file, shipped as `static.tsv`
  (exact English → Polish, compared trimmed). Postfix `ThanksForPlayingController.Setup` swaps the
  end-screen labels (`♥ GAME OVER ♥`, `Better love next time!`, `♥ LOVE HAS PREVAILED ♥`,
  `Thanks for playing!`, string constants in code); postfix `CreditsController.Start` swaps credits
  headings under `creditsContainer` (names stay). Patched separately: if they fail, the language
  still works. Only when Polish is the current language.
- BepInEx entrypoint moved to `Localizer..cctor` (`plugin/BepInEx.cfg`, see Tests).

Uncertain until tested: BepInEx 5.4.23 x86 on Unity 5.0.2 (old Mono); chainloader timing vs the
first `Localizer` access; language list in Options accepting a 12th entry.

## Files

| File | Purpose |
| --- | --- |
| `translations/en-pl-review.json` | 325 LocalizationSet keys + 26 `Static.*` screen texts. |
| `translations/structure.yaml` | 10 groups, intro/ending/tutorial sequences for the workspace. |
| `plugin/BepInEx.cfg` | Entrypoint override shipped as `BepInEx/config/BepInEx.cfg`. |
| `tools/extract.py` | Reads the 11 sets → `work/ref-<code>.json`, adds new English keys to the review file. |
| `plugin/Plugin.cs` | BepInEx plugin. |
| `tools/build_plugin.py` | Compiles plugin, writes `pl.tsv` + `static.tsv`, assembles package (`--compile-only` to check). |
| `docs/INSTALL-plugin.txt` | Player readme (`READ-ME.txt`). |

## Build

Needs `csc.exe`, the installed game (references from `Managed`), `vendor/bepinex/win_x64` core
for compiling and `vendor/bepinex/BepInEx_win_x86_5.4.23.5.zip` for the package.

```powershell
.venv\Scripts\python.exe games\lovers-in-a-dangerous-spacetime\tools\build_plugin.py --game "C:\Games\Lovers in a Dangerous Spacetime"
```

## Tests

- 2026-09-29: plugin compiles against the GOG 1.4.5 assemblies. Vertical 0.1 package (213/325
  entries: menus, settings, controls, intro, tutorial, hub, ship/character select, first campaign
  lines) built and extracted into the GOG install (adds files only, nothing overwritten).
- First launch: **crash** before the first screen (`mono.dll` access violation). Stack:
  `UnityEngine.Application..cctor` → `Chainloader.Initialize` → `ThreadingHelper.Initialize` →
  `GameObject.AddComponent`, called from `MonoManager::LoadAssemblies`: Unity 5.0 runs
  `Application`'s static constructor while loading assemblies, too early to create objects.
  Fix: package ships `BepInEx/config/BepInEx.cfg` with `[Preloader.Entrypoint]`
  `Assembly-CSharp.dll` / `Localizer` / `.cctor` (runs on the game's first text lookup, before
  the language list exists). Other settings keep BepInEx defaults.
- Retest by the user, 2026-09-29: game starts, Polski in the language menu, vertical texts shown.
  Log: `Chainloader` started from Assembly-CSharp, `Polish active: 213 of 325 texts`.
  `Application.version` reports `1.0`; the real build is `1.4.5` (TextAsset `version`).
- Full translation (325/325 + 26 screen texts) built; credits and end screen not seen in game yet.

## Game material

Repo holds only translation text and tools. *Lovers in a Dangerous Spacetime*, its text and
characters belong to Asteroid Base; unaffiliated. Works only with a legal copy.
