# GRIME: decisions

## Direction

Status: user accepted all recommended proposals on 2026-10-04 ("wszystko według propozycji").
Ordinary UI decisions remain agent decisions. Source: GOG 1.3.5, extracted I2 table, `work/source.json`.
Apply `.claude/skills/localization/RULES.md`. Audio and reading conditions remain unverified;
adapt cautiously until the opening test. Do not assume absence of English dialogue.

### Tone (agreed with user)

Precise UI, restrained ritual/body imagery in lore; preserve the contrast with childish NPCs.
No added archaism, jokes or explanation of ambiguous lore. Translate meaningful creature/area
names; keep personal names provisionally, verify identity before assigning gender.

The following is one contiguous keyed exchange, not a reconstructed scene. Speaker is identified
by the `Rockhead Art Trader` key; addressee appears to be the player from the body references.
Keys share `WorldText/NPC/Rockhead Art Trader/Dialog Term: NPC Art_ Trader : Listen:`.

| Suffix | Full EN | Recommended PL |
| --- | --- | --- |
| 0 | `<j>Ohohoh!<j> Such <i>long</i> and <i>shapely</i> limbs you have!` | `<j>Ohoho!<j> Ale masz <i>długie</i> i <i>kształtne</i> kończyny!` |
| 1 | `The curves very much remind of the stranger's art, did they work your body?` | `Te krągłości tak przypominają dzieła nieznajomej istoty. Czy to ona ukształtowała twoje ciało?` |
| 2 | `Does the... the <i>old pain</i>... bother you? I mean... with that body...` | `Czy ten... ten <i>dawny ból</i>... ci dokucza? To znaczy... z takim ciałem...` |
| 3 | `Oh no no, I asked it! Forget I asked it!` | `O nie, nie, padło to pytanie! Zapomnij o nim!` |
| 4 | `We shouldn't say it! Say it or think it! ` | `Nie wolno nam o tym mówić! Ani mówić, ani myśleć! ` |

Lines 1 and 3 avoid unverified character gender. Check other-language evidence before full
translation; do not preserve clumsy gender avoidance if context allows a natural gendered form.
Alternative for 0: `Och! Jakże długie i kształtne masz kończyny!` raises the register and weakens
the spontaneous voice; not recommended. Keep the original hesitation and taboo in 2–4.

### UI (agent decisions)

| Key | Full EN | PL |
| --- | --- | --- |
| `General/Accept` | `Accept` | `Zaakceptuj` |
| `General/Continue` | `Continue` | `Kontynuuj` |
| `UI/MainMenu/CreateNew` | `Create a New Save` | `Utwórz nowy zapis` |
| `UI/Settings/Options/LargerText` | `Larger Speech Text` | `Większy tekst dialogów` |
| `UI/Settings/Options/EnableTextShake` | `Enable Text Animation` | `Animacja tekstu` |

Use imperatives for actions; sentence case unless the source is all caps. Preserve tags, style
names and action identifiers. Text length is a test concern, not an invented character limit.

### Linked world terms (agreed with user)

| Key | Full EN | Recommended PL | Significant alternative |
| --- | --- | --- | --- |
| `UI/TutorialMessages/Vessel Header` | `LOST VESSEL` | `UTRACONE NACZYNIE` | `UTRACONA POWŁOKA` |
| `UI/TutorialMessages/SurrogateHeader` | `Surrogate` | `Surogat` | `Zastępca` |
| `UI/TutorialMessages/BreathHeader` | `Breath` | `Tchnienie` | `Oddech` |
| `UI/TutorialMessages/StaminaHeader` | `Force` | `Wigor` | `Moc` |
| `General/Mass` | `Mass` | `Masa` | — |

Vessel: Naczynie preserves the image of a body being filled/worn by another will; Powłoka reads
more naturally as a body but loses the container image. Surrogate: Surogat preserves the strange
world vocabulary; Zastępca is clearer but sounds like a role/person. Breath: Tchnienie covers both
life principle and healing resource; Oddech is more physiological. Force is spent on attacks and
dashes; use Wigor to distinguish it from Strength (`Siła`). Mass is literal currency/body matter.
Ardor provisionally `Żar`: appetite-linked reward multiplier, not attack damage; verify related
lines before settling. Hunt Points provisionally `Punkty łowów`; Traits `Cechy`; Absorb `Pochłoń`.

### Instruction and lore sample (agreed with user)

Key: `Item/Data_Item_Consumable_Simple/Item_Consumable_Breath Wisp Desc`.

EN: `Breath is existence. Awareness. A seed of life.\nIt is the sole difference between us and the very ground we walk on.`

PL: `Tchnienie to istnienie. Świadomość. Ziarno życia.\nTylko ono odróżnia nas od ziemi, po której stąpamy.`

Key: `UI/TutorialMessages/GrowText`.

EN: `Enter a <style="Surrogate">Surrogate</style> to GROW your vessel.\n\nUpgrade attributes using <style="Mass">MASS</style>.\nAcquire and upgrade talents using <style="Hunt Point">HUNT POINTS</style>.`

PL: `Wejdź do <style="Surrogate">Surogatu</style>, by ROZWIJAĆ swoje naczynie.\n\nZwiększaj atrybuty za pomocą <style="Mass">MASY</style>.\nZdobywaj i rozwijaj talenty za pomocą <style="Hunt Point">PUNKTÓW ŁOWÓW</style>.`

Variants never go in `en-pl-review.json`. The accepted direction is recorded in the bible.
The user confirmed that the opening vertical works on 2026-10-04 and authorized the full text.

## Vertical implementation

- Append language `Polski` / `pl` to I2; retain every original column. Untranslated keys use
  English in the new column. Font references use the existing English/Latin font roles.
- GameOptions builds its selector from I2's list and stores the language name in the settings
  INI. The existing Hebrew-removal index correction also applies to the appended language.
  Selection and persistence still need an in-game test.
- Yon is the opening NPC (external identity lead: https://grime1.wiki.gg/wiki/Yon);
  dialogue comes from original `WorldText/NPC/Ted/...NpcMechanism` entries, not the wiki.
  Biological gender remains unverified. The full text uses provisional grammatical agreement;
  preserve excitement and avoid cumbersome gendered past tense for the silent player.
- Carven → Rzeźbieni (agent decision): sculpted-body association. Dash → Zryw; backstep →
  Odskok w tył. Literal force in the stamina quotation remains siła; the resource is Wigor.

## Check in game

- Language selector: Polski appears, English remains English, choice survives a restart.
- Menu and all settings: Polish glyphs, wrapping, dropdown labels and highlighted buttons.
- Fresh save: movement/jump/absorb/attack/dash prompts; preserve action icons and animations.
- First Surogat: attribute panel, Wigor vs Siła, tutorial text and line breaks.
- Yon: first exchange and weapon gift; no cut-off lines or broken `<j>` animation.
- Inventory and the first boss: initial weapon description, bestiary, Żar tutorial.
- Confirm whether dialogue has intelligible English audio and whether lines wait for input.

## Review

Independent read-only fresh-context review, 2026-10-04, using localization-review.
Scope: 2,648/2,648 entries, 2,643 non-whitespace; all type-0 keys and original English match extraction.
No gaps or drift. No game launch, audio/performance or clipping judgment.
Batches: 0–248 (92–156 reread after truncation), 249–389, 390–534, 535–704, 705–879,
880–1052, 1053–1259, 1260–1437, 1438–1554, 1555–1689, 1690–1834, 1835–1969,
1970–2104, 2105–2239, 2240–2374, 2375–2514, 2515–2647. Numeric scene suffixes checked.

Input identities (SHA-256):
- Text: 0298b74b74aa8d07964aed642beaa66ecdc59319c4ea7acec7e7a22fd78a43a5
- Extraction: 7a33ef26685e41c11bb5813d5b4bac42f93dbb8c01cb95db6f20e85cf05855bd
- Bible: b7e115a566d22c6de0fd07c955cef029e282ef3db2a76f0462431c7c8dce4bc7
- Structure read by reviewer: caf61e8cdb36932dc26e6b5ef2078d148fa3dcb5ccfc69d6e79f994b874c93c6

### Pre-vertical decisions

Keep Tchnienie, Naczynie, Surogat, Wigor/Siła, Żar, Punkty łowów, Cechy and Rzeźbieni.
Late descriptions and Listener's meditation confirm life, container and sculpting images.
Żar's base effect is a Mass reward multiplier; certain Traits additionally grant damage at Żar thresholds.
Keep restrained lore, spontaneous NPC contrast and Hebrew fragments without added explanations.
Yon retains cruelty before disillusionment; Shidra retains manipulation and defensive conviction.
Correct Shapely to singular Kształtny, Fidus's title: English prayers explicitly say Sole Shapely;
original FR/IT/RU armor and Yon final corroborate. This corrects an agent decision, not a user ruling.

### Fixes and ordinary editing

All changes below applied by the lead. Fidelity fixes: singular Shapely, abducted sibling vs effigy,
Followers taken below, Pincer damage scaling, humble vs poor, Rockbed wrongness vs moral evil,
Surrogate quote addressing the player rather than its vessel, past completion in Vase dialogue.
UI fixes: one Cenotaph City name and one Prey Gauntlet name; variable counts avoid Polish declension errors.
Owl editing restores bittersweet trade and removes invented cutting/visibility while preserving couplets.
Ordinary delegated editing: Yon uses colloquial nie tak instead of diagnostic nieprawidłowość;
Creep becomes Pełzak to distinguish Crawler/Pełzacz; mining rhyme no longer invents an eye;
legacy talents uses Cechy; Koda grammatical paradigm made consistent without biological inference.
No accepted user term was replaced.

#### `AreaTitle/Checkpoint/Carven Palace - The Shapely`

EN:
```text
Carven Palace
The Shapely
```

Old PL:
```text
Pałac Rzeźbionych
Kształtni
```

Applied PL:
```text
Pałac Rzeźbionych
Kształtny
```

#### `Bestiary/Follower/Desc`

EN:
```text
After earning enough of the flesh, Palace servants are taken below until they adjust to the added presence.


Very slow, but unpredictable and dangerous in large numbers.
```

Old PL:
```text
Po zasłużeniu na dostateczną ilość ciała sługi Pałacu schodzą w dół, dopóki nie przywykną do dodatkowej obecności.


Bardzo powolne, ale nieprzewidywalne i groźne w dużej liczbie.
```

Applied PL:
```text
Po zasłużeniu na dostateczną ilość ciała sługi Pałacu zabiera się na dół, gdzie pozostają, aż przywykną do dodatkowej obecności.


Bardzo powolne, ale nieprzewidywalne i groźne w dużej liczbie.
```

#### `Bestiary/MiniCraver/Name`

EN:
```text
Creep
```

Old PL:
```text
Pełzacz
```

Applied PL:
```text
Pełzak
```

#### `Item/Armor Sets/Formal/Set Name`

EN:
```text
Formal Coda
```

Old PL:
```text
Odświętna Koda
```

Applied PL:
```text
Odświętny Koda
```

#### `Item/Data_Item_Consumable_Simple/Item_OLD_Quest_Lithic_Art_Statue Desc`

EN:
```text
Made by a denizen of Lithic.
Someone there is sure to appreciate this.

A rough effigy of a Stoneborn, possibly a close sibling of the artist. Likely of one taken by Carven servants. 
```

Old PL:
```text
Dzieło mieszkańca Lithic.
Ktoś tam z pewnością je doceni.

Nieporadna podobizna Zrodzonego z kamienia, być może kogoś z bliskiego rodzeństwa artysty. Zapewne zabranej przez sługi Rzeźbionych. 
```

Applied PL:
```text
Dzieło mieszkańca Lithic.
Ktoś tam z pewnością je doceni.

Nieporadna podobizna Zrodzonego z kamienia, być może kogoś z bliskiego rodzeństwa artysty. Zapewne przedstawia kogoś zabranego przez sługi Rzeźbionych. 
```

#### `Item/Data_Item_Equipable_Armor_Chest/Armor_6b_Chest Desc`

EN:
```text
The garment of an Embroider known for having captured the Shapely's previous form, before the world rumbled and their flesh awakened.
```

Old PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnych, zanim świat zadrżał, a ich ciała się przebudziły.
```

Applied PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnego, zanim świat zadrżał, a jego ciało się przebudziło.
```

#### `Item/Data_Item_Equipable_Armor_Chest/Armor_Coda1_Chest Name`

EN:
```text
Formal Coda Chest
```

Old PL:
```text
Odświętna Koda — napierśnik
```

Applied PL:
```text
Odświętny Koda — napierśnik
```

#### `Item/Data_Item_Equipable_Armor_Hands/Armor_6b_Hands Desc`

EN:
```text
The garment of an Embroider known for having captured the Shapely's previous form, before the world rumbled and their flesh awakened.
```

Old PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnych, zanim świat zadrżał, a ich ciała się przebudziły.
```

Applied PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnego, zanim świat zadrżał, a jego ciało się przebudziło.
```

#### `Item/Data_Item_Equipable_Armor_Hands/Armor_Coda1_Hands Name`

EN:
```text
Formal Coda Hands
```

Old PL:
```text
Odświętna Koda — rękawice
```

Applied PL:
```text
Odświętny Koda — rękawice
```

#### `Item/Data_Item_Equipable_Armor_Legs/Armor_6b_Legs Desc`

EN:
```text
The garment of an Embroider known for having captured the Shapely's previous form, before the world rumbled and their flesh awakened.
```

Old PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnych, zanim świat zadrżał, a ich ciała się przebudziły.
```

Applied PL:
```text
Szata Hafciarza znanego z uwiecznienia dawnej formy Kształtnego, zanim świat zadrżał, a jego ciało się przebudziło.
```

#### `Item/Data_Item_Equipable_Armor_Legs/Armor_Coda1_Legs Name`

EN:
```text
Formal Coda Legs
```

Old PL:
```text
Odświętna Koda — nogawice
```

Applied PL:
```text
Odświętny Koda — nogawice
```

#### `Item/Data_Item_Equipable_Weapon_Melee/Item_Weapon_Ascended Greatsword Name`

EN:
```text
Shapely Greatsword
```

Old PL:
```text
Wielki miecz Kształtnych
```

Applied PL:
```text
Wielki miecz Kształtnego
```

#### `Item/Data_Item_Equipable_Weapon_Melee/Item_Weapon_Pincer Glaive Short Desc`

EN:
```text
Attack speed increases with each successful hit.

Every hit generates a Tarbile stack that can be transferred to Prey using the Special Attack.

<b>Special Attack</b> - Spins the weapon, transferring all accumulated Tarbile stacks and dealing increased damage based on the amount transfered.

Every several seconds Prey are dealt damage equal to the amount of stacks currently applied, consuming a stack in the process. 
```

Old PL:
```text
Szybkość ataku rośnie z każdym udanym trafieniem.

Każde trafienie tworzy ładunek smołożółci, który można przenieść na zdobycz atakiem specjalnym.

<b>Atak specjalny</b> — obraca broń, przenosząc wszystkie zgromadzone ładunki smołożółci i zadając obrażenia zwiększone o ich liczbę.

Co kilka sekund zdobycz otrzymuje obrażenia równe liczbie nałożonych ładunków. Zużywa to jeden ładunek. 
```

Applied PL:
```text
Szybkość ataku rośnie z każdym udanym trafieniem.

Każde trafienie tworzy ładunek smołożółci, który można przenieść na zdobycz atakiem specjalnym.

<b>Atak specjalny</b> — obraca broń, przenosząc wszystkie zgromadzone ładunki smołożółci i zadając zwiększone obrażenia zależne od liczby przeniesionych ładunków.

Co kilka sekund zdobycz otrzymuje obrażenia równe liczbie nałożonych ładunków. Zużywa to jeden ładunek. 
```

#### `Item/Data_Item_Equipable_Weapon_Melee/_Weapon_Melee_Coda_ScytheSword Desc`

EN:
```text
To ensure the excellence of the Performance, only the most skilled  of the Coda may become its centerpiece, and wield the Scythesword in combat. 

In the end, however, the Performance had to settle for the second. 

The perfection of a single artform did not satisfy the needs of the first.
```

Old PL:
```text
By zapewnić doskonałość Występu, tylko najbieglejszy z Kod może stać się jego centralną postacią i władać kosomieczem w walce. 

Ostatecznie jednak Występ musiał zadowolić się drugim. 

Doskonalenie jednej tylko sztuki nie zaspokajało potrzeb pierwszego.
```

Applied PL:
```text
By zapewnić doskonałość Występu, tylko najbieglejszy z Kodów może stać się jego centralną postacią i władać kosomieczem w walce. 

Ostatecznie jednak Występ musiał zadowolić się drugim. 

Doskonalenie jednej tylko sztuki nie zaspokajało potrzeb pierwszego.
```

#### `UI/Talents/Boss_Shidra (Gauntlet)/Bonus Text`

EN:
```text
Boss Gauntlet unlocked via the Surrogate.
```

Old PL:
```text
W Surogacie odblokowano Łowy na bossów.
```

Applied PL:
```text
W Surogacie odblokowano Próbę łowów.
```

#### `UI/Talents/Damaged Healing Shards/Bonus Text`

EN:
```text
Drop <n> healing shards on taking damage. The shards heal for 10% of the damage taken on pick up.
```

Old PL:
```text
Po otrzymaniu obrażeń upuszczasz <n> odłamków leczniczych. Podniesienie odłamka leczy 10% otrzymanych obrażeń.
```

Applied PL:
```text
Po otrzymaniu obrażeń upuszczasz odłamki lecznicze w liczbie <n>. Podniesienie odłamka leczy 10% otrzymanych obrażeń.
```

#### `UI/Talents/Max Breath Overload Wisps/Bonus Text`

EN:
```text
Gaining Breath beyond maximum capacity releases <n> Vessel Wisps at nearby enemies. Damage scales with Health.
```

Old PL:
```text
Zdobycie Tchnienia ponad maksymalną pojemność wypuszcza <n> Ogników Naczynia ku pobliskim wrogom. Obrażenia rosną wraz ze Zdrowiem.
```

Applied PL:
```text
Zdobycie Tchnienia ponad maksymalną pojemność wypuszcza ku pobliskim wrogom Ogniki Naczynia w liczbie <n>. Obrażenia rosną wraz ze Zdrowiem.
```

#### `UI/Talents/Resonance vulnerability on repel/Bonus Text`

EN:
```text
Repeling an attack puts <n> stacks of Attunement on the attacker.
```

Old PL:
```text
Odepchnięcie ataku nakłada na atakującego <n> poziomów Dostrojenia.
```

Applied PL:
```text
Odepchnięcie ataku nakłada na atakującego Dostrojenie. Liczba ładunków: <n>.
```

#### `UI/TutorialMessages/BossRefightNGHeader`

EN:
```text
Prey Gauntlet + Reality Shift
```

Old PL:
```text
Łowy na bossów + Zmiana rzeczywistości
```

Applied PL:
```text
Próba łowów + Zmiana rzeczywistości
```

#### `UI/TutorialMessages/BossRefightNGText`

EN:
```text
Access the <style="Pull">Prey Gauntlet</style> through any <style="Surrogate">SURROGATE</style> to glimpse into <style="Pull">OTHERWHERE</style> and face previously fought Great Prey.


Use <style="Pull">Reality Shift</style> to abandon this reality and discover a new distorted one, with changed Prey and endless progression.

<style="Quote">"An unnecessary indulgence."</style>
```

Old PL:
```text
Wejdź na <style="Pull">Łowy na bossów</style> w dowolnym <style="Surrogate">SUROGACIE</style>, aby zajrzeć w <style="Pull">INNOGDZIE</style> i zmierzyć się z pokonaną wcześniej Wielką zdobyczą.


Użyj <style="Pull">Zmiany rzeczywistości</style>, aby opuścić tę rzeczywistość i odkryć nową, zniekształconą, z odmienioną zdobyczą i nieskończonym rozwojem.

<style="Quote">„Zbyteczna zachcianka”.</style>
```

Applied PL:
```text
Podejmij <style="Pull">Próbę łowów</style> w dowolnym <style="Surrogate">SUROGACIE</style>, aby zajrzeć w <style="Pull">INNOGDZIE</style> i zmierzyć się z pokonaną wcześniej Wielką zdobyczą.


Użyj <style="Pull">Zmiany rzeczywistości</style>, aby opuścić tę rzeczywistość i odkryć nową, zniekształconą, z odmienioną zdobyczą i nieskończonym rozwojem.

<style="Quote">„Zbyteczna zachcianka”.</style>
```

#### `UI/TutorialMessages/BossRefightText`

EN:
```text
Access the <style="Pull">Prey Gauntlet</style> through any <style="Surrogate">SURROGATE</style> to glimpse into <style="Pull">OTHERWHERE</style> and face previously fought Great Prey.


<style="Quote">"An unnecessary indulgence."</style>
```

Old PL:
```text
Wejdź na <style="Pull">Łowy na bossów</style> w dowolnym <style="Surrogate">SUROGACIE</style>, aby zajrzeć w <style="Pull">INNOGDZIE</style> i zmierzyć się z pokonaną wcześniej Wielką zdobyczą.


<style="Quote">„Zbyteczna zachcianka”.</style>
```

Applied PL:
```text
Podejmij <style="Pull">Próbę łowów</style> w dowolnym <style="Surrogate">SUROGACIE</style>, aby zajrzeć w <style="Pull">INNOGDZIE</style> i zmierzyć się z pokonaną wcześniej Wielką zdobyczą.


<style="Quote">„Zbyteczna zachcianka”.</style>
```

#### `UI/TutorialMessages/GrowText`

EN:
```text
Enter a <style="Surrogate">Surrogate</style> to GROW your vessel.

Upgrade attributes using <style="Mass">MASS</style>.
Acquire and upgrade talents using <style="Hunt Point">HUNT POINTS</style>.
```

Old PL:
```text
Wejdź do <style="Surrogate">Surogatu</style>, by ROZWIJAĆ swoje naczynie.

Zwiększaj atrybuty za pomocą <style="Mass">MASY</style>.
Zdobywaj i rozwijaj talenty za pomocą <style="Hunt Point">PUNKTÓW ŁOWÓW</style>.
```

Applied PL:
```text
Wejdź do <style="Surrogate">Surogatu</style>, by ROZWIJAĆ swoje naczynie.

Zwiększaj atrybuty za pomocą <style="Mass">MASY</style>.
Zdobywaj i rozwijaj cechy za pomocą <style="Hunt Point">PUNKTÓW ŁOWÓW</style>.
```

#### `UI/TutorialMessages/SurrogateText`

EN:
```text
An imprinted Levolam becomes your <b>checkpoint</b>, and <style="Surrogate">Surrogate</style>.

Whenever you are shattered you will reform at the last created <style="Surrogate">Surrogate</style>.


As you reform, so will most Prey. Use their <style="Mass">MASS</style> to develop your Vessel.

<style="Quote">"A shard of the womb you once inhabited, it can be used as such again."</style>
```

Old PL:
```text
Levolam z twoim odciskiem staje się <b>punktem kontrolnym</b> i <style="Surrogate">Surogatem</style>.

Za każdym razem, gdy rozpadniesz się na kawałki, odtworzysz się w ostatnim utworzonym <style="Surrogate">Surogacie</style>.


Wraz z tobą odtworzy się też większość zdobyczy. Użyj ich <style="Mass">MASY</style>, by rozwijać swoje naczynie.

<style="Quote">„Odłamek łona, w którym niegdyś przebywało twoje naczynie. Może znów pełnić tę rolę”.</style>
```

Applied PL:
```text
Levolam z twoim odciskiem staje się <b>punktem kontrolnym</b> i <style="Surrogate">Surogatem</style>.

Za każdym razem, gdy rozpadniesz się na kawałki, odtworzysz się w ostatnim utworzonym <style="Surrogate">Surogacie</style>.


Wraz z tobą odtworzy się też większość zdobyczy. Użyj ich <style="Mass">MASY</style>, by rozwijać swoje naczynie.

<style="Quote">„Odłamek twego dawnego łona. Może znów pełnić tę rolę”.</style>
```

#### `WorldText/NPC/Coda Paintmaker/Dialog Term: NPC_Coda_Painter: Coda Painter:1`

EN:
```text
Forgive the poor attempts of a humble Coda at capturing your deep splendor.
```

Old PL:
```text
Wybacz ubogiemu Kodzie te marne próby uchwycenia twojego głębokiego splendoru.
```

Applied PL:
```text
Wybacz skromnemu Kodzie te marne próby uchwycenia twojego głębokiego splendoru.
```

#### `WorldText/NPC/Coda Performer/Dialog Term: NPC_Coda_Performer welcome: Welcome:1`

EN:
```text
Welcome to <b>Cenotaph City</b>! All of this is the Coda's gift to YOU!
```

Old PL:
```text
Witaj w <b>Mieście Cenotafu</b>! Wszystko to dar Kodów dla CIEBIE!
```

Applied PL:
```text
Witaj w <b>Mieście cenotafów</b>! Wszystko to dar Kodów dla CIEBIE!
```

#### `WorldText/NPC/Coda Shrinekeeper/Dialog Term: NPC_Coda_Checkpoint presenter: Checkpoint Dialogue:1`

EN:
```text
Every single object in Cenotaph City has been handcrafted and placed for your viewing pleasure. 
```

Old PL:
```text
Każdy przedmiot w Mieście Cenotafu wykonano ręcznie i ustawiono dla przyjemności twoich oczu.
```

Applied PL:
```text
Każdy przedmiot w Mieście cenotafów wykonano ręcznie i ustawiono dla przyjemności twoich oczu.
```

#### `WorldText/NPC/Messengers Plea/Dialog Term: NPC_Servant RockCollector: post vulture:0`

EN:
```text
By the Flesh, thank you! Praise the Shapely! 
```

Old PL:
```text
Na Ciało, dziękuję! Chwała Kształtnym!
```

Applied PL:
```text
Na Ciało, dziękuję! Chwała Kształtnemu!
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: GSF Is NGP: 1:0`

EN:
```text
Does this reality seem strange, and a little confused?
```

Old PL:
```text
Czy ta rzeczywistość dziwnie zmącona się zdaje?
```

Applied PL:
```text
Czy ta rzeczywistość dziwna, zmącona się zdaje?
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: GSF Is NGP: 1:1`

EN:
```text
It is the result of being sorely used.
```

Old PL:
```text
To skutek tego, że ktoś ją tak zużył i kraje.
```

Applied PL:
```text
To skutek nadużycia — po nim zamęt zostaje.
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: GSF Owl: 1:0`

EN:
```text
Our wants align, but I'm a guest.
Soon returning to my nest.

```

Old PL:
```text
Pragnienia mamy zgodne, lecz gościem jestem przecie.
Wkrótce wrócę do gniazda, w swoim własnym świecie.

```

Applied PL:
```text
Pragnienia mamy zgodne. Wkrótce do gniazda wrócę.
Jestem tu tylko gościem — więc pobyt swój skrócę.

```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: Listen:0`

EN:
```text
You have yours and I have mine.
Yet someday, may find combined.
```

Old PL:
```text
Ty masz swoje, a ja swoje.
Może kiedyś złączą się oboje.
```

Applied PL:
```text
Ty masz swoje, ja mam moje.
Może kiedyś się połączą — i te moje, i te twoje.
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: ListenNGP:1`

EN:
```text
The Heart now possess a tear.
```

Old PL:
```text
W Sercu tkwi rozdarcie, możesz ujrzeć je też.
```

Applied PL:
```text
W Sercu tkwi rozdarcie — ono ucierpiało też.
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: Repeat:0`

EN:
```text
It returns, again we meet.
Every trade is bittersweet.
```

Old PL:
```text
Wracasz, znów spotkanie nas czeka.
Każda wymiana to słodycz daleka.
```

Applied PL:
```text
Wracasz, znów się spotykamy.
W każdym handlu gorycz ze słodyczą mieszamy.
```

#### `WorldText/NPC/Owl/Dialog Term: NPC_Owl: Trade:0`

EN:
```text
A gift for you? Exchange a treat.
Let's make a deal, a trade complete.
```

Old PL:
```text
Dar dla ciebie? W zamian przysmak daj.
Dobijmy targu, na wymianę czas.
```

Applied PL:
```text
Dar dla ciebie? Za przysmak oddany.
Dobijmy targu — układ dokonany.
```

#### `WorldText/NPC/Rockbed Trader/Dialog Term: NPC_Rockbed Lithic trader: Listen:0`

EN:
```text
<j>MooOmmMssssSss... I FeEL... WrOng...<j>
```

Old PL:
```text
<j>MaaAAmYYyyy... CzUJę... COś ZłeGO...<j>
```

Applied PL:
```text
<j>MaaAAmYYyyy... CzUJę... Że COś jest Nie TaK...<j>
```

#### `WorldText/NPC/Rockbed Trader/Dialog Term: NPC_Rockbed Lithic trader: Listen:1`

EN:
```text
<j>I FEeeeeeEeeEL... Someone else's WrOng...<j>
```

Old PL:
```text
<j>CZuuuUUJĘ... CudZE Zło...<j>
```

Applied PL:
```text
<j>CZuuuUUJĘ... CudZE PoCzuCIE... że coś jest Nie TaK...<j>
```

#### `WorldText/NPC/Rockhead/Dialog Term: NPC Mining siblings: Mining Siblings:0`

EN:
```text
Since the sky broke, 
Siblings from rock awoke!
```

Old PL:
```text
Gdy pękło niebo wysoko,
Rodzeństwo otwarło oko!
```

Applied PL:
```text
Gdy niebo pękło, świat się zmienił,
Rodzeństwo zbudziło się w kamieniu!
```

#### `WorldText/NPC/Ted/Dialog Term: NPC - Yon final (Post Key): Final Yon:3`

EN:
```text
I... I still... feel... <j>WRONG<j>.
```

Old PL:
```text
Ja... ja nadal... czuję... <j>NIEPRAWIDŁOWOŚĆ<j>.
```

Applied PL:
```text
Ja... ja nadal... czuję... że coś jest ze mną <j>NIE TAK<j>.
```

#### `WorldText/NPC/Ted/Dialog Term: NPC - Yon final (Post Key): Final Yon:8`

EN:
```text
But... I have no one left to ask... you've eaten the Shapely... and now you will go eat the Formbringers too...
```

Old PL:
```text
Ale... nie mam już kogo zapytać... zjadasz Kształtnych... a teraz pójdziesz zjeść też Nadawców formy...
```

Applied PL:
```text
Ale... nie mam już kogo zapytać... Kształtny został przez ciebie pożarty... a teraz pójdziesz zjeść też Nadawców formy...
```

#### `WorldText/NPC/Vase/Dialog Term: NPC_Vasehead Second Finish: Second Finish:1`

EN:
```text
Why hello again! You would not believe it but you just missed it! It closed up right as you passed it by! I think you should definitely do this all again, but faster! 

```

Old PL:
```text
Witaj ponownie! Nie uwierzysz, ale właśnie ci umknęła! Zamknęła się, gdy przechodzisz obok! Zdecydowanie musisz zrobić to wszystko jeszcze raz, ale szybciej!

```

Applied PL:
```text
Witaj ponownie! Nie uwierzysz, ale właśnie ci umknęła! Zamknęła się akurat w chwili twojego przejścia! Zdecydowanie musisz zrobić to wszystko jeszcze raz, ale szybciej!

```

#### `WorldText/SpeechVolume/Speech Term: Speech Sealed Doors Locked:0`

EN:
```text
"No Dead One may enter Cenotaph City.
We shall be sealed, until the gift may unwrap."

The "Unsealer" is required.
```

Old PL:
```text
„Żaden Martwy nie wejdzie do Miasta Cenotafu.
Pozostaniemy odgrodzeni, dopóki nie będzie można otworzyć daru”.

Potrzebny jest „Otwieracz pieczęci”.
```

Applied PL:
```text
„Żaden Martwy nie wejdzie do Miasta cenotafów.
Pozostaniemy odgrodzeni, dopóki nie będzie można otworzyć daru”.

Potrzebny jest „Otwieracz pieczęci”.
```

### Open context and in-game checks

Grammatical defaults are sourced, not biological facts. Local player nouns govern agreement;
no global gender conversion. Other minor stylistic variants remain open for the user's language review.
No significant accepted-term change awaits approval.

Check Fidus checkpoint and Hafciarz descriptions; Prey Gauntlet header/body; Traits at low/high ranks;
Owl NG+ bubbles; Rockbed distorted speech; Yon final monologue; Listener combat phases;
Vase repeated-course dialogue. Check long text scrolling, Polish glyphs, animation and timing.

Re-check: all changed lines and repeated source dependencies, singular Shapely family, city/mode names,
Creep/Crawler names, Koda set labels and plural genitive. Build enforces original English, unique IDs,
exact tag/token counts, all 13 original language columns and unchanged other serialized objects.

Post-fix text SHA-256: `b1ab057a9165acd62b5dfd56549d5256918bf6f50bf05d419773a6a1cd6cbc4a`.


Additional paradigm check: `WorldText/NPC/Coda Bellkeeper/Npc Name`, EN `Coda Bellkeeper`,
old PL `Dzwonnik Kod`, new PL `Dzwonnik Kodów` applied to match the recorded plural genitive.
Final report has no missing entries, token, speaker-gender, address or duplicate-source inconsistency.
Remaining report hints were read: ordinary other/shapely word uses are not named lore terms;
placeholder seconds use invariant `s`; typography flags compare dispensable outer whitespace or
immutable tag quotes; length/capitalization remains a visual testing concern. Names, Hebrew and laughs
are intentional English matches. Report is not proof of in-game layout.
