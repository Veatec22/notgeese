# Katana ZERO: technical

GOG 1.0.5. 2851/2851 entries (menus, UI, dossiers, all dialogue, messages, credits). Delivered as a
**delta patch** of `Katana ZERO.exe` and `data.win` (~150 KB package).

## Existing translations

GrajPoPolsku announced a project in Nov 2021 for GOG 1.0.5; no package, last post (June 2024) an
unanswered progress question. The Netflix mobile version reportedly has Polish (not PC). Steam: 10
languages, no Polish. ZenHAX: other-language translators used `exestringz`/HxD; changing string
length crashed the game.

## Engine and texts

GameMaker Studio 2, bytecode 17, **YYC** (native x86, 32-bit, ASLR). No text files and no mod
loader; `data.win` holds graphics, audio and fonts; all text is compiled into `Katana ZERO.exe` as
`.data` constants. Languages in order: EN, JA, KO, DE, FR, ES, PT, RU, ZH-Hans, ZH-Hant.

1. **Arrays `text[language * 32000 + n]`** in `init_lines` (dialogue, 2492) and `init_misc_text`
   (UI, 267). Key = `function:line`: the GML line number YYC stores with every assignment.
2. **Menus and settings** in `init_option_translations` (92): ten strings created in turn plus
   `"end"`, then a script picks one. Key = `function:EN` (`#2` on repeats).

The picker's language name is entry `init_misc_text:1790` in each language, so "Polski" is a normal
text. Dialogue tags: colors `[r] [o] [y] [a] [p] [l]`, close `[/]`, effects (`[*]`, `[!]`,
`[^<>]`, combined like `[r!^<*>]`), `[@]`, `[./]`; an asterisk outside brackets is a speech pause.
`tools/review.py` requires identical tags and line breaks; pause count only reported.

## Method

No plugin: YYC has no runtime to hook; a proxy DLL would need a native loader and in-memory
`data.win` patching. **Polish takes the Russian slot** (fixed 10-language table). Russian has the
best drawing path: all fonts for non-Latin and Latin languages are sprite fonts made with one
`font_add_sprite_ext`, and Russian uses `spr_xirod_font_rus` (full Latin) instead of the Latin-1
TTF `font_xirod`. We only append Polish letters to them.

Exe (`tools/build.py`):
- new section `.ngpl` after `.reloc` with Polish strings (UTF-8, zero-terminated);
- every `mov [esp], addr` / `mov [esp+4], addr` of the Russian version gets the Polish address
  (English if untranslated); each site must have a relocation entry, so ASLR works;
- char maps of four sprite fonts (221, 190, 158, 99 chars) get the missing Polish letters appended;
- verification: every entry in every language read back; outside swapped addresses and the header
  the file is byte-identical.

data.win:
- 90 new letters (16 in five fonts, 8 in `spr_big_font`, xirod also gets ó/Ó) on two new texture
  pages, one per font texture group, added to the group's page list in TGIN (new list, pointer
  moved). **A page outside every group never loads** (first vertical: letters invisible).
- New TPAG items and new copies of six sprite structures with longer frame lists; the SPRT list
  points to the copies.
- **A second `TPAG` chunk right before TXTR** with the full list (old items in order + ours). The
  runner's TXTR handler (`0x18ea6e0`) maps each TPAG item's page number (`+0x14`) to a video-memory
  texture id (`g_TexIDs[tp]`, allocator `0x19bcea0`), but only for items in the TPAG chunk list;
  the TPAG handler (`0x18e974c`) just remembers the list position, so the later chunk wins
  (second vertical: still no letters; third: **confirmed in game**).
- Page pointers after the TXTR list and PNGs at the end of TXTR; all three insertions are multiples
  of 0x80 (72 320 B, 57 KB of it a copy of the old list = plain copy in the patch). Only texture and
  audio data move; their pointers (TXTR list, PNG addresses, AUDO list) are shifted.
- Verification: chunk order, new TPAG list = old + ours, font frames (old unchanged, new = recipe),
  every PNG and sound start at the new address, image order, texture groups.

Uncertain: other places where the runner assumes one TPAG chunk; other exceptions for the Russian slot.

## Polish letters

`tools/fonts.py` composes them from game letters: acute = "é" − "e", dot = "i" dot or one of "Ё",
ogonek = mirrored "ç" cedilla at the right leg, "ł" stroke drawn. Xirod lacks "é" and "ç" and gets
marks synthesized from "Ё" dots. Preview: `tools/fonts.py --preview <file.png>`. Fonts have no „”
or en dash (nor Russian «»), so texts use `"` and `-`.

## Build

After a test install the game dir is patched, so build from the backup:

```powershell
.venv\Scripts\python.exe games\katana-zero\tools\extract.py --game backups\katana-zero
.venv\Scripts\python.exe games\katana-zero\tools\review.py
.venv\Scripts\python.exe games\katana-zero\tools\build.py --game backups\katana-zero
.venv\Scripts\python.exe tools\patch.py release --original "backups\katana-zero\Katana ZERO.exe" --built "games\katana-zero\dist\build\Katana ZERO.exe" --relative "Katana ZERO.exe" --original backups\katana-zero\data.win --built games\katana-zero\dist\build\data.win --relative data.win --readme games\katana-zero\docs\INSTALL-patch.txt --out-dir games\katana-zero\dist --game-name katana-zero --package-name Katana-ZERO --version <version>
```

Batches: `tools/batch.py dump` / `merge` (entries in game order with Russian context; repeated
English lines fill in by themselves). `work/` (extracted texts) is git-ignored.

## Tests

- Vertical confirmed in game: Polish letters, menus, warning, first dialogue; day counter and
  "WYSUŃ KASETĘ" (shortened at the user's request, small field).
- Full translation built, verified from both files, installed on GOG 1.0.5; full playthrough pending.
