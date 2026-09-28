# Hyper Light Drifter: translation decisions

The game tells its story through images and has no dialogue: text is UI only, 110 menu entries and
16 hints. No characters or forms of address; hints use "ty", imperative ("Przytrzymaj", "Tnij").

## Where Polish lives

**Polish replaces Italian, listed as "POLSKI".** Language codes are hard-coded in the exe
(7 entries). Italian uses the same Latin font as English; Russian is out (its font draws Cyrillic
in place of "ó"). This version has no Italian.

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| dash | zryw | short (11-char field), a lunge; "unik" suggests defense only | decision |
| gun(s) | broń palna | the game separates the slash-charged gun from the sword (DE "Schusswaffe", IT "arma da fuoco") | files |
| warp | teleportować się | as FR, ES, DE | files |
| Home (Warp Home) | dom | the central town you return to; "baza" sounds military | decision |
| gear | wyposażenie / sprzęt | "sprzęt" where length matters | decision |
| Newcomer | Nowicjusz | mode name, not declined ("w trybie Nowicjusz") | decision |
| Boss Rush | Maraton bossów | descriptive; "boss" stays in Polish games | decision |
| Fully Loaded / Mid-Range / Naked | Pełny zestaw / Średni zestaw / Na golasa | loadouts in Boss Rush; FR/ES/DE read "Mid-Range" as a range and lost the sense | decision |
| achievements / trophies | osiągnięcia / trofea | Polish Steam and PlayStation terms | decision |
| co-op | kooperacja | | decision |
| Credits | Twórcy | short, as in Polish releases | decision |

"Naked" → "Na golasa": as casual as the original; the description says "Nic poza pistoletem".

## Deliberate departures

- "SFX Volume / Music Volume" → "Efekty / Muzyka" (15-char field; FR and IT also use one word).
- "Minutes" → "min": the game builds "N Minutes since last save" without plurals; the abbreviation
  fits any number. "Minute" → "minuta".
- "Warp Home to change gear" → "Wróć do domu, by zmienić sprzęt" (full "Teleportuj się…" was 2× longer).
- "Quit To Title" → "Wyjdź do menu głównego" (the title screen is the main menu here).
- Key names in the binding screen as caps nouns: CELOWANIE, LECZENIE, ZRYW, ZMIANA BRONI
  (12 chars vs "11 chars max"; German has 14).
- The font is caps-only; no Polish quotes or dashes (not in the font, not needed).

## Review

2026-09-25, fresh-context subagent: 126/126 read in 7 batches, no gaps; tags `[BUTTON_*]`,
`[spr_*]` intact; limits kept except the deliberate `SwapWepConfig`. No meaning, grammar or tag
errors. Two fixes applied: "Broń palna w pełni naładowana cięciami miecza" ("fully" was missing),
"Odblokowano Średni zestaw w Maratonie bossów" (consistent loadout name). All early decisions **keep**.

## Open

Current text stays until decided:

1. `Phrases/REMINDERGUN`: if it shows with an empty gun, use "Cięcia mieczem ładują broń palną".
2. `SpecialConfig` "SPECJALNY" (only adjective among action names): "GRANAT" if it throws a grenade,
   or "BROŃ SPEC."; `ShootConfig` "STRZAŁ" → "STRZELANIE" (low priority).
3. `notapplicable` N/A → "Brak" reads as "not assigned"; option "N/D".
4. Control modes "Standardowe / Kooperacja / Alternatywne": option `COOPCONTROLS` → "Kooperacyjne".
5. `COOP_DISABLED` "Wyłączona" vs ON/OFF "Włączone/Wyłączone": gender mismatch if shown together.
6. Low priority: "Poziom trudności według twórców.", "obiekty" in `Phrases/AMMO`, "NADPISAĆ TEN
   ZAPIS?", "Kierunek zrywu", `MINUTE` "min".

## Check in game

1. Language list and all screens: "POLSKI", the 16 composed letters (blanks = coordinate clamping,
   broken font = PNG rejected), ogonki on the mode screen ("ŁAGODNIEJSZE WYZWANIE.").
2. Settings: "Rodzaj zrywu: Za kursorem", "Tryb ekranu: Okno maks. / Pełny ekran", co-op row values.
3. Key binding: "ZMIANA BRONI" (12 vs 11), "INTERAKCJA", what SPECIAL does, where "Brak" appears.
4. Pause: "Wyjdź do menu głównego" and its confirm dialog.
5. Load screen: "Mniej niż minuta od ostatniego zapisu", "N min od…", "PUSTY", "ZASTĄPIĆ TEN ZAPIS?".
6. Boss Rush unlock messages (up to 47 chars) and "Maraton bossów ukończony".
7. New game: "(Odblokowane po ukończeniu gry)", "(ZABLOKOWANE: brak DLC Alt Drifter)".
8. First hints: comma right after an icon, longest "Przytrzymaj […], by podnieść przedmioty";
   when REMINDERGUN and CAPE show.
