# Anger Foot: translation decisions

Facts and sources: `translations/bible.yaml`. Translated before the direction/review process;
later checked against the localization standard: all 1100 dialogue lines read, 210 entries fixed.
Style and terms of the first translation kept.

## Characters

- **Speaker and addressee gender come from the game table** ("NPC (Female)" > "Player"). Report
  over all dialogue: zero -łem/-łam, -łeś/-łaś mismatches.
- **Anger Foot is masculine** when addressed ("Pomogłeś temu miastu"). Table says only "Player";
  Russian is consistently masculine ("ты опоздал").
- **Pizza Świnia: feminine declension, masculine gender.** "Pizza Świni", "Pizza Świnio!", but
  "Pizza Świnia próbował nas zabić" (male in the table).
- **Baron Mazi / Umysł Brudu: masculine**, although the table says "Neutral"; the names are masculine.

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Shit City | Zasrane Miasto | same force | decision |
| Pollution Gang | Gang Smrodu | shorter and funnier than "zanieczyszczeń" | decision |
| the CEO | Prezeska | Office Boss (Female) | table |
| goon | zbir | | decision |
| sneakers | buty / sneakersy | "buty" in speech, "sneakersy" in fashion contexts | decision |
| shoe (UI item) | buty (plural) | one pair; singular "but" mixed with "buty" before review | user |

## Fixes during the standard check

- **Polish capitalization** (188 entries): achievements, goals, shoes, levels, collectibles and
  credit roles in sentence case. Capitals kept for world proper names (gangs, bosses, Wieża
  Zbrodni, Śmieciowa Góra, districts, clubs, English block names).
- **Level names in quotes inside achievement descriptions** so lower-case names don't blend in:
  "Spuść wodę w „Nowym początku”."
- **Plurals with {0}:** non-personal nouns rebuilt to fit any number ("Wytęp karaluchy: {0}",
  "Ukończ poziom w czasie poniżej {0} s", "kopiąc mniej niż {0} razy"). "Zabij {0}
  zbirów/wrogów" kept: masculine-personal form is right for 2+.
- **Meaning errors:** "No overtime pay" = "Nadgodziny niepłatne" (not "Żadnych nadgodzin");
  "You're giving me away!" = "Wydasz mnie!" (playing dead); "Włącz pad".
- **Idioms:** "Świeć, Pizza Świnio, nad jego duszą...", "Cztery w pamięci...", "ukradł nam
  ubrania z grzbietu", "Bo jak nie... ...to kopnę tę stertę butów".

## Opportunities taken

- **Song/bong** (developers asked for adaptation): "JA TEŻ UWIELBIAM TEN TOWAR!".
- **Trash Fest / Cash Fest:** "Szajs Fest" / "Hajs Fest", rhyme kept.
- **Developer / developing a hunger:** "Pracuję w dziale rozwoju." / "Rozwija mi się apetyt."
  ("deweloper" in Polish means a property developer).
- **Lactose / lack toes** ("Good luck translating this"): via Glut Glina, ex-boss of the Violence
  Gang: "Szkoda tylko, że nie trawię glutenu." / "Miałem podobny problem w poprzednim gangu." /
  "Nie trawiłem Gluta." Boldest change: the foot-fetish hint is lost from the text (the
  character still stares at feet). Literal fallback: "Mam nietolerancję laktozy" / "Nie
  zniosłem braku palców u stóp".
- Kept as good: "Na drugi etat kradnę koty", "Zmiany kryminatyczne są prawdziwe", "Ale z ciebie
  KĄSEK!", "D.P.P.K.G.S.", "Kupkowo".

## Deliberate departures

- "Kopnąłeś {0} razy." stays although 1 gives "1 razy": post-level card; "Kopnięcia: {0}" kills the tone.

## Review

Independent review, 2026-10-02, fresh-context subagent (`localization-review`).

- **Scope:** `en-pl-review.json` SHA-256 `ad40c11b…6a2941` (before fixes). 1774/1774 entries read
  (1060 dialogue, 714 UI) in 13 batches: dialogue in `structure.yaml` order, the rest by key group.
  Manifest: `work/review/manifest.md`. No EN/context drift vs `work/ref-all.json`. Unresolved, no
  context: 27962 (Minit reference), 28935 `Requires ` (empty in RU/FR/DE/ES, probably unused).
- **Fixes applied** (premises verified by the lead):

| id | EN | old PL | new PL | reason |
| --- | --- | --- | --- | --- |
| 27262 | Movie night is on hold. | Wieczór filmowy odwołany. | Wieczór filmowy musi poczekać. | postponed, not cancelled (27326, 27643) |
| 27317 | We still have our whole lives ahead of us! | Mieliśmy przed sobą całe życie! | Mamy jeszcze przed sobą całe życie! | Goo Cop urges dying Bag Cop to live; past tense gives up |
| 27405 | …until I've seen every dancer. | …każdej tancerki. | …wszystkich tancerzy. | dancers are assorted (male) enemies |
| 27842 | Drones. Slaves to the system... | Trutnie. | Trybiki. | "truteń" = idler, contradicts "harują" |
| 27987 | I'm not a corporate drone. | …korporacyjnym trutniem. | Nie jestem korposzczurem. | joke inverted: pooping on company time is what a truteń does |
| 28510 | Crosshair Opacity | Przezroczystość celownika | Krycie celownika | slider read backwards |
| 28883 | …without any tanks breaking | …nie rozbijając żadnej butli | …bez rozbicia żadnego zbiornika | specimen vats, not gas cylinders (28847 "butla z propanem") |
| 28831 | Go on a trip and destroy a toilet | Wybierz się w podróż i zniszcz kibel | Zniszcz kibel na haju | "trip" = getting high (context) |
| 27576 | Well, look at me now! | spójrzcie | spójrz | addressee is the player, singular |
| 28025 | …is behind on its targets. | nie wyrabia celów | nie wyrabia normy | collocation |
| 28741 | Big Brain Booties | Wielkomózgie Kapcie | Wielkomózgie kapcie | sentence case for shoes |
| 27701 | It's bring your child and make them work day. | dzień przyprowadź dziecko… | dzień „Przyprowadź dziecko i daj mu robotę”. | event name needs quotes |
| 27763 | Yes.... | Tak.... | Tak... | typo |

  Rejected: 27964 "46217" → "46 217" with a non-breaking space: NBSP appears nowhere in the file,
  font support unverified; a plain space risks a mid-number wrap in the bubble.
- **Pre-vertical decisions:** all **keep**: Zasrane Miasto (pairs with Kupkowo, Miłe Miasto),
  Gang Smrodu (pays off in 28035, 28051, 27895), Prezeska, zbir, buty/sneakersy, Pizza Świnia
  declension, Szajs/Hajs Fest, sentence case, quoted level names, Anger Foot / Baron Mazi masculine,
  other adaptations. Glut/lactose pun: keep, final call in game. "Kopnąłeś {0} razy": keep, a
  whole-game count of 1 is practically impossible.
- **Discussed, user decisions 2026-10-02** (all applied, 25 entries):
  1. 28672 Put Foot: "Daj gazu" → "Gaz do dechy" (user's choice over "Noga w podłogę"; foot lost, accepted).
  2. 28683 Pork Braai: "Wieprzowe braai" → "Świniobicie".
  3. Shoe item plural: 28722 "Odblokowano nowe buty", 28727 "Buty odblokowane!", 28724 "Losuje buty
     po każdej śmierci", 28936 "Wybrać nowe buty?", 28799 "Losowe buty". "Moc buta" kept.
  4. 28922 "SKOMPLETUJ KOLEKCJĘ". 5. 28253 "Wyjęty korek". 6. 28237 "Pokusa zwyciężyła".
  7. 28606 "Coraz wyżej". 8. 27490 "Carol i Mike". 9. 28815, 28891, 28893, 28895 "w czasie {0}".
  10. Calques as recommended: 28020 "To się nazywa nauka!", 27583 "I najlepiej się bawimy!", 27733
     "puszczę z dymem całe to miejsce!", 27848 "gdzie się podział budżet", 28098 "Możesz zostawić nas
     samych?", 27860 "Jako że sam jestem stażystą, nie wolno mi mówić nic poza „Tak”.", 27784 "Tak robi
     siedmiu na dziesięciu prezesów, którzy odnieśli sukces.", 28786 "Oszołom gapiów", 27187 "Najlepsza
     ofiara, jaką dziś mieliśmy!".
  Not raised, current text kept: 28886, 28269, 27637, 27333, 28793, 28665, 28696, 28457, 27711, 28935.
- **Post-fix state:** report unchanged (gender 0, address 0, terms 0, tokens 0, missing 0,
  plurals 0, English 0, consistency 0, typography 0; length 14, capitals 5) after both rounds.

## Check in game

- Settings → Pad: three aim-assist options of 31–34 chars ("Przyciąganie wspomagania celowania")
  next to the slider. Gameplay: "Krycie celownika" at 0 = invisible crosshair? Graphics: are
  quality options ("Wysoka/Niska/Średnia", feminine) reused for "Zasięg cieni" (masculine)?
- Death screen: "NACIŚNIJ DOWOLNY PRZYCISK, BY ZACZĄĆ OD NOWA" (44 chars) fits?
- Level goal picker (stars): "Wytęp karaluchy: 20", "Ukończ poziom w czasie poniżej 45 s" in the frame;
  "Ukończ poziom w czasie 01:25" readable; "w butach {0}" with real shoe names.
- Long bubbles: 27744 (RnD reception, 145 chars), 27928 (Trevor McGee), shrinking-font jargon
  27801–27813.
- Pizza District, lactose scene (27593–27597): does the lactose/Glut pun work, or go back to literal?
- Boiler room 27378–27381 (utwór/TOWAR); Office Boss Aftermath B 27668–27673 ("PIZZA ŚWINI!" chain).
- Crime Tower: 27352 → 27353 ("MIŁEGO MIASTA!"), ending prompts 28914/28915, final "Kopnąłeś {0} razy.".
- ALL-CAPS Polish letters in every font style: DJ 27279–27283, Mic Screamer 27832–27834, tutorials.
- World map challenge lock: is "Wymaga " + shoe name (28935) ever shown?
