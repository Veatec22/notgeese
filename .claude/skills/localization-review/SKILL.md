---
name: localization-review
description: Independent review of a game's whole Polish localization after the full translation. Check EN/PL meaning, edit dialogue, and re-evaluate pre-vertical decisions in light of the whole game. Separate certain fixes from options to discuss; does not replace in-game testing.
---

# Review after full translation

A separate review of all text in the full translation, not another look at the sample. Read
[RULES.md](../localization/RULES.md).

## Launch and responsibility

The lead agent starts a subagent in fresh context (no translation history; with `fork_turns`
pick `none`) and passes: this skill, game dir and scope; the full `en-pl-review.json`, bible and
`docs/decisions.md`; scene context, game material and limits from `docs/technical.md`; current
`l10n_report.py` output as hints, not a substitute for the text.

Reviewer is read-only and returns findings to the lead; never spawns another reviewer or writes
translations. The lead records results, applies fixes, talks to the user. No subagent available →
say there was no independent review; never present your own reread as one.

## Full scope

First fix the count and ids of entries to review using the game's own id scheme (e.g.
`table` + `term`, not always `key`). Compare EN/PL with the extraction; report gaps and drift
instead of guessing which is current. Don't change shared formats for the review.

Read whole entries by scenes and functional groups. Split big games into batches and record key/
scene coverage so the review can resume without gaps (manifest may live in `work/`). The report
truncates and caps output: it can't prove completeness. After batches, synthesize terms, voices
and decisions for the whole game. Missing context ≠ error: mark read but unresolved.

## Passes

1. **Fidelity and correctness.** Meaning, negation, conditions, quantities, omissions, additions,
   character references, gender, addressee, terms, tag syntax.
   [Knowledge and foreshadowing](../localization/RULES.md#knowledge-perspective-foreshadowing):
   certainty, scope, source of information, emotion and its cause. Judge omitted details against
   later scenes; never explain a hint earlier than the original. No context → flag doubt, not a
   certain error. Mechanics instructions deserve the same care as dialogue.
2. **Editing.** Read the scene in Polish without constantly peeking at EN: rhythm, comebacks,
   subtext, voices. Then check every proposed change against EN, context and bible. Shorter or
   fancier isn't better by default. Judge [strategy](../localization/RULES.md#strategy): did
   adaptation keep function without changing facts, did literalness lose the effect? Compensation:
   check the whole linked scene and whether the player can see it; omission: reason and real loss.
   Departing from EN words is not an error; "transcreation" doesn't excuse a meaning change.
   [Audio](../localization/RULES.md#audio-vs-text-only): with dubbing catch drift in content,
   register, bluntness vs the audible original; with text/mumbling judge meaning and effect, don't
   undo a good adaptation just to look like EN. Without recordings don't claim performance checks.
   Judge concision against [reading conditions](../localization/RULES.md#reading-conditions) in the
   bible; without data name the scene and risk for a test instead of a certain length error.
3. **Decisions on the whole.** Revisit every significant pre-vertical choice: tone, names, terms,
   relationships, adaptation degree. Do later scenes confirm them? Does a term mean something else
   later, was a voice oversimplified? Verdict: **keep**, **proposed change** or **no context**,
   with keys/examples and scope of consequences.

Certain errors may be fixed with a concrete reason. Stylistic options and uncertain
interpretations go to the conversation. Never override user rulings; reopen one only with new
evidence from the full game: show the earlier choice, the new premise and a recommendation.
Different taste alone never justifies returning to a rejected option.

## Output and closing (lead agent)

Add a `## Review` section to `games/<game>/docs/decisions.md`:

- **Scope:** date, text identity (e.g. SHA-256 of inputs), total/read entries, batches/scenes, gaps.
- **Fixes:** key, EN, old PL, new PL, reason, status (proposed / applied / rejected with reason).
  Reviewer never claims changes the lead hasn't made.
- **Pre-vertical decisions:** verdicts, including kept ones.
- **To discuss:** scene/keys, EN, current PL, recommendation, optional second option, gain and
  cost. Group repeated issues. Show the user usually 5–10 top topics; the cap doesn't limit the review.
- **Check in game:** concrete scenes/screens and what the test should settle.

The lead verifies premises and applies certain fixes; presents stylistic options and waits on
those not delegated, keeping current text meanwhile (independent fixes and builds may proceed).
Choices and rejections update the bible and `docs/decisions.md`.

After integration re-check changed lines and their dependencies, file consistency, tokens and the
report with the game's validators/build. A global term or voice change means checking every
affected occurrence. Record the re-check scope and post-fix state. No loops of full rewrites.
Open proposals and missing in-game tests stay explicit at handoff.
