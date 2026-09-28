---
name: localization-direction
description: Set the direction of a game's Polish localization before the vertical, after a positive technical analysis. Prepare an EN/PL sample and settle significant tone, character voice and terminology choices with the user; record them for the translator and reviewer.
---

# Direction before the vertical

Goal: the user sees concrete language options before the vertical fixes a style for the full
text. A small editorial trial on real game text, not a build.

## Prepare

1. Read `games/<game>/docs/technical.md`, existing bible and `docs/decisions.md`. Keep earlier
   agreements; don't ask again. Establish audio: intelligible dialogue, mumbling only, or text only
   (may differ per scene); record it and its source in bible `style.adaptation`
   ([audio rule](../localization/RULES.md#audio-vs-text-only)). Establish
   [reading conditions](../localization/RULES.md#reading-conditions) (click vs auto-dismiss,
   player busy meanwhile) with source or explicit doubt in `style.reading_conditions`, per text
   group if they differ; reflect them in the sample.
2. Read [RULES.md](../localization/RULES.md). From the extraction take a short coherent exchange
   plus menu/settings, instructions and descriptions where present. Usually 10–20 entries. Pick
   material that shows a real choice: humor, formality, telling names, character contrast. Never
   invent dialogue; if material is thin, say so.
3. Keep keys, context and full EN. Establish speaker, addressee and order where there is evidence;
   sorted keys don't rebuild a scene. Later text may inform tone; don't spoil the plot needlessly.
4. Write the recommended PL and, only where the choice matters, an alternative. Apply
   [strategy](../localization/RULES.md#strategy): show where precision vs adaptation is needed and
   what must survive. Say what a variant changes: distance between characters, bluntness, rhythm,
   mechanic clarity, name association. A wrong translation is not an equal variant of taste.

## Talk and record

Write the sample to `games/<game>/docs/decisions.md`, section "Direction": keys/scene, EN,
recommended PL, variant, reason, status **proposal** / **agent decision** / **agreed with user**.
Usually 3–5 topics, no artificial minimum. Never write variants into `en-pl-review.json`.

Show the user this sample and ask about the significant choices. No survey about every name or
comma. If earlier agreements suffice or there are no meaningful variants, state the direction and
move on. After asking, wait before dependent translation (independent technical prep may go on).
Silence never turns a proposal into an agreement. If the user delegates the choice, decide.

Then fill `translations/bible.yaml` (format in the [localization skill](../localization/SKILL.md#bible-format)):
tone, voices with examples, terms, adaptation limits, rejected options. `source: user` only for
actual user rulings; the rest is `decision` or an open fact needing context.

Hand the direction to the [localization skill](../localization/SKILL.md) and build the vertical
(menu, settings, start of the game per `AGENTS.md`). Full translation still needs the user's
in-game confirmation of the vertical.

## Limits

- A game with a few labels and no dialogue needs no rich bible.
- The sample sets a starting point; the reviewer re-evaluates it after full.
- Don't reread literature per game; `RULES.md` holds the conclusions.
