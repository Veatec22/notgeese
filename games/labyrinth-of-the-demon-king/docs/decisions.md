# Labyrinth of the Demon King: translation decisions

Locres has no speakers. Bible and `structure.yaml` (2026-10-02) take speakers from the dialogue
DataTable that defines each key (`tools/key_sources.py`); hero lines inside NPC tables are read from
the text. Independent full review completed on 2026-10-02; details below.

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

### Scope

- 2026-10-02: fresh-context, read-only reviewer; all 1120/1120 entries read by asset context, followed by reconstructed dialogue scenes. No omitted entries.
- Source comparison: all 1120 unique keys and complete EN strings match `work/en.locres`; no gaps or drift. Dialogue branching is reconstructed, not a verified playthrough.
- Review input SHA-256 (`translations/en-pl-review.json`): `055bf24f42f26551c04da287fe757d501ca42c8c7b0d94b815d695b9f6993e50`.
- Bible input SHA-256: `d4ad6bc07a3cac43698a1e082efb68f81b311eb4045883e2fd9c6f68d5dc2c43`; structure input: `f1d0d288bbc3950e9f130e00a5f6820296586428f14661257ba5459007573de3`.

- Coverage: stable context-sort indices 0–149, 150–349, 350–474, 475–569, 570–729, 730–834, 835–944, 945–1044, 1045–1119 (zero-based). Truncated output for 426–437 reread in full.
- Scene pass: all 294 unique entries in all 12 reconstructed sequences reread: servant 43+24, merchant 36+6+65, kappa 23+8+33+6, priest 26+11, Demon King 13.
- Functional coverage: menu 37, settings 74, tutorial 25, HUD 84, servant 67, merchant 107, kappa 70, priest 37, Demon King 13, notes 72, items/maps/levels 260, achievements 54, world 220.
- English extraction SHA-256: `a21b8c409d78fd066ef0a5cd9f4e41efc11dccf6bea74a321ec7d35387cad846`. Pre-review decisions SHA-256: `e372dfb7551e88e21706c34edd99955f66415f0c15ad7e3a6ccc0e6b0c9efdf6`; technical: `b1939ba82b8e1cff77d8ca4d4838683c1effc6ff8742d100e104f3e66b097ef1`.

### Fixes

All 18 fixes applied in 0.3. Excerpts below identify each change; other text unchanged.

- `50AE40F24B5714F2BE6B97A1892FD53B` — EN: it wouldn't be very fun if I told you the answer Old PL: gdybym podał ci odpowiedź New PL: gdybym podała ci odpowiedź Gender: merchant is feminine. **Applied.**
- `BFB38F5B423C59F9391872A0931F6F43` — EN: With what has been stolen, he can’t attest to the claims. Old PL: Pozbawiony tak wiele, nie może potwierdzić oskarżeń. New PL: Tak wiele mu odebrano, że nie może potwierdzić oskarżeń. Language: invalid case government; preserve non-specific loss. **Applied.**
- `D2F4575047D57112A3AEEB82BB585256` — EN: Have you seen the key for the kitchen pantry? Old PL: Widziałeś klucz do kuchennej spiżarni? New PL: Widziałaś klucz do kuchennej spiżarni? Gender: hero addresses the merchant. **Applied.**
- `B851203F4EE41911DCB7E0A64F71CAFE` — EN: The sinners mouths and tongues are nailed together with hot iron nails. Old PL: Usta i języki grzeszników przebija się rozpalonymi żelaznymi gwoździami. New PL: Usta i języki grzeszników spaja się rozpalonymi żelaznymi gwoździami. Meaning: restore nailed together, not merely pierced. **Applied.**
- `FB7C55454BCB5075761AA5B310FFD8EF` — EN: I'll leave them locked in there. Old PL: Zostawię ich w zamknięciu. New PL: Zostawię go w zamknięciu. Meaning: one male kappa, singular they. **Applied.**
- `68D7D75B45E18C7653DB9295F59F946B` — EN: No. I'm going to free them. Old PL: Nie. Uwolnię ich. New PL: Nie. Uwolnię go. Meaning: one male kappa, singular they. **Applied.**
- `4977DB944DFE21FEF33C0AB91BAAA086` — EN: Open Inventory to equip and use items Old PL: Otwórz ekwipunek, aby wyposażyć i używać przedmiotów New PL: Otwórz ekwipunek, aby się wyposażyć i używać przedmiotów Language: equip calque and mismatched case government. **Applied.**
- `6F6041FA4E267AFC1E3C5EBDDD77C481` — EN: Open Inventory to equip and use items Old PL: Otwórz ekwipunek, aby wyposażyć i używać przedmiotów New PL: Otwórz ekwipunek, aby się wyposażyć i używać przedmiotów Language: equip calque and mismatched case government. **Applied.**
- `971FD3714BDEF99B5E9D37B8F160EBE7` — EN: Open Inventory to equip and use items Old PL: Otwórz ekwipunek, aby wyposażyć i używać przedmiotów New PL: Otwórz ekwipunek, aby się wyposażyć i używać przedmiotów Language: equip calque and mismatched case government. **Applied.**
- `B7D711F843FB4991B65486BB9ED9FD61` — EN: Open inventory to equip talismans Old PL: Otwórz ekwipunek, aby wyposażyć talizmany New PL: Otwórz ekwipunek, aby założyć talizmany Language: equip calque. **Applied.**

- Boundary quotes in eight notes: EN and old PL `"…"`; new PL `„…”`. Polish typography convention; internal text, CRLF and trailing spaces unchanged. **Applied.**
  Keys: `33E446D944A4BEE81F0289B12145F58E`, `76E9A1334D6D529F6D00EE8B23AF13D4`, `8037FCAF4604889047AF98AB8DDA8ED8`, `B416DE354489C74CE8A2F892F9AEC92E`, `D9634BA340F615C7838E18BB40722943`, `308B1AC74C1D0E2319D4B1B538BBCDC7`, `4D16AA104D8E067CECA0E384538E25A1`, `EBC92F4D4D117B4009008ABB95EABDE1`.

### Pre-vertical decisions

No direction session took place; documented choices are not evidence of user approval.

| Choice | Verdict and whole-text evidence |
| --- | --- |
| Quiet Japanese folk horror; text-only adaptation | Keep. Captivity, hell notes and culinary threats support restraint; actual presentation remains unverified. |
| Puzzles before rhyme | Keep. Court testimonies preserve order, accusations, injuries and participants (`BFB38F5B423C59F9391872A0931F6F43` and linked notes). |
| Male hero; feminine servant and merchant | Keep. Full scenes and sourced RU evidence agree; two remaining merchant-related gender errors corrected. |
| Casual kappa | Keep; bible refined for occasional explicit vulgar/anatomical humour. Source includes “crap” and “prick”, not only mild swearing. |
| Calm priest; theatrical Demon King | Keep. Priest's vanity, forgetfulness and spending concerns remain; all 13 King lines support laughter, mockery and show imagery. |
| Modern letters' stronger language | Keep. Soapland/Yakuza notes remain distinct from historical NPC exchanges. |
| Recognizable Japanese weapons, creatures and objects | Keep. Descriptions explain function; intentional names documented in bible. No blanket macron normalization. |
| Król Demonów; Labirynt | Keep. Titles and inflections are consistent; “Labiryncie” report hits are false positives. |
| Strażnik / Dozorca | Keep with generic prison-role exception. `25950E264B7DCE102525D08B229F2EC9` establishes Warden as a role and Jailer as a particular boss. Key drop still needs in-game confirmation. |
| Tower/Hell names | Keep. Matching location prompts, notes and achievements support Powtórzeń, Miażdżenia, Lamentu, Nieustającej Męki; uninterrupted torment supports expanded No Interval. |
| Królewski Sąd | Keep. King adjudicates accusations; judicial court, not royal household. |
| garda / parowanie; obuchowe / cięte / kłute | Keep. Tutorial, weapon categories and vulnerabilities agree; “sparuj” report hits are false positives. |
| zgnilizna / trucizna / krwawienie | Keep. 100% rot death, poison damage, stacked bleeding and their treatments remain distinct. |
| Krwawnik; Ostrze Chryzantemy | Keep. Blood hunger/infusion and related weapon/coin references support the names. |
| Ritual / Purifying Incense | Keep. NG+ ritual cost and rot treatment are distinct. |
| koło z klejnotem | Keep. Six colours, inscriptions and inner/outer parts remain distinct. |
| butsudan / shirikodama / mon | Keep. Later context explains function and preserves cultural identity/anatomical setup. |
| Joined “Znajdujesz: ” | Keep. Nominative item names avoid unknown gender/case; trailing space preserved. Test assembled output. |
| Eight repeated locked-door sentences collapsed | Keep. Exact duplicate carries no additional fact or clue. |
| Cons. → Zużyw. | No context. Inventory screenshot needed. |
| Achievement adaptations | Keep provisionally. Images/unlock context unverified. |
| Imperative UI, sentence case, Polish quotes | Keep. Proper names and source all-caps justified; eight quotation pairs fixed. |
| Click-through dialogue / menu reading conditions | No independent presentation context. Review cannot certify timing, wrapping or reading comfort. |

### To discuss

All proposals remain open; current text kept. Evidence is the source entry and linked scene, not a new user ruling.

| Key / scene | EN and current PL | Recommendation, gain and cost |
| --- | --- | --- |
| `6E3467A7455C10613B42D7B0DC804A27`, inventory | Cons. → Zużyw. | Screenshot of tab and contents. If consumables: Zużywalne (or Użytkowe if needed for width); if consumption, assess the actual value. No semantic change without context. |
| `344BBD654BDB16FB2CEA84B4404A2198`, merchant knife | Merchant's Backup → Odwód handlarki | Zapas handlarki; clearer Zapasowy nóż handlarki. Description `3266B9FF4A8533B8C06C50BA8578EE7B` identifies a backup knife. Gain: natural spare-weapon sense; cost: first loses military flavour, second adds explicit weapon type to name. |
| `616DD9BE4DC83AEEAE0A088CF31F3EB2`, hanged man | They're dead. → Nie żyją. | Likely Nie żyje. Singular actor name and “the body” support one target; verify whether visual interaction groups bodies. |
| `0211FE0A431525D4F02921862BC66345`, maps | Exit → Wyjdź | Wyjście if a map location; keep Wyjdź if closing action. Defining map widgets alone do not settle function. |
| `FC8C741A403377E5B2C0F3A3338C17FE`, combat help | Need to be charged → wymagają przygotowania | Consider wymagają przytrzymania przycisku ataku. Gain: concrete input; cost: narrower than general charging mechanic. HOLD controls already convey it. |
| `007D19BC4A49B90FBD2F3BBD11560A45`, `EA0EF56342776ABE337FAC89DDC88ED5`, prison | prison warden / Warden's Key → dozorca więzienia / Klucz dozorcy | Keep contextual role exception; document in bible. Confirm drop and boss before normalizing to Strażnik. |
| Achievement titles: `8ED1CF6847FCC3F4CF26C3A52586D35A`, `28E5CA8A4A4F0FF3949E738FB904B526`, `6D1361244D181D5F889FEFA7EC3796D0` | Hanging With The Boys / Fortifying Fortitude / Pop Goes The Nuppeppo → Wiszenie z kumplami / Hartowanie hartu / Nuppeppo robi puf | Keep provisionally. Text preserves wordplay or sound; judge with image/unlock event. No purely taste-based rewrite proposed. |
| `F564214448EB57CE779556A14CE7ABF3`, merchant hint | could tell you more → mogą wiedzieć więcej | Consider mogą powiedzieć ci więcej. Gain: obtain information rather than just assume knowledge; cost: guardians may communicate through inscriptions, context unverified. |
| `D3EF2ECC45A1524AC814208A23AD1A1B`, research | grown far larger than → urosły znacznie większe od krewniaków | są znacznie większe od krewniaków (smoother, less explicit growth) or urosły znacznie bardziej niż ich krewniacy (retains process). Optional edit. |

### Verification

- Rechecked all 18 changed entries against EN, linked merchant dialogue and court context. Keys, English source, other metadata and remaining 1102 Polish entries unchanged.
- Post-fix translation SHA-256: `9cc9292024361cd039716053d793f38d4ab200d104319528a1b743f434f0cb89`.
- Post-fix report: missing 0, tokens 0, gender 0, address 0, plurals 0, typography 0; terms 8, consistency 6, English 4, length 8, capitals 19 remain review hints. English hits fell from 16 to 4 after documenting intentional names; those four are laughter.
- 0.3 build passed live-source identity, locres round-trip, token/CRLF checks and archive payload validation. Overlay tests passed: reject unrelated assets and corrupt chunks; retain all 12 original language labels.
- Workspace validation and site build passed.
- ZIP prepared in `dist/` and copied byte-identically to `site/public/pobierz/`; game not launched or installed during this review. No new in-game evidence.

## Check in game

No new screenshots or playthrough evidence. Test with 0.3:

1. Merchant pantry exchange: “Widziałaś”, feminine response, both choices about one prisoner.
2. Combat tutorial: heavy attack hold, kick, three parries and three dodges; first free dodge and cooldown.
3. Inventory: screenshot Cons. tab, its contents, equip action, talismans and weapon categories.
4. Maps: screenshot Wyjdź in place; determine button or location; long labels and all tower names.
5. King's Court: all statues and full testimony sequence; solve using Polish alone, check order and accusations.
6. Four Heavenly Kings: directions, black/white/red/blue, offerings, sockets and upper/lower gems.
7. Pool wheels: six colours, inner/outer parts; servant's “albo to koło, albo czarne” must stay uncertain.
8. Hanged man: screenshot target and Nie żyją to settle singular/plural.
9. Prison: Klucz dozorcy drop source and priest's role/title explanation.
10. Joined pickups: one/multiple arrows, mon, shirikodama bag, clothing; assembled text, spacing and prompt.
11. Long notes: eight quoted notes, hell descriptions, research; wrapping, scrolling, quotes and macrons.
12. NG+: ritual incense confirmation, before/after counter; reduction applies to player and NPC bonuses.
13. Late servant scenes: captivity, cannibalism and failed escape; correct order, no early explanation.
14. Demon King rematch/mask: broken blade and “ładna twarz” fit visible equipment.
15. Achievement images/unlocks: three wordplay titles and long descriptions.
