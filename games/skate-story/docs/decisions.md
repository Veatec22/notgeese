# Skate Story: translation decisions

The translation was reviewed against the localization skill (bible, check report, all narration,
dialogue, poems, items, UI read): 19 entries changed, mostly gender and a few awkward lines.
Facts: `translations/bible.yaml`. Spoilers below.

## Characters

- **Skater: masculine.** Genderless in EN ("the Skater", "it"); Polish follows "skejter" and "demon".
  RU does the same.
- **Beea (flower seller): feminine.** Was "gdybym miał kwiaty", "Już sprzedałem"; RU "я обменяла".
  Oscar calls her "ta ślicznotka" (was "ten słodziak").
- **Skeleton from the Square of Regret: masculine.** Was "Myślałam"; RU "я понадеялся", FR "il m'a vu".
- **Millstone (ch9): masculine.** RU feminine, ES and FR masculine; Polish "kamień" is masculine.
- **Frotue: masculine about himself, "Żaba" (f) in narration** ("spytała Żaba").
- **Licha from the Department of Death: feminine, "pan" to the Skater.** RU doesn't settle it.
- **False Sun: neuter.**

## Terms

Skater = Skejter (capitalized); underworld = podziemie; Crest = pieczęć; Moon = Księżyc; Moon Vision
= Księżycowy Wzrok; combo = kombo; stomp = tupnięcie; Thinkpiece = Myślokształt; Soulflower =
duszokwiat; Moonflower = Księżycowy Kwiat; Fuss = Zgiełk; Blood Seer = Krwawy Wieszcz; Sloucher =
Garbus; Eternal Centipede = Wieczna Stonoga; Oblivion = Zapomnienie; deck = blat; contract = umowa
(once "kontrakt"); stale = oklepany; soul expired = dusza wygasła. Trick names ollie, kickflip,
heelflip, revert, manual, grind kept. HOUSE/CHEESE letters in the world: dialogue and descriptions
give the English word plus the meaning DOM/SER; letter models unchanged.

## Fixes in the skill pass

- **Opening echo:** ch8 repeats the game's first lines ("This Demon was hungry and tired…"); both now
  "Ten demon…".
- "Ty chybotliwy draniu" (Wobbly bastard); "Powietrze rozdarł krzyk 40 000 dusz"; "jednym wdechem";
  "przed nią" (before the Centipede).
- Deck "Literature": "Pierwszy list z „Frankensteina”" (the novel opens with Walton's letter);
  "Dead Typographer": "zanim niemal oślepł".
- Philoso rhyme: "a Księżyca zjesz niemało". Typography "1400 °C".

## Opportunities taken

- **Hamlet** ("to die, to skate, perchance to repeat"): "Sposób, by umrzeć, jeździć — powtarzać
  może", echoing the Polish "śnić może".
- Philoso's rhymes, "jestem zajęty byciem W KROPCE", "Demon Dom Ser", "Skejter poczuł wszystkość".

## Deliberate departures

- Capitals in world entity names ("Pranie Diabła", "Łańcuch Deskorolki") as in EN; lowercase where EN
  is.

## Review

2026-09-26, fresh-context subagent, read-only: 2305/2305 in 12 batches, no gaps; speakers inferred
from content (TYPE column not in the review file). Very good translation; terms ~100% consistent,
tags intact. All early decisions kept. 17 certain fixes applied, e.g. "Spójrz przez swoją rękę"
(through the glass arm, not over the shoulder), the Devil's letter "wypalił się" (not "spalony"),
"święto Księżycowych Kwiatów", "Doszło do mojej wiadomości", "Metro nie chciało się już dalej
cofać", "Zaraz miał się rozlec daleki skrzek" (imminent), "oklepany" and "wygasła" unified, "Skejter"
capitalized on the ollie obelisk, "szare klify", "Całe Podziemie", "wytopiły się z lodu".

**Open, waiting for the user (current text stays):**

1. Licha's phone, pain/pane [1034]: "Ze... szkła i... bólu?" → "Ze... szkła i... szyby?" (echo of
   the tagline twist "ze szkła i bólu").
2. Lyceum → "Liceum" (11 entries in ch1) or "Likejon" (Aristotle's school); recommend "Liceum".
3. "Ten Bolgias" → "Dziesięć Jarów" [339], [342] or "Dziesięć Rowów" (Malebolge, [1754] talks of
   "rowy"); recommend "Rowów".
4. Rhymes: Philoso [795] last line "Za trud twój Myślokształt niech będzie zapłatą." → "Masz więc
   Myślokształt — nie trudziłeś się marno."; Larry [990] "KARMIĄ MNIE WIBRACJE. / JEDŹ DLA MNIE,
   BESTIO." → "WIBRACJE — MOJA STRAWA. / JEDŹ DLA MNIE, BESTIO KRWAWA."
5. Wire motif in poems [2245], [2251]: "żylaste sługi Zgiełku" → "druciani funkcjonariusze
   Zgiełku"; "Szorstka sierść Diabła" → "Druciana sierść Diabła".
6. Newcomers' Market as a stock exchange [1388]: "…jak na giełdę trafia każda nowa dusza podziemia"
   (careful: "…jak notuje się każdą nową duszę…").
7. Penin "skarbie" → "złotko" [1522] (jeweler's condescension; Beea says "skarbie" next to him).
8. Deck "Let's Chug Bile Tea" [66]: "Chluśnij Żółciową Herbatą" reads as "splash" → "Obalmy Żółciową
   Herbatę" (or "Chlapnijmy Żółciowej Herbaty").
9. "NIE! MA NAS!" [2207] (EN "NO! IT'S GOT US!") reads as "we don't exist" → "NIE! ZŁAPAŁO NAS!"
   ("DORWAŁA NAS!" if the Centipede is the subject).
10. Horn of Sin [1879]: "…nagromadzonym grzechu powyżej 10 000 punktów… Nie waż się sprawić, żeby
    zatrąbił." ("accumulated": the combo sum counts).

Lower-priority variants: [484]/[576] "Pokaż interfejs w scenach"; [798] "No więc"; [906] "Filozofem
wstrząsnęło"; [1061] "bez twarzy"; [1089] "flaczał"; [956] "jestem twoim szczęśliwym znakiem";
[1153] "przyszpilimy"; [1236] "My tu tylko przesypiamy przejazdem"; [1491] "To moi byli…"; [1476]
"ostatnia rzecz, do której była przykuta"; [2250] "zwymiotował"; [186] sticker "Try Hard";
[33]/[35]/[37] achievement description length. `[n]` = position in `en-pl-review.json` from 0.

No context: [620]/[621] HUD "DUSZA / WAŻNOŚĆ", [496] "ZAKOŃCZENIE" (ender trick?), [388]–[404]
trick modifiers joined with names, [1478] thinkpiece as an op-ed, [1574] "later, skater" rhyme,
[2256] "Pudełko z upominkiem", [115] deck "Oneway Stop" (road sign → "Jednokierunkowy stop"?).

Check report after: missing 0, tokens 0, gender 0, address 0, consistency 0, typography 0; terms
12 (Polish pronouns instead of repeating "Skejter"), English 1 ("II. GRIND"), length 19 (settings,
level names).

## Check in game

1. Settings → Gameplay/Graphics/Accessibility: long options next to toggles ("Wyłącz spowolnienie
   przy tupnięciu", "Automatyczne centrowanie kamery"), is "Interfejs scen" clear?
2. Soul counter HUD in ch1: "DUSZA … WAŻNOŚĆ".
3. Combo screen and Philosopher boss: trick modifiers, "ZAKOŃCZENIE", phase 3 goal [893].
4. Lyceum, Rabbit [772]: how Moon Vision looks (looking through the hand).
5. ch3 flower shop and ch7 banquet: Beea in feminine; Oscar's "ślicznotka z kwiaciarni" line.
6. ch4 Square of Regret: HOUSE/CHEESE letters with dialogue [1378]; Slouchers' silhouette.
7. ch2 station phone [1034]: "szkła i… bólu?".
8. ch8: level name "Ulica Minus Sześćset Sześćdziesiąta Szósta" (42 chars).
9. Moon Vision menu "Pudełko z upominkiem" [2256]; decks "Oneway Stop" [115], sticker "Try Hard"
   [186]; ch7 "Czy odczuwasz czasem tęsknotę?" [1811] length; achievements 17–19.
