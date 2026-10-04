# GRIME: technical

## Inspection (2026-10-04)

- Installation: `C:\Games\GRIME`, GOG game ID `1415154613`, build ID
  `57311255189223593`. PlayerSettings version `1.3.5`; Unity `2021.3.30f1`, Mono, x64.
- No available Polish translation found. [GOG](https://www.gog.com/en/game/grime)
  lists no Polish support. Search results for a Polish patch concern GRIME II.
- Other translation lead: [Calypso's Turkish patch](https://techolay.net/sosyal/konu/grime-turkce-yama-2026.190366/).
  Not downloaded; no technical assumptions taken from it.
- BepInEx/Harmony blocked by stripped `Managed/mscorlib.dll`: no `GetPEKind` string,
  `AmbiguousMatchException` has three constructors. Apply the repo's documented delta fallback.

## Texts and fonts

- `GRIME_Data/data.unity3d` (83,762,322 bytes), SHA-256
  `aea9e6c80778d895e47f0890c505dccb2f80a2e661fee84ee84074ddfc526e9d`.
  I2 `LanguageSourceAsset` `I2Languages`, MonoBehaviour object 190, 2,491,000 bytes.
  Code is in `Managed/AD_Localization.dll`, not Assembly-CSharp.
- 2,655 unique terms: 2,648 text terms (three empty English values), seven font references.
  Prefixes: WorldText 1,210; Item 804; UI 385; Bestiary 154; AreaTitle 45;
  General 41; DLC 9; Fonts 7. Includes unused/demo/temp entries; active scope still needs checking.
- 13 columns: en, de, fr, es, it, ru, zh-CN, ja, ko, ar (disabled), pt, he, zh-TW.
  English is column zero. Serialized term Description is absent despite the managed field.
  Source header is 56 bytes; terms precede languages. Preserve flags, touch arrays and trailing settings.
- Tokens include `<an=...>`, `<style="...">`, `<sprite=...>`, `<j>`, `<cspace=...>`,
  standard TMP tags and line breaks. Style names and action identifiers remain English.
- The bundled NotoSerif-Regular TTF has all 18 Polish letters. Inspected TMP fonts are dynamic
  (`m_AtlasPopulationMode = 1`); the initial atlas lacks many Polish glyphs. Runtime generation
  and every UI font role still require an in-game check.
- NPC keys include scene/branch names and numeric line suffixes. Sort numeric suffixes within
  each branch; lexical order alone is wrong. Internal NPC names can differ from visible names.

## Extraction

```powershell
.venv\Scripts\python.exe games\grime\tools\extract.py --game "C:\Games\GRIME"
```

Writes all columns and source hash to ignored `work/source.json`; never changes the game.

## Verdict and verification

Go via delta patch. A scratch experiment changed one English value to a longer UTF-8 string
including Polish lowercase letters, saved the LZ4 bundle, reopened it and parsed all 2,655 terms.
All 13 language definitions and every other value survived; only object 190 changed, every other
serialized object's raw bytes matched. Output: ignored `work/reinjection-check.unity3d`.
This was a file-only experiment. See the vertical below for the current installed state.

## Vertical 0.1 (2026-10-04)

355/2,648 text entries translated: main menu, all settings, common actions, checkpoint and
attribute UI, inventory/legend, core tutorials, opening prompts, Yon's first conversation and
weapon gift, opening area names, first weapon and selected creature/item descriptions.
Other entries fall back to English. Direction accepted by the user; bible started.

- Appended I2 language `Polski` / `pl`, column 13; original 13 columns and font references retained.
  `GameOptions.LoadLanguages` uses `LocalizationManager.GetAllLanguages`; `SetUILanguage`
  maps dropdown labels back to the same list. The Hebrew-removal correction covers the new
  final column. Settings save/load stores language names; persistence still needs testing.
- `tools/bundle.py` preserves original UnityFS compression blocks. It appends the new I2 object
  to the serialized resources file, updates only its object-table pointer/size and file length,
  and shifts the following resource node's directory offset. Old object bytes remain unreferenced
  in the local build. Modified metadata/boundary blocks and appended bytes are compressed anew.
  No resource streams or other objects are rebuilt. This keeps the delta ZIP at 1,154,234 bytes.
- Build refuses a different original SHA-256 before creating output. After saving/reopening,
  exactly I2 object 190 differs; original language values/flags, object set and new source match.
- Python delta release verified reconstruction; the packaged C# applier was applied/restored in
  ignored `work/applier-test`, with exact built/original hashes. ZIP has only the patch, applier
  and `READ-ME.txt`. No rewritten game asset ships.
- Synthetic bundle tests verify source relocation, all untouched bytes and external resource data,
  reuse of compressed blocks, and refusal of ambiguous object metadata.
- Localization report: no token, gender, address, term, consistency, English, plural, capital or
  typography hits among translated entries; eight UI length hints remain for in-game inspection.
  Untranslated remainder is expected at this stage. No independent full review yet.
- Site build and `tools/check_games.ts` pass. Cover and five gallery images exist. Public download
  remains disabled (`download.kind: none`), status `in-progress`; workspace structure/review and
  Storage icon are pending full translation/review, not claimed complete.

```powershell
# Clean original is also available under backups/grime after the test install.
.venv\Scripts\python.exe games\grime\tools\release.py --game "E:\Repos\niegesi\backups\grime"
.venv\Scripts\python.exe -m unittest discover -s games\grime\tools -p "test_*.py"
```

Local vertical installed using `tools/install.py` into `C:\Games\GRIME\GRIME_Data`.
Original: `backups/grime/GRIME_Data/data.unity3d`; matching player backup:
`C:\Games\GRIME\GRIME_Data\data.unity3d.przed-spolszczeniem`. Applier, patch and readme
extracted into the game directory. Installed file matches the verified build. No game launched.

Restore with the applier in the game directory or:

```powershell
.venv\Scripts\python.exe tools\install.py --game "C:\Games\GRIME" --backup "backups\grime" --restore
```

## Full translation 0.2 (2026-10-04)

The user confirmed that the installed opening vertical works ("śmiga elegancko") and authorized
the full translation. This is a user-reported in-game result, not a claim that the agent launched
the game or independently checked screenshots. Audio intelligibility, dialogue timing and exact
layout limits remain unverified.

All 2,648 text entries are accounted for, including 2,643 non-whitespace originals. Three empty
and two whitespace entries remain empty/whitespace; developer identifiers, personal names and
credits are intentionally retained. Complete scope includes all DLC descriptions, NG+ branches,
items, armor, bestiary, UI, tutorials, NPC dialogue, memories and ambient speech.

The full build reopens successfully; only I2 object 190 differs. Every original language value,
flag and other serialized object remains identical. The packaged C# applier reconstructs the
exact built hash and restores the exact original hash in a scratch copy. Bundle unit tests pass.
No game assets are shipped. No game was launched.

Workspace structure: 12 groups, 173 numerically ordered dialogue branches. Multi-speaker or
uncertain branches retain unknown speakers instead of invented assignments. Bible character
families use the game's NPC keys. Icon exported from original GRIME.exe, uploaded to Storage
`game-icons/grime.png`; public PNG fetched and decoded (128×128, 45,400 bytes). Icon is outside
the repo and package. Cover and five gallery images already exist.

Full independent review and its 42 integrated edits are recorded in `docs/decisions.md`.
Final package: `dist/GRIME-PL-0.2-latka.zip`, 1,225,849 bytes; byte-identical copy in
`site/public/pobierz/`, referenced by game.yaml. Status testing, tested partial.
Installed 0.2 through `tools/install.py`; the existing original backup was retained and verified.
The old vertical applier/patch were moved into ignored work/retired-vertical-package; 0.2 package
contents are beside GRIME.exe. The adjacent player's original backup remains unchanged.
Site build and workspace validation pass. No commit/push or game launch performed.
Next user test: descriptions and scrolling, advanced trait conditions, Shidra/Heod/Yon scenes,
Coda finale, ending-choice prompts and NG+ tutorials. A complete playthrough is still pending.
