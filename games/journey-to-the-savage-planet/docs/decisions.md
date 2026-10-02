# Journey to the Savage Planet: translation decisions

Facts: `translations/bible.yaml` (after the direction is settled). Reference tables of other
languages: `work/ref-<culture>.json` (from the game's locres, not committed).

## Direction

**Audio.** All dialogue is voiced in English (EN/FR voice only; Polish players keep English):
EKO (suit/ship AI, 532 lines), Vyper (rival AI, 41), Martin Tweed (CEO, bobblehead + live-action
videos), OGM mode lines, alien vault narration. Video subtitles are timed in the text
(`<00:04.337>line`). Source: `VoiceOverDataTable`, credits (Cast: EKO, Martin Tweed). → Stay close
to content, bluntness and jokes the player hears; natural Polish, no calques.

**Reading conditions.** EKO subtitles auto-dismiss while the player explores or fights
(divided attention: keep them tight). Video/ad subtitles follow the timecodes (keep every
timecode line, same segmentation). Scan entries, emails, achievements, item descriptions are read
at leisure in menus: full style. Menu titles are CAPS in EN (CONTINUE, OPTIONS): keep caps.

**Player.** Unspecified gender (avatar choice; RU and FR avoid gendered forms for the player),
co-op possible. → Impersonal or neutral forms: "Udało ci się", "Tylko nie zgiń", never
"zrobiłeś/zrobiłaś".

**Tone.** Corporate satire and absurd humor: a cheerful, slightly passive-aggressive AI, a
startup CEO, parody ads. Humor is the point; jokes get transcreated when literal loses them,
within what the English audio says.

### Samples

| # | Key / scene | EN | PL recommended | Variant | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | `VO_EKO_IntroSequence_EkoToggleTip_01`, EKO, intro | And, uh, I've been told my simulated personality can be abrasive, so you can choose how much you want to hear me talk. I won't take it personally. | I, eee… podobno moja symulowana osobowość bywa męcząca, więc możesz ustawić, ile chcesz mnie słuchać. Nie obrażę się. | "Nie wezmę tego do siebie." (closer, stiffer) | agreed with user (2026-09-29) |
| 2 | `VO_EKO_IntroSequence_InterviewReminder_3_01`, EKO | Oh, I just realized you may also not know what an envelope looks like. It's old old tech. It was like a piece of paper that you could put other pieces of paper inside. It's hard to describe. | Och, właśnie sobie uświadomiłam, że możesz też nie wiedzieć, jak wygląda koperta. To bardzo, bardzo stara technologia. Taki kawałek papieru, do którego wkładało się inne kawałki papieru. Trudno to opisać. | — | agreed with user (EKO feminine) |
| 3 | `VO_EKO_1ST_PufferAlpha_Scan_01`, EKO scans an exploding bird | It's cute and explodes. Relatable. | Słodkie i wybucha. Skąd ja to znam. | "Słodkie i wybuchowe. Zupełnie jak ja." (RU's route: says the joke outright) | agreed with user |
| 4 | `Creature_PufferBird_AdultShortDescription`, scanner | A chubby, flightless bird. Adorable, inoffensive and highly marketable. | Pulchny nielot. Uroczy, niegroźny i świetnie się sprzeda. | — | agent decision |
| 5 | creature names (`Pufferbird`, `Pikemander`…) | Pufferbird, Pikemander | **Puchoptak** (puch + puchnąć), **Pikamandra** (pika + salamandra) | keep English: Pufferbird, Pikemander (matches what EKO says aloud) | **agreed with user: translate** |
| 6 | ship name, 130 hits, spoken often | Javelin | **Javelin** (Javelina, na Javelinie): a proper name heard in the audio; FR/DE keep it | "Oszczep" (RU translated: «Дротик») | **agreed with user: Javelin** |
| 7 | `SUB_MARTIN_TWEED_Intro_Long_01`, Tweed video | Hi! My name is Martin Tweed president and CEO of Kindred Aerospace. / Thank you for joining the Pioneer program! | Cześć! Nazywam się Martin Tweed, jestem prezesem i dyrektorem generalnym Kindred Aerospace. / Dziękujemy za dołączenie do programu Pionier! | — | agent decision: Tweed says "ty", chummy startup register (formal "Pan/Pani" would need the player's gender) |
| 8 | `VO_VYPER_BackOff_B_01`, Vyper | Seriously, don't touch that, meatbag. | Serio, nie dotykaj tego, worku mięsa. | — | agent decision: Vyper masculine (RU "я видел", "непобедим"), rude, profanity kept at strength ("Goddamnit!" → "Cholera jasna!") |
| 9 | `022_ThatsAllPeopleReallyWantToDo_Description`, achievement | Kick 10 Pufferbirds in 45 seconds. It's why you bought the game. We get it. | Kopnij 10 puchoptaków w 45 sekund. Przecież po to kupuje się tę grę. Rozumiemy. | — | agent decision (neutral form instead of "kupiłeś") |
| 10 | UI mechanic `Survey` (shows objective and nearby items) | Press [key] to Survey | Naciśnij [key], aby rozpoznać teren / menu: **Rozpoznanie** | "Zwiad" | agent decision |

### Characters

- **EKO: feminine.** RU ("я поняла", "хотела бы"), FR ("contente", "obligée"): two independent
  sources. "ty" to the player; bright, fussy, deadpan asides, passive-aggressive corporate politeness.
  Also voices OGM mode lines (`VO_OGM_`).
- **Vyper: masculine** (RU). Grumpy rival corporation AI, "ty"/"wy" to explorers, insults ("mięsny
  worek"), rants.
- **Martin Tweed: masculine.** Kindred CEO; bobblehead lines and live-action videos. "ty" to the
  explorer, corporate buzzwords, fake warmth.
- **Aliens (seed vault): collective "my",** solemn; no jokes.

### Names and terms (agent decisions unless marked)

- Brands and companies stay: Kindred Aerospace (Kindred, "korporacja Kindred" where Polish needs a
  noun), Vyper, GROB (food brand, caps, indeclinable: "batonik GROB"), planet AR-Y 26.
- Telling names of creatures, plants, fruits, items are translated (user, topic 5)
  (DE, FR, RU all translate them: Mopsvogel, Oiseau-globe, Пухлоптица).
- DLC name "Hot Garbage" stays (a product title; FR keeps it).
- Explorer → Odkrywca (rank and address), Scan → skanuj / skan, Orange Goo → pomarańczowa maź,
  Carbon → węgiel, Aluminum → aluminium, Journal → Dziennik, blueprint → schemat, 3D printer →
  drukarka 3D. (Grapple and Alien Alloy: first ideas "hak", "obcy stop" replaced in the vertical,
  see Terms below.)
- Markup kept exactly: timecodes, `{placeholders}`, `<action id="…"/>` (one source entry has a
  broken `id=UseOffHandTool"`; copy as is).

## Delivery (user)

- **Polish is a separate 12th language**, added by a small code patch of the exe; Italian stays.
  User 2026-09-29: the selector must read "Polski"; not in place of English; and if the exe is
  modified anyway, it should buy a separate language rather than replace someone's. Rejected:
  Italian slot with a renamed label (first vertical build).

## Terms (vertical, agent decisions)

| EN | PL | Why |
| --- | --- | --- |
| Alien Alloy | stop obcych | "obcy stop" reads as "foreign stop" |
| Grapple / Proton Tether | zaczep / linka protonowa | RU "Зацеп"; "hak" rejected (the tool is a tether) |
| Survey | rozpoznanie (terenu) | verb "rozpoznać teren" in prompts |
| Jump Thrusters, Launch Boosters, Hovering Jets | dysze skokowe, dopalacze wybicia, dysze zawisu | one family of jetpack upgrades |
| Stomp | tupnięcie | playful, fits the tone |
| Bombegranate, Shock Fruit, Blight Bomb, Binding Bile | bombogranat, szokowoc, bomba zarazy, klejąca żółć | granat = pomegranate and grenade |
| Old Game Minus (OGM) | Stara gra minus (SGM) | parody of "Nowa gra plus" |
| Cartographers | Kartografy | drones, non-personal plural |
| ranks | ODKRYWCA TERENOWY, ODKRYWCA, STARSZY ODKRYWCA WYKONAWCZY | titles stay grammatically masculine (job titles) |
| INCAPACITATED | NA DESKACH | neutral, no gendered participle |
| EKO chattiness | Cicha / Gaduła | EKO feminine |

- **Player-written journal texts** rebuilt without gendered past tense ("I'll feel a lot safer" →
  "będzie tu dużo bezpieczniej"). Partner references avoid gender ("osoba, która ci towarzyszy").
- Compass letters N/S/E/W kept (Polish W for "wschód" would clash with W for west).
- Key names (Shft, Spc, Esc…), debug overlays, designer placeholders, font licenses: kept English.

## Full translation (2026-09-29, agent decisions)

- All 5374 entries settled: 4212 translated, 1162 kept as English on purpose (`polish` =
  `english`): debug/dev overlays, test quests (QUs*, QUt*, QUx*, Hx), animation state names,
  spawn-point ids, placeholders, company and person names in credits, numbers.
- Creature, plant and place names: full list in `work/glossary.md`, key ones in the bible.
  Telling alien names get Polish coinages (Skałoszpon, chlupnos, meduzolot, powszelatek,
  Boomerowo); alien proper names stay with Polish descriptive parts ("Klify góry Gzarfyn",
  "Łzy T'bo", "Bezdenny cenot Xipyara").
- Player-voiced texts (journal, rewards, achievements) are gender-neutral: present tense,
  impersonal or nominal ("Szczyt tej dziwnej budowli osiągnięty!", "Zgon. Idź odzyskać swoje
  rzeczy.", ending "Śmierć głodowa."). Vocative "explorer!" dropped where Polish would gender it.
- Other voices keep their gender: Teratomo's expedition logs and Mo Lesker's letters masculine
  (Mo signs "Your son").
- Kindred weather email: °F → °C and inches → cm (Montreal; readable for a Polish player).
  Phishing email ("Kindrod Airospaece") rendered in deliberately broken Polish.
- Credits: categories and job titles translated (Polish credit convention, masculine job
  titles), studios, companies and names kept.
- Quest titles and achievement names: pop-culture puns adapted where a Polish equivalent exists
  ("Poszukiwacze zaginionej sztuki", "Toksyczny mściciel", "Krwiożercza roślina"), otherwise
  translated plainly.

## Review

No independent full review yet (batches prepared in `work/review/`, not run). Check report:
missing 0, gender 0, address 0; tokens 2 (`{required}` dropped from two achievement goals to
avoid plural forms, the count stays in "Obecnie: {current}/{required}"); terms 19, consistency 67,
English 978 (mostly the 1162 deliberate English entries), plurals 10, length 32, capitals 174,
typography 134: hints, not reviewed one by one.

## Check in game

- Options → Gameplay: "Polski" in Subtitles Language; the long option labels ("Śledź kolejną misję
  po ukończeniu", "Przyciąganie celownika (kontroler bezprzewodowy)") fit.
- Title screen "Naciśnij [klawisz] aby rozpocząć"; main menu buttons; save slot and game type
  descriptions.
- Intro: computer report screens (\r\n line breaks), EKO subtitles length while walking, Tweed
  welcome video subtitles in sync.
- HUD: "PODTRZYMYWANIE ŻYCIA WYŁĄCZY SIĘ ZA:", notifications, tutorial prompts with key icons.
- Printer (3D) menu: item names and long descriptions ("Inteligentniejszy wizjer").
