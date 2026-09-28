# Broforce: technical

GOG build 57322835742607320 (1.0.3148), `C:\Games\Broforce`. Unity 2017.4.7f1, Mono, x64.
`mscorlib.dll` is full (has `GetPEKind`): BepInEx 5 starts without workarounds.
Officially 9 languages, no Polish; no available fan translation (Steam forum threads are
pre-localization promises; modding scene = Unity Mod Manager, nothing on text).

## How the game stores text

Own `Localisation.LanguageManager` (`BitCode.Singleton<T>`):

- `LanguageManagerConfig` (ScriptableObject in `resources.assets`): codes
  `en fr de es es-419 pt it jp ko zh-hans`.
- Per language four banks in `resources.assets`: `StringLanguageBank` (408 entries),
  `SpriteLanguageBank` (empty), `RawImageMaterialLanguageBank`, `ReactionBubbleConfigLanguageBank`.
  `ChangeLanguage(code)` loads all four via `Resources.Load`; any null → no change.
- `GetLocalisedString(key)` is the single entry point. `LocalisedText`, `LocalisedTextMesh`,
  `LocalisedMenuItem` refresh on `LanguageChanged`; code menus call `GetLocalisedString`.
- `LanguageMenu.SetupItems` builds entries from `Languages`, name `LANGUAGE_NAME_<code>`;
  choice saved in `PlayerOptions.overrideLanguage`. Start: `GetSystemLanguage()` maps the OS
  language (no Polish → en), then the saved choice wins.
- `LanguageFallbackFont[]` swaps whole fonts for jp/ko/zh.

Outside the bank: bro names and sprite text (kept), a few keyless debug labels.
`tools/bank.py` reads banks raw (no type trees in files).

## Plugin

BepInEx 5.4.23.5 x64, `plugin/Plugin.cs`:

- `LanguageManagerConfig.get_Languages` postfix adds `pl` ("Polski" in the menu);
- `Load{String,Sprite,RawImageMaterial,ReactionBubbleConfig}Bank` prefixes: `pl` → `en`;
- `GetLocalisedString` postfix: `LANGUAGE_NAME_pl` → "Polski"; under `pl` text from `pl.tsv`,
  missing keys logged once;
- `GetSystemLanguage` postfix: Polish Windows → `pl`;
- after bank load logs the count of keys without Polish ("Game text bank: …").

Removing the plugin: saved `pl` is ignored (`ChangeLanguage` checks the list), game falls back
to the system language.

## Fonts

| Font | Kind | Polish letters | Where |
| --- | --- | --- | --- |
| HUDSONNY_BROFORCE | dynamic TTF | Ł ł Ó ó only | menus, most text |
| akzidenz-grotesk-* | dynamic TTF | Ł ł Ó ó only | UI Text (campaigns, lobby) |
| HUDSONNY_BROFORCE_ICONS | bitmap 512×1024 RGBA32 | Ł ł Ó ó, `˛ ˙ ´`, É, Ç | cutscenes, THREAT LEVEL, warnings |
| K-TYPE - NYC | bitmap 512×512 Alpha8 | same | |
| White_Font_8bitWonder | bitmap 256×256 RGBA32 | ASCII only (Latin-1 empty) | waiting for players, cutscenes |
| HudsonOutline | bitmap, scale ≠ 1 | non-ASCII already broken in the original | campaign seconds counter |
| 04B_11, 8-BIT WONDER, ArcadeClassic… | TTF | none | keyless labels |

**Bitmap fonts** (`plugin/PolishGlyphs.cs`): reads the atlas (Blit → ReadPixels), composes a
letter from the base and an accent of the same font (acute cut from É over E, dot from `˙`,
ogonek from `˛` at the bottom-right), places it in free atlas space (prefix sums over char
rects and pixels) and adds a `CharacterInfo`. Writes with `Graphics.CopyTexture` into the same
texture (RGBA32/Alpha8), else a new texture on the font material. Missing accents are drawn in the
stroke width measured on "I", with the font outline. Orientation: glyph bottom-left
(vert.x, vert.y+vert.height) ↔ (uv.x, uv.y); `flipped` chars (W, w, ´, dashes) lie transposed:
(s, t) ↔ (uv.x + t·uv.w, uv.y + s·uv.h). Composition in atlas texels, separate x/y scale
(HudsonOutline 2.0 × 1.87). HudsonOutline's non-ASCII entries are copies from ICONS pointing at
random atlas spots: detected by reversed uv orientation vs A–Z and treated as missing. When no
space is left and the texture is replaced anyway (BC7), the atlas doubles in height and old uvs
are rescaled (needed for Ź).

**Dynamic fonts** stay: Unity takes missing glyphs from a system font. Hudson is caps-only, so
system ń/ą/ź came out lower-case; texts drawn with dynamic Hudson are written in caps. Style still
differs; candidate fix: move such texts to HUDSONNY_BROFORCE_ICONS with composed letters.

**3D titles** (`plugin/PolishText3D.cs`): `Text3D` ("DOŁĄCZ DO GRY") uppercases text and uses one
mesh per letter from `characterList`/`meshList` (charA…charZ in scenesshared, A–Z only), width
from `SourceFont` (K-TYPE, `GetCharacterInfo(c, 42)`); unknown char = space. Meshes: extruded in z
(±13.75), height 35.2, "I" stem 8.7, no UV. Before `UpdateText(string)` the plugin adds Ą Ć Ę Ł
Ń Ó Ś Ź Ż = base mesh + a mark prism (flat faces, outward normals).

## Build

```powershell
.venv\Scripts\python.exe games\broforce\tools\build_plugin.py --game "C:\Games\Broforce"
```

Checks keys and placeholders against the game bank, refreshes EN in `en-pl-review.json`,
compiles, writes `dist/Broforce-PL-<version>.zip`. The package carries only BepInEx, plugin and
`pl.tsv`; fonts, atlases and banks stay on the player's disk.

## Tests

- Vertical: "Polski" and texts work; bitmap fonts first skipped (flipped chars, HudsonOutline
  scale, 8bitWonder space) → fixed; menus and map with Polish letters; "DOŁĄCZ DO GRY" with Ł and Ą
  after `PolishText3D` (user). Log: "3D titles: added 9 letters", ICONS, K-TYPE, 8bitWonder,
  HudsonOutline composed.
- Full 397/397 built and installed; check report clean. Full playthrough pending.
