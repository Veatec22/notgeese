# Cyber Hook: translation decisions

Facts and sources: `translations/bible.yaml`.

## Characters

- **Dron masculine** ("nie byłem szczery", "czułem się samotny"): RU ("Уверен"), ES ("Estoy
  seguro"), PT ("o Dron") and reviews. French (the developers are French) makes Dron female ("je
  suis sûre"). Least certain decision.
- **Dron speaks the ending**: same speaker as in the tutorial, so Dron confesses creating the
  levels, Numero ("nieudany eksperyment") and the player.
- **Numero masculine, name indeclinable** ("dla Numero"): always inside a color tag; declension
  would split the tag.
- **Player: impersonal where possible** ("udało ci się", "jesteś z powrotem", "należy ci się
  wolność"). The original treats the player as male ("spider boi", FR "Tu es revenu"), so
  masculine stays only for a reference: "Hej, w końcu się obudziłeś!" (Skyrim).
- **Dron and Numero use "ty"; Numero to both at once "wy".**
- **Intro terminal: impersonal machine messages** ("Wykryto biegacza", "Nie można odinstalować
  świadomości").

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| runner | biegacz | what Numero and Dron call the player | decision |
| hook | hak | game/gadget name CYBER HOOK stays, the item is a hook | decision |
| Timewarp | spowolnienie (czasu) | what the mechanic does; "zaginanie czasu" only in BEND TIME | decision |
| replay | powtórka | Polish racing/platformer releases | decision |
| leaderboard | ranking | Polish Steam | decision |
| personal best / PB | rekord (osobisty) | "RO" unreadable, "PB" foreign | decision |
| flying green probes | latające zielone sondy | FR "sondes" | fr |
| Airdash | skok w powietrzu | in-game description: second jump in the air | decision |
| Retract | zwolnienie haka | releases the hook | decision |
| world names | Początek, Trening, Wyzwanie, Mistrzostwo, Zwątpienie, Gniew, Koniec | literal | decision |

## Level names

- Descriptive names translated ("Wieża śmierci", "Miejska dżungla", "Bezwładność").
- Proper names and untranslatable puns kept: Speedy Luke, Big Bank, Zartan, PropulZone, Koma,
  Klonk, Rabator, Xitra, Rotato, Tobledrone, Castle Trashers, cORE, Korridor, Slipgate, Skorpion,
  JCVD, La Grange, Metropolis X, Ring Ring, Three 6.
- References with an established Polish title: Captain Hook → "Kapitan Hak", Hang'em High →
  "Powieś go wyżej", Master AirBender → "Mistrz powietrza". "Thinking with Timers/Buttons/Hooks" →
  "Myśl zegarami / przyciskami / hakami" (Portal).

## Opportunities taken

- Cut-off swears keep the effect: "JETTISON CARGO MOTHER F" → "ZRZUCIĆ ŁADUNEK SKUR",
  "Sh…iii…t" → "Sz…laaa…g", "mo#&-#!(#&&" → "sk#&-#!(#&&".
- "spider boi" → "Ale z ciebie teraz mały pajączek, co?" (no player gender); "Red is DED!" →
  "Czerwone to zgon!".

## Deliberate departures

- **Game CSV bugs fixed**: English players see just "Hey" instead of "Hey, you're finally awake!"
  and two descriptions lose quotes; our texts bypass the CSV.
- **Tutorial end** (`Tutorial_Line_04_*`) has English text instead of keys; the plugin recognizes
  and swaps it (16 lines in `raw-keys.json`).
- **Three DLC lines without game rows**: content unknown, not invented.
- **Polish in English's slot**: "English" is labeled "Polski".
- "..." kept where the original has it; not every font has "…".

## Review

No independent full review yet. Check report: missing 0, tokens 0, gender 0, address 0,
consistency 0; 5 overlong labels fixed. False alarms left: terms 6 (`<sprite name="Hook">`, game
name), English 5 (language names, "DNA"), typography 55 (straight quotes inside TMP tags), length 3
(checked in game or paged dialogue).

## Check in game

- Level select, longest names: "Młody mikser powietrza", "Przetwarzanie odpadów", "Społeczeństwo
  w biegu", "Klasyczny skok wzwyż".
- Between-world talks: Dron's longest lines (world 5: probes and slow-down; world 7) stay in the window.
- DLC ending and credits (`dialog_ending_credits_*`): Dron's first-person gender.
- Tutorial intro after returning from a level (`Tutorial_Line_04_*`): raw keys really turn Polish.
- Options: "Autopuszczanie haka", "Wyłączona" (V-Sync), shortened for field width.
