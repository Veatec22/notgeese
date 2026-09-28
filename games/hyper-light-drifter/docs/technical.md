# Hyper Light Drifter: technical

GOG `C:\Games\Hyper Light Drifter`, build 52291896322577314 (release version: read it in GOG
Galaxy). 126/126 entries (110 `MenuText.txt`, 16 `Phrases.txt`). Steam lists EN, FR, IT, DE,
ES, JA (files also have RU); no available Polish translation or fan tools found (a
spolszczeniepl.com "RePack" is a game repack).

## Engine and files

GameMaker Studio 1.4, bytecode 16, **YYC** (native x86, 32-bit, ASLR).
`HyperLightDrifter.exe` (628 812 800 B) holds the whole `data.win` as a FORM block in `.data`
(file 0x1017620, RVA 0x1019a20); the runner reads it from the exe image in memory (writes 0x1419a20
into a {pointer, size} struct at `0x1043176`, passed to the chunk dispatcher `0x106cf60`).

Texts live in two plain files next to the exe:

- `MenuText.txt` (UTF-8 BOM, CRLF): 110 entries `=|KEY|n`, then lines `ENG|`, `FRN|`, `SPA|`,
  `JAP|`, `GER|`, `ITA|`, `RUS|`. Lines without `|` are author limit comments ("15 Chars max").
- `Phrases.txt` (UTF-8 no BOM, CRLF): 16 hints `PHR|KEY|n` with `[BUTTON_*]` and `[spr_*]`.

Language codes and picker names are compiled into the exe (`ENG FRN SPA ITA JAP GER RUS` at
0xfdcc19; `ENGLISH FRANÇAIS ESPAÑOL ITALIANO JAPANESE DEUTSCH РУССКИЙ` at 0xff1611). No room for an
eighth, so **Polish takes Italian's place** (Latin slot, same font as English). Russian is out:
`f_cyr` draws Cyrillic in the Latin-1 range ("ó" shows as "у"). `Credits.txt`, `BackerNames.txt`
untouched.

## Fonts

8 fonts; Latin uses `f_uni` ("Visitor TT2 BRK", 9 pt, 1072 glyphs, 512×256 atlas on texture page
10 at (2, 1030)): 5×7 pixels with rows 0–1 for accents; lower case = small capitals (not always
identical, `n` ≠ `N`). All 18 Polish letters have glyph entries (5×7, advance 6) but **empty atlas
cells** (GameMaker rendered a range the face lacked); Ó/ó are real. `tools/fonts.py` composes 16
letters from the game's own: acute = "Ó" − "O", dot = one pixel in row 1, ogonek = two pixels in
rows 7–8 like the "Ç" cedilla (height 9), Ł = stem moved to column 1 + diagonal. Preview
`dist/font-preview.png`.

## Method: delta patches of three files

No plugin: YYC is native code without a runtime to hook (like Katana ZERO). Texts: `ITA|` lines
carry Polish (English if untranslated); the rest byte-identical. Exe (`tools/build.py`):

1. "ITALIANO" → "POLSKI" in place (zero-padded).
2. 16 `f_uni` glyphs get new cells in the empty band of page 10 (from row 1424; page content and
   every TPAG end at 1418). Changed in place: x, y (relative to the font rect, pointing outside it
   on the same page) and height (9 for ogonek letters).
3. New page-10 PNG (`tools/pngsplice.py`): original deflate stream copied bit-exact to the last
   symbol before row 1424, end-of-block code from the original block's table, "last block" bit
   cleared, new blocks with our rows (filter 0), new Adler-32, IDAT split like the original.
4. That PNG sits in a new `.ngpl` section at the end of the exe (read-only data); the TXTR pointer
   for page 10 points to it as an offset from FORM in memory. The old PNG stays. PE header: section
   count, SizeOfImage, checksum (CheckSumMappedFile; yields the stored 0x257afcc5 on the original).

Why not in place: FORM sits in `.data` before game globals (can't grow), and the new PNG is 136 B
longer (the original encodes 624 empty rows in 2483 B with a fixed table). Re-encoding the whole page
fits but would ship 113 KB of game graphics. The exe patch is 747 B (492 new bytes). The TXTR
handler (`0x106d2e0`) passes the PNG pointer to texture creation (`0x1112360`) with one size for
all pages; PNG length isn't derived from pointer differences, so a PNG outside FORM is safe.

Build verification: exe byte-identical outside declared spots; FORM chunks unchanged; other pages
point to the same PNGs; new PNG decodes to the intended image with only Polish letter pixels
changed; non-Polish glyphs unchanged; texts change only `ITA|` lines, each equal to the review PL;
every translated char has pixels in `f_uni`.

Uncertain until tested: whether the runner clamps glyph coords to the font rect (symptom: blanks
where Polish letters should be) and whether the PNG loader accepts our stream (symptom: broken
page 10, menu fonts).

## Build

```powershell
.venv\Scripts\python.exe games\hyper-light-drifter\tools\review.py --game backups\hyper-light-drifter
.venv\Scripts\python.exe games\hyper-light-drifter\tools\build.py --game backups\hyper-light-drifter
.venv\Scripts\python.exe games\hyper-light-drifter\tools\install.py --game "C:\Games\Hyper Light Drifter" [--restore]
.venv\Scripts\python.exe tools\patch.py release --original backups\hyper-light-drifter\HyperLightDrifter.exe --built games\hyper-light-drifter\dist\build\HyperLightDrifter.exe --relative HyperLightDrifter.exe --original backups\hyper-light-drifter\MenuText.txt --built games\hyper-light-drifter\dist\build\MenuText.txt --relative MenuText.txt --original backups\hyper-light-drifter\Phrases.txt --built games\hyper-light-drifter\dist\build\Phrases.txt --relative Phrases.txt --readme games\hyper-light-drifter\docs\INSTALL-patch.txt --out-dir games\hyper-light-drifter\dist --game-name hyper-light-drifter --package-name Hyper-Light-Drifter --version <version>
```

Build accepts only originals (SHA-256 in `tools/hld.py`).

## Tests

- Files: build verification above; the patch rebuilds the build byte-exact (`patch.py release`).
- In game: **not tested yet** (first game with letters in a new exe section).
