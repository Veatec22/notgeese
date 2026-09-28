# Laika: Aged Through Blood: translation decisions

Direction wasn't settled separately (project predates the direction step); the user confirmed the
vertical in game with no remarks on tone or terms. Decisions are the agent's unless marked user.
Facts: `translations/bible.yaml`.

## Characters

- **Laika: feminine, "ty" to everyone.** Rough, swears, ironic. To her mother "matko" (EN "mother"
  is cold; RU "мама", ES "madre"), to Puppy "kochanie". Names in nominative ("Jakob, spójrz na
  mnie!", "Hilda"); vocative only from others (Hilda "słodka Laiko", Maya "Avo", ritual "bracie
  Jakobie").
- **The Elder (Starsza): feminine.** EN uses non-binary "ey/em/eir" (`D_B_Carey_AfterMissions3`,
  `Q_D_1_Mines_BackHome`); RU "я слышала", ES "LA ANCIANA". Polish needs gender in her own past
  tense and has no established non-binary form in games. A deliberate loss: the only identity from
  the original that disappears.
- **Unae, undertaker: masculine.** EN "Was he wearing…", ES "el enterrador"; RU has a woman;
  original wins.
- **Roy calls Laika "radiowcu" but uses feminine forms** (RU "потеряла").
- **Kidgutter is a bird child-captain** (ES "Soy un niño").
- Other genders from RU past tense and EN pronouns (list in the bible). Tally, Dally, Xoot:
  impersonal forms. Dally's "two brothers" contradicts Kally being a woman in the source → "Mam
  dwoje rodzeństwa".
- **Verbal tics kept:** Carey "cholernie pewna" and mocking by swapping vowels for "i"
  ("Pribiwiłiś gitiwić łidigi isti?"), Kris "Rzecz w tym", Borden "nie wiem", Walterio
  "Przezabawne!", Molly "założę się", Zooey "Miażdżąco!"/"żołnierzu", Petey "Jesteśmy
  zgubieni!", Mina "Swędzi!", Herman "wiesz?", Xoot "Pewniaczek!", Renato "ty palancie"
  (EN "you wanker"), Hectist "zakuty łbie".

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Where We Live, Where All Was Lost… | Tam, Gdzie Żyjemy; Tam, Gdzie Wszystko Przepadło… | sentence-names; in text "tam, Gdzie Żyjemy" works as an adverbial like EN; needs "w miejscu, Gdzie" when a noun must agree | RU "Там, Где Мы Живём" |
| viscera (currency) | wnętrzności | singular "wnętrzność" exists, numerals always agree | decision |
| Birds | Ptaki (capital) | enemy empire | EN |
| bike | motor | colloquial, fits | decision |
| bone memorial | kościana kapliczka | checkpoint and place of memory | decision |
| Grim Biker | Ponura Motocyklistka | plays on "Ponury Żniwiarz" | decision |
| bonehead | zakuty łeb | blockhead + bone helmet and bike | decision |
| Hectist | Hektystka, hektystyczny | neologism stays one | decision |
| heartglaze | sercolśń | flower-name neologism | decision |
| Wastelands / Wastelanders | Pustkowia / Pustkowianie | | decision |
| Floating City / Undernest / the Egg | Latające Miasto / Podgniazdo / Jajo | | decision |
| dash | zryw | short, for buttons | decision |
| funerary friend | pogrzebowa przyjaciółka | Puppy is a girl | decision |
| Advanced Electromagnetic Radiocommunications Maintenance Technician | Zaawansowany Technik Konserwacji Elektromagnetycznej Radiokomunikacji | length joke | decision |
| wreath | wieniec (never "wianek") | funeral, not a head garland | review |
| Closure (quest) | Pożegnanie | rejected "Zamknięcie" (calque), "Domknięcie" | user |
| Where We Say Who (credits zone) | Tam, Gdzie Mówimy, Kto Jest Kim | rejected "…Mówimy, Kto" (cut off), "Tam, Gdzie Wymieniamy Imiona" | user |
| Gutsy Gus | Gus Gardziel | alliteration kept, "brave" lost; option "Gus Śmiałek" (left as is) | decision |

## Opportunities taken

- "I want to rock" → "Chcę się bujać" / "Chcę fotel bujany".
- Quest names: "High Spirits" → "Na oparach", "Family Tree" → "Drzewo genealogiczne",
  "Hell High" → "Piekielne wyżyny", "The Bonehead's Hook" → "Hak zakutego łba". "Dead Bomb" →
  "Niewybuch".
- "Language!" → "Nie wyrażaj się!" / "Nie przeklina się!" (as RU/ES/FR adapt).

## Deliberate departures

- `D_4_FloatingCity_OldTown_CloseGauge_OfficeUndone_INSIDER_2`: EN says west to the Office
  District, which quests place NE → "na wschód" (symmetric line confirms layout).
- `D_3_TheBigTree_CatacombsFail_BreakFail3_LAIKA_1`: EN "all four secondary pillars", there are 8
  → "czterech par".
- `D_K_Village_Maya_Undone_MAYA_4/LAIKA_5`: "guts" pun → "ma ikrę" / "skończy z flakami na
  wierzchu" (partial).
- Numerals with {0} rebuilt: "Kule +{0}", "Surowce +{0}%".
- Profanity (user): only lines weaker than EN strengthened ("Nie pierdol. Wiem, że to ty." for
  Herman's "Don't fuck with me", "Nie pierdol, Shaza.", "wydymasz" for "fuck me over"); lines
  stronger than EN stay ("robi mnie w chuja", "Wszystkie Ptaki to skurwysyny"). Rejected: leveling
  both ways.
- `D_F_PuppysBirth_Labor_02_MAYA_5` "PUSH, YOU PUSSY!" → "PRZYJ, CIPO!" (user). Rejected "CIOTO"
  (homophobic slur shouted at a woman in labor), "MIĘCZAKU".

## Review

2026-09-24, fresh-context subagent, read-only: 3470/3470 read (dialogue in script order by 716
scenes; 49 keys without a script ordered by key number). All early decisions kept. Applied: 15
certain fixes (Gusto/Rollo are women, female names in -o don't decline; "Jestem radiowcem";
"żebyśmy my, Renegaci"; "w miejscu, Gdzie… znanym"; syntax, "dwuskrzydłowe", "pogrzebowa
przyjaciółka" once), 11 likely ones ("closure" calques, "Język!", "Zgubiłaś mnie" → "Pogubiłam
się", "Najstarszy worek stracony", "nieptasich" with Ptaki capitalized), plus editorial points
(wieniec, "Hilda" from Laika, "dwoje rodzeństwa", calques list, "ŁÓDŹ", "Strząśnij martwe
liście", "moglibyśmy"). User settled profanity, "Pożegnanie", credits zone name. Check report
after: missing 0, tokens 0, gender 0 (three Primo quotes of Laika ignored in the bible).

## Check in game

1. Zone names on the entry banner and map: "Tam, Gdzie Spoczywają Przodkowie" (32 chars),
   "Tam, Gdzie Warczą Nasze Motory" (30).
2. Settings: "SYNCHRONIZACJA PIONOWA", "SPOWOLNIENIE ROZMÓW" (does it read as slowing the walkie
   talks?), "CZUŁOŚĆ MOTORU (PAD)", "ZASTOSUJ" (limit 8).
3. Glyphs beyond Polish letters: "—" in quest descriptions, "º" (360º), "Í" in BEÍCOLI,
   Anthropologist's symbols ♊♋, "…".
4. Long walkie bubbles while riding: `D_B_Gunlady_BeforeKidnap4` (119), `D_B_Molly_DuringKidnap`
   (114), `D_S_TutorialHook_Briefing_Undone1_ANARCHIST_2`.
5. Tutorials with icons: `UI_TUT_CANDLES_DESC` (114 chars, limit 50), hook, dash, wheelie.
6. "Najstarszy worek stracony" in the log (limit 20).
7. Floating City: Factory → Office District is really east.
8. Carey's mocking reads as mocking, not a font bug.
9. Feminine achievements (Hazardzistka, Zabójczyni…), if the game shows them; store overlays use
   the publisher's English.
