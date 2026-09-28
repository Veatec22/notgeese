# Rain World: translation decisions

Base game, Downpour and The Watcher. Sources for every term: `translations/bible.yaml`.

## Characters

- **Looks to the Moon: female, nickname "Luna".** RU "Смотрящая-на-Луну", "я устала"; EN "she" in
  pearls and chatlogs. A feminine noun fits better than "Księżyc". To the player: "mały stworku",
  "przyjacielu", "mały archeologu" (vocatives from `NameForPlayer`).
- **Five Pebbles: male, nickname "Kamyk".** RU "я занят", EN "he/him". In Downpour the same class
  also speaks for pre-collapse Luna (Spearmaster): gender line by line from RU.
- **Spinning Top (The Watcher) = Bąk: masculine** (RU dialogue 209 "Я провёл").
- **Echoes and ancients: no gendered forms** ("przysiadało się", "nie udało mi się"); adjectives
  neuter after "echo" ("przykute do wspomnień"). EN doesn't say who they were.
- **Player: masculine after the noun "ślimakot"** ("wróciłeś", "jesteś głodny"); iterators speaking
  of it as an animal: neuter after "stworzenie".
- **Iterators of unknown gender: no gendered forms** (GW, HR, UU, WO, EOC, PG, SI, PI, No
  Significant Harassment's peers, Unparalleled Innocence): "doszły mnie", "nie wypada mi"; RU does
  the same. Male per RU: SCS, BZN, NGI. Added after review.
- **Ancients' letters genderless**, except pearl 238: the author writes "Nine-Leaf, when he comes"
  (Ea-nasir complaint parody): masculine there.
- **Developers in the Downpour commentary: no gendered first person.** Real people (Andrew, Will,
  Dakras, Norgad, Screams, Cappin, Slugitar…); no guessing gender from nicknames: "udało mi się",
  "moim zamiarem było", passive voice. Others only as the original says ("he" of Cappin, Will,
  Screams; "they" or no pronoun: Minkimaro, Ender, Topicular, Andrew, Slugitar, RatRat, Tollycastle,
  Joar: genderless). Developers address the player masculine ("Skoczyłeś sam…"), as decided for the
  player.

## Slugcats

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Survivor | Ocalały | wiki has both "Przetrwaniec" and "Ocalały"; RU "Выживший"; the vertical's "Przetrwaniec" changed to the more natural one | wiki-pl, ru |
| Monk / Hunter | Mnich / Łowca | established on the Polish wiki | wiki-pl |
| Gourmand | Smakosz | "indulger of the simpler pleasures" | decision |
| Artificer | Pirotechnik | "master of pyrotechnics and explosives"; wiki "Artyficer" is a calque; "Pirotechniczka" rejected | user |
| Rivulet / Spearmaster / Saint | Strumyk / Włócznik / Święty | wiki and RU | wiki-pl, ru |
| Watcher | Obserwator | DLC name "The Watcher" stays English | wiki-pl |
| slugpup | ślimakocię (Jolly Co-op "maluch") | diminutive like "kocię" | decision |

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| iterator | iterator | wiki "Przeliczacz" inconsistent; RU keeps "итератор"; pearl 20 puns "iterujemy… Iteratory"; "Przeliczacz" rejected | ru, user |
| Sliver of Straw | Drzazga Słomy | female ("She's quite legendary"); sliverists → drzazgiści | decision |
| Seven Red Suns / No Significant Harassment | Siedem Czerwonych Słońc (SCS) / Brak Znaczącego Nękania (BZN) | chatlog codes translated with the names; the game colors lines by the translated code | ru, game code |
| Big Sis Moon | Starsza Siostra Luna (SSL) | same | ru |
| passage | przeprawa | "przejście" clashes with room passages | decision |
| Expedition / perk / burden | Wyprawa / atut / brzemię | | decision |
| Scavenger | zbieracz | they collect and trade; wiki "Grabiarze" | decision |
| Void Sea / Void Fluid | Morze Pustki / Płyn Pustki | | ru |
| ripple / warp (Watcher) | fala / przeniesienie | RU "рябь" | decision |
| Lizard / Vulture | jaszczur / sęp | "jaszczurka" too small | ru |
| Ascension | Wzniesienie (not "Wniebowstąpienie") | | decision |
| Five Pebbsi | Pięć Kamyksi | Pepsi pun; the ad image stays English | decision |
| Joke Rifle | żartostrzelba | the developers' April Fools' joke | decision |

Regions, subregions and creatures: full list in the bible (Obrzeża, Korony Kominów, Szeregi Farm,
Zewnętrzne Rubieże, Rurowisko; skolopendra, muchoperz, kluskomucha, spadoskorek, Tatko Długonogi).

## Opportunities taken

- "Five Pebbsi" → "Pięć Kamyksi".
- Batfly/batnip → muchoperz/muchomiętka (catnip → kocimiętka).
- Chatlog group names glued as in EN: [DRZAZGAOCEANU], [AZYLNATRZECHKLEJNOTACH], [KLATKAOMENU].

## Deliberate departures

- **Andrew calls the Artificer "she" and "her children".** The name stays "Pirotechnik" (the whole
  game uses it; RU masculine "Техник"); those few commentary lines go via "ta postać"/"jej", and
  "matczyna miłość" stays.
- **Region abbreviation expansions** in commentary ("(OE) Outer Expanse…") stay English: they
  explain the English abbreviations in game files.
- **Colons** in stats ("Czas:", "Śmierci:") without a space before, unlike EN "Time :".
- **Capitals in proper names** (echo names, Pebbles' chambers: "Magistrala Systemów Ogólnych") as in
  EN: they work as names and titles.
- **` : -30` suffix in four Luna lines (138/139)** stays: an instruction that makes the game skip
  those lines, same as in English.
- **`-ru2` keys** (Russian plural of "rounds" for 2–4 in arena) translated though likely used only in
  Russian; the base entry has genitive ("RUND NA SESJĘ").
- **"Luna" is also a city in the commentary:** "miasto Luna" where both meanings meet (RU has the same
  clash).

## Review

2026-09-24, fresh-context subagent, read-only: 4914/4914 in 25 batches of 200 in file order (2474
`str:`, 2440 `dlg:`); doubtful spots compared with RU, the literal dump, game IL and region display
names. No tags lost. All certain errors applied (98 entries changed), incl.:

- ` : -30` restored in `dlg:138.txt#11/#15`, `dlg:139.txt#7/#11` (otherwise Polish would show lines
  English hides);
- `str:PREVIOUS` "WSTECZ" next to BACK's "WSTECZ" in three menus → "POPRZEDNIA";
- CL mistranslated as "Samotne Wieże" → "Milcząca Konstrukcja" (`uw_d01-saint`, `ms_x02-white`);
- reversed meaning in `dlg:100.txt#3`, `dlg:140.txt#5`; "lotne" (volatile calque) → "niestabilne";
  "2 wyzwań" → "ukończ łącznie wyzwania: ##"; "Uwieszony mamy" → "Trzymaj się mamy";
  "Wniebowstąpienie" → "Wzniesienie";
- iterator and developer gender brought in line with the rules (chatlogs, broadcasts, Topicular and
  Ender);
- editorial: UI labels, iterator voices ("Dawno spełniliśmy swoje zadanie"), echoes, commentary
  ("mądry Polak po szkodzie" in Will's mouth → "łatwo być mądrym po fakcie"), Watcher 216 "A...
  SELF." → "Jakaś... JAŹŃ.".

Kept after review: pearls 237/238 masculine (238 exception), "Templariusz zbieraczy" / "Uczeń
zbieraczy", mixed "starożytni"/"Starożytni" (capital where developers write "Ancients" as a name).
All early decisions kept; user confirmed "Pirotechnik" and "iterator" (2026-09-24). Check report
after: missing 0, tokens 0, gender 0, address 0; terms 9 (false hits: "rot", "Basilisk Lizard",
"challenge"), consistency 31 (singular/plural creature pairs, `-ru2`), English 44 (emoticons,
"Hmmm…", names), length 34 (to check in game), plurals 3 and capitals 29 (unreviewed hints, mostly proper names), typography 1 (chatlog header "[ZAPIS TRANSMISJI :
…]" in game format).

## Check in game

1. **Chatlogs and broadcasts (Downpour):** the plugin passes plain text through the game's
   decryption; garbage or an empty pearl means this mechanism. Easiest: Spearmaster's broadcast
   antenna or a chatlog pearl brought to Luna. Speaker colors, incl. untranslated codes (EOC, NGI,
   HR, HF, UU).
2. **Developer commentary:** do lines fit? Polish is 20–40% longer; the ten longest got manual
   `<LINE>`; longest row ~150 chars like EN. Developer names before the colon stay.
3. **Luna conversation and pearl reading:** speaker colors, wrapping, Polish letters in bubbles;
   vocatives ("mały archeologu" at sentence start, "Nie! Mały stworku... zjadłeś... mnie!").
4. **Long Remix and Expedition labels:** "Ochrona przedmiotów przed rybami odrzutowymi", "Ukryj
   odliczanie deszczu w bezpiecznych miejscach", "Naciśnij POTWIERDŹ, aby wejść w interakcję"; Jolly
   Co-op "Kamera (nie) przełącza graczy".
5. **Arena and sandbox:** creature names singular/plural, "RUND NA SESJĘ", "Aby odblokować, ukończ
   łącznie wyzwania: ##".
6. **Spearmaster, Luna (pearls 138/139):** "Jest..." and "Jeśli on..." must not appear, as in EN.
7. **Options → backgrounds, backups:** "WSTECZ" and "POPRZEDNIA" side by side; does "POPRZEDNIA" fit?
8. Where the game shows "Trzymaj się mamy".
