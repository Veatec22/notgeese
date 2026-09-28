# Wild Bastards: translation decisions

Facts and sources: `translations/bible.yaml`.

## Characters

- **Outlaw gender from the text and the French and Italian tables** (Russian is empty). Women:
  Pajęcza Rosa, Fletch ("archère"), Kaznodzieja/Esther ("sacerdotessa"), Francisco ("Chaste's
  daughter"), Młoda (the third bastard), cut Cuffs and Legs. Men: Billy, Casino, Kaboom, Roswell,
  Spike, Sędzia, Sierżant, Hopalong, Smoky, Rawhide, McNeil, Barrabas, Chaste.
- **"Psze pani" / "panienko" in dialogue is Fletch**: she leads the gang because she remembers the
  future (French "ange-gardienne"); hence "Posłałabym też Sędziego".
- **Nicknames with meaning translated, names not:** The Judge → Sędzia, Sarge → Sierżant, Preach →
  Kaznodzieja (feminine syntax: "Kaznodzieja dała"), Spider Rosa → Pajęcza Rosa. Billy, Casino, Kaboom,
  Roswell, Spike, Hopalong, Smoky, Rawhide, Fletch stay.
- **Rawhide says "we" and talks childishly:** "The Billy", "Many Helps", "Scrubly" → "Ten Billy",
  "Wielu Pomocy", "Cieniasny" (a robot with a squirrel swarm inside).
- **Smoky SHOUTS IN CAPS** when his beans are criticized: kept.
- **Western dialect** as colloquial, slightly rural Polish ("ano", "psiakrew", "żeście", "niech mnie"),
  no phonetic misspelling. Spike says "stary" (cockney "mate"); Roswell and Rosa speak correctly and
  haughtily; the Judge drops legal phrases ("Przychylam się", "Orzekam remis").
- **Profanity at equal strength:** fuck → kurwa/pieprzyć/wyruchać, shit → gówno, sumbitch → sukinsyn,
  goddamn → cholerny.
- **Lines with an unknown addressee** ("…Pals", "…JailPals": thanks for finding) are genderless; any
  outlaw can be the rescuer.
- **Talent (ace) and general trait names are nouns** ("Zabójczość", "Szybkie ręce", "Krzepa"); an
  adjective would give the outlaw's gender away.

## Terms and puns

| EN | PL | Why |
| --- | --- | --- |
| Wild Bastards (gang) | Dzikie Bękarty | "bastards" are also Chaste's illegitimate children, the plot; game title stays |
| Chastener | Karzyciel | Chaste + chasten |
| Homestead | Ostoja | haven for outcasts, the Drifter's destination |
| Drifter, Lucky Lady | unchanged | ship names |
| mod | przedmiot | Polish "mod" means a game modification |
| bunch / gang | grupa / banda | "grupa" is a squad on the planet map |
| roadblock / posse / pack | blokada / obława / sfora | |
| Prince | książę | Chaste's children: McNeil, Francisco, Barrabas |
| Hole in the Wall | Dziura w Murze | Butch Cassidy's gang hideout |
| snuff (Kram) / cramm | tabaka / cramm | cramm is currency, untranslated |
| infamy | niesława | |
| Gunhand | rewolwerowiec | |
| Yellowbelly | cykor | coward, enemy behind a shield |
| Cranker | korbiarz | crank gatling |
| Bushwhacker | czatownik | lurks in the bushes |
| Mortician | grabarz | summons ghosts |
| Ironclad | żelaźniak | |
| Blaster (grenadier) | wysadzacz | |
| Stinger | żądłak | |
| Gunbarrel / gunbucket | lufa | "Wygląda jak beczka" |
| Jackbox | skrzynka-pułapka | jack-in-the-box |
| Kyote | kojot | |
| Earsplitter | uszorwacz | |
| Pepperbox | pieprzniczka | Polish name of this gun |
| Cruxmas | Gwiazdka Cruxa | Jorge Crux is the local Jesus |
| Stitch | Szew | a hole in space |
| juice / shine | bimber | |
| stunt | popis | |
| showdown | starcie | |
| backdoor | furtka | |

## Opportunities taken

- "Bought the farm" (Hopalong wanted a farm and died): "dostałeś kawałek ziemi, tylko nie taki, jak
  chciałeś", "poszedł wąchać kwiatki od spodu".
- Little Jeb censors swearing and innocent words: "żałosne worki ch-słów", "możecie ż-słowo do woli"
  (e-word = eat).
- Casino's "Manwidth" (manpower + bandwidth): "przepustowości na chłopa".
- Wanted-poster charges: Cephaloculpa → "Głowobójstwo", Paletticide → "Podniebienniobójstwo",
  Jaywalking → "Łażenie po jezdni".
- Sarge "What's the charge?" → "Jaki zarzut?", the Judge "Sustained" → "Przychylam się".

## Deliberate departures

- Descriptions with numbers rebuilt as "Name: <d>" to avoid numeral agreement ("Nietykalność po
  zabójstwie, sekundy: <d>").
- "Send: {0} for {1} jumps" → "Wyślij: {0}. Liczba skoków: {1}." (names in placeholders stay
  nominative).
- Some names shortened for UI ("Czapka z folii", "Bomba migdałowata", "Handlarz").
- Weekdays shortened ("pon."), am/pm → "rano" / "po poł.".

## Review

No independent full review yet. Check report: missing 0, tokens 0, terms 0 (exceptions in the bible);
left: consistency 93 (same English in different places, e.g. "Tough" as an enemy trait and as an ace
name, deliberately different), English 6 (proper names: Grizzly, Casino, Legs, Las Calaveras .45,
Calavera Uno/Dos), plurals 10 (number always after a colon), length 50 (item and ace names),
capitals 10 (proper names), typography 9 (straight quotes in `<sprite name="…">`).

## Check in game

- **Dialogue speakers:** keys don't name them. Riskiest: intro scenes (FletchIntro, SpikeIntro,
  RoswellIntro, PreachIntro) with several speakers. Wrong self-gender → the scene name is enough.
- **Outlaw screen:** long ace names and item descriptions ("Sojuszniczy zaprawiony rewolwerowiec",
  "Ponowne losowanie znalezionych przedmiotów: <d>").
- **Sector map events (SME):** descriptions with several numbers and choice buttons.
- **Outlaw status:** "Rany", "Zmęczenie", "Naładowanie", "Rozproszenie" (nouns instead of adjectives)
  on the card.
- **Time cards:** "rano" / "po poł." and short weekdays.
