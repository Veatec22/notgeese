# Children of the Sun: translation decisions

## Direction

Text only: no dialogue, no voice; story told in wordless cutscene art (source: survey of string
table and scenes, `docs/technical.md`). 170 entries: UI, tutorial, death reasons, score
categories, level titles, challenge hints, a dream poem, endless mode. Reading: menus and level
info wait for the player; tutorial prompts and death reasons show during or right after a shot
(short, read at a glance; to test).

Tone: terse, dark, a bit poetic in titles/poem/hints; crude streak in a few jokes (score category
"Dick", arcade minigame title). Protagonist: a girl (Wikipedia, store page) hunting a cult.

### 1. Level titles: translate (agreed with user)

Titles are short poetic phrases, shown on the map and level intro. Translate, keep brevity and
double meaning where present. Place-like plain names translate plainly.

| Key | EN | Recommended PL | Variant | Note |
| --- | --- | --- | --- | --- |
| LV_TheBarn | Old Home | Stary dom | Dawny dom | |
| LV_HuntingStand | Gallery of Heads | Galeria głów | | trophy heads at a hunting stand |
| LV_Factory | Manufacturing Lies | Fabryka kłamstw | Produkcja kłamstw | "fabryka" keeps the place (Factory) |
| LV_Marketplace | Open Mic Night in Hell | Wieczór otwartego mikrofonu w piekle | | user; rejected "Otwarta scena w piekle" |
| LV_Motel | This is no Paradise | To nie jest raj | Żaden to raj | |
| LV_Cemetery | Bury your Past | Pogrzeb przeszłość | | imperative, like EN |
| LV_Endless | Nightmare Paralysis | Paraliż senny | | user: simpler than proposed "Paraliż przysenny"; rejected "Koszmarny paraliż" |

Alternative to the whole topic: leave titles in English (stylish, but Polish game should be Polish).

### 2. Crude jokes: same strength, feminine protagonist (agreed with user)

| Key | EN | Recommended PL | Variant |
| --- | --- | --- | --- |
| hit_dick (score: hit body part) | Dick | Fiut | Krocze (softer) |
| pacman_title | I Just Killed a Man / Now I'm Horny | Właśnie zabiłam człowieka / I jestem napalona | Właśnie zabiłem… (masculine) / impersonal rebuild |

Feminine because the protagonist is a girl and the minigame plays inside her story; Queen echo
("Mama, just killed a man") survives either way. RU drops gender ("Человек убит").

### 3. Mechanic terms (agreed with user)

| EN | PL | Why |
| --- | --- | --- |
| Re-Aim | przecelowanie (Re-Aim Indicator → wskaźnik przecelowania) | one word, declines; "ponowne celowanie" too long for HUD |
| Bullet Time | czas lotu | user; proposed "czas kuli" rejected |
| Powershot | silny strzał | plain, says what it does |
| Weakpoints | słabe punkty | standard |
| Targets / enemies | cele / wrogowie | |
| Mark (them) | oznacz | |

Tutorial mood: imperative 2nd person singular ("Przytrzymaj przycisk", "Wyceluj"); RU uses formal
plural, Polish games default to "ty".

### 4. Poem and challenge hints (agent decision)

Poem (dream level, 5 couplets) addresses "you" (father figure / cult leader). Free verse; keep images
and the final threat, avoid gendered 1st person where Polish allows ("A ja – twoim błaznem").

| Key | EN | PL |
| --- | --- | --- |
| dream_poem_01a/b | You drugged me with kindness / So I can pretend I exist | Odurzyłeś mnie dobrocią, / bym mogła udawać, że istnieję |
| dream_poem_02a/b | You were my father / And I was your fool | Byłeś moim ojcem, / a ja – twoim błaznem |
| dream_poem_05a/b | Soon the sun will start shining / Through a bullet shaped hole in your head | Wkrótce słońce zaświeci / przez dziurę po kuli w twojej głowie |

01b needs gender ("bym mogła"); feminine per protagonist. Alternative neutral: "bym udawać mógł…"
no; impersonal "by dało się udawać, że istnieję" loses the voice.

Challenge hints are riddles pointing at a condition (shed: "The Virus is in their heads" = head
shots). Keep the hint recoverable: "Wirus siedzi im w głowach". Never explain the condition outright.

### 5. "Dead" → "Trup" (agreed with user)

Key `gameplay_dead` "Dead" (kill screen, flying letters at the end): "Trup", user ruling.

### 6. Capitals and broken source (agent decision)

EN Title Case → Polish sentence case ("Return to Menu" → "Wróć do menu"). 

### 7. Player addressed as a woman (agent decision, follows topic 2)

Death reasons in 2nd person past are feminine: `fail_geometry` "Trafiłaś w coś twardego",
`fail_outoflevel` "Posunęłaś się za daleko" (after review, user).

## Full translation (2026-10-08)

170/170 entries; check report clean except three length hints (`menu_holdToSkip`,
`options_vsync` seen fine in the vertical, `LV_Marketplace` to check).

- Poem: the addressee ("you", father figure) is masculine ("Odurzyłeś", "Byłeś", "stałeś się
  obcy", "Zostaniesz jedynakiem"); speaker feminine only in 01b ("Bym mogła"). Lines keep the EN
  layout: capital letter, no final punctuation.
- Opportunity: `challenge_highwayBridge` "Just passing through" → "Tylko przelotem" (bullet flight
  + passing by).
- Challenge riddles kept vague: `challenge_huntingStand` "Dwa w jednym", `challenge_riverb`
  "Modlitwa za modlitwą zabija" (praying enemies one after another), `challenge_bunker` "Minęło
  sporo czasu" (EN "It's been a long time"; may hint at a time condition).
- `endless_tutorial_04`: "Sacrifice yourself with your own bullet" → "Poświęć się, trafiając się
  własną kulą" (mechanic: the player hits herself to bank the score).
- `endless_tutorial_02` keeps the trailing space of the EN.
- Credits stay in the original (names, scene text outside the table).

## Review

- **Scope:** 2026-10-08, independent reviewer in fresh context (no translation history).
  170/170 entries read by group, EN identical to `work/source/en.json`, tags and line breaks
  intact. Input before fixes = full 0.1; after fixes `en-pl-review.json` SHA-256 9c6037b245b3d9cc….
- **Fixes applied:**
  - `endless_tutorial_04`: "trafiając się własną kulą" → "trafiając samą siebie własną kulą"
    ("trafiać się" means "to happen"; feminine player).
  - `tutorial_movement`: "Rozejrzyj się po okolicy" → "Poruszaj się po okolicy" (EN instructs
    movement, not looking).
  - `tutorial_reAim`: "aby go użyć" → "aby przecelować" ("go" had no clear antecedent).
- **Pre-vertical decisions:** all kept (level titles, crude jokes, przecelowanie / czas lotu /
  silny strzał / słabe punkty, feminine player, Trup, sentence case).
- **To discuss:** poem 04a/04b addressee (may be the girl herself, not the father; neutral "Będziesz
  jedynym dzieckiem"); `fail_outoflevel` "Posunęłaś się za daleko" (keeps the moral double
  meaning); `tutorial_aim` "czysty strzał" calque → "wolne pole do strzału"; `endless_tutorial_03`
  "Naciśnij na ołtarzu" → "Użyj ołtarza"; `challenge_swamp` "Przy bakach" → "Od baków";
  `aroundUser` → "Wyniki zbliżone do twojego"; `multikill` (decide after seeing the trigger);
  `pacman_title` "A teraz jestem napalona" (optional).
- **User rulings on the review (2026-10-08):**
  - `dream_poem_04b` → "Będziesz jedynym dzieckiem" (neutral, keeps who "you" is open);
    04a "I tak stałeś się obcy" kept; feminine "Zostaniesz jedynaczką" rejected.
  - `fail_outoflevel` → "Posunęłaś się za daleko" (literal + moral); "Poleciałaś za daleko" replaced.
  - `tutorial_aim` keeps "Gdy masz czysty strzał"; "wolne pole do strzału" rejected.
  - `endless_tutorial_03` → "Użyj ołtarza, by przyzwać ich więcej." (matches `interact`).
  - `challenge_swamp` → "Od baków z paliwem świat płonie jaśniej".
  - `aroundUser` → "Wyniki zbliżone do twojego".
  - Open: `multikill` (after seeing its trigger), `pacman_title` line 2 unchanged.

## Check in game

- Options: "Polski" at the end of the language list; switching to it and back to English.
- Long labels: "Synchronizacja pionowa", "Światło wolumetryczne", "Odwróć oś Y celowania".
- Score lines on the win screen (`multikill` "Kilku naraz", `hug` "Uścisk": meaning of Hug unknown,
  check what triggers it).
- Tutorial prompts during aiming and flight: length, Polish letters in every font.
- Map: long level titles ("Wieczór otwartego mikrofonu w piekle", "W pogoni za kłamstwami").
- Dream level: poem lines layout.
- Arcade minigame: title on two lines, uppercase instructions.
- Endless mode (Options unlock prompt, intro, altar tutorial).
