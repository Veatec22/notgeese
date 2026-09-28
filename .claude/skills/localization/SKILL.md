---
name: localization
description: Translate a game's vertical or full text into Polish in the Not Geese repo, plus follow-up translation and fixes. Uses the game bible, the agreed direction, editorial rules and the check report; after a full translation hands everything to an independent reviewer.
---

# Localization

Goal: hit as many opportunities and pitfalls as possible on your own. Report = hints, never a
build blocker. Stay proportional: bible and report exist to save fixes, not to become a project.

Before the vertical run `localization-direction`. Read the game's `docs/decisions.md` and
[RULES.md](RULES.md). Don't reopen settled choices without new evidence. Full translation only
after the user confirms the vertical in game.

## Steps

1. **Bible** `games/<game>/translations/bible.yaml`, started before the vertical, grown with the
   full text (format below): characters (gender, how and to whom they speak, key regex), terms
   with forms, names kept in English, source of every fact, style with examples. Source order
   in [RULES.md](RULES.md#sources). Sources silent → decide, `source: decision` + one-line `note`.
2. **Translate** per bible, [strategy](RULES.md#strategy) and [pitfalls](RULES.md#pitfalls):
   speaker/addressee gender, plurals with placeholders, wordplay, UI length, subtitles,
   typography, register, profanity. Look for opportunities, not only errors. Work by scenes and
   functional groups, not random key batches. Add new facts to the bible; keep doubts for the reviewer.
3. **Check report** after each larger batch and before a build:
   `.venv\Scripts\python.exe .claude\skills\localization\scripts\l10n_report.py games\<game>`
   → `work/l10n-report.md`. Read every section, fix real issues, silence recurring false alarms
   in the bible (`keep_english`, `ignore`), never in the script.
4. **Review after full:** `localization-review`. Later small fixes: check the changes and what
   depends on them; full review again only after a new full or on request.
5. **Handoff:** update `docs/decisions.md` (template below) and summarize it to the user.

Ordinary choices: decide. Significant options: discuss twice, on the sample before the vertical
and after full on the review. User's choice → bible `source: user` with the rejected option in
`note`; never change it silently; new evidence from the whole game justifies a new conversation,
not a quiet swap. End with "check in game": concrete screens and scenes where decisions are least sure.

Don't: turn report heuristics or taste into build blockers; rewrite working text to please the
report; invent lore (a decision is marked as a decision).

## Bible format

Read by humans and `l10n_report.py`. Pick sections that fit the game. Before the vertical:
style, characters, a few terms from the sample.

```yaml
sources:                     # ids that facts refer to
  - id: keys
    description: '`term` field, e.g. vo_e3m1_7_syn: speaker at the end of the key'
  - id: cast
    description: Voice cast
    url: https://english-voice-over.fandom.com/wiki/Turbo_Overkill_(2023)
  - id: ru
    description: Russian table of the game, past-tense gender

style:
  tone: dry humor, short comebacks, no modern memes
  adaptation: free with idioms; no added lore, no stronger profanity   # plus audio situation and its source
  reading_conditions: dialogue waits for click; combat barks auto-dismiss during fights (source or "to test")
  source: decision            # user only after an actual agreement
  note: starting point from the sample, re-check after full

characters:
  - id: syn
    name: SYN                 # as in the Polish text
    gender: f                 # m | f | n (neuter/collective) | ? (unknown)
    key: '_syn$'              # regex on `term` or `key`; report then checks gender
    addresses_player: ty      # ty | pan | pani | wy | -
    register: solemn, godlike, no profanity
    declension: indeclinable ("bez SYN")
    examples:                 # 1–3 real lines showing the voice
      - {key: vo_e1m1_3_syn, en: '…', pl: '…', note: '…'}
    source: [cast, ru, keys]

terms:
  - en: biocore               # case-insensitive, may be a regex
    pl: biordzeń
    forms: [biordz]           # accepted PL stems
    source: decision
    note: one word like "rdzeń"; same in UI and dialogue

keep_english: [Paradise, Vector-4]   # names left as is; report won't flag them

settings:
  dialog_key: '^vo_'          # regex on term/key: subtitles
  max_line: 42                # indicative, confirm in game; not checked by the report

ignore:                       # deliberate report exceptions
  - {check: gender, key: 'vo_e3m9_24_syn', reason: quoting another character}
```

`check` values: `missing tokens gender address terms consistency english plurals length
capitals typography`. `source`: ids from `sources`, `decision` (+ `note`) or `user` (user's
ruling, overrides everything; `note` keeps the rejected option; silence never makes `user`).

Stems in `forms`: cut before a consonant that alternates ("artefak" for Artefakt/Artefakcie,
"piłonog" + "piłonodz"). Too short catches random words, too long misses cases.

Gender affects: 1st person past ("zrobiłem/zrobiłam", "-łbym/-łabym"), adjectives about oneself,
addressee ("jesteś pewien/pewna", "pan/pani"), 3rd person ("SYN pochłonęła").

Bible holds current rulings. Samples, open alternatives and discussion history go to the game's
`docs/decisions.md`. When a ruling changes, note the previous choice, the new evidence and the
outcome; keep rejected options on record.

## `docs/decisions.md` template

Started before the vertical, updated after full; never overwrite history with a fresh template.
Separate agent decisions, user rulings and open proposals. Be concrete: what, why, how we know.
Skip the obvious. Each point should be disputable in one sentence. Omit empty sections.

```markdown
# <Game>: translation decisions

## Direction
Tone, audio situation, reading conditions, adaptation limits. Status per topic:
proposal / agent decision / agreed with user.

## Characters
- **SYN: feminine, indeclinable.** Voice: Patricia Summersett (cast), "protect your mother". 60 lines.

## Terms
| EN | PL | Why | Source |
| --- | --- | --- | --- |
| biocore | biordzeń | one word, declines like "rdzeń" | decision |

## Opportunities taken
- SYN/sin pun: "to macie tu syna skurwysyna!" (TurboVoices 295).

## Deliberate departures
- Hand-broken lines in recordings joined; the field wraps by itself.

## Review
Scope read (entries, batches, gaps), fixes applied, verdicts on early decisions
(keep / proposed change / no context). Language review done ≠ tested in game.

## Open
Unresolved proposals: scene/keys, EN, current PL, recommendation, gain and cost.

## Check in game
- Episode 3 finale subtitles: longest lines, possible clipping.
```
