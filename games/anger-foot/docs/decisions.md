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

No independent full review yet. Check report after fixes: gender 0, address 0, terms 0, tokens 0,
missing 0, plurals 0 (silenced with reasons), English 0, consistency 0 (two deliberate variants),
typography 0; length 14 (bubbles wrap; settings listed below), capitals 5 (proper names).

## Check in game

- Settings → Pad: three aim-assist options of 31–34 chars ("Przyciąganie wspomagania celowania")
  next to the slider.
- Death screen: "NACIŚNIJ DOWOLNY PRZYCISK, BY ZACZĄĆ OD NOWA" (44 chars) fits?
- Level goal picker (stars): "Wytęp karaluchy: 20", "Ukończ poziom w czasie poniżej 45 s" in the frame.
- Sewers, Debauchery Gang bar: does the lactose/Glut pun work, or go back to literal?
