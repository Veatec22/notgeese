# Possessor(s): translation decisions

## Direction

Agent decisions; no direction session (the user asked to go straight from the probe to the full
translation). To revisit with the user at review.

- **Audio:** characters speak in barks/gibberish (no English voice lines found in the tables), so
  text-only rules: free with idioms and rhythm, facts and foreshadowing kept.
- **Tone:** Luca is a 16-year-old (DOCK_01_SURVIVOR_02_0600), sarcastic and scared; colloquial
  Polish ("stary", "serio", "kurde", "no"). Rhem is usually formal, cold and condescending, with
  emotional profanity exceptions at EN strength; he softens over the game. Dessa is pathetic and venomous; Tens is gruff ("mała").
- **Profanity at EN strength:** shit → cholera/kurde/gówno by context, fuck → kurwa/pierdolić
  (only where EN has it: "F… fuck you" → „P… pierdol się”, "I wish I fucking could"), dick →
  dupek, piece of shit → gnój, get bent → wal się.
- **UI:** imperative 2nd person singular ("Naciśnij", "Pokonaj"), sentence case, Polish quotes.
- **Forms of address:** Luca uses "pan/pani" with adults she does not know well (Foss, Tens,
  Rutto, Beverly, Tesca, Lustro, Vern, the plant researcher); adults use "ty" with her. Teacher
  Foss and Mr. Demars use "ty" (Polish school norm; the Russian table uses "вы").

## Characters

- **Luca: feminine.** 16, Blue Pass family; lived with her mom in a colony before Sanzu; has a
  sister and a bedridden grandpa. Declension Luki/Luce/Lukę/Luką; vocative written "Luca".
- **Rhem: masculine.** Rhema, Rhemowi, Rhemem.
- **Dessa: masculine** (RU "Десса убил"), Rhem's former partner, the one-horned demon who killed
  Kaz. Declines like Kuba: Dessy, Dessę, Dessie. EN typo "Dehsa" rendered Dessa.
- **Kaz (Maurice Kazinski): masculine**, rich exec family. Flashbacks B and K settle it via RU
  masculine forms; flashback F (CampusHill) follows that reading, RU "единственный" there taken as
  an RU slip.
- **Tens: feminine**, the Hunter (łowczyni); **Moja, Dau, Beverly, Tesca: feminine**;
  **Foss, Renzo, Tygo, Orren, Vern, Lustro, Rutto, Wayne: masculine.** Demon women: "demonica".

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| chroma | chroma (chromy, chromę) | coined demon word, one form in UI and dialogue | decision |
| possess / possessed | opętać / opętany | standard Polish | decision |
| host | nosiciel / nosicielka | demon's body or object | decision |
| feral | zdziczały | demons gone mad | decision |
| Rift | Wyrwa | interdimensional tear | decision |
| pocket (space) | kieszeń | between worlds | decision |
| affix | wszczep | demon organs implanted in weapons; "They'll affix you up" → „Wszczepi ci, co trzeba” | decision |
| gear / inventory | ekwipunek / rzeczy | menu tabs | decision |
| pursuit | zadanie | quest log | decision |
| whip | bicz | weapon | decision |
| vault | skarbiec | the lab door | decision |
| blue/pink/silver pass | niebieska/różowa/srebrna przepustka | lowercase everywhere | decision |
| Sunken City, Fluorescent Park, Campus Hill, Dead Mall, Rusted Dockyard, Inverted Plaza, Skyscraper Remnants, Buried Streets | Zatopione Miasto, Park Jarzeniowy, Wzgórze Kampusowe, Martwa Galeria, Zardzewiałe Doki, Odwrócona Plaza, Ruiny Wieżowca, Zasypane Ulice | descriptive district names translated | decision |
| Agradyne, Sanzu, SanZooQuarium, Infinergy, Aquamax, Rancho Mirage Flats | unchanged | brands and place names; Agradyne neuter like "Google" | decision |
| Dark Cyclopean Dynasty | „Mroczna dynastia cyklopów” | Polish title case; fans: Nocni Wojownicy | decision |
| Venderpup | Handlopies | vendor + pup | decision |
| Buttermilk, Pondscone, Gentle (horse people), Bucephalus | Maślanka, Podpłomyk, Łagodny, Bucefał | telling names; historical Bucefał | decision |

## Opportunities taken

- "Whinney! — Who's Whinney?" → „Parsk! Parsk!” / „Kto to jest Parsk?” (horse sound taken as a name).
- Renzo's motto "If you've got the skills, you can pay the bills" → „Kto ma głowę, ten ma premiowe”.
- "Hold Your Horses" (horse quest) → „Wstrzymaj konie”; "Broken Records" → „Zdarta płyta”;
  "Knot Frogs" → „Wcale Nie Żaby”; "Down the Drain, Up the Tower" → „Na dno i na szczyt”.
- Dracula "is also a landlord" → „kamienicznikiem” (Polish landlord jab).
- MLM cult in the Zoo kept as Polish MLM jargon (upline, downline, lewarować, zimny rynek).

## Deliberate departures

- `<DLang.Pose>` map line (PSE font, ASCII only) translated without diacritics: „Obietnice - Strach - Wina - Dobro”.
- Bort's growls and horse sounds lightly Polonized (GRAAA, Ihaha).
- Developer strings (BLANK, CUT, Attack - Eyeball, GetItem - …) left as in the game; DEBUG lines translated.

## Open (for review with the user)

- Whole direction above was set by the agent without a sample session.
- „chroma” collides with Polish „chroma” (feminine of "chromy", lame); kept as the game's coined word.
- Luca's declension (Luki, Luce, Lukę) vs leaving the name undeclined.
- Flashback F speaker assignment (see Characters).

## Review

### Scope

2026-10-02: independent fresh-context, read-only reviewer; all 3890/3890 entries read in full.
Reviewed by table and Articy scene in file order, including all endings, inspectables, repeated
and developer/menu entries. No coverage gaps. Extracted English matches all 3890 unique keys
and source texts; no drift. No game launch, audio-performance or visual-layout check.

Input SHA-256:

- `translations/en-pl-review.json`: `6ce00b7be6fcde3fff6c1b9875067c5e9f758e2368297488aa68f735e7b15996`
- `translations/bible.yaml`: `bcd03b17d450df3219ca203454bdb56d96a54aa241c1deadc6f1c1ecc1336356`
- `translations/structure.yaml`: `50496f124d08435c2d3746d5ae864ee598d47d4f71c73011df420091af5449b4`
- `docs/decisions.md`: `c042674f234e07e6435a0326c436644deda22ad91146b1f5260ec36850549681`

| Table | Read / total |
| --- | ---: |
| UI | 303/303 |
| Game | 282/282 |
| Narrative | 143/143 |
| Articy_Intro | 260/260 |
| Articy_Region_CampusHill | 318/318 |
| Articy_Region_FluorescentPark | 343/343 |
| Articy_Region_SunkenCity | 480/480 |
| Articy_Region_Dockyard | 129/129 |
| Articy_Region_InvertedPlaza | 201/201 |
| Articy_Region_Zooquarium | 283/283 |
| Articy_Region_DeadMall | 172/172 |
| Articy_Region_Lab | 217/217 |
| Articy_Region_Dream | 94/94 |
| Articy_SideQuests | 469/469 |
| Articy_Default | 113/113 |
| Articy_Inspectables | 83/83 |

### Fixes

17 verified corrections applied by the lead. Wording chosen to repair the evidenced defect;
stylistic alternatives remain proposals below.

- **Applied:** `Articy_Region_CampusHill/ARTICY/DFr_CAMPUS_01_SETTING_0800_0x010000000000C88B.Text`
  - EN: We are <i>people.</> We teach our children.
  - Old PL: Jesteśmy <i>cywilizowani.</> Uczymy nasze dzieci.
  - New PL: Jesteśmy <i>osobami.</> Uczymy nasze dzieci.
  - Reason: Restore the assertion of demon personhood; being civilized is a different claim.

- **Applied:** `Articy_Region_SunkenCity/ARTICY/DFr_LUCA_FLASHBACK_K_1400_0x010000000000E739.Text`
  - EN: I'm not gonna die to save a contractor's kid who's OBSESSED with making me LOOK LIKE SHIT!
  - Old PL: Nie zginę, żeby ratować dzieciaka jakiejś podwykonawczyni, która ma OBSESJĘ na punkcie robienia ze mnie GÓWNA!
  - New PL: Nie zginę, żeby ratować dzieciaka jakiejś podwykonawczyni! Masz OBSESJĘ na punkcie robienia ze mnie GÓWNA!
  - Reason: The obsession belongs to Luca, not her mother; direct address resolves the relative-clause attachment.

- **Applied:** `Articy_Region_SunkenCity/ARTICY/DFr_POCKET_DEHSAMATTERS_0900_0x010000000000E182.Text`
  - EN: If I were in Dessa's place, I'd want him to do everything he could to save me!
  - Old PL: Gdybym był na miejscu Dessy, chciałbym, żeby ktoś zrobił wszystko, by mnie ocalić!
  - New PL: Gdybym był na miejscu Dessy, chciałbym, żeby on zrobił wszystko, co w jego mocy, by mnie ocalić!
  - Reason: Restore Dessa as the reciprocal rescuer and the limit of his ability.

- **Applied:** `Articy_Region_InvertedPlaza/ARTICY/DFr_PLAZA_03_PREBOSS_1200_0x010000000000EF3E.Text`
  - EN: She's not. She gave up our friendship when she gave up on home.
  - Old PL: Nie jest. Porzuciła naszą przyjaźń, kiedy porzuciła dom.
  - New PL: Nie jest. Porzuciła naszą przyjaźń, kiedy zrezygnowała z powrotu do domu.
  - Reason: Dau abandoned the prospect of returning home, not the home itself.

- **Applied:** `Articy_Region_InvertedPlaza/ARTICY/DFr_PLAZA_TORTURECHROMA_0900_0x010000000000EDE9.Text`
  - EN: I just crank it as high as it can go before the pig passes out. Then I just let it cycle for a few hours.
  - Old PL: Ja po prostu podkręcam na maksa, zanim świnia straci przytomność. A potem zostawiam ją na kilka godzin w cyklu.
  - New PL: Podkręcam tak wysoko, jak się da bez doprowadzania świni do utraty przytomności. A potem zostawiam to na kilka godzin w cyklu.
  - Reason: Restore the maximum setting below unconsciousness and the apparatus/process as the thing cycling.

- **Applied:** `Articy_Region_Zooquarium/ARTICY/DFr_POCKETZOO_WORKINGFORDEMONS_0800_0x010000000000D421.Text`
  - EN: You ever think about how maybe your problem is that you don't understand what it's like to be a big old pile of flesh?!
  - Old PL: A myślałeś kiedyś, że może twój problem polega na tym, że nie rozumiesz, jak to jest być wielką starą kupą mięsa?!
  - New PL: A myślałeś kiedyś, że może twój problem polega na tym, że nie rozumiesz, jak to jest być wielką kupą mięsa?!
  - Reason: Big old intensifies pile of flesh without claiming old age.

- **Applied:** `Articy_Region_Zooquarium/ARTICY/DFr_ZOO_02_BANTER_03_0600_0x010000000000CF22.Text`
  - EN: Yeah… it sucks, but I'm not going to lose sleep over most of these fish.
  - Old PL: No… to słabe, ale nie będę zarywać nocy przez większość tych ryb.
  - New PL: No… to słabe, ale większość tych ryb nie spędza mi snu z powiek.
  - Reason: The idiom means worry, not deliberately staying awake.

- **Applied:** `Articy_Region_Zooquarium/ARTICY/DFr_ZOO_03_MLM_01_1100_0x010000000000D01C.Text`
  - EN: I thought you liked doing things the easy way.
  - Old PL: Myślałam, że lubisz iść po najmniejszej linii oporu.
  - New PL: Myślałam, że lubisz iść po linii najmniejszego oporu.
  - Reason: Correct the Polish idiom.

- **Applied:** `Articy_Region_Dream/ARTICY/DFr_DREAM_08_SAVERHEM_02_1200_0x010000000001575F.Text`
  - EN: What can I even do to make up for it? What do you <i>want</> me to do?
  - Old PL: Co mogę w ogóle zrobić, żeby to naprawić? Czego <i>chcesz,</> żebym zrobił?
  - New PL: Co mogę w ogóle zrobić, żeby to naprawić? Co <i>chcesz,</> żebym zrobił?
  - Reason: Correct the case required by zrobić in this construction.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_DEMON_BEAR_QUESTSTART_0100_0x0100000000012136.Text`
  - EN: Oh yeah! It's driving me crazy, man. It's locked and I can't open it!
  - Old PL: No jasne! Doprowadza mnie to do szału, stary. Jest zamknięte i nie mogę otworzyć!
  - New PL: No jasne! Doprowadza mnie to do szału, stary. Są zamknięte i nie mogę ich otworzyć!
  - Reason: The locked object is drzwi, plural in Polish; restore pronoun agreement.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_DEMON_HOOLIGANS_START_1400_0x01000000000125D4.Text`
  - EN: You will feel a little… <i>under the weather.</> But push through! It will fortify you!
  - Old PL: Poczujesz się trochę… <i>nie w sosie.</> Ale wytrzymaj! To cię wzmocni!
  - New PL: Poczujesz się trochę… <i>niewyraźnie.</> Ale wytrzymaj! To cię wzmocni!
  - Reason: The euphemism describes physical illness after ingestion, not a bad mood.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_SURVIVOR_ARCHIVES_4TO6_0300_0x0100000000012873.Text`
  - EN: I'm continuing my rewatch. I'm on the mini-arc where the main character loses his face.
  - Old PL: Kontynuuję maraton. Jestem przy minisezonie, w którym główny bohater traci twarz.
  - New PL: Kontynuuję maraton. Jestem przy krótkim wątku, w którym główny bohater traci twarz.
  - Reason: A mini-arc is a plot section, not a season; the quest distinguishes seasons elsewhere.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_SURVIVOR_ARCHIVES_7TO9_0100_0x010000000001289D.Text`
  - EN: I'm so excited to finally finish Dark Cyclopean Dynasty, kid. Do you have the episodes yet?
  - Old PL: Tak się cieszę, że w końcu skończę „Mroczną Dynastię Cyklopów”, mała. Masz już te odcinki?
  - New PL: Tak się cieszę, że w końcu skończę „Mroczną dynastię cyklopów”, mała. Masz już te odcinki?
  - Reason: Match the adopted title spelling and Polish capitalization.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_SURVIVOR_ARCHIVES_NONE_0100_0x010000000001281F.Text`
  - EN: I'll keep my eyes peeled for you.
  - Old PL: Będę miał oczy szeroko otwarte.
  - New PL: Będę miała oczy szeroko otwarte.
  - Reason: Luca is the speaker; use feminine agreement.

- **Applied:** `Articy_SideQuests/ARTICY/DFr_SURVIVOR_PLANTS_START_1600_0x01000000000126DE.Text`
  - EN: You know what? Your research sounds legit to me. I'll get your plants!
  - Old PL: Wiesz co? Jak dla mnie te badania brzmią legitnie. Przyniosę pani te rośliny!
  - New PL: Wie pani co? Jak dla mnie te badania brzmią legitnie. Przyniosę pani te rośliny!
  - Reason: Remove the within-line ty/pani conflict; preserve pani used in the scene.

- **Applied:** `Articy_Default/ARTICY/DFr_DESSA_TRUTH_1600_0x0100000000015E6B.Text`
  - EN: Even a big old dumbass like me can tell you are <i>not</> done with this guy.
  - Old PL: Nawet taka wielka stara idiotka jak ja widzi, że <i>nie</> skończyłeś z tym gościem.
  - New PL: Nawet taka skończona idiotka jak ja widzi, że <i>nie</> skończyłeś z tym gościem.
  - Reason: Big old intensifies the self-insult; it does not assign old age to sixteen-year-old Luca.

- **Applied:** `Articy_Default/ARTICY/DFr_POCKET_NIGHTMAREBATTLE_2_AFTER_0900_0x01000000000137DA.Text`
  - EN: Back when it was just little old Luca in here, shit was NORMAL!
  - Old PL: Kiedy siedziała tu tylko mała stara Luca, wszystko było, kurde, NORMALNE!
  - New PL: Kiedy siedziałam tu tylko ja, zwykła Luca, wszystko było, kurde, NORMALNE!
  - Reason: Little old is self-deprecation, not literal size and age.

Metadata: aligned the workspace group label with the adopted district name, „Martwa Galeria”.

### Pre-vertical decisions

- **Keep:** Luca feminine; Kaz, Dessa and Rhem masculine. Whole narrative supports the assignments.
  Flashback F: FR F0900 „ma pote”, F1700 „meuf”, DE F0900 „meine Freundin”, ES F0900 „amiga mía”
  independently identify Luca as Kaz’s female addressee. RU „единственный человек” does not prove a male addressee.
- **Keep:** the intimate former Rhem–Dessa relationship; lab confrontation and `DESSA_TRUTH`
  confirm it. The full game also supports coercion and emotional abuse, not merely disagreement.
- **Refine:** Rhem is usually formal and restrained, with emotional exceptions at EN strength.
  `Articy_Region_SunkenCity/ARTICY/DFr_RHEM_FLASHBACK_6_1000_0x010000000000E809.Text`
  contains „Damn it” → „Do cholery”;
  `Articy_Region_Dream/ARTICY/DFr_DREAM_07_KILLRHEM_02_1100_0x01000000000156F0.Text`
  contains „damn second” → „cholerną sekundę”. Preserve these; bible updated.
- **Keep provisionally:** Luca’s pan/pani with unfamiliar adults. Tens’s „Mów mi Tens” permits
  but does not require switching to ty; user preference remains open. Researcher agreement fixed separately.
- **Keep:** translated districts; unchanged brands; chroma and its feminine inflection; Wyrwa,
  kieszeń, opętanie, nosiciel, zdziczały, wszczep, pursuit → zadanie and equipment/UI terms.
  No systemic terminology issue found. Chroma’s Polish adjective collision and Luca’s declension
  remain user-facing direction options; the full text gives no new reason to replace them.
- **Keep:** translated horse names, Handlopies, Bucefał, Parsk/Whinney exchange, Wstrzymaj konie,
  Wcale Nie Żaby, Zdarta płyta, Na dno i na szczyt, Dracula’s kamienicznik joke and deliberate MLM jargon.
- **Keep provisionally:** Renzo’s „Kto ma głowę, ten ma premiowe”: rhyme and money motive survive;
  the coined phrasing is an editorial choice, not an evidenced meaning defect.
- **Keep:** usual Luca/Rhem contrast, other character voices, UI imperatives, sentence case,
  Polish quotation marks, lightly Polonized sounds and untouched developer labels.
  Profanity generally matches EN; the Tens example below remains open.
- **Keep:** ASCII-only `<DLang.Pose>` text; propose Dobroc as a precision option below.
- **No context:** assumed click-through dialogue and gibberish audio were not verified by this
  reviewer. Reading time, exact speaker presentation and fit still need in-game checks.

### To discuss

Four proposals **approved by the user and applied** (2026-10-02): autonomy, demon personhood,
acceptance instead of indifference, and To do bani. The remaining five are **proposed, not applied**.

- **Own person: autonomy:** `Articy_Region_Lab/ARTICY/DFr_ENDING_05_EARTH_OR_GO_CHOICE_0400_0x010000000000FDA7.Text`
  - EN: But… I won't stay with you. You deserve to be your own person. I deserve that, too.
  - Old PL: Ale… nie zostanę z tobą. Zasługujesz na to, żeby być sobą. Ja też na to zasługuję.
  - Applied PL: Ale… nie zostanę z tobą. Zasługujesz na to, żeby żyć własnym życiem. Ja też na to zasługuję.
  - Gain / cost: Emphasizes independence during separation; current być sobą foregrounds authenticity and remains defensible.
  - Status: approved by the user and applied (2026-10-02).

- **Acceptance versus indifference:** `Articy_Default/ARTICY/DFr_POCKET_KILLRHEM_0500_0x010000000001578D.Text`
  - EN: Now you’re <i>okay</> with me trying to kill you?!
  - Old PL: To teraz jest ci <i>obojętne,</> że próbowałam cię zabić?!
  - Applied PL: To teraz <i>nie masz nic przeciwko</> temu, że próbowałam cię zabić?!
  - Gain / cost: Closer to okay with; current obojętne may convey Luca’s emotional interpretation. Longer.
  - Status: approved by the user and applied (2026-10-02).

- **Demon personhood motif:** `Articy_Region_FluorescentPark/ARTICY/DFr_POCKET_REVENGEBAD_0500_0x010000000000B112.Text`
  - EN: Well, the "demon" possessing him was a person, too. But yes.
  - Old PL: Cóż, „demon”, który go opętał, też był kimś. Ale tak.
  - Applied PL: Cóż, „demon”, który go opętał, też był osobą. Ale tak.
  - Gain / cost: Makes personhood explicit, matching the corrected school conversation; current był kimś is humane but less precise.
  - Status: approved by the user and applied (2026-10-02).

- **Rhem’s syntactic calque:** `Articy_Intro/ARTICY/DFr_POCKET_SEALED_IN_0900_0x010000000000A87E.Text`
  - EN: I mean, good luck leaving the city at all. You're sealed in.
  - Current PL: Chodzi mi o to, że powodzenia z wydostaniem się z miasta w ogóle. Jesteś tu zamknięta.
  - Proposed PL: Mówię o samym wydostaniu się z miasta. Powodzenia. Jesteś tu zamknięta.
  - Gain / cost: More natural Polish and precise mockery; changes sentence rhythm.

- **Luca’s To ssie:** `Articy_Intro/ARTICY/DFr_STREETS_08_PHOTO_0900_0x01000000000179AD.Text`
  - EN: It sucks... I can’t even look at a picture of her now without getting <i>angry.</>
  - Old PL: To ssie… Nie mogę teraz nawet spojrzeć na jej zdjęcie, żeby się nie <i>wściec.</>
  - Applied PL: To do bani… Nie mogę teraz nawet spojrzeć na jej zdjęcie, żeby się nie <i>wściec.</>
  - Gain / cost: Removes a conspicuous English calque; loses a possible deliberate teen anglicism.
  - Status: approved by the user and applied (2026-10-02).

- **Tens’s profanity:** `Articy_Region_FluorescentPark/ARTICY/DFr_PARK_TENS_RIFT_0300_0x0100000000013524.Text`
  - EN: Typical Agradyne nonsense. It was a clown car company on its best days. Constant negligence and chaos.
  - Current PL: Typowy burdel w stylu Agradyne. Nawet w najlepsze dni ta firma przypominała cyrk. Ciągłe zaniedbania i chaos.
  - Proposed PL: Typowy absurd w stylu Agradyne. Nawet w najlepsze dni ta firma przypominała cyrk. Ciągłe zaniedbania i chaos.
  - Gain / cost: Nonsense is milder than burdel; current wording naturally evokes institutional disorder but is more vulgar.

- **Rhem’s usual formality:** `Articy_Region_CampusHill/ARTICY/DFr_CAMPUS_06_RIFT_WARNING_REACTION_1100_0x010000000000B7A1.Text`
  - EN: Would you have believed me? You're an angry child, Luca. The brat of a spoiled empire.
  - Current PL: Uwierzyłabyś mi? Jesteś wkurzonym dzieckiem, Luca. Bachorem rozpieszczonego imperium.
  - Proposed PL: Uwierzyłabyś mi? Jesteś rozgniewanym dzieckiem, Luca. Bachorem rozpieszczonego imperium.
  - Gain / cost: Rozgniewanym fits the usual formal voice; current wkurzonym can be an emotional exception.

- **Moja’s beneficial action:** `Articy_Region_SunkenCity/ARTICY/DFr_SUNKEN_05_BOSS_OUTRO_0800_0x010000000000DED7.Text`
  - EN: Moja made me better. Now I… can't breathe...
  - Current PL: Przy Moi czułam się lepiej. A teraz… nie mogę oddychać…
  - Proposed PL: Dzięki Moi było mi lepiej. A teraz… nie mogę oddychać…
  - Gain / cost: Restores causality rather than mere presence; current subjective symptom phrasing remains plausible.

- **Kindness on the vault map:** `Articy_Intro/ARTICY/DFr_THE_VAULT_MAP_0300_0x010000000000A692.Text`
  - EN: <DLang.Pose>Promises - Fear - Blame - Kindness</>
  - Current PL: <DLang.Pose>Obietnice - Strach - Wina - Dobro</>
  - Proposed PL: <DLang.Pose>Obietnice - Strach - Wina - Dobroc</>
  - Gain / cost: Dobroć is more precise than Dobro; ASCII Dobroc follows the cmap finding (PSE-Regular has only ASCII). No user report of missing
    glyphs in this line is recorded; font fallback/rendering has not been tested in game. Keep the current Dobro pending a wording decision.

### Unresolved readings retained

- `Articy_Intro/ARTICY/DFr_STREETS_08_PHOTO_0800_0x01000000000179A8.Text`:
  EN „We never should have come here” → „Nigdy nie powinniśmy byli tu przyjeżdżać”.
  The relocation group may include more family than mother/Luca; feminine plural is not proven.
- `Articy_Region_Lab/ARTICY/DFr_ENDING_02_KILL_0100_0x010000000000FBFB.Text`:
  EN „I’m sorry they did this to us” → „Przepraszam, że nam to zrobili”.
  `Articy_Region_Lab/ARTICY/DFr_ENDING_02_KILL_0200_0x010000000000FC00.Text`:
  EN „I’m sorry you hurt so much...” → „Przepraszam, że tak bardzo cierpisz…”.
  Przykro mi is a sympathy reading; Rhem’s guilt supports apology. Keep pending context/preference.
- `Articy_Region_Lab/ARTICY/DFr_LAB_01_RHEMWANTSTOGOALONE_SAVED_1600_0x01000000000157F2.Text`:
  EN „like static” → „jak elektryczność statyczna”. Noise/interference is also possible;
  the supernatural metaphor does not settle it. Keep current wording.

### Integration check

Lead re-read all changed entries with their linked scenes; verified referents, personhood motif,
idioms, gender/address, title spelling and threshold condition. Original English and key order unchanged.
All occurrences of the adopted TV title checked for capitalization; Rhem voice exceptions checked
against EN; flashback F corroborated using three other game languages.
Final input SHA-256: `990f473b331d4c10bd6491ba9aca4f397e5363d7fa78190871d2c0dfa83573fa`.
Build and l10n report re-run after integration: 3890/3890 entries, 16 tables; source, tokens/newlines,
locres, pak, empty IoStore and ZIP read-back pass. Missing/tokens/gender/address/terms/consistency/
English/plurals/capitals/typography: 0; length hints: 14, unchanged.
Follow-up (2026-10-02): four user-approved wording changes applied; linked scenes and token
checks rechecked, local build and l10n report pass. Length hints now 15: the accepted
`POCKET_KILLRHEM_0500` wording adds one layout hint (69 characters vs 50 in EN), not a proven
overflow. No change to the vault map wording.
Local verification ZIP remains 0.1; published `site/public/pobierz/Possessors-PL-0.1.zip` is unchanged.
No release, install, launch or full-playthrough confirmation performed.

## Check in game

- Lines in demon style `<DLang>` / `<DLang.italic>` / `<DLang.Bold>` (Cheekers' „chromę”, Dessa's
  shouting, Beverly's demon): Polish letters must render; the style may use a different font.
- The vault map (THE_VAULT_MAP_0300): PSE font line.
- Settings: „Efekty dźwiękowe” (was SFX), „Limit klatek na sekundę”, window mode descriptions.
- Map pickups and abilities: „Przebijające nurkowanie”, „Nieodwiedzone pomieszczenie”, „Klucz do wentylatorni”.
- Long dialogue lines (Tens' quest briefing, Dessa's final speeches) for box overflow.
- Input icons inside tutorial sentences („Naciśnij [X], aby…”).

- School personhood exchange (`CAMPUS_01_SETTING_0800`) and subsequent revenge conversation:
  confirm speaker attribution and delivery of the personhood motif.
- Archive quest without episodes (`SURVIVOR_ARCHIVES_NONE_0100`): confirm Luca speaks;
  plant researcher (`SURVIVOR_PLANTS_START_1600`): confirm addressee and formality.
- Torture flashback (`PLAZA_TORTURECHROMA_0900`): verify machine context and wrapping after correction.
- Earth/go choice (`ENDING_05_EARTH_OR_GO_CHOICE_0400`), apology ending and Rhem/Dessa scenes:
  assess emotional rhythm and the open autonomy/acceptance wording options.
- `POCKET_KILLRHEM_0500`: check wrapping of the accepted „nie masz nic przeciwko” wording.
