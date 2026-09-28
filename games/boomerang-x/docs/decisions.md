# Boomerang X: translation decisions

Facts and sources: `translations/bible.yaml`. Translated before the direction stage existed;
decisions written down afterwards (2026-09-26), then independently reviewed.

## Direction

Calm, slightly fairy-tale mantid world; terse menus; Tepan warm, chatty, awkward, food humor,
no swearing. Place names translated; beings and peoples (Tepan, Kaspidae, Kenak, Atsil,
Vashkatar, Entacca, Yoran) kept.

## Characters

- **Tepan: no grammatical gender** (agreed with user, option A). Developer notes always say
  "they"; one note allows feminine "if needed" (found by the reviewer). Past tense rebuilt
  impersonally, stiffest spots smoothed: "mignęło mi, jak przechodzisz", "Tylko parę razy mi
  to mignęło", "Nie trzeba było w ogóle tak długo tam zostawać", "w nogi — wszystkie sto —
  i precz stamtąd!", "na moich oczach nigdy nie zadziałała", "im dłużej to trwało".
  *Rejected:* option B feminine.
- **Player: no gender** (agent). Tepan uses "ty"; gendered forms avoided. "friend" → "bratnia
  duszo" (user; rejected "przyjacielu", masculine).
- **Kaspidae feminine** (after "modliszka"), **Pustelnik masculine** (after the noun),
  **Kenak masculine** (developer note).

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| Flux / Slingshot / Scattershot | Strumień / Zryw / Odłamki | short, one word like EN; 20-char limit | decision |
| Needle / Blaze / Oblivion Comet | Igła / Żar / Kometa Zapomnienia | | decision |
| … Kill (combo) | Zabójstwo … | "Trafienie" means hit | user |
| The Grudge Pit | Dół Porachunków | arena for settling feuds; rejected "Dół Urazy" | user |
| HUD Scale | Wielkość HUD-u | option changes HUD only; rejected "Wielkość interfejsu" | user |
| Endless Run / leaderboard | Bieg bez końca / ranking | | decision |

Also user: "Sterowanie klawiaturą i myszą" / "Sterowanie padem" (rejected "Zmień…");
"otoczone szczególną powagą" for "solemn" (rejected "wyjątkowo uroczyste"); toggle labels as
nouns: "Przerywnik na początku gry", "Odrodzenie od ostatniej fali" (rejected imperatives).

## Technical limits on text

`|pause|`, `|short_pause|`, `|long_pause|` pace dialogue; `[[…_icon]]` button icons; `{0}`,
`{1}`; `<size=80>`. Control-screen titles ~15 chars per line (developer note). `max_length`
counts without tags.

## Review

2026-09-26, fresh-context subagent, 359/359 entries read in 14 batches, no gaps. Tags match EN in
all entries; 3 `max_length` overruns fixed. 10 certain fixes applied, e.g. "Skąd ty się tu
wziąłeś?" → "bierzesz?" (player gender leak), "jako towarzysz towarzyszowi" → "po
przyjacielsku" (gender leak), "Wymazali po nim wszelki ślad" → "Zatarł tu wszelkie ślady"
(Kenak is the subject), "Tryb światłoczuły" → "Tryb dla wrażliwych na światło", "Połącz
ponownie" (limit). User then accepted 8 topics (19 more entries). Verdicts on early decisions:
keep all except Tepan (reopened, settled as option A).

## Open

Not decided, current text stays:

- `millipede_funnel_lore_3`: "Nie umiem ci się dostatecznie odwdzięczyć" → "Nie wiem, jak ci dziękować."
- `allow_all_accessibility_explanation`: "Biegi z tymi ustawieniami trafiają do osobnego rankingu."
- Minor Tepan lines: "Niejedno próbowało!", "Nigdy nie przyszło mi do głowy...", "Ciągle się
  zastanawiam, czy...", "prawda?" for "nieprawdaż?", "wyszperać" for "uskładać", "wsadzali
  rośliny w swoich zmarłych", `sewers_lore_8` "zesłało mnie" (sender may be Kaspidae).
- UI: "Porusz gałką dla akcji", "następuje wtedy ognisty wybuch", "urozmaicić rozgrywkę",
  "żeby gra była łatwiejsza albo trudniejsza", "słabych punktów", "Patrzenie w górę…",
  "(w poziomie)/(w pionie)", "Poleca szef kuchni.".
- No context: "DWÓR STROICIELI" (court = court or arena yard?), "WYMAGANI:", "Wyważony pod pada".

## Check in game

1. Tepan's dialogue box with the longest lines (`chasm_lore_1`, `chasm_default_2`,
   `funnel_lore_3`, `sauna_lore_3`, `statue_room_default_4`) and `|pause|` pacing.
2. Key-binding screen ("Naciśnij przycisk dla akcji / „Skok”"): centering, two lines, „” glyphs.
3. Combo notifications in Dead Stock: "Zabójstwo bez Strumienia x3" width and letter size.
4. Longest option labels vs the value column.
5. FOV slider: values ending in 2–4 would make "{0} stopni" wrong → "{0}°".
6. Unlock screens and area titles in caps with ż ł ę ("ŁAŹNIA PUSTELNIKA").
7. Tutorial plaques with icons; difficulty prompt (both rows); wave HUD "FALA 2/5", "WYMAGANI:".
