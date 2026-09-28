# The Hong Kong Massacre: translation decisions

## Direction

Text only: dialogue entries have no audio files or sequences; none of the game's 78 audio clips is
speech (asset survey). Free editing within meaning, facts and emotion. Typewriter 50 chars/s;
dialogue scenes (interrogation room, bar hub) are calm; whether lines wait for a click and when
boss taunts show is to be tested.

The English is written by non-native speakers: typos ("prize on your heads", "Your dead", "You
where"), stiff uncontracted forms ("let us", "I can not") across all characters, "old fashion".
Treated as writing, not a voice trait: Polish is natural, intended meaning translated.
**Agent decision.**

Sample (keys by conversation title and entry id in the "THKM" database):

### 1. How the interrogator addresses the hero: ty or pan

Police officer Siu-Wong Lo interrogates the hero, a former detective; later offers a cigarette,
tells a story from his rookie days, gets him out when the triad storms the station, and sends him
to Disco Shou. Protocol lines (dictated for the record) are impersonal either way.

| Key | EN | Recommended PL (ty) | Variant (pan) |
| --- | --- | --- | --- |
| POLICE 01 #3 | First Interrogation with the suspect regarding the events that took place between the June 10 and June 13. | Pierwsze przesłuchanie podejrzanego w sprawie zdarzeń z 10–13 czerwca. | same |
| POLICE 01 #4 | Present at the interrogation is Police officer Siu-Wong Lo and the suspect. | Obecni: funkcjonariusz Siu-Wong Lo oraz podejrzany. | same |
| POLICE 01 #6 | So let us start at the beginning. We know that you came back to Hong Kong on June 10, arriving at 17:15 with flight 1435 from Bolivia. | Zacznijmy od początku. Wiemy, że wróciłeś do Hongkongu 10 czerwca o 17:15, lotem 1435 z Boliwii. | …Wiemy, że wrócił pan do Hongkongu… |
| POLICE 02 #8–9 | Is there something that I am missing here? / If you do not want to talk I can not help you. | Czegoś tu nie wiem? / Jak nie będziesz mówić, nie mogę ci pomóc. | Czegoś tu nie wiem? / Jeśli nie chce pan mówić, nie mogę panu pomóc. |
| POLICE 05 #6 | Grab a gun! It is not safe for you here any more! | Bierz broń! Nie jesteś tu już bezpieczny! | Niech pan bierze broń! Nie jest pan tu już bezpieczny! |

Ty: cop to ex-cop, the genre's tone, the later cigarette and escape feel natural. Pan: colder
procedural distance at first, the warmth then shows only in content; stiff in the shootout.
Recommendation: ty. **Agreed with user (2026-09-28): ty**; rejected: pan.

### 2. Level titles: translate or keep English

~30 chapter titles are one-liners, several film/idiom references; location lines under them.

| Scene | EN | Recommended PL | Note |
| --- | --- | --- | --- |
| Level_Appartment_01 | DEATH COMES KNOCKING AT THE DOOR | ŚMIERĆ PUKA DO DRZWI | the hero literally knocks |
| Level_Appartment_03 | GOT A BLACK BELT! IN GUNS | MAM CZARNY PAS! W STRZELANIU | |
| (drug lab) | BIG TROUBLE IN THE SECRET DRUG LAB | WIELKA DRAKA W TAJNYM LABORATORIUM | Polish title of *Big Trouble in Little China*: "Wielka draka w chińskiej dzielnicy" |
| Level_Casino_07 | TAKING DOWN THE HOUSE | ROZBIĆ BANK | "the house" = the casino; Polish casino idiom |
| (hotel casino) | ALWAYS BET ON RED | ZAWSZE STAWIAJ NA CZERWONE | |
| (bank office) | I WANT TO MAKE A WITHDRAWAL | CHCĘ WYPŁACIĆ GOTÓWKĘ | bank-robbery cliché |

Variant: keep titles in English like film titles (loses the jokes for many players, mixes
languages on one screen). **Agreed with user (2026-09-28): translate**, transcreate puns; rejected: English.

### 3. Triad and boss names

| EN | Recommended PL | Variant |
| --- | --- | --- |
| The Two Headed Dragon | Dwugłowy Smok | The Two Headed Dragon |
| THE RAT / THE TIGER / THE DOG / THE SERPENT / THE DRAGON (boss epithets) | SZCZUR / TYGRYS / PIES / WĄŻ / SMOK | English |
| Anthony "The Boss" Tsang | Anthony „Boss” Tsang | Anthony „The Boss” Tsang |
| Tiger Claws, Deadly Snakes, wild dogs, bad wolves (gangs) | Tygrysie Pazury, Zabójcze Węże, dzikie psy, złe wilki | English |

Telling names carry the animal motif of the boss fights; translated they read. Personal names,
districts, streets, restaurants and brands (Red Dragon Restaurant, Disco Inferno, Double Fortune)
stay. **Agreed with user (2026-09-28): translate**; rejected: English.

### 4. Voices (agent decisions)

- **Liu Cheng, bartender:** childhood friend ("brothers for life"), warm, ty.
  BAR c1 01 #3–5: "Welcome back, I have been waiting for you." → „No, jesteś wreszcie. Czekałem
  na ciebie.”; "Still drinking old fashion?" → „Dalej pijesz old fashioned?”; "Here you go! For
  old times sakes." → „Proszę! Za dawne czasy.” The cocktail keeps its real name, spelled right.
- **Mr Tequila:** drunk, speaks of himself in the third person, childlike. BAR c3 03_C #3:
  "Me Tequila! That is Mr Tequila by the way." → „Ja Tequila! Znaczy się, pan Tequila.”; #7
  "Some bad wolves, very bad!" → „Złe wilki, bardzo złe!”. Broken grammar kept.
- **Disco Shou** (actor record says "Disco Cho"; lines say Shou → Shou): talks in disco song
  quotes. Polish rhythmical disco slang with the same content (tonight, Disco Inferno, pack your
  guns, they're fast); song lines not translated literally, scat „Rum bum bum” kept.
- **Bosses:** short taunts; "you dirty pig" (to an ex-cop) → „ty parszywy psie” (Polish slur for
  cops, same force).
- "They are calling it The Hong Kong Massacre in the media." → „W mediach nazywają to masakrą
  w Hongkongu.” The game title stays English on the logo only.

### 5. UI (agent decisions)

All caps as in the original. Buttons imperative or noun („NOWA GRA”, „KONTYNUUJ”, „WYJDŹ DO
MENU”), settings per Polish Steam/Microsoft („ROZDZIELCZOŚĆ”, „SYNCHRONIZACJA PIONOWA”).
„Hongkong” one word. Dates Polish: "June 14, 1992. HONG KONG" → „14 CZERWCA 1992. HONGKONG”.
Stat labels with a value after them („ZABICI WROGOWIE: 12”) to avoid plural forms.

## Full translation (2026-09-28)

424/424 entries: 106 dialogue lines (one key serves both "Boss_5" conversations), 248 labels,
14 label + value patterns, 56 control mapper texts. Done at the user's request before the
vertical was checked in game (the user decided to test the whole thing at once, at 1920×1080).

### Opportunities taken
- "ASSAULT ON THE POLICE STATION" → „ATAK NA POSTERUNEK” (Polish title of *Assault on Precinct 13*).
- "BIG TROUBLE IN THE SECRET DRUG LAB" → „WIELKA DRAKA W TAJNYM LABORATORIUM”.
- "TAKING DOWN THE HOUSE" (casino) → „ROZBIĆ BANK”; "ONE BLOODY MARY COMING UP" → „JEDNA
  KRWAWA MARY, JUŻ PODAJĘ”; "TIME TO PUT DOWN SUK-WAHS WILD DOGS" → „CZAS UŚPIĆ DZIKIE PSY
  SUK-WAHA” (put down = put to sleep, as Chef Lung's „uśpili jak psa”).
- Boss_3 (Kenneth, THE DOG) "you dirty pig" → „ty parszywy psie” (Polish slur for cops).
- Bartender's "Good fortune!" → „Niech ci szczęście sprzyja!”.

### Deliberate departures
- Typos and non-native English fixed silently in meaning: "prize on your heads" (price), "Your
  dead", "or he will shot", "MEDUIM", "MUSIC VOMLUME", "THE DRUNK ROSTER" → „THE DRUNK ROOSTER”.
- Business names stay English with the apostrophe fixed („KONG AND SHING'S DIM SUM”,
  „TEQUILA'S STEAKHOUSE”); generic nouns translated („RESTAURACJA RED DRAGON”, „HOTEL I KASYNO
  HOI-SAN”, „DZIELNICA WAN CHAI”). Streets, estates and districts keep the official English form
  („TUNG CHOI STREET”, „FU CHEONG ESTATE”) in titles and dialogue alike.
- Disco Shou: song-quote lines rendered as rhythmic Polish disco talk with the same content,
  line breaks kept; scat „Rum bum bum…” unchanged. The actor record says "Disco Cho", the lines
  "Disco Shou"; lines kept as written, speaker label untouched (not in the label table).
- NPC barks with no known listener made gender-neutral: „Widział ktoś mojego psa?”, „Wiesz coś
  o tych terrorystach w wieżowcu?” (a *Die Hard* nod, kept).
- Tutorial lines with tab gaps for key icons keep the tab count; short Polish words before the
  gaps („UŻYJ … DO RUCHU … DO CELOWANIA”, „ZA ZDOBYTE … KUPUJ I ULEPSZAJ BROŃ”).
- Stats as „ETYKIETA: wartość”; "UNLOCK {0}?" → „ODBLOKOWAĆ: {0}?” (weapon name in nominative).
- Credits blob (license notices) and debug panel labels left in English.

## Check in game
- Fonts: ą ć ę ś ź ż in Fjalla One (menus, level cards) and ą ę in Ostrich Sans (dialogue) come
  from a system font; do they show, and how different do they look? `LogOutput.log` lists which
  Bahnschrift/Arial names Unity sees.
- Length: „SYNCHRONIZACJA PIONOWA” in graphics options, „PISTOLET MASZYNOWY” on the weapon
  screen, „ZABICI WROGOWIE ŁĄCZNIE: n” on results, long level locations on the level card.
- Tutorial icon gaps (first level and the rooftop jump level).
- Interrogation: officer's lines are masculine („zaczynałem”, „widziałem”); check the model.
- Speaker labels („Policjant”, „Barman”, „Kucharz Lung”, „Pan Tequila”) appear where the game
  shows names; `untranslated.txt` shows any English label the plugin didn't know (e.g. Rewired
  action names in the controls window).
- Boss taunts: when and how long they show; the longest is Boss_5.

## Review

Independent review, fresh context, 2026-09-28.

**Scope.** `en-pl-review.json` SHA-256 `ea115a20…2a38a64` before fixes, `5a5748c3…0d761a3b8` after.
424/424 entries read EN vs PL: 106 dialogue (POLICE 01–05, BAR c1–c5, Boss_1–5, People Around
the Bar 1–5), 248 `ui/` (menus, options, results, upgrades, tutorial, level titles/locations,
epithets, dates, tips, speaker labels), 14 `fmt/`, 56 `rewired/`. Also compared `ui/` against
every `UI.Text` / `Dropdown` string in `work/survey.json`. Report before and after: only the two
known length hints (`ui/V-SYNC`, `ui/SMG`); tabs, newlines, edge whitespace and placeholders
equal EN in all entries.

**Gap (not fixable by editing PL).** `Dropdown` options aren't extracted: graphics quality
LOW / MEDIUM / HIGH and mouse mode UPDATED / ORIGINAL / HARDWARE (level1, sharedassets3). Only
HIGH and UPDATED are in the file (they are also caption `m_Text`), so the open list shows
"LOW, MEDIUM, WYSOKA" and a selected LOW shows English. Proposed: extract `m_Options[].m_Text`;
PL „NISKA”, „ŚREDNIA” (jakość), „ORYGINALNY”, „SPRZĘTOWY” (tryb). Skipped as placeholders by
`extract.py`, unresolved without the game: "FIRST COME FIRST SERVED", "First Enemy Killed"
(sharedassets0), "SCORE", "TEAHOUSE", "DUAL".

**Fixes.**

| Key | EN | Old PL | New PL | Reason | Status |
| --- | --- | --- | --- | --- | --- |
| `ui/UPDATED` | UPDATED | ZAKTUALIZOWANO | ZAKTUALIZOWANY | meaning: option of the MOUSE MODE dropdown (UPDATED / ORIGINAL / HARDWARE), an adjective for „TRYB MYSZY”, not "has been updated" | applied |
| `ui/COMPLETED` | COMPLETED | UKOŃCZONO | UKOŃCZONE | consistency: code sets it in the challenge row whose default is NOT COMPLETED → „NIEUKOŃCZONE” (three rows; `LevelDataBaseUI`) | applied |
| bible `chef` | Chef Lung | szef kuchni Lung | kucharz Lung | bible disagreed with the text („Kucharz Lung” label, „do kucharza Lunga”) | applied (bible only) |

**Pre-vertical decisions.**
- Interrogator says ty (user): **keep.** Later scenes confirm it: cigarette and wedding story
  (POLICE 03), rookie story (POLICE 04 TMPE), escape (POLICE 05 #6–8); protocol lines stay
  impersonal (POLICE 01 #3–5, 02 #3). Pan would clash with „Bierz broń!” and the anecdote.
- Level titles translated (user): **keep.** Whole set reads as one voice; references land
  (ATAK NA POSTERUNEK, WIELKA DRAKA…, KRWAWA MARY, ROZBIĆ BANK, KONIEC Z GRZECZNOŚCIAMI). One
  calque listed below.
- Triad and epithets translated (user): **keep.** The animal motif ties across text only when
  translated: Tequila's „złe wilki” ↔ W POSZUKIWANIU ZŁYCH WILKÓW, Chef Lung's „uśpili jak psa” ↔
  CZAS UŚPIĆ DZIKIE PSY SUK-WAHA ↔ PIES, WĄŻ ↔ ZABÓJCZE WĘŻE / UTNIJ WĘŻOWI OGON, SMOK ↔ MAGAZYN
  SMOKA, Dwugłowy Smok everywhere.
- Agent decisions: natural Polish over non-native EN, Disco Shou naming, masculine officer and
  bartender, „ty parszywy psie”, business names in English, stat labels „ETYKIETA: wartość”:
  **keep.** Doc note: section 5's example „14 CZERWCA 1992” applies to caps sources only; mixed-case
  sources ("June 14, 1992. HONG KONG") correctly give „14 czerwca 1992. HONGKONG”.

**To discuss** (current text stays until decided).

| Keys | EN | Current PL | Recommendation | Gain / cost |
| --- | --- | --- | --- | --- |
| `dlg/BAR  c1 02/9` | Enough of that now! | Dość tego! | „Dobra, dość już o tym!” | "Dość tego!" reads as irritation right after a warm family legend; the EN only changes topic. |
| `dlg/BAR c2 03_B/5` | …he was executed in cold blood… | …więc stracili go z zimną krwią. | „…więc zabili go z zimną krwią.” | Two lines after „Ja straciłem brata”, „stracili go” first reads as "lost him"; costs the formal "executed" nuance. |
| `dlg/BAR  c5 01 disco/5` | Those cats are fast as lightning. | Te koty są szybkie jak błyskawica. | „Te typki są szybkie jak błyskawica.” | "cats" (Kung Fu Fighting) is jive for "guys"; Polish „koty” reads literally. Option 2: keep as a song nod. |
| `dlg/Boss_2/3` | I have a bullet with your name on it. | Mam kulkę z twoim imieniem. | „Na tej kulce jest twoje imię.” or keep | Current is a known film calque, understood; low priority. |
| `dlg/POLICE 02/3` | Interrogation continues. The time is 16:45… | Przesłuchanie trwa dalej. Godzina 16:45, … | „Ciąg dalszy przesłuchania: godzina 16:45, 14 czerwca 1992.” | Mirrors POLICE 01 #5 protocol form; removes pleonasm. |
| `dlg/BAR c1 01/6`, `/7` | So the time has finally come? / Got all the information that you wanted about… | Czyli nadszedł ten czas? / Mam wszystko, czego chciałeś, o Dwugłowym Smoku. | „Czyli w końcu nadszedł czas?” / „Zebrałem wszystko, co chciałeś wiedzieć o Dwugłowym Smoku.” | Restores "finally" (the year of waiting); smoother word order. |
| `dlg/BAR  c4 01/9` | Let us have a toast for our lost brother Chan Dung-Yu. | Wypijmy za naszego utraconego brata, Chan Dung-Yu. | „Wypijmy za Chan Dung-Yu, naszego brata, którego straciliśmy.” | „utraconego brata” is stiff for a toast. |
| `ui/BANG, BANG, FEELS GOOD TO BE BACK` | BANG, BANG, FEELS GOOD TO BE BACK | BANG, BANG, DOBRZE BYĆ Z POWROTEM | „BANG, BANG, DOBRZE WRÓCIĆ” | „dobrze być z powrotem” is a calque; shorter on the card. |
| `ui/THE TWO HEADED DRAGONS BANK OFFICE - WAN CHAI DISTRICT` | …BANK OFFICE… | BANK DWUGŁOWEGO SMOKA – … | keep, or „BIURO BANKU DWUGŁOWEGO SMOKA – …” | "office" dropped; the level is an office floor. Minor. |

**Check in game** (in addition to the list above).
- Options: graphics quality and mouse mode dropdowns, open and closed (see gap);
  „ZAKTUALIZOWANY” fits the field.
- Level stats panel: challenge rows show „NIEUKOŃCZONE” / „UKOŃCZONE”.
- Boss taunts and Disco Shou: whether the actor name label shows; if so
  `Anthony "The Boss" Tsang` and "Disco Cho" stay English (no `ui/` entry; would need
  `Anthony „Boss” Tsang`), check `untranslated.txt`.
- "MUSIC OFF" → „BEZ MUZYKI”: confirm it is a toggle/challenge label where "no music" reads right.

Re-check after fixes: the two changed entries and their pairs (NOT COMPLETED, MOUSE MODE);
`l10n_report.py` unchanged (length=2, rest 0). Not tested in game.

### After review (agent, 2026-09-28)
- Dropdown options were missing from extraction (graphics quality LOW/MEDIUM/HIGH, mouse mode
  UPDATED/ORIGINAL/HARDWARE): `extract.py` now reads `Dropdown.m_Options`; added „NISKA”,
  „ŚREDNIA” (quality, feminine like „WYSOKA”), „ORYGINALNY”, „SPRZĘTOWY” (mode, masculine like
  „ZAKTUALIZOWANY”). Speaker label `Anthony "The Boss" Tsang` → „Anthony „Boss” Tsang” added;
  "Disco Cho" stays.
- Options 1–7 applied as agent decisions (none touches a user ruling): BAR c1 02/9 „Dobra, dość
  już o tym!”; BAR c2 03_B/5 „zabili go”; disco/5 „Te typki” (the *Kung Fu Fighting* "cats" nod
  would read as literal cats); POLICE 02/3 protocol form; BAR c1 01/6–7; BAR c4 01/9 toast;
  „BANG, BANG, DOBRZE WRÓCIĆ”. Option 8 kept as is („Mam kulkę z twoim imieniem”, „BANK
  DWUGŁOWEGO SMOKA”).
- Section 5 date rule clarified: caps only where the English is in caps.
