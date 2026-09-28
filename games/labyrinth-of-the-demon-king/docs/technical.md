# Labyrinth of the Demon King: technical

GOG buildId 59111742023178281 (store 1.31), Unreal Engine 4.27. 1120/1120 locres entries (menus,
settings, controls, dialogue, tutorials, notes, items, maps, achievements). Delivered as an
**overlay pak + tiny IoStore** (~84 KB ZIP); game files untouched.

## Existing translations

None available found; Steam has no Polish. A Korean fan translation exists (reference only).

## Engine and texts

- `Shinigami/Content/Paks/pakchunk0-WindowsNoEditor.pak`: PAK v11, unencrypted index, mount
  `../../../`; beside it `.utoc`/`.ucas` (IoStore v3, Indexed, no encryption or compression) and
  `global`.
- `Localization/Game/en/Game.locres` sits uncompressed in the plain PAK: locres v3, 1120 entries,
  empty namespace, unique keys, ~60k chars. Byte-exact round trip (`tools/locres.py`, same codec as
  SPRAWL). 11 game languages, no Polish; config lists vi-VN without a locres.
  `InternationalizationPreset=All`.
- Texts keep CRLF paragraph breaks, placeholders and tags; build checks them. Locres has no speaker
  labels.

## Method

- Overlay PAK `pakchunk99-notgeesePL_P.pak` with only `pl/Game.locres` (translated entries only;
  missing entries fall back to source).
- The language picker needs a label: overlay IoStore (`.utoc`/`.ucas`) carries only
  `UI_LanguageSlot` (~24 KB), its package store entry and container header. `tools/language_slot.py`
  finds the CDO by name and appends `pl -> Polski` to `LanguageStrings` (updates map size/count,
  export sizes/offsets; the 12 original labels byte-identical). No blueprint code or language enum
  changed; `GetLocalizedCultures` discovers `pl` by itself (confirmed in game).
- `tools/iostore.py` writes a one-package container: chunk id, minimal store entry, dependency list
  pointing at original packages (not copied), ExportBundlesSize, directory index, blocks, SHA-1 in the
  32-byte UE4 hash field. Layout per CUE4Parse (`FIoContainerHeader`, `FFilePackageStoreEntry`,
  `FIoChunkId`) and UEcastoc `utoc.go`.
- Allowed content is checked inside both containers: PL locres, that widget, minimal header, size cap.
  Negative tests rejected a foreign asset in the PAK, a loose `resources.assets` and a damaged chunk.
  No game-version checksum anywhere.

## Fonts

UI font `ShipporiMinchoB1-Regular_Font` is composite (fallback typeface, sub-typefaces, culture
ranges) and falls back to Lora/NotoSerif/EB Garamond, which have all 18 Polish letters. No fonts
shipped; confirmed in game.

## Build

```powershell
.venv\Scripts\python.exe games\labyrinth-of-the-demon-king\tools\build.py --game "C:\Games\Labyrinth Of The Demon King"
.venv\Scripts\python.exe games\labyrinth-of-the-demon-king\tools\test_overlay.py
```

`tools/analyze.py` re-extracts texts into `translations/en-pl-review.json` and writes
`work/analysis.json`; `tools/inspect_iostore.py` dumps chosen IoStore chunks to `work/`.

## Tests

- Vertical confirmed in game by the user: separate "Polski" in the picker, switching, choice saved,
  Polish letters, sample texts.
- Full translation built, checked from files, installed (original containers SHA-identical before
  and after); full campaign not played. Check long dialogue, notes, puzzle hints, map names and item
  messages.
- Unknown: whether the widget survives game updates.
