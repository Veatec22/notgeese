# BPM: Bullets Per Minute: technical

GOG build `55844760674411649` (`C:\Games\BPM BULLETS PER MINUTE`). 859/859 entries.
No official or available fan translation (search engines claim Polish exists; the store
language table says no).

## Engine and paks

Unreal Engine 4.25, pak v11. Eleven `pakchunk0*-WindowsNoEditor.pak`, each with a `.sig`
(**pak signing on**). Entries uncompressed. **Index is AES-256 encrypted.** The key posted online
(`766D2004…`) is fake; the real one is written by eight `mov dword [reg+disp], imm32` at
`.text+0xddc33b` of the exe. Never committed: `extract.py` finds it and stores `work/aes.key`.
`tools/game_pak.py` reads the index and extracts files.

## Texts

`BPM/Content/Localization/Game/<culture>/Game.locres`, v3, 859 entries (~2.3k words).
Cultures: en, de, es, fr, it, ko, pt, ru, zh-Hans-CN. `Game.locmeta` v0 (cultures from folders).

## Language selection

C++ `SetUILanguage(EBPMLanguage)`; the enum has 10 fixed entries: en, fr, it, de, es, **ja**,
pt, ru, zh-Hans-CN, ko. `WBP_UISettingPanel` lists `GetLocalizedCultures` with
`GetCultureDisplayName`; `StoreSettings` maps culture → enum, unknown → English (0)
(bytecode read with `tools/kismet.py`). A separate `pl` culture shows up but saves as English.

The **ja** slot exists but the game ships no Japanese `Game.locres`. Polish goes to
`Localization/Game/ja/Game.locres` in an overlay pak; no language disappears. The menu name
comes from ICU: `icudt64l/lang/en.res` has one standalone UTF-16 "Japanese"; the build
overwrites it in place with "Polski" + zero padding (no offsets move). ICU data, not
publisher content.

## Fonts

No game font has ąćęłńśźż (MotorBlock, Proletariat, RunyTunes, NotoSansJP; some have ó/ń),
nor the composite fallback `DroidSansFallback`: missing letters render as a question-mark diamond.
Licenses forbid shipping their glyphs (MotorBlock, Proletariat "all rights reserved";
RunyTunes forbids derivatives). `tools/fonts_pl.py` adds 16 letters to the `.ufont` as
composite glyphs: reference to the font's base letter + our own drawn diacritic. Opened with
`recalcBBoxes=False` so fontTools doesn't re-encode every glyph (else the patch would carry
outlines); bboxes and `maxp` computed from the base letter. Patch adds ~800 B per font, no
publisher outline.

Fonts touched: `MotorblockFontRuntime` (25 widgets: menu, HUD, credits) → `MotorBlockFinalCyr`;
`RunyTunesRuntime` (level transitions, boss bar) → `RunyTunesRevisitedNF`. `NotoSansJP-Bold`
is only used by the rhythm test (texts not in `Game.locres`). `MotorblockFontOffline` (bitmap)
only in `BP_BankOut`. `tools/render.py` renders a sample to PNG. `tools/uasset.py` reads/writes
small UE4.25 packages byte-exact (kept for Font assets, unused in the build).

## Build and package

```powershell
.venv\Scripts\python.exe games\bpm\tools\extract.py "C:\Games\BPM BULLETS PER MINUTE\WindowsNoEditor"
.venv\Scripts\python.exe games\bpm\tools\release.py "C:\Games\BPM BULLETS PER MINUTE\WindowsNoEditor" <version>
```

`extract.py` finds the key and extracts to `work/extract` the English locres, two fonts,
`en.res` and other languages' locres (reference). `build.py` (run by `release.py`) →
`dist/BPM-PL_P.pak`: `ja` locres from `en-pl-review.json`, two fonts with Polish letters,
`en.res` naming "Polski"; inputs pinned in `tools/sources.json`.

`release.py` → `dist/BPM-PL-<version>-latka.zip`: two **format 3 (create)** patches, applier,
`READ-ME.txt`:

- Pak patch creates `BPM-PL_P.pak` from three slices of the player's
  `pakchunk0-WindowsNoEditor.pak` (two `.ufont`, `en.res`; located via the decrypted index;
  data after the 53-byte entry header). ~72 KB own bytes (66 KB is our locres).
- Signature patch creates `BPM-PL_P.sig` as a copy of the player's `pakchunk0_s4-WindowsNoEditor.sig`
  (zero own bytes).

Checksums cover the slices only, not the 3 GB pak. Steam may lay out paks differently; then the
applier refuses without touching the disk (unchecked).

## Tests (user, 2026-09-22, GOG)

- Pak without `.sig` is ignored silently; with a `.sig` copied from `pakchunk0_s4` it mounts
  (block checksums vs signature mismatch doesn't block).
- `pl` culture listed but saves as English; `ja` slot shows Polish and persists.
- Drawn Polish letters: "teraz jest elegancko".
- Vertical (menu, settings, HUD, start) accepted; full translation installed with the applier,
  items, trials, later realms and credits not played.
- Applier: created files byte-identical to the build; restore deletes both; re-apply and
  double-click from the game dir work.

## Next

1. Full test incl. the "Polski" list name.
2. Would a fake `.sig` suffice (drop the signature patch)?
3. Steam: same `pakchunk0` layout as GOG?
