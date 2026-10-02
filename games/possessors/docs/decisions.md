# Possessor(s): translation decisions

## Direction

Agent decisions; no direction session (the user asked to go straight from the probe to the full
translation). To revisit with the user at review.

- **Audio:** characters speak in barks/gibberish (no English voice lines found in the tables), so
  text-only rules: free with idioms and rhythm, facts and foreshadowing kept.
- **Tone:** Luca is a 16-year-old (DOCK_01_SURVIVOR_02_0600), sarcastic and scared; colloquial
  Polish ("stary", "serio", "kurde", "no"). Rhem is formal, cold and condescending, no slang or
  swearing; he softens over the game. Dessa is pathetic and venomous; Tens is gruff ("mała").
- **Profanity at EN strength:** shit → cholera/kurde/gówno by context, fuck → kurwa/pierdolić
  (only where EN has it: "F… fuck you" → „P… pierdol się”, "I wish I fucking could"), dick →
  dupek, piece of shit → gnój, get bent → wal się.
- **UI:** imperative 2nd person singular ("Naciśnij", "Pokonaj"), sentence case, Polish quotes.
- **Forms of address:** Luca uses "pan/pani" with adults she does not know well (Foss, Tens,
  Rutto, Beverly, Tesca, Lustro, Vern, the plant researcher); adults use "ty" with her. Teacher
  Foss and Mr. Demars use "ty" (Polish school norm; the Russian table uses "вы").

## Characters

- **Luca: feminine.** 16, Blue Pass family; lived with her mom in a colony before Sanzu; has a
  sister and a bedridden grandpa. Declension Luki/Luce/Lukę/Luką; vocative written "Luca".
- **Rhem: masculine.** Rhema, Rhemowi, Rhemem.
- **Dessa: masculine** (RU "Десса убил"), Rhem's former partner, the one-horned demon who killed
  Kaz. Declines like Kuba: Dessy, Dessę, Dessie. EN typo "Dehsa" rendered Dessa.
- **Kaz (Maurice Kazinski): masculine**, rich exec family. Flashbacks B and K settle it via RU
  masculine forms; flashback F (CampusHill) follows that reading, RU "единственный" there taken as
  an RU slip.
- **Tens: feminine**, the Hunter (łowczyni); **Moja, Dau, Beverly, Tesca: feminine**;
  **Foss, Renzo, Tygo, Orren, Vern, Lustro, Rutto, Wayne: masculine.** Demon women: "demonica".

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| chroma | chroma (chromy, chromę) | coined demon word, one form in UI and dialogue | decision |
| possess / possessed | opętać / opętany | standard Polish | decision |
| host | nosiciel / nosicielka | demon's body or object | decision |
| feral | zdziczały | demons gone mad | decision |
| Rift | Wyrwa | interdimensional tear | decision |
| pocket (space) | kieszeń | between worlds | decision |
| affix | wszczep | demon organs implanted in weapons; "They'll affix you up" → „Wszczepi ci, co trzeba” | decision |
| gear / inventory | ekwipunek / rzeczy | menu tabs | decision |
| pursuit | zadanie | quest log | decision |
| whip | bicz | weapon | decision |
| vault | skarbiec | the lab door | decision |
| blue/pink/silver pass | niebieska/różowa/srebrna przepustka | lowercase everywhere | decision |
| Sunken City, Fluorescent Park, Campus Hill, Dead Mall, Rusted Dockyard, Inverted Plaza, Skyscraper Remnants, Buried Streets | Zatopione Miasto, Park Jarzeniowy, Wzgórze Kampusowe, Martwa Galeria, Zardzewiałe Doki, Odwrócona Plaza, Ruiny Wieżowca, Zasypane Ulice | descriptive district names translated | decision |
| Agradyne, Sanzu, SanZooQuarium, Infinergy, Aquamax, Rancho Mirage Flats | unchanged | brands and place names; Agradyne neuter like "Google" | decision |
| Dark Cyclopean Dynasty | „Mroczna dynastia cyklopów” | Polish title case; fans: Nocni Wojownicy | decision |
| Venderpup | Handlopies | vendor + pup | decision |
| Buttermilk, Pondscone, Gentle (horse people), Bucephalus | Maślanka, Podpłomyk, Łagodny, Bucefał | telling names; historical Bucefał | decision |

## Opportunities taken

- "Whinney! — Who's Whinney?" → „Parsk! Parsk!” / „Kto to jest Parsk?” (horse sound taken as a name).
- Renzo's motto "If you've got the skills, you can pay the bills" → „Kto ma głowę, ten ma premiowe”.
- "Hold Your Horses" (horse quest) → „Wstrzymaj konie”; "Broken Records" → „Zdarta płyta”;
  "Knot Frogs" → „Wcale Nie Żaby”; "Down the Drain, Up the Tower" → „Na dno i na szczyt”.
- Dracula "is also a landlord" → „kamienicznikiem” (Polish landlord jab).
- MLM cult in the Zoo kept as Polish MLM jargon (upline, downline, lewarować, zimny rynek).

## Deliberate departures

- `<DLang.Pose>` map line (PSE font, ASCII only) translated without diacritics: „Obietnice - Strach - Wina - Dobro”.
- Bort's growls and horse sounds lightly Polonized (GRAAA, Ihaha).
- Developer strings (BLANK, CUT, Attack - Eyeball, GetItem - …) left as in the game; DEBUG lines translated.

## Open (for review with the user)

- Whole direction above was set by the agent without a sample session.
- „chroma” collides with Polish „chroma” (feminine of "chromy", lame); kept as the game's coined word.
- Luca's declension (Luki, Luce, Lukę) vs leaving the name undeclined.
- Flashback F speaker assignment (see Characters).

## Review

No independent full review yet. Check report (2026-10-02, with speakers from `structure.yaml`):
missing 0, tokens 0, gender 0, address 0, terms 0, consistency 0, English 0, plurals 0,
typography 0; length 14 (settings labels, to check in game).

Speakers in `structure.yaml` are reconstructed from the text (the game data has none) and checked
against Polish gender forms; flashbacks A1/A2/B/E/F/G/K follow the Kaz/Luca reading above.

## Check in game

- Lines in demon style `<DLang>` / `<DLang.italic>` / `<DLang.Bold>` (Cheekers' „chromę”, Dessa's
  shouting, Beverly's demon): Polish letters must render; the style may use a different font.
- The vault map (THE_VAULT_MAP_0300): PSE font line.
- Settings: „Efekty dźwiękowe” (was SFX), „Limit klatek na sekundę”, window mode descriptions.
- Map pickups and abilities: „Przebijające nurkowanie”, „Nieodwiedzone pomieszczenie”, „Klucz do wentylatorni”.
- Long dialogue lines (Tens' quest briefing, Dessa's final speeches) for box overflow.
- Input icons inside tutorial sentences („Naciśnij [X], aby…”).
