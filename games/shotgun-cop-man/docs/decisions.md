# Shotgun Cop Man: translation decisions

Facts and sources: `translations/bible.yaml`. First game done before the direction/review
process existed; checked against the localization standard afterwards (2 entries changed).

## Characters

- **Shotgun Cop Man, Satan, Pedro: male.** Russian table: "Ты арестован" to Satan, Pedro
  "я попал в Ад"; matches the English.
- **Shotgun Cop Man talks like a pompous B-movie cop:** arrest formulas, pathos. The original
  "Shotgun Cop Man is I" is deliberately clumsy; user ruling (2026-09-28): rhymed archaic
  "Shotgun Cop Man imieniem mym! Sprawiedliwość to mój hymn!" (was "Jam jest Shotgun Cop Man!").
- **Hero's name stays English and indeclinable.**

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Ophelia | Ofelia | user chose consistency with My Friend Pedro PL, where "Ofelia" is used throughout (rejected "Ophelia", 2026-09-28) | user |
| (to) Pedro | Pedrowi | declension as in My Friend Pedro PL ("Pedra") | pedro |
| Mitch the Butcher | Mitch Rzeźnik | as in My Friend Pedro PL | pedro |
| Kill All | Eliminacje | user rejected "Bez ocalałych" | user |
| Try again | Ponów | user rejected "Jeszcze raz" | user |
| Speedrun | Na czas | reads naturally | decision |
| Steam Workshop | Warsztat Steam | official Polish Steam name | decision |

## Opportunities taken

- "Shotgun Cop Man imieniem mym! Sprawiedliwość to mój hymn!" (user) keeps the clumsy pathos with a rhyme.
- Boss epithets capitalized like nicknames ("Wściekły Tyłek", "Rozczarowany Szatan"), per the
  Polish rule for epithets ("Bolesław Chrobry").

## Review

Independent review, 2026-09-28, fresh-context subagent, read-only.

- **Scope:** `translations/en-pl-review.json` after applying the user's workspace export
  (9 corrections), SHA-256 `ca96af65…e4d5d5`; all 485 entries read by group (menu, settings,
  controls incl. console variants, tutorial, HUD/rating, dialogue, Pedro DLC 1–15, level editor,
  campaigns/Workshop, achievements, credits/demo). `mLvlChineseEnd` is empty in EN and PL.
  Gap: no `work/ref-*.json` dumps in this session.
- **User corrections (2026-09-28, applied):** `epExploder` Eksploder, `epTroubleSeeker` Zadymiarz,
  `epZigZag` Piorunujący Zygzak, `gIntro4` Idź do piekła., `PedroDLCBoss3` Ophelia (both later
  revised, see Fixes),
  `PedroDLCSpeech11` Czujesz to? To zapach wyjścia z piekła., `pSpeech0` Shotgun Cop Man imieniem
  mym! Sprawiedliwość to mój hymn!, `pSpeech5` Przed sprawiedliwością nie uciekniesz!, `pSpeech8`.
- **Checks:** tokens (`[back]`, `[play]`, `<size>`, `<b>`, `\n`), final punctuation, typography,
  gender, negations: clean. Report after fixes: `terms=0 english=0`, 17 length hints (unchanged).

### Fixes

| Key | EN | Old PL | New PL | Reason | Status |
| --- | --- | --- | --- | --- | --- |
| pSpeech8 | Go ahead, see if I won't catch up! | Jasne, próbuje dalej – i tak cię złapię! | Jasne, próbuj dalej – i tak cię złapię! | typo in user correction: 3rd person instead of imperative | applied |
| PedroDLCBoss3 | Ophelia | Ophelia | Ofelia | user: match My Friend Pedro PL (more occurrences) | applied |
| epZigZag | Zig Zag Zapper | Piorunujący Zygzak | Piorunujący zygzak | user: sentence case like other editor items | applied |
| bcPromoLand | Promo-Land | Kraina promocyjna | Promolandia | user: closer to the playful original | applied |
| (bible, decisions) | pSpeech0 | "Jam jest" | user's pSpeech0 | docs described text that no longer exists | applied |

### Pre-vertical decisions

All **keep**: male hero/Satan/Pedro; pompous cop voice (now carried by the user's pSpeech0);
English indeclinable hero name; Ofelia, Pedrowi/Pedra, Mitch Rzeźnik (My Friend Pedro PL);
Eliminacje; Ponów (Redo in the editor shares the word on another screen, no clash); Na czas;
Bez obrażeń; Warsztat Steam; kampanie społeczności; element; capitalized boss epithets.

### Options not taken (user picked none, text unchanged)

- `epDoubleShooter` "Podwójny strzelec": listed among weapons, "strzelec" reads as a person;
  option "Podwójny miotacz" if in-game it is a gun.
- `mCustomCamp`, `mCustomCampComing`, `mClearMsg` "kampanie społeczności": option
  "kampanie użytkowników" (the delete warning may suggest own campaigns get deleted).
- `pSpeech1`/`pSpeech2` both open with "Stój"; option "Nie ruszaj się, Szatanie!".
- `eoSpawnGroup` "Grupa generatora", `mccSteamTermsInfo` "ten element": minor options.

## Check in game

- Level editor: longest element names ("Menedżer pojawiania się przeciwników", "Strefa
  aktywowana przez przeciwnika") in the narrow element library.
- Rating screen: hit counter next to "Otrzymane trafienia:".
- Satan chase: `pSpeech0` (57 chars vs 37 EN) fits and is readable while moving; `pSpeech8`.
- Pedro DLC: `Ofelia` boss card next to `Mitch Rzeźnik`; bubbles PedroDLCSpeech1–15.
- Level editor weapons list: is Double Shooter a gun ("Podwójny strzelec");
  `epEnemyTrigZone` "Strefa aktywowana przez przeciwnika" fires when an enemy enters.
- Options → Clear All Saved Data: read `mClearMsg` in context.
