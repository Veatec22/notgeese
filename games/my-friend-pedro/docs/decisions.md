# My Friend Pedro: translation decisions

Direction settled with the user on an existing full translation (2026-09-24, "wszystkie twoje
wnioski bardzo fajne"): all three recommendations accepted. Facts: `translations/bible.yaml`.
Spoilers below.

## Direction (user)

- **Pedro: light, colloquial, fake-caring, not a tough guy.** Humor comes from contradictions
  (`w101-8` scolds for leaving a gun, `w101-9` urges picking it up), not from swearing. Keep
  "gamoń", "świr", "kurczę" where EN has them; don't slang every polite or theatrical line.
  `w102-18` "Hm...|No to teraz chyba musisz ich wszystkich pozabijać." (was "No cóż, teraz chyba
  musisz zabić ich wszystkich").
- **Puns: recreate the mechanism in Polish, keep deliberate awkwardness, add no new jokes.**
  `w410-1` "Chyba jesteśmy na właściwym torze, żeby znaleźć kolej.|Heh... tor... kolej.|Wybacz,
  taki już mam tok... tor myślenia." Rejected: "na dobrej drodze do torów", "myśli po szynach".
- **Achievement names play with words and may keep "combo".** "Mumbo Combo" → "Czary-combary"
  (x10), "Comb-o-ver" → "Combo na zaczes" (x20; was "Combo na boczek"). Rejected: descriptive
  "Combo x20".
- Mitch stays rough ("półgłówku", "nieroby") without extra swearing.

## Characters

- Pedro m, "ty" to the player; Mitch m; Ofelia f (Denny's sister, calls the hero "brother" in
  `w511-1`); Denny m, theatrical host, panicky when threatened. Not all `w*` keys are Pedro.

## Terms

| EN | PL | Source |
| --- | --- | --- |
| focus | skupienie | decision |
| split aim | rozdzielanie celowania | decision |
| Mitch the Butcher / Ophelia | Mitch Rzeźnik / Ofelia | decision |
| Internet Service Protectors (ISP) | Internetowa Straż Porządkowa (ISP) | decision |
| Old Town / District Null / Pedro's World / The Sewer / The Internet | Stare Miasto / Dzielnica Null / Świat Pedra / Kanały / Internet | decision |
| haters | hejterzy | decision |
| Mumbo Combo / Comb-o-ver | Czary-combary / Combo na zaczes | user |

Kept: names, ISP codes, gamer slang and abbreviations (LOL, GG, GLHF), key names (Tab, Home, Page
Down), game title. Grade quips A/B/C/S start with the matching letter. Old Twitter integration texts
translated as the source; the integration itself unverified.

## Fixes outside style

- `w102-14`: PL reversed who disliked whom → "albo ktoś, kto akurat im się nie spodobał".
- `w54-1` (review): closed circuit → "w obwodzie zamkniętym", not "obiegu".
- `w57-4` (review): EN gives no years → "Minęło tyle czasu...", not "Tyle lat...".

## Review

2026-09-24, fresh-context subagent, read-only: 721/721 in six batches, then all Polish dialogue
again. All early decisions kept (Pedro's voice, puns, achievement names, terms, UI clarity:
`hChW`/`mChgWep`, `mKick`/`bul28` differ on purpose). Two certain fixes applied (above). Check
report: all 0 except 18 length hints.

Open options, not applied (lead's recommendation first):
1. `w20-3` "Father Christmas"/"fathers" setup lost in Polish: "To ja, wasz świąteczny ojczulek —
   Mikołaj!"; or keep as is.
2. `w101-6` "Nieźle cię tam załatwili" names no culprit in EN; hero knocked himself out
   (`w512-2`): "Nieźle cię zamroczyło".
3. "Shit" stronger in PL ("Kurwa!"): `eAlerted1` "Cholera!", `w28-2` "O kurczę! Cholera, cholera,
   cholera..."; `w401-1` "KUUUURWAAAAAA...!" stays.

## Check in game

- `w102-18`, `w410-1`, "Combo na zaczes" (x20), `w54-1`, long `w511-1`/`w512-2` (reading time,
  splitting).
- HUD `hSec` ("DRUGA BROŃ"), trigger `interact6` ("Przewróć"): meaning unconfirmed from tables.
- `pHint3`, `pHint4`, `in36`: length with split-aim and scope icons.
- Results A/C/S, modifier labels, "Prędkość czasu w skupieniu".
