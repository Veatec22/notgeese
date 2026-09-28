# Editorial rules, pitfalls, sources

Read before the direction sample, translation and review. Local synthesis of editorial practice;
apply without rereading the literature. Not proof that LLMs do it well, not a rigid style norm.

## Strategy

Preserve the text's function and the player's experience; word similarity is not a goal.
Choose per problem in context, not one strategy per game; they combine.

| Need | Approach |
| --- | --- |
| Technical info, instruction, UI | Precise translation and terminology; literal when it works in Polish. |
| Idiom, colloquialism, cultural reference | Domesticate: natural equivalent of the function. |
| Foreignness that builds the world | Foreignize: keep realia and identity. |
| Recognizable name or established term | Keep the original form on purpose (not an omission). |
| Tone, humor, name losing effect | Transcreate: freer form, same function. |
| Untranslatable joke, rhythm, pun | Compensate: recreate the effect by other means in the line or scene. |
| Existing universe | Follow the right translation tradition and references. |

Before translating: text type and function, speaker and addressee, scene, register, terms,
known field/time limits. Use group context; no mandatory per-entry metadata or scoring.
Never fill unknowns with guesses presented as facts.

Limits of adaptation: meaning, mechanics, plot facts, needed ambiguity, tokens. Inside them keep
function, voice and natural Polish; EN syntax matters least. A name must still point to the right
object; text must fit the picture and any original audio left.

Canon: check the specific Polish release, series continuity and game context; don't import names
from another adaptation. Conflict with bible or user ruling → show evidence, don't override.

Order: faithful translation first, then adaptation or compensation. Omission last, after checking
what is lost: never drop a hint, condition, fact or trait because it's hard. Don't move
compensation into an optional branch the player may miss. Record a significant loss or shift
with keys in `docs/decisions.md`; a recurring rule goes to the bible.

### Knowledge, perspective, foreshadowing

Freedom of form never changes what a character knows, assumes or feels, dubbed or not. Keep
certainty, scope and source of information: "may" stays uncertain, "reportedly" isn't a fact,
an unknown number doesn't become a specific one. "Someone may have followed us" → "Możliwe, że
ktoś nas śledził"; "Mamy ogon" raises the certainty.

Improve how an emotion is expressed, don't swap it or its cause for drama. When shortening, check
whether a detail foreshadows a later event or change; unclear function → keep it and flag it,
don't explain early. Record confirmed links with keys.

### Audio vs text only

- **Audible dialogue, esp. English:** stay closer. Keep content, register, bluntness, emotional
  strength and intent matching the performance. "Fuck you" → "odczep się" softens too much; pick a
  Polish equivalent of comparable force. Don't smooth or amplify profanity by taste. Still natural
  Polish, no calques.
- **Text only or mumbling:** more interpretation and freer editing. Meaning, intent, character and
  scene effect come first; rebuild sentences, idioms, jokes rather than defending EN wording. Keep
  facts, mechanics, emotions audible in the mumbling.

Partial dubbing: apply per scene/line. No access to the recording ≠ no dubbing; record the doubt
and adapt cautiously meanwhile.

### Reading conditions

Audio sets adaptation freedom; presentation sets concision. Does the text wait for a click or
vanish on its own? Is the player fighting or doing a task meanwhile? May differ per scene.
Click-through → more room for rhythm and style within the UI. Auto-dismiss → mind reading time;
during active play mind divided attention. Shorten without losing meaning, character, bluntness.
Never set a character limit without data for this game. Record conditions per text group in the
bible; without timing or visuals name scenes for the user to test instead of declaring text too
long or readable.

### What to judge

- **Function:** who talks to whom, what they want or hide, why this answer. Keep information,
  intent, relationship.
- **Voice:** vocabulary, sentence length and shape, directness, rhythm, formality, humor. An
  adjective ("sarcastic") isn't enough; keep a few real PL examples in the bible.
- **Scene:** a comeback answers the previous line; a punchline needs setup. Map dependencies
  between lines and adapt linked lines together; keep the mechanism that triggers the reply
  (a deliberately wrong line the next one corrects stays wrong). After a change check the whole
  chain. Consistent voice ≠ same tone in anger and calm.
- **Naturalness:** remove calques and needless pronouns. Keep deliberate stiffness, awkwardness,
  repetition, pathos. Don't make everyone one witty narrator.
- **Adaptation:** recreate the effect, check meaning lost, emotional strength, fit to the world.
  No added facts, no removed ambiguity needed later. Memes, regionalisms and stronger swearing are
  not the default way to "add craft". Go back to the source after every edit.
- **UI and subtitles:** an instruction must lead to the same action. Shorten per real limits,
  keeping conditions. EN length is not the PL field limit; display time and attention matter too.

### What justifies a change

Separate **meaning error**, **terminology**, **language**, **style**, **technical** (simple MQM-like
categories, no scoring). Separate category from certainty: "style" can be a breach of the agreed
register or an equal option to discuss. Give evidence, not declared confidence. Context beats
recipes; mark missing data, never invent intent, identity or dialogue order. A good line may stay.
The number of fixes is not the reviewer's goal.

## Pitfalls

**Grammar from context**
- Speaker/addressee gender: past tense, conditional, adjectives, "pan/pani" (source: bible). Player
  gender selectable or speaker unknown → impersonal: "Udało się", "Trzeba było".
- Foreign names: masculine on a consonant decline ("Mawa", "z Mawem"), feminine on a consonant
  don't ("do Ripper"); silent final y with apostrophe ("Johnny'ego"); acronyms per bible.
- Numbers in placeholders: 1 zabójstwo, 2–4 zabójstwa, 5–21 zabójstw, 22–24 zabójstwa. No plural
  support → rebuild: "Zabójstwa: {0}". Never "{0} zabójstw" where 1 or 2 is possible.
- Names in placeholders: gender and case unknown → keep the placeholder in nominative ("Gracz: {name}").

**UI**
- Capitals: only first word and proper names ("Wyjdź z gry"), unless the original is all caps.
- Mood: one convention per game, imperative 2nd person ("Przytrzymaj", "Zapisz") or infinitive.
- Length: Polish runs 20–30% longer. Short fields (buttons, tabs, HUD): shorter synonym, never cut meaning.
- Platform/settings terms per Microsoft Terminology and Polish Steam (Rozdzielczość,
  Synchronizacja pionowa, Osiągnięcia).

**Subtitles**
- 42 chars × 2 lines is a film reference, not a game limit; confirm field width, font, wrapping.
- Readable in display time and during play? No timing/visuals → flag a test risk; PL/EN length
  ratio proves nothing.

**Style and tone**
- Register per bible: who swears, who is formal, who is solemn.
- Profanity of the same strength as the original: don't soften, don't add.
- Wordplay: look for a Polish equivalent (SYN/sin → "syna skurwysyna"); else keep the effect
  another way and record it.
- Telling names (enemies, skills): translate if they carry meaning; places and brands stay. Bible.
- Cultural references: keep when Polish players know them, else adapt.

**Typography and tech**
- Quotes „…”, inner ‚…’ or »…«; dash " – " or " — ", not " - ".
- No space before ? ! : ; (Polish, not French).
- Numbers: space for thousands (932 000), decimal comma (1,5).
- Tokens, tags and literal `\n` exactly as in the original.
- No English leftovers outside `keep_english`.

## Sources

Facts about the game, strongest first:

1. **Game files.** Keys/ids (speaker, scene, text type): list suffixes/prefixes once and map them
   to characters. **Other languages of the same game** encode gender: Russian, Ukrainian, Czech
   (past tense, adjectives), French, Spanish, German (noun gender). Strong hint, not an oracle
   (Turbo Overkill RU: SYN correct "я пришла", Ripper wrong "я убил"). Two independent sources
   settle it. Dump via the game's tool (e.g. `tools/other_languages.py`) to `work/ref-<lang>.json`
   (never committed). Also comments, metadata, column and scene names in tables.
2. **Cast and credits.** Actor gender doesn't prove character gender. Some games carry credits
   in a table (Turbo Overkill: TurboEx1).
3. **Wiki, TV Tropes, developer posts:** lore, relationships, joke context.
4. **Our translations of related games** in `games/` (crossovers, DLC characters, same studio):
   names and terms must match (Shotgun Cop Man's Pedro DLC ↔ My Friend Pedro PL: "Ofelia", "Pedra").
5. **Official Polish releases in the genre and earlier series entries:** terms players know.
6. **Official Polish platform texts:** Steam, GOG, consoles ("Osiągnięcia", "Zapisz grę", buttons).

Norms: [Microsoft Polish Style Guide](https://download.microsoft.com/download/b/d/c/bdc253ac-dbf3-4261-86a2-ffedfa718425/pol-pol-StyleGuide.pdf) (UI, not dialogue style),
[Microsoft Terminology](https://learn.microsoft.com/en-us/globalization/reference/microsoft-terminology),
[Netflix Polish Timed Text](https://partnerhelp.netflixstudios.com/hc/en-us/articles/216787928-Polish-Timed-Text-Style-Guide) (film reference only),
[WSJP](https://wsjp.pl), [SJP PWN / Poradnia](https://sjp.pwn.pl/poradnia), [RJP](https://rjp.pan.pl).
Use the web deliberately: one question, one source, record it in the bible. Link and conclude;
never copy others' texts into the repo.
