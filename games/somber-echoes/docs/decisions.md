# Somber Echoes: translation decisions

1507/1507 entries; the 111 accepted vertical entries unchanged. Polish is a separate language `pl`
("Polski" in the selector); English stays original (user decision). Facts: `translations/bible.yaml`.

## Characters

- **Adrestia and Harmonia: women, twins** (TheFracture1.1–1.2, GOG description). Adrestia gets
  feminine forms in all descriptions and achievements: "Łuczniczka", "Miłośniczka sztuki",
  "Wojowniczka przestworzy", "Całkiem niezła inżynierka", "Godna dźwięcznego ostrza".
- **Journal in feminine first person** (Adrestia); dialogue narrator in third person; Adrestia's lines
  kept apart from the narrator's.
- **Aether and Nyx as a pair:** masculine-personal plural ("wyjaśnili", "ryknęli"), since Aether is
  male.

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Aether / Nyx | Eter / Nyks | Polish mythological forms, consistent with power names | decision (vertical accepted) |
| Fracture | Rozłam | plot event, declines well; figurative "fracture" translated otherwise | decision |
| Radiance / Nocturne | Blask / Nokturn | light–night pair; Nokturn keeps the musical, nocturnal ring | decision |
| Ashfall / Cesspit / The Grove | Popielisko / Ściekowisko / Gaj | map zones as Polish place nouns | decision |
| Centimanes | Sturęcy | Polish name of the hekatoncheires | mythology |
| Circe (chamber) | Kirke | Polish form; the C.I.R.C.E. system keeps the acronym ("Interfejs C.I.R.C.E.") | decision |
| Pythia | Pytia | Polish form | mythology |
| Gladius, Arbiter | unchanged | weapon names; "gladius" lowercase inside upgrade names ("Wzmocniony gladius 1") | decision |
| Via Regia, Via Pelagus, Opera Publica | unchanged | Latin street names, as in EN | decision |
| The Maiden (memory/statue) | Panna | archetype series (Wojownik, Żeglarz, Łowczyni), ties to Demeter and Kore | decision |
| Poseidon's Blight | Niedola Posejdona | distinct from "Udręka Demeter" | user |
| Exit (map legend) | Wyjście | legend items are nouns; button hints stay "— Wyjdź" | review |

Also in the bible: Spopieleni, Feniks, Legion Helikonu, Mojry, boska dwójca.

## Deliberate departures

- The narrator's inversions ("his gratitude he extended") not copied; elevated tone via vocabulary,
  not word order or rhyme.
- Source typos (Ather, vulnurable, deaccelarate) fixed.
- Boss achievements as verbal nouns ("Oślepienie Cyklopa", "Uciszenie Harmonii"), not copied
  participles.
- "No stone left unturned" → "Pod każdym kamieniem".

## Review

2026-09-25, fresh-context subagent, read-only: 1507/1507 in five batches (dialogue by scene), no
gaps; newlines, placeholders and `[ICON:…]` tokens intact. All term decisions kept. 8 certain fixes
applied: "Ostatni raz widziano ją żywą, gdy szła…", CirceAutoSecurity1.2 "komory Kirke", "doszła do
godności Pytii", "Wyrocznia z pustym wzrokiem orzekła", "zagubiła się" (not "zaginęła"), "o moich
rysach i rysach Harmonii", map "Wyjście" ×2. User decisions 2026-09-26 applied: "Niedola
Posejdona", "Sam sobie wrogiem" (Own worst enemy), "Na dobrej drodze" (Well on your way), "Moje
wewnętrzne oko nabiera mocy." (mind's eye).

**Open, text unchanged:**

1. Kirke ↔ C.I.R.C.E. bridge (`CirceAFOnAI1.1` and other "Interfejs C.I.R.C.E. — … — aktywny"):
   recommend keep; option "Interfejs komory Kirke (C.I.R.C.E.)".
2. "Czysta Nyks" as matter (`NecklaceProduction1.1`, `NyxInfusedFibre_DESC`) reads as the goddess:
   option "z czystego Nokturnu" (NyxPotency1.1 says Nocturne is named after Nyx); would need a pass
   over all Nyx-as-substance.
3. `TUT_GatherAether` "aby odnowić Adrestię" → "aby Adrestia odzyskała siły".
4. "Bow & Spear aim" → "Celowanie łukiem i włócznią" (the bow is "Nocny rozbłysk"): recommend keep.

Low priority: "lecz wciąż się trzymający" (SurvivorCPC1.1); "w czasie dziewiczego rejsu"
(SacredOak_DESC); "Eter i Nyks, gniew wcielony, ryknęli jednym głosem." (DivineWrath1.1); "coraz
bardziej się zbliżając" (PoseidonFleeing1.1); "nietykalność" instead of "niewrażliwość"; "Pozwól
Hefajstosowi ukończyć naszyjnik"; "Kolekcjonerka" (Completionist); "Kolekcja" instead of
"Znajdźki"; "Ramię fabryczne" capitalized; "dumny i wyprostowany" (DefacedStatue1.2); unclear whose
betrayal in HephaestusTraitorFull1.5; two hint conventions ("— Wyjdź" vs "Wyjście").

No context (text unchanged): `STRING_Menu/Log` and Journal both "Dziennik" (two tabs?); "Ocalały" for
women?; "Assembly Hall" → "Hala montażowa" (key says offices); "feebleness of Nocturne" (EN typo?);
"świątyni Ponad Bogiem" (which room?); `TUT_EvadeEnemy` "następnego wroga" (following = chasing?).

Check report after: missing 0, tokens 0, gender 0, address 0, plurals 0; terms 9 (`[ICON:Aether]`,
"Fracture" as a crack), English 22 (icon tokens, same words in Polish), typography 27 (source trailing
spaces; kept only in "Poziom {num} " where it may join text), capitals 6 (icon labels), length 9,
consistency 3 ("Exit" as button "Wyjdź" vs map "Wyjście", intended).

## Check in game

1. Language selector: "Polski" at the end, switches at once, kept after restart (hooks tested only
   on a model).
2. Map: where "Wyjście" shows; long names "System podtrzymywania życia (1)", "Sklepy z egzotycznymi
   roślinami", "Przeprawa przez nieczystości".
3. First Kirke chamber in the Lower Quarters: security messages and "Interfejs C.I.R.C.E.": does the
   player connect the names?
4. Survivors: "Ocalały" shown for women? Menu: are Log and Journal two tabs?
5. Long lines: AntenorHubris1.1 (126-char row), NyxOverflow, SpecimentGrowth, StrandedInTheVoid,
   ArtemisMissing, LoveLetter: wrapping and display time.
6. Challenges and ranking: "Strącenie Ptaka stymfalijskiego", "Celowanie łukiem i włócznią", "Gracz
   w rankingu światowym" truncation.
7. All-caps headers: does Ą render (Maitree-Cinzel Medium lacks it)?
