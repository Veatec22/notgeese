# Katana ZERO: translation decisions

The speaker isn't stored with entries, so gender and form of address come from the Russian version
of the same line (past tense, "ты/вы") and neighboring lines. Facts: `translations/bible.yaml`.

## Characters

- **Zero: male, short and cold.** RU "пришел", "понял". Player reply choices masculine
  ("Przyszedłem", "Nie wiedziałem"). Name stays "Zero".
- **Therapist and Zero use "ty" both ways** (RU "ты"); clinical tone, swearing only in anger
  ("NIE PRZERYWAJ MI, KURWA!").
- **The Girl: feminine, "ty" to Zero** (RU "поняла", "нарядилась").
- **Receptionist (hotel Murdower, later Ośrodek Badań Synergicznych) uses "pan"**; Zero answers
  impersonally or with "pani" ("Proszę przestać do mnie mówić"). RU "вы", feminine "расслышала".
- **Snow: female** (RU "впечатлена", "надеялась"); name stays "Snow", not "Śnieżka".
- **V: male, very vulgar, drops Russian swears.** Cyrillic interjections ("Сука охуеть", "Блять")
  stay; the rest with profanity of the same strength.
- **Kissyface male** ("panie Kissyface"). **Komedia male**, casual ("Nie wiedziałem, że masz
  sumienie"). **Tragedia** speaks archaic Polish ("Usłuchaj mego rozkazu", "błędne serce").
- **Woman in the Chinatown VIP (NULL): feminine** ("Jestem zbyt zmęczona na zemstę").

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| the Dragon | Smok | Chinese dragon nickname, declines naturally; RU "Змей" | decision |
| Chronos | Chronos (Chronosu, Chronosem) | drug name, masculine | decision |
| NULL, Gamma NULL | NULL, NULL Gamma | program name, caps | decision |
| New Mecca / Third District | Nowa Mekka / Trzecia Dzielnica | translatable, readable | decision |
| Juncture | Juncture | authorities, no good Polish equivalent | decision |
| dossier | teczka | natural in speech and UI ("Otwórz teczkę") | decision |
| precognition | dar przewidywania | sounds better in dialogue than "prekognicja" | decision |
| withdrawal | głód | addiction slang, short | decision |
| cromag | kroman (kromański) | war slur from Cro-Magnon, keeps the insult | decision |
| *Hang up* | *Rozłącz się* | imperative like other starred options | decision |
| Behemoth, Leviathan | Behemot, Lewiatan | Polish biblical forms, the girl's plushies | decision |
| Strong Terry | Silny Terry | TV strongman nickname, declined | decision |
| trick or treat | cukierek albo psikus | established | decision |
| PRESS TO EJECT | WYSUŃ KASETĘ | the level is a VHS tape; short, small field | user |

## Opportunities taken

- Club council of thin Rickys: "Skinny Ricky / Slender Richard" → "Chudy Ryś / Ryszard Chudy".
- Casino bouncers: "Bill Betonowa Ściana", "Mark Moralnie Niezłomny", "Lenny Wyrozumiały".
- Day counter declined in Polish: "ZOSTAŁO 10 DNI", "ZOSTAŁY 4 DNI".
- The receptionist's card game keeps absurd card names ("Zębatka Wiecznego Chaosu", "Kwantowy
  Biomałż Fraktalnej Katastrofy") and the trap-card joke.

## Deliberate departures

- **Straight quotes "..." instead of „...”** (fonts lack Polish and Russian quotes); en dashes → hyphen.
- Height and weight in target dossiers in cm and kg, as in Russian.
- Song titles, brands and proper names (Murdower, Chinatown, Studio 51, Webflix) stay.
- A few lines have one pause `*` more or less than the original (Polish word order).

## Review

No independent full review yet. Check report after the last batch: missing 0, tokens 0, gender 0;
only false alarms left (English 36: onomatopoeia, names, song titles; capitals 22: weapons, floors,
cards; terms 4: declension "Nowej Mekce", "Behemocie", a song title; length 10: settings;
consistency 2: "go/je" for evidence vs pass).

## Check in game

- Settings and controls: longest labels ("SYNCHRONIZACJA PIONOWA", "PRZEWROT PRZY LĄDOWANIU",
  "DLA SŁABSZYCH KOMPUTERÓW"); Russian has similar lengths.
- Big titles and level names (xirod), ó/Ó only since the full translation ("POZIOM UKOŃCZONY").
- Restart prompt "(Naciśnij DOWOLNY PRZYCISK, aby zacząć od nowa)", twice as long as EN.
- Choice conversations in the club (Electrohead), V's limo and the bunker: dense effect tags on the
  right words.
- Receptionist at Ośrodek Badań Synergicznych: many branches, "pan/pani" forms.
