# Possessor(s): technical

GOG gameId 1839377078, buildId 59986480383674421, `C:\Games\Possessor(s)`. Heart Machine,
publisher Devolver. `ProjectVersion=1.8.0` (DefaultGame.ini). Unreal Engine 5, custom branch
(`++HeartMonster+jenkins-Pose-Release-GamePackage-CL-141295`), project name `Pose`.

## Existing translations

No available Polish translation found (2026-10-01); Steam/GOG list EN, FR, DE, ES, JA, KO,
PT-BR, RU, ZH-Hans, ZH-Hant. No fan translations found in any language.

## Format

`Pose/Content/Paks/Pose-Windows.pak`: pak v11, unencrypted index, mount `../../../`, 4713 files,
Oodle compression (decompressed with a local FModel `oodle-data-shared.dll`, never shipped).
IoStore `Pose-Windows.utoc/.ucas` v8 (same layout as Holy Shoot). Reader: `games/sprawl/tools/game_pak.py`
unchanged.

Localization: 16 game tables in `Pose/Content/Localization/<Table>/<culture>/<Table>.locres`
(locres v3), all listed in `DefaultGame.ini` `LocalizationPaths`. Cultures staged: en, de, es,
fr, ja, ko, pt-BR, ru, zh-Hans, zh-Hant.

| Table | EN entries | words |
| --- | ---: | ---: |
| Articy_Default | 113 | 1233 |
| Articy_Inspectables | 83 | 3236 |
| Articy_Intro | 260 | 2540 |
| Articy_Region_CampusHill | 318 | 3298 |
| Articy_Region_DeadMall | 172 | 1666 |
| Articy_Region_Dockyard | 129 | 1167 |
| Articy_Region_Dream | 94 | 816 |
| Articy_Region_FluorescentPark | 343 | 3439 |
| Articy_Region_InvertedPlaza | 201 | 2013 |
| Articy_Region_Lab | 217 | 2032 |
| Articy_Region_SunkenCity | 480 | 4755 |
| Articy_Region_Zooquarium | 283 | 2707 |
| Articy_SideQuests | 469 | 4454 |
| Game | 282 | 1407 |
| Narrative | 143 | 917 |
| UI | 303 | 1117 |
| Total | 3890 | 36 814 |

Articy tables: namespace `ARTICY`, keys `DFr_<SCENE>_<NNNN>_0x<id>.Text` (dialogue fragments in
order within a scene; speaker not in the key). Markup: UE rich text `<i>…</>`, `<b>`,
`<DLang.Bold>`, `<Header>`, `<Keyword.Item>`, `<Location>`, input decorators
`<Action id="Jump"/>`, placeholders `{0}`, `{ItemName}`, `{br}` etc. Some `<…>` spans are plain
in-world names (`<Agradyne Executive Board Room>`), not tags; keep as written.

## Fonts

cmap check (fontTools on `.ufont`): CormorantGaramond, Gloock, NotoSans, Raleway (all weights) have
the full Polish alphabet. `PSE-Regular` has only ASCII (95 glyphs); used by `<DLang.Pose>`
(1 entry: "Promises - Fear - Blame - Kindness", likely an in-world script). Keep that span ASCII.
This is a cmap finding, not a user report or an in-game test of fallback/rendering.

## Delivery

Overlay pak `Pose/Content/Paks/pakchunk99-notgeesePL_P.pak` with culture `pl` for all 16 tables
(UI, Game, Narrative, 13 Articy) + empty IoStore container `.utoc/.ucas`
(`games/holy-shoot/tools/iostore_empty.py`, container id fixed in `build.py`). No plugin: the
native `PoseSettings` language setting enumerates localized cultures, so Polish appears by itself
(probe 1). No game file replaced; no game asset in the ZIP (4 files incl. READ-ME).

## Build

```powershell
.venv\Scripts\python.exe games\possessors\tools\extract.py --oodle "<local oodle-data-shared.dll>"
.venv\Scripts\python.exe games\possessors\tools\build.py
```

`extract.py` writes all cultures of every table to `work/loc/<culture>/`, plus `DefaultGame.ini`.
`build.py` checks the review file against the extracted English, tags/placeholders/newlines per
entry, locres round trip per table, pak and IoStore read-back, ZIP contents → `dist/Possessors-PL-<version>.zip`
and a staged `dist/Pose/Content/Paks/` for local install. `tools/batch.py` (`init`, `show`, `put`,
`putn`, `puten`, `stats`) handles translation batches; `show` prints the Russian line as a gender hint.
Keys in `translations/en-pl-review.json`: `<Table>/<namespace>/<key>`.

## Tests

- Probe 1 (20 UI entries in `pl/UI.locres`) **confirmed in game** (user, 2026-10-01): Polish
  appears in the language list by itself, so the setting enumerates localized cultures; no UE4SS
  needed. The pak + empty IoStore container mounts.
- Probe 2 (83 entries: UI, tutorial hints, Narrative, prologue scenes) **confirmed in game** by
  the user (2026-10-01): dialogue and pursuits from the overlay show up beyond the menu.
- Full translation 0.1 (3890/3890) built and copied over the probe files (2026-10-01). Check
  report clean except 14 length hints. Published as 0.1 `testing` at the user's request before
  review. In-game test of the full text pending.
- Independent fresh-context review (2026-10-02): all 3890 entries read; extracted English
  matches exactly. Lead applied 17 certain corrections, aligned the workspace district label,
  refined Rhem's voice rule and corroborated flashback F with FR/DE/ES. Four editorial proposals accepted by the user and applied; five
  remain open in `docs/decisions.md`. No new in-game evidence.
- Post-review local build: 3890/3890 entries, 16 tables; source, tokens/newlines, locres, pak,
  empty IoStore and ZIP read-back pass. Check report: only the unchanged 14 length hints.
  Local `dist/Possessors-PL-0.1.zip` contains the corrections; the published 0.1 package is
  unchanged. Next: settle open wording choices, check listed scenes/layout in game, then bump
  the package version on the next release. No install or launch during review.
- Follow-up (2026-10-02): four user-approved wording changes built and verified; length hints
  now 15 (`POCKET_KILLRHEM_0500` adds a hint). All other l10n checks remain at zero.
- Released 0.2 (2026-10-02) with the review corrections; the in-game copy is still 0.1.
