# Rain World: technical

GOG v1.11.8 (build 59599002084023645), Downpour 1.9.16, The Watcher; Unity 2020.3.45 Mono x64.
4913/4913 entries (+ `POLISH` for the language button): 2473 `strings.txt` entries, 1654 lines of
conversations, pearl readings, echoes, chatlogs and broadcasts, 787 lines of Downpour developer
commentary; ~62k words, 401 conversation files in `text_pol`. Delivered as a **Remix mod with a
plugin** adding a separate language "POLSKI"; no game file replaced; no BepInEx shipped (the game
has its own).

Out of scope: Inv minigame (`mods/moreslugcats/content/text_eng`, English in every language),
credits (`text/credits`, names), images with text. `mods/watcher/pearls` and `pearlslides` are
animation scripts without text.

## Existing translations (2026-09-23)

- [Polish Translation](https://steamcommunity.com/sharedfiles/filedetails/?id=3465699028) on Steam
  Workshop (Astronomia, 2025-04-17): base game only, replaces English, Downpour announced; not
  available for GOG through official channels.
- [Ukrainian Localization](https://steamcommunity.com/sharedfiles/filedetails/?id=3761321599):
  full with DLC as a Workshop mod; proof a separate language via mod works. No sources found.
- Polish official wiki (Miraheze): naming source, see the bible.

## Game

- Own **BepInEx 5.4.17** with MonoMod and `BepInEx.MultiFolderLoader`. Plugins load only from
  enabled mods: `StreamingAssets/mods/<id>/plugins/*.dll`, list in `StreamingAssets/enabledMods.txt`
  (set by the REMIX menu). The game cleans `BepInEx/plugins` by `whitelist.txt`: put nothing there.
- DLCs (moreslugcats = Downpour, watcher, expedition, jollycoop, rwremix) are mods in `mods/` too.
- `mscorlib` not stripped.

## Texts

Code: `InGameTranslator`, `Conversation.LoadEventsFromFile`, `Menu.OptionsMenu`.

- **Languages** are `InGameTranslator.LanguageID : ExtEnum`; new ones can be added at runtime.
  Text folder `text/text_` + first three letters of the name (`LocalizationTranslator.LangShort`):
  `Polish` → `text_pol`. Options save the name (`Language<optB>Polish`).
- **strings.txt:** CRLF lines `key|text`, first char a marker (`0` plain, `1` encrypted; all plain
  today). Key is the English literal in code or an id (`tips-distract`, `mod_menu_restart`).
  `LoadShortStrings` loads English, then the current language **only if
  `StreamingAssets/text/text_<lang>/strings.txt` exists in the base game**; mod files come after. So
  the plugin loads ours itself (postfix on `LoadShortStrings`). `Translate` returns the argument on a
  missing key: untranslated stays English.
- **Conversations:** `text_<lang>/<N>[-<character>].txt`, XOR-encrypted:
  `Custom.xorEncrypt(text, 54 + N + language_index * 7)` (names without a number: sum of
  `char - '0'`), first char then set to `1`. Key = slice `[54:54+1447]` of
  `RWCustom.Custom.encrptString`; `rw.py` reads it from Assembly-CSharp and checks it on `1.txt`
  (not stored in the repo). A file starting with `0` is read without decryption: ours are plain.
  Missing file → the game falls back to English ("RETRY WITH ENGLISH"). Line instructions:
  `N : N : text`, `N : text : N`, `SPECEVENT : …`, `PEBBLESWAIT : N`; `<LINE>` = line break.
  `rw.split_dialogue_line` separates text from instructions. Only name clash base/DLC: `36.txt`
  (both "NOT IN USE").
- **Region names** (`world/<reg>/displayname.txt`) are translated via `strings.txt`: plain `str:`.
- **Fonts:** an unknown language gets the base `font` and `DisplayFont`
  (`InGameTranslator.LoadFonts`), which have all Polish letters (BMFont descriptions in
  `resources.assets`). No language-specific images.
- **Options menu** builds language buttons from the fixed `OptionsMenu.languageOrder` (10 languages,
  two 220 px columns, rows every 40 px). Label = `Translate(name.ToUpper())`: hence
  `POLISH|POLSKI`.

### Chatlogs, broadcasts, developer commentary (Downpour)

- `MoreSlugcats.ChatlogData.DecryptResult` decrypts chatlogs, Spearmaster broadcasts (`lp_*`) and
  commentary **unconditionally** with the current language index, reads via `Encoding.Default` and
  skips the first line (header). Plugin prefix: text starting with `0` is returned as is. Our files'
  first line is `0-<name>`, then plain text.
- Commentary path (`DevCommPath`) falls back to English on a missing file. Russian commentary files
  are 28-byte stubs: nobody translated it officially; we do.
- Speaker color in chatlogs comes from `colors.txt` via `Translate(code)`
  (`Conversation.InitalizePrefixColor`), so translated iterator codes (SCS, BZN, PK…) are
  `strings.txt` entries and must match line prefixes.

## Delivery

Remix mod `notgeese-polski` (`RainWorld_Data/StreamingAssets/mods/notgeese-polski/`):

| File | Purpose |
| --- | --- |
| `modinfo.json` | REMIX menu info. No `target_game_version` (absent = current; nothing pinned). |
| `plugins/notgeeseRainWorld.dll` | `plugin/Plugin.cs`: registers `LanguageID("Polish")`, adds it to `languageOrder` (transpiler by field name), loads `text_pol/strings.txt`, lets plain chatlogs through `DecryptResult`, logs game and Unity versions and every text without a Polish entry. |
| `text/text_pol/strings.txt` | Polish `key|text` entries, marker `0`. |
| `text/text_pol/<file>.txt` | Conversations, pearls, echoes, chatlogs, broadcasts, commentary: the English file with replaced lines, plain text with marker `0`. |

The build checks no BepInEx and no game file is packed. The player enables the mod in REMIX and
picks the language in options. Disabling the mod with Polish selected leaves an unknown language:
the readme says switch to English first.

## Build

```powershell
.venv\Scripts\python.exe games\rain-world\tools\extract.py      # work/en.json from the game (+ literal map)
.venv\Scripts\python.exe games\rain-world\tools\build.py        # dist/notgeese-polski + dist/Rain-World-PL-<version>.zip
.venv\Scripts\python.exe games\rain-world\tools\review.py       # translations/en-pl-review.json
.venv\Scripts\python.exe games\rain-world\tools\install.py      # test: copy the mod into the game (--remove)
```

`extract.py` compiles `tools/StrMap.cs` (Mono.Cecil from the game dir) and adds to each entry the
classes where the text sits in code: translator context and sample selection. Keys in
`translations/en-pl-review.json`: `str:<strings.txt key>` and `dlg:<file>#<line>`. The build refuses
a package when a translation loses a tag (`<PlayerName>`, `{ERROR}`…), has a newline instead of
`<LINE>`, or `|` in text. Batches: `tools/batch.py make|show|merge|status` in `work/batches/`.
`translations/structure.yaml`: 11 groups (`dlg:` by conversation file kind, `str:` by code class or
DLC; code location in `context`).

## Tests

- Vertical **confirmed in game** by the user 2026-09-24: POLSKI in options, menus, start of the
  Outskirts.
- Full translation after independent review: built and installed; in-game test pending. What to
  check: `docs/decisions.md`.

`work/` (ignored) holds decrypted game texts and the Assembly-CSharp literal dump, for analysis only.
