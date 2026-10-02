# Labyrinth of the Demon King: translation decisions

Locres has no speakers. Bible and `structure.yaml` (2026-10-02) take speakers from the dialogue
DataTable that defines each key (`tools/key_sources.py`); hero lines inside NPC tables are read from
the text. No independent review yet.

## Voices

- Protagonist male. Maid and cat merchant feminine (from context).
- Kappa casual; priest calm; modern letters keep their vulgar register.
- Japanese weapon and creature names stay recognizable.

## Terms

| EN | PL |
| --- | --- |
| Demon King | Król Demonów |
| Labyrinth | Labirynt |
| Warden / Jailer | Strażnik / Dozorca |
| Tower of Repetition / Crushing Assembly / Lamentation / No Interval | Wieża Powtórzeń / Miażdżenia / Lamentu / Nieustającej Męki |
| Hell of… | Piekło… (matching its tower) |
| King's Court | Królewski Sąd |
| guard / parry | garda / parowanie |
| blunt / slash / pierce | obuchowe / cięte / kłute |
| rot / poison / bleed | zgnilizna / trucizna / krwawienie |
| Bloodletter | Krwawnik |
| Chrysanthemum Blade | Ostrze Chryzantemy |
| Ritual / Purifying Incense | kadzidło rytualne / oczyszczające |
| Gem Wheel | koło z klejnotem (color as described) |
| butsudan, shirikodama, mon | kept |

## Priorities and departures

- Puzzles: meaning, directions, numbers and order first; King's Court testimonies don't rhyme at
  the cost of hints.
- Joined messages: "There is…" → "Znajdujesz: " so the item name stays nominative; trailing spaces
  kept.
- Eight source texts repeat the locked-door sentence twice; Polish has it once.
- "Cons." → "Zużyw." provisionally; needs UI context.
- Some achievement jokes adapted freely; judge with the achievement image.

## Review

No independent full review yet. Check report (2026-10-02): missing 0, tokens 0, plurals 0; terms 8,
consistency 6, English 16, length 8, capitals 19, typography 8: hints, not reviewed one by one.
Speaker check against `structure.yaml` found two masculine forms in the merchant's lines
(„Tak jak obiecałem”, „co mówiłem?”; she is feminine, RU agrees): fixed to „obiecałam”, „mówiłam”
in 0.2.

## Check in game

Long dialogue and notes, hell descriptions, puzzle hints, map names, item messages (declension),
speaker gender.
