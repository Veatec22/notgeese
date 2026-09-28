# SPRAWL: translation decisions

SPRAWL was translated before the repo had a direction step; these decisions were reconstructed
(2026-09-26) from the earlier notes and the translation itself. None were user decisions until the
review below; the user confirmed the translation works in game, not tone or terms. Speakers come from
`Dialogue_Subs` keys (`E1M1_FATHER_…`, `REAPER_…`, `E3M2_POLITICIAN_…`). Facts:
`translations/bible.yaml`.

## Decisions

1. **Codenames stay English, indeclinable:** SEVEN, SIX, FIVE, program numbers (One…Six). SEVEN is
   the heroine, feminine ("byłaś"); SIX masculine ("byłem").
2. **Places and roles translated:** Father → Ojciec, Reaper → Żniwiarz (SIX's codename and the
   program: "program ŻNIWIARZ"), Spire → Iglica, Walled City → Miasto za Murem, Dark City → Ciemne
   Miasto, Badlands → Pustkowia, Overseer → Nadzorca, Pythia → Pytia, Bullet Time → spowolnienie
   czasu.
3. **Maker, faction and unit class names stay:** SPRAWL, AEON, NCO, ICARUS, GOR, IMAGO-DEI, Domand,
   weapon names and models (MEGATECH A8, SHOGO-KENBISHI…), classes Ghost, Spectre, O.H.G.R, Oni,
   Bull, Okami, Sendai, Suzumebachi. The descriptive part is translated ("Lekki mech klasy
   Spectre"). Companies always "korporacja AEON", "korporacja Domand" (user); full "AEON Cybertech"
   stays. "the Sprawl" → "SPRAWL" (caps, indeclinable, neuter).
4. **Registers:** Father calm, haughty, coolly ironic, "ty" to SEVEN, split lines joined with "…";
   SIX mocking, yelling ("Po prostu zdechnij!", "Tatuś"); military reports in CAPS as EN; hacker
   chats lowercase without punctuation, profanity kept at strength ("jebany", "chuju"), hackers
   masculine (EN doesn't say); Makashima and Halcyon: "pan" from a subordinate, "ty" from a superior;
   Mother a female narrator, broken sentences, glued words, repetitions and interference are
   intentional, not smoothed.
5. **Technical:** `<red>`, `<amber>`, `<blink>`, icons `<img id="…"/>`, entities `&lt;…&gt;`, code
   strings and Latin in broadcasts unchanged; `ß` in a codex address kept. `[REDACTED]` →
   `[UTAJNIONO]`.
6. **Interpretive spots:** `Tutorials/E1M1_COMBAT_10_BODY` "overkill" → "doszczętnie zniszczyć";
   "SEVERED STEEL" stays (reference to another game); Club Simulacra / Klub Null difference from the
   source kept.

Other terms: squad captain → dowódca oddziału; weapons testing arena → arena testów broni; chaingun →
minigun (the game calls it Minigun); karta dostępu, drzwi pancerne, wślizg, bieg po ścianie, słaby
punkt; "implant" for ICARUS implant vs "wszczepy" for cyberware (EN distinction).

## Review

2026-09-26, fresh-context subagent, read-only: 717/717 read in full (codex and Mother's broadcasts
included), by namespace and scene; no gaps. All decisions kept; only the E1M4 title challenged.
Applied fixes (16 items, 31 fields), e.g.: "Nie żyjesz!" (the only masculine form to the player;
PK/HRD simulations may not be SEVEN), "Miasto za Murem" in the E1M1 title, "Są podatne" (O.H.G.R
mechs), "Teraz nie cofną się przed niczym" (stop at nothing), sector ranges and "UNIESZKODLIWI CEL"
in operation orders, "DLACZEGO PO PROSTU NIE WYŁĄCZYLI OD RAZU NASZYCH SYSTEMÓW?", "megapolis
dusząca się", "głowę dowódcy", "Uciekła za mury sieci", "(DLA ZAAWANSOWANYCH)", Mother04 "a
niezatrzymana" (double negation reversed EN), "…" glyph in all Father intro lines.

User decisions 2026-09-26:

- E1M4 "Ghost Wetware" stays "Biologiczne widmo" for now; rejected "Ghost Wetware" as a name and
  "Wetware klasy Ghost" (Ghost units debut on E1M4); reopen after testing the level.
- Death screen "Nie żyjesz!"; rejected "Zginęłaś!".
- Hacker chat `e1m5.chatlogcasemrph` "ona do nas też nie należy" (keeps the hint that the reaper is
  a woman).
- Father: "A w zamian ja wreszcie będę… / …wolny." (he was never free), "wykonać skok wiary", "nie
  natkniesz się na tego kogoś", "Na twoim miejscu przygotowałbym minigun."
- SIX: "To niemożliwe!", "I tak dobrze, że ten robak zdechł.", "Przekaż temu czemuś, co szepcze…"
  (EN "whatever" dehumanizes Father).
- Fong: "Egzystencja skazana na zagładę…" (doomed).
- `e2m2.transit` "spill over areas" → "TERENÓW PRZYLEGŁYCH"; rejected restoring Mother's stepped
  indentation and "Manifest cyborga" (stays "Manifest cyborgów").

**Open, text unchanged:** Father: HALLMARK_D "wzorcowym egzemplarzem swojego rodzaju",
FRIEDHACKER_B "zakłócających porządek anomalii", AT_SWITCH_B "żeby cię zablokować", GARAGE_C
"Stamtąd przejdziesz po dachach…", ASSISTED_SUICIDE_D "a nie zamierzam dłużej być więźniem",
INTRODUCING_L "niewypowiedzianych okropieństw"; `EnemyNames/NINJA` "Tajna jednostka Ghost"; "lekkie
patrole" calque; CONFIRM_RETURN_TO_MENU_MESSAGE "Na pewno chcesz wrócić do menu?"; CONTROL_*
"Strzał" → "Strzelanie"; WALLRUNNING_04_BODY "Wykorzystaj to w narożnikach, by dostać się";
COMBAT_10_BODY "dają nagrody"; codex word order in `e1m4.syserrorspire`, "wbiegał głową w mur"
(`e3m2.mother777`), semicolon in `e3m3.kintsukuroi`.

Unresolved, no change: whom "the emergent victor of the corporate schisms" describes
(`e2m4.syserrorgorcomplex`); feminine addressee in MOTHER01; mother03 refrain feminine singular
with plural verb; masculine speaker in `e3m1.cybernetics`; `E1M5_SIX_TEASER_A/B` sounds like Father;
`ACME_UNKNOWN_VOICE_*` masculine, echoing Father (keep the "zniszcz(cie) maszyny" and gold echoes);
THREE masculine in HRD1_FLAVOUR (EN "they"); "grozisz mu, samuels?" and "w komorze" in
`e3m2.faustian`.

Check report after: missing 0, tokens 0, gender 0, address 0, terms 0, consistency 0; the rest are
names, false alarms or in-game checks.

## Check in game

1. Death screen in campaign, horde and time trial.
2. Settings labels (`SETTINGS_AUTOSWAP`, `SETTINGS_WALLRUNTILT`, `SETTINGS_STRAFETILT`,
   `SETTINGS_FPSLIMIT`, `SETTINGS_GAMEPAD_AUTOAIM`, `SETTINGS_MOUSE_AUTOAIM`, `SETTINGS_VSYNC`,
   `CONTROL_EQ_SMG`) and `DIFFICULTY_HWP_DISCLAIMER`.
3. Boss bar and enemy names: `SHOTGUNNER` (39 chars), `RAIL_TURRET`, `BOSS_TWO_RAIL`.
4. Parkour/PK map list: does "(DLA ZAAWANSOWANYCH)" fit?
5. Pickup messages `PU_SMG` (41), `PU_MINI`, `PROMPT_PRESSINTERACT` (48), `PROMPT_MELEE`.
6. Subtitles `E1M1_FATHER_ENABLING_CYBERWARE_B`, `E2M4_FATHER_FOUR_GENERATORS_A`: readable in time?
7. Codex: scrolling the longest pages (`E1M1.OPERATIONORDERS`, `e2m2.transit`, `e3m1.cybernetics`,
   `e3m2.lightmech`, `e1m3.mauricepadilla-fong01`), capital ŻŹĆŚŁ in the codex font, Mother04
   interference reads like EN.
8. "…" glyph in all dialogue subtitles.
9. Level select: E1M1 and E1M4 names.
