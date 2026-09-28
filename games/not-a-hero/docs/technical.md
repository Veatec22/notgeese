# NOT A HERO: technical

GOG (exe FileVersion 1.0.0.0, a resource version, not the release), Clickteam Fusion compiled to
C++ by Chowdren (SDL2, OpenAL). 2750/2750 entries. Delivered as **delta patches** (`tools/patch.py`)
of `NOT A HERO.exe` (UI strings only), `Assets.dat`, `Src/talk.ini`, `Src/ENDS.ini`,
`Src/chat.ini`, `Src/LEVELS/SETTINGS.ini`. No plugin: native Chowdren runtime, no code loading
point. **Polish replaces English**; the language screen's British flag (image 6170) becomes a Polish
flag in the colors and frame of the game's French flag.

## Existing translations

No available Polish translation and no useful tools from other fan translations found (searched
spolszczenie, fan translation, tradução, traduzione, руссификатор; results confuse the game with
the Resident Evil 7 DLC). GOG: EN, DE, ES, FR, IT. Porter mp2.dk (Chowdren, localization);
Assets.dat container: github.com/snickerbockers/fp-assets.

## Game files

- `NOT A HERO.exe`: 4 134 400 B. GOG ID 1429698467.
- `Assets.dat`: 32 336 434 B. Table of 18 831 uint32 offsets at 0x92D2; first 18 793 images
  (header `<6HI`: w, h, …, length; zlib RGBA), 18793 the font block, then 37 D3D shaders.
  `tools/assets.py` appends changed images at the end and repoints only their entries; the rest is
  byte-identical.
- `Src/talk.ini` (briefings + word pools), `Src/ENDS.ini` (debriefs + pool copies),
  `Src/chat.ini` (in-level lines, hints), `Src/LEVELS/SETTINGS.ini` (mission names, descriptions,
  challenges). `-fre/-ger/-ita/-spa` variants have no pools.
- `menu/<lang>/<n>.png`: 557 menu images per language; English ones live in Assets.dat. Image
  number comes from EXE code (`build.menu_map`).
- Audio (`Audio/` OGG/WAV) untouched.

## INI text

- CP1252 in; changed lines written in the game encoding (`fonts.encode`), rest byte for byte.
  `tools/ini.py` defines entries (file|section|key; repeated chat.ini section `[PASSIVEUP7]` gets
  `~2`, `~3`) and guards the engine: `$END$`, `$LEVELSELECT$`, `$RESTART$`, `@` unchanged; count of
  `#` and `^` unchanged (timing and events counted per line: `SPAWNLINE`, `SPAWNWORD`, `BLNEWn`,
  `PICn`, `OBJn`); no new tokens. Token-only lines untouched.
- Random word pools: every `$NAME$` token has its own replacement code in the EXE, so no new pools.
  Official FR/DE/IT/ES dropped them. Polish: adjective pools as adverbs, noun and verb pools replaced
  by fixed words (bible `randomizer`).
- `OBJn=1` shows the mission item image at line n; `$SUBJECTOBJECT$` stays (nominative) to match
  the image. In FR `OBJNUM` sets the item in the scene; unchecked in English mode.
- Atlas 5873 (dialogue font) has BunnyLord's head in the `*` cell: censorship.

## Fonts

Atlases 32 × 7 cells for bytes 32–255 (Windows-1252 glyphs). 21 atlases (`tools/fonts.py`) get
Polish letters composed from base letter pixels. Game encoding (`fonts.encode`): Polish letters at
CP1250 positions where FR/DE/IT/ES texts don't use them; Ś Ł Ń Ę ż moved to free cells (0x8A, 0xA4,
0xD0, 0xCB, 0xBE), since in CP1250 they'd take Œ £ Ñ Ê ¿ (the language screen once showed
"ESPAŃOL"). ASCII and other languages' glyphs untouched (cell comparison). 19 atlases found via EXE
constructors; 5392 and 5873 (dialogue window) by atlas shape after test 1. Atlas 789 has another
layout, skipped. „ ” (0x84/0x94) and – (0x96) exist, so texts use Polish quotes.

## Menu images (`build.menu_images`, `tools/menus.py`)

Positions and faces measured on originals (`tools/locate.py`, pixel bands):

- main menu (0–87, 277–279, 298–301, 304–345, 480–496), sound (280–297), pause (497–536),
  tutorial boards (537–556): font 3017/2088;
- mission select DAY 1–21 / SECRET 1–3 (88–276): atlas 3424, spacing 7, rows every 14 px from
  y=66; the game draws digits without left indent, so the number comes from position;
- character cards (355–412): 3424, spacing 9, description from y=71 every 13 px, `{…}` = red;
- election progress (346–354): 3424 + 3037 for the caption; first row 2 px lower (accent would
  leave the image);
- big "DAY 22" (786): 3424 ×2 and ×3, underline redrawn;
- reset (336–345), controller (1892, 149), "SHOOT HER" (446–476: 3037, spacing 11).
- EXIT signs (414–444) stay: the frame doesn't fit WYJŚCIE.

Trap: with 10 px row spacing (controller) top diacritics hit the previous row; words without them
chosen there.

## EXE strings (`tools/exe.py`)

143 English UI strings in `.rdata` (0x303318–0x30720c). Code copies them with a fixed length
(`push len; push str; call assign`, inline `movq`/`mov` in static initializers; checked with
capstone), so Polish has at most the English byte count; shorter padded with spaces (around for
messages, at the end for column labels). DE/IT/FR/ES are separate strings. Skipped: debug (ANIM,
STATE, SPELL LINE, data export), title. Language screen: one string `ENGLISH\nESPAÑOL…`
(0x30683c, 45 bytes); first item → "POLSKI ".

## Build

```powershell
.venv\Scripts\python.exe games\not-a-hero\tools\build.py --game "C:\Games\Not A Hero"
```

Output `dist/build`, previews `dist/preview`, patch ZIP in `dist/`. Pins original checksums and
refuses patched files; with the translation installed build from `--game backups\not-a-hero`.
`tools/extract.py` dumps texts to `work/`; `tools/review.py` refreshes EN in
`translations/en-pl-review.json` from the game; `tools/structure.py`: 7 groups and 57 BunnyLord
monologues (talk.ini briefings, ENDS.ini debriefs) in line order; named sections are the word
lists. Local test: `tools/install.py --game … [--restore]` (backups in `backups/not-a-hero/` and
`*.przed-spolszczeniem` next to game files).

## Tests

- Test 1 (2026-09-22): no Polish letters in dialogue; dialogue font (5392/5873) was missing; added.
- Test 2: Polish letters in dialogue work. No sound was a game bug: a fresh `Bin/Profile.ini` lacks
  `SFXVOL`/`SOUNDTRACKVOL`, volume starts at 0 (in the player readme).
- Full translation: installed; image previews, patch reconstruction and check report verified
  outside the game. In-game playthrough pending; what to check: `docs/decisions.md`.
