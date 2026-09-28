# OTXO: technical

GOG 1.106, GameMaker compiled to native code (YYC). 1364 entries: menus, settings, tutorial, 102
liquors, all beach characters' dialogue, the Scripture of Bekatua, the whole journal, weapon names,
run stats. 104 more keys are empty or symbolic in the original and stay untouched. **Polish takes
the Chinese slot**; the package is one text file (72 KB) plus readme, no game bytes at all.

## Existing translations

No Polish found. A Japanese fan mod (WitheredPoppiMk-4) replaces the same Chinese-slot files and
tells players to check that "the flag changed to Chinese"; a Turkish set also just replaces files.

## Format

Texts are plain INI files next to the exe, one per language, UTF-8, CRLF, one section, lines
`<number>="<text>"`:

```
script_english.ini                    [english]             1468 values
OTXO_script_english_fre-FR.ini        [french]
OTXO_script_english_ger-DE.ini        [german]
OTXO_script_english_por-BR.ini        [portuguese]
OTXO_script_english_rus.ini           [russian]
OTXO_script_english_spa-ES.ini        [spanish]
OTXO_script_english_zho-CN.ini        [chinese-simplified]
```

**There is no eighth slot:** `data.win` has no bytecode chunks; the six file names and seven section
names are literals in `OTXO_Release.exe`. A `script_polish.ini` would never be read. Polish replaces
Chinese; after install the game has no Chinese; restoring the backup brings it back.

## Why Chinese: fonts

29 baked fonts in `data.win`; most can't write Polish:

| font | face | glyphs | Polish |
| --- | --- | --- | --- |
| `font1`, `font2`, `font6` (menus) | ITC Avant Garde Gothic | 190 | only `ó` |
| `font1_rus` (Russian variant) | Noto Sans Mono | 273 | only `ó` |
| `font4`, `font5`, `dialoguefont1` (dialogue) | Courier New Baltic | 437 | full |

`obj_font_loader` loads TTF fonts from next to the exe (`notosans.ttf`, `yahei.ttf`, both with all
18 Polish letters). Chinese is the only slot drawing UI with a font from disk instead of a baked
one. `build.py --slot ger-DE` builds the same for another slot.

## Build

```powershell
.venv\Scripts\python.exe games\otxo\tools\extract.py --game "C:\Games\OTXO"
.venv\Scripts\python.exe games\otxo\tools\build.py --game "C:\Games\OTXO"
.venv\Scripts\python.exe games\otxo\tools\ref_extract.py "C:\Games\OTXO"
```

The English file is the template: section header swapped, translations put into existing lines, so
untranslated entries stay English and the original's quirks survive (8 keys without quotes, one line
with a char after the closing quote, other languages with different key sets, French repeats four
keys). The build refuses to write unless:

- rewriting English with no translation gives it back byte for byte;
- the result has the same key set and line count as English;
- every value read back is a translation or the untouched original;
- the section header is `[chinese-simplified]`;
- no text contains a quote or newline;
- the archive reopened matches the output byte for byte.

Source `script_english.ini` pinned by SHA-256. Output `dist/OTXO_script_english_zho-CN.ini` and
`dist/OTXO-PL-<version>.zip`. `extract.py` refreshes English in `translations/en-pl-review.json`
(104 empty keys skipped). `ref_extract.py` dumps all languages to `work/ref-all.json`; Russian was
used for gender and to confirm joined texts ("В: ", "СРАЖАЕТСЯ С: "). `translations/structure.yaml`:
9 groups by line-number blocks. Test install: `tools/install.py` at the repo root.

## Flag stays Chinese

- Flags are one sprite `sprFlags`, 7 frames of 100×50 px on texture page 1 at known coordinates.
- A TXTR entry is seven numbers: `scaled, mips, blob length, width, height, ?, pointer`; the third is
  the compressed length, so a smaller blob with a fixed length shifts nothing.
- The wall is the codec: **GameMaker doesn't use public QOI.** A from-scratch decoder diverges on all
  three pages; no format variant matches the header pixel count (page 0: 4 096 declared, best 4 912;
  page 1: 67 108 864 vs 65 789 785; page 2: 33 554 432 vs 40 018 942). Different errors mean a
  different construction, to be read from an implementation, not data.
- UndertaleModTool would produce a modified 15.8 MB `data.win` with all game content: forbidden to
  ship; a binary patch doesn't help (re-encoding changes the whole 8 MB stream, breaks on updates).

## Tests

- French slot (1.106): slot takeover works, font doesn't ("Język" as "J zyk", matching the
  `font1`/`font2`/`font6` glyph table). Restored.
- Chinese slot: **confirmed in game** with full Polish letters (Nowy przebieg, Opcje, Język, Wyjdź do
  pulpitu, ZATWIERDŹ).
- Full translation installed, not played: long liquor descriptions and journal wrapping (longest
  157 chars), stats screen, language kept between runs. More in `docs/decisions.md`.
