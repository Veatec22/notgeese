# NOT A HERO: translation decisions

Facts: `translations/bible.yaml`.

## BunnyLord's random words

- **Adjective pools as adverbs.** Briefings and debriefs draw words from pools (`$AWESOME$`,
  `$TERRIBLE$`, `$FUCKING$`…). Official FR/DE/IT/ES dropped the pools for fixed sentences; new pools
  are impossible (each token has its own EXE code). Polish adverbs don't decline (NIESAMOWICIE,
  OKROPNIE, TOTALNIE…): "JEST $AWESOME$", "$TERRIBLE$ PODLI PACHOŁKOWIE", "BĘDZIE $FUCKING$
  $TERRIBLE$". Randomness kept in ~90% of places; sentences fit every value.
- **Noun and verb pools replaced by fixed words** (LOCATION, MAFIA, NOUN, VERB, PARTS…): they'd need
  cases. Choices come from the pool itself and keep the tone (WOMBAT, GALARETOWA MAFIA, KOLOSEUM
  PIZZY).
- **Mission item `$SUBJECTOBJECT$` stays** (the game shows its image): nominative, in quotes or
  after a colon ("TOWAR: „TORT”").
- DISSAPOINTED as "JEST MI SMUTNO/PRZYKRO…", QUANTITIES as indeclinable time adverbials, INSULTS only
  after "CO ZA".

## Characters

- **BunnyLord: male; "wy" to the team, "ty" to the agent.** The agent is the player's pick, incl.
  Samantha and Kimmy, so address to the agent is gender-neutral ("poszło ci", "twoja rozprawa", never
  "zrobiłeś"): debriefs, intro talks, in-level lines.
- **DOOD → MORDO**: colloquial, gender-neutral.
- **In-level phone calls are to Steve** ("MR STEVENSON", "GOOD BOY"): masculine.

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| THE SHOOTORIAL | STRZELOUCZEK | strzelanie + samouczek | decision |
| GLOBAL MEGALORD | MEGALORD ŚWIATA | progress image is 127 px, GLOBALNY doesn't fit | decision |
| BUNNYLORD FUN CLUB | FUN KLUB BUNNYLORDA | keeps fan/fun | decision |
| BUNNYWAGON / BUNNYCOPTER | KRÓLIKOWÓZ / KRÓLIKOPTER | telling names | decision |
| milkshake | koktajl | short, declinable | decision |
| TWEETSIES | ĆWIERKACZ | childish diminutive as in EN | decision |
| GET TO THE CHOPPA | DO HELIKOPTERA | established Predator quote | decision |
| TRIAD YAKUZA | TRIADA YAKUZA | the gang mix-up is the original's joke | decision |

## Opportunities taken

- Asterisk censorship (K*REWSKO, ZAJ*BIŚCIE): the dialogue font draws BunnyLord's head at `*`, as in
  the original.
- Mission titles: "SKOK WSZECHMOGĄCY" (Bruce Almighty), "CZARNY PIAR", "POSZŁO Z DYMEM", "PODANA NA
  ZIMNO", "JIPI-KAJ-EJ"; Jesus: "HEJ, ZEUS".
- Polish quotes „” and en dash: glyphs exist in the game fonts.

## Deliberate departures

- **EXE HUD strings have the English byte limit:** PON./WT./…, "VODKAVILLE. DZ. 1", "MENU GŁ.",
  "ŚLIZG = BTN", counters " OFIAR", " ŻYWI.", " ZGON.", " ZOST.".
- **Challenges with numbers** as "LABEL: @" ("EGZEKUCJE: 3") so numerals always agree.
- **EXIT signs stay**: the frame doesn't fit WYJŚCIE; the sign is universal.
- **Polish takes English's place:** Polish flag and POLSKI instead of the British flag and ENGLISH.
  Other languages keep working (Polish letters don't take French or Spanish glyphs). No sixth
  language possible (list in code), and only English mode has random words. English returns on
  restore.
- **Pad message** "DLA KLAWIATURY / ODŁĄCZ PADA / LUB KLAWISZ K": 10 px rows don't fit top
  diacritics; words without them.
- Level 3 "BILLBOARD Z KRÓLIKIEM": name also in the EXE, 24-byte limit.

## Review

No independent full review yet. Check report: missing, tokens, gender, terms, consistency,
plurals 0. Length: 6 longer dialogue lines (the window wraps) and one character card that fits.
Typography: 3 intended EXE padding spaces. Capitals: 2 false alarms (commands with a key).
Exceptions in the bible `ignore`.

## Check in game

1. First briefings and debriefs with random words: do adverb sentences sound natural across draws
   (repeat a few times)?
2. Briefings with a mission item (days 4, 6, 11, 16): Polish name shown, matches the image?
3. HUD in play: KRYTYCZNE!, ŁADUJ!, EGZEKUCJA!, goals ("ZABIJ DILERÓW!"), "10 S ZOSTAŁO!": length
   and centering after padding.
4. Results / stats screen (WYNIKI): column alignment of EXE labels.
5. Mission select and character cards: DZIEŃ 1…21, descriptions under names.
6. Intro (talk with BunnyLord before training) and the "DZIEŃ WYBORÓW" ending, if reachable.
