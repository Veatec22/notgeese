# Void Bastards: translation decisions

Facts and sources: `translations/bible.yaml`.

## Characters

- **B.A.C.S.: male** (voice Kevan Brighting). HR and OH&S corporate newspeak: "zadania do realizacji",
  "wskaźniki KPI", "Twoja kandydatura została wybrana", "interesariusze". Polite-passive-aggressive,
  never vulgar.
- **The player has a random gender** (Mr, Mrs, Ms titles in game data). Everything said to or about
  the player is genderless: present tense, impersonal voice ("próbowano użyć karty"), "bystra osoba"
  instead of "bystry"; "ty" where it needs no gendered form. **Character traits are nouns**
  ("Nerwowość", "Krzepa", "Dziurawe ręce"); an adjective would give gender away. `_past` achievement
  descriptions impersonal ("Zbudowano…").
- **Pirates speak Scots** (developers give a standard English gloss in context). Polish: street slang
  ("ziomy", "gnojek", "kurde"). Captain Li Hua and Luli genderless (unknown).

## Terms and puns

| EN | PL | Why |
| --- | --- | --- |
| client | klient | satire: prisoners called "clients" |
| brownie points | punkty lizusa | points for sucking up to the boss (developer context) |
| Merit | zasługa | currency; short |
| authorise (hacking) | autoryzacja | the developers' word |
| lock / unlock (doors) | blokować / odblokować | "zamykać/otwierać" changed the mechanic (review) |
| upscale | przerób / złom do przeróbki / Przerobiono | "ulepsz" clashes with workshop upgrades; rejected "uszlachetnij" (user) |
| Veteran / Senior (enemy ranks) | weteran after the name / Starszy | "Woźny weteran", "Skryba weteran" (user) |
| Gunpoint (turret) | Muszka | "at gunpoint" → "na muszce" |
| Screw (guard) | Klawisz | prison slang |
| Juve | Gówniarz | "rude adolescent" in context |
| Janitor | Woźny | |
| Stapler / Staple | Zszywacz / Zszywki | staple shotgun |
| Whackuum / Smackuum | Walkurzacz / Tłukurzacz | walić + odkurzacz |
| Clusterflak / Clusterfluck | Klasterflak / Klasterfuks | |
| Surgery 4 Dummies | Chirurgia dla bystrzaków | Polish "…dla bystrzaków" series |
| Operating Theatre | Teatr operacyjny | "half theatre, half operating room" |
| Tombs (cells) | Kazamaty | |
| OH&S | BHP | |
| hab / nuc bay (modules) | kwatery / moduł min atomowych | as on the ship map (review) |
| rehydrate | nawodnić | whole game |
| line printer / ID card | drukarka wierszowa / identyfikator | short in the parts grid |
| Sargasso Nebula | Mgławica Sargassowa | like the Sargasso Sea |

Untranslated: Void Ark (indeclinable, masculine), S.T.E.V., P.A.L., B.A.C.S., FTL, WCG, company names
(CNT, Otori, Krell, Xon, Lux, Pac, Tydy), Regulator, Nebulator, Ion Bru, Cool Pops.

## Opportunities taken

- "Client Expired" → "Klient wygasł"; "Hard Bastard" → "Twardy Drań"; "Easy Peasy" → "Bułka z masłem".
- British sayings in achievements: "Brown Noser" → "Lizus", "Kippers for Breakfast" → "Śledzik na
  śniadanie", "Cor Blimey!" → "O ja cię kręcę!", "Coffin Dodger" → "Trumna poczeka"; "Sknera".
- "Shoplifters unite!" → "Złodzieje sklepowi wszystkich krajów, łączcie się!".
- Robo-pet "plod" (slang for police) → "krawężnik"; "Zarządzanie pieczarkowe" (rejected "Metoda
  pieczarki").

## Deliberate departures

- Numbers appended in code written as labels ("Spal paliwo: {[x]}", "Punkty lizusa za te
  ustawienia: " with the trailing space) to avoid numeral agreement; profile counters "COUNT dni /
  COUNT dzień", "Skoki: COUNT".
- `_PLURAL` items in nominative plural (labels).
- Key names: symbols in Polish (Gwiazdka, Małpa, Ukośnik), special keys as printed (Backspace, Home,
  Page Up).
- **Action log** (top right) has one line for the title, the game draws a caption below: budget ~20
  chars as EN. "Wezwano dostawę" (matching "wezwij dostawę"), "Odszkodowanie".
- Controls in imperative: "Strzelaj", "Skacz", "Biegnij" (user).

## Review

2026-09-26, three fresh-context subagents, read-only, 2480/2480 in three batches (narration 591,
items and mechanics 912, UI and systems 977). Direction kept in full. 31 certain fixes (hab/nuc bay
modules, lock/unlock in HackDoor and hints, capital after a period in 12 weapon descriptions, "Przygotuj
się na wszystko!" instead of masculine "Bądź gotowy", trailing space before the appended number,
"nawodniono" in the Void Ark description, reversed Ion Bru joke, "kurzu i brudu", "nieaktywnego
drona-bombę").

User decisions 2026-09-26 (31 more entries): B.A.C.S. tutorial without stiff gender workarounds ("Czy
wiesz, że na tym statku jest brzęczek?", "Nie wiesz, dokąd iść?", "…zanim ktoś cię zabije albo się
udusisz.", "Zamiast budować w warsztacie lokalizator części."); `_past` achievements "Udana ucieczka z
mgławicy…", "Doprowadzono S.T.E.V. na drugą głębokość mgławicy.", "Przeżyto spotkanie z piratami.";
pirates "Jakiś frajer puścił…" (dobber = idiot), Li Hua "mam tam wyleźć i zrobić to za was??", "Luli
ciągle gada…"; controls in imperative; enemy ranks; "przerób"; "Proszę czekać dalej — i przy okazji
szukać identyfikatora.", "Zarządzanie pieczarkowe", "Sknera".

**Open, text unchanged:** "Pirat mat" → "Pirat bosman"; `Challenges/hacker` "Autorytet" → "Figura
autorytetu"; `Workbench/ProgressUpgradeTitle` "Zadanie!" → "Do realizacji!"; "Gdzie tu najbliższa
stacja… papiernicza?"; fidelity gaps (ToxicResist_L1 nausea time, PlasmaLauncher_L2 half reload,
MonsterScan_L1 "do budowy", DepthProgress_L4 "nakazane", UNOBSERVANT, LOOKS_THE_PART, SUSPICIOUS
"wykrywają tę postać", BombDescription "wyłączyły"); comic and B.A.C.S. polish ("A teraz cię
wysuszymy przed podróżą FTL.", "Areszt bezterminowy.", "Sprytnie!", "Nawet w postaci woreczka
proszku…", "Requisitions" = "Zaopatrzenie"); length fallbacks ("Piraci namierzają!", "Przechodzenie
poza pasami.", LPM/PPM/ŚPM, "VP ds. muszek", "Świadectwo rej.", ŁAD/MOST) only if the test shows cuts.

No context: which DifficultySelect variant the game uses and what follows the number;
`Interact/UsesAvailable`, `Remaining`, `SecondsAvailable`, `Discovered`, `To`, `StockRemaining`,
`Workbench/UseProgressPart` (appended numbers/names); `NPC/Boss`, `NPC/Allied` combinations; Star Map
"Zyskano/Utracono"; `Title/*CuteName` with Pan/Pani; `Stat/PiratesEscaped`.

Check report after: 0 hits except 18 length; 15 typography hits (EN trailing spaces without appended
content) are bible exceptions.

## Check in game

- Challenges → difficulty: space before the brownie-point number and what follows it.
- Control settings: long "Lewy/Prawy/Środkowy przycisk myszy", also in `KEY` hints.
- Workshop and parts locker: "Chirurgia dla bystrzaków" (24), "Świadectwo rejestracji" (22),
  "Wiceprezes ds. muszek" (21), "Zagrożenia środowiskowe" (23), "Stymulator XTC", "Wyściółka
  kaftana".
- Ship map: ŁADOWNIA, MOSTEK next to KWAT, SPRZ.
- Star map: event titles ("Namierzenie przez piratów!", "Tunel czasoprzestrzenny"), ship names
  ("Statek rekonwalescencyjny Xon"), "Zyskano/Utracono".
- Character profile: offenses ("Przechodzenie przez jezdnię w niedozwolonym miejscu."), ammo
  descriptions.
- Subtitles: `BuzzController_3_Player`, `Sentinels_2_BACS` readable in time; "Złodzieje sklepowi…"
  shown long enough.
- Options: "Synchronizacja pionowa".
