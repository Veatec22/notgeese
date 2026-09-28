# OTXO: translation decisions

The translation predates the localization skill; reviewed against it on 2026-09-22 (bible, check
report, all 1364 entries read, gender compared with the game's Russian file): 15 entries changed.
Facts: `translations/bible.yaml`.

## Characters

- **Otxo: male.** The journal is a father searching for his son; RU masculine throughout.
- **Girl at the bar (liquor importer): feminine.** Was "sam udźwignę", "mógłbym". Journal 9174: "The
  girl at the bar has rewarded me with new drinks"; only the bartender and she are in the Rose Room.
  RU doesn't settle it, FR has masculine "Désolé": a decision, not a certainty.
- **Bartender: "pan" only on the first visit**, then "ty"; where EN says "sir" again (weapon ban),
  impersonal. Was "Wybacz pan, ale nie obsłużę uzbrojonego" (gruff; he's polite) → "Przepraszam, ale
  uzbrojonych nie obsługuję".
- **Bekatua: feminine** (after "istota"), consistent in the Scripture of Bekatua.

## Fixes in the review pass

- **Joined death-screen texts:** the game appends the location to "IN " and the boss to "FIGHTING "
  (RU "В: ", "СРАЖАЕТСЯ С: "). Was "W NIESKOŃCZONY HOL", "WALKA Z LEGIONISTA" → "MIEJSCE:
  NIESKOŃCZONY HOL", "PRZECIWNIK: LEGIONISTA".
- **Bar bill:** "Twój rachunek to 2 monet." broke for 2–4 → "Rachunek w monetach: 2."
- Meaning: "kick your enemies to death" was "zakopać" (bury) → "skopać wrogów na śmierć".
- "kręci jednobrękiem" (not a word) → "zakręcenie jednorękim bandytą"; "którzy tam patrolują" →
  "którzy ją patrolują".
- Church of Steel: "uśmiecha się do takiego oddania"; "Deadliness is next to godliness" →
  "Śmiercionośność jest bliska świętości" (proverb echo and alliteration).
- Journal: "próbowałem rezydencji" (calque) → "szturmuję rezydencję"; "czołgać się na czworakach" →
  "się czołgać".

## Opportunities taken (kept from the first version)

"Hair of the Dog" = "Klin", "Sprzedasz papierosa?", "wilku morski", shanty "Sally Racket, hej-ho",
"Kochamy Cvnkę, o tak, o tak!" and its echo on the mad journal pages ("kochamy to o tak").

## Deliberate departures

- " Years Later" → " lat później". RU and FR translate without a number ("Годы спустя", "Des années
  plus tard"), so the game likely doesn't prepend a digit; check at the ending.

## Review

No independent full review yet (only the review pass above). Check report: gender 0, address 0,
tokens 0, missing 0, plurals 0, consistency 0, capitals 0 (world names, ignored in the bible).
Terms 2 (false: "roll" of waves, short combo counter), English 1 ("Laser"), length 3 (bubbles and
settings wrap), typography 1 ("." after the coin count, intended). RU gender comparison: 104
masculine and 6 feminine lines agree with PL.

## Check in game

- Death screen "MIEJSCE: …", "PRZECIWNIK: …": does the colon look right?
- Bar, first visit with a weapon, damage bill "Rachunek w monetach: 37."
- Importer in the Rose Room: if the bartender speaks, revert to "sam", "mógłbym" (2 words in
  6508–6509).
- Ending: nothing before "lat później".
