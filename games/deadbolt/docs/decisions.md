# DEADBOLT: translation decisions

Facts and sources: `translations/bible.yaml`.

## Direction (agreed with user 2026-09-25)

Facts behind the sample: the hero is a reaper, male (fireplace: "should not have to spend **his**
time in darkness"; enemies "**He's**... coming..."). Mission descriptions and notes in the reaper's
first person, some JSON narration in second person (inconsistency is in the original). The
fireplace/flames = "my employer", calls the hero "friend", speaks only in verse; the refrain "A man
with a heart / ambition / desire…, cannot live with me" returns 8 times. "Knock" is a mechanic
(knocking lures enemies), so the verb stays in the knocking verse.

1. **Flames' verses: rhyme and rhythm, fixed refrain "…nie może przy mnie żyć"** (option A).
   "-yć" gives rhymes (być, kryć, gnić, bić). *Rejected:* B free verse, closer to the words.
   After the review the user allowed more freedom: every stanza rhymes, refrain unchanged, the
   mission's point (whom to kill, what to check) and `&y&`/`&b&` highlights stay; imagery and word
   order may shift ("bred by the undead" → "nieumarli karmią je krwią", "or Ibzan is crowned" →
   "nim Ibzan na tronie zagości"). 14 stanzas rewritten (missions 2, 3, 5, 9, 10, 14, 17–23, Vall);
   m1, m4, m6, m8, m11, m12, m16, m24, m25, m27 already rhymed or are free in EN. *Rejected:* the
   reviewer's m14 "zgubione - / w morzu żądzy i bólu" (no rhyme).
2. **"reaper" = żniwiarz** (lower-case; "grim reaper" = "ponury żniwiarz"). *Rejected:* "kosiarz"
   (jokey, can't carry fireplace scenes); "Kostucha" (feminine vs "he").
3. **Gang names stay English** (Zombie Kingz, 1000 Year Royals, The Dredged: brands; "Kingz"
   slang spelling). World concepts translated: Świece, to Miejsce, Charon, piekielne ogary,
   filakteria. *Rejected:* Królowie Zombie, Tysiącletni Arystokraci, Wyłowieni (read as descriptions).
4. **Tape swearing: "jebany" for "fucking"** (one level for the whole game). *Rejected:* "pieprzony"
   (proposed by the agent, slightly weaker than EN).

## Agent decisions

- Purchase notification texture: "NEW WEAPON" → "NOWA BROŃ" (2026-10-04, user report).
  `sNewWeapon` frame 0; existing color erase/mask method, lower weapon-name plate untouched.

- Charon's texture headings: "WEAPON UPGRADE" → "ULEPSZ BROŃ", "PRIMARY" → "GŁÓWNA",
  "SECONDARY" → "DODATKOWA" (2026-10-03, reported untranslated in game). Labels patched in
  memory with existing color erase/mask recipes; no publisher texture included in package.

- UI hints imperative in caps as in EN (`&y&'E'&!&: OTWÓRZ SEJF`); menus sentence case
  ("Powrót do gry", "Wyjdź do menu głównego"); "Wł./Wył."; "Diegetic Music" → "Muzyka z otoczenia".
- Mission titles adapted where punned: "Dead Simple" → "Śmiertelnie proste", "New High" → "Nowy
  haj", "Supply and Demand" → "Popyt i podaż", "Bar Hopping" → "Od baru do baru". Latin and foreign
  quotes stay ("Lux in Tenebris", "Le Sniper Du Cœur", "Quid Pro Quo", "Baba Yaga").
- Fireplace = "płomienie / kominek / mój pracodawca"; to the hero "przyjacielu".
- Narration person as in the original; developer jokes kept ("ror2 when", test strings).
- **Straight quotes and hyphens** (fonts lack „ ” and en dash), also in verses.
- **Appended names and numbers after a colon**: `Kill &r&` + name → `Zabij: &r&` + name;
  `You have died ` + n → `Liczba zgonów: ` + n + `. Spróbuj innej taktyki!`; weapon pickup
  `'&!&: WEŹ BROŃ: ` + name (the code appends the weapon name in caps nominative).
- **"Controls" translated only in the pause menu** (same string is a Prefs.ini section).
- "Gore/Blood" → "Krew i flaki"; "Shoot/Enter" → "Strzel/zatwierdź" (assumes Enter = confirm; test).
- "The flames roar to life." → "Płomienie z rykiem budzą się do życia." (one translation everywhere).
- "Stop suckin lmao!" translated after the review ("Weź się ogarnij, lol!"): the only English death tip.
- "GODDAMN" (s1763) → "CHOLERNIE zimno" (user; rejected "PRZEKLĘCIE").

## Review

2026-09-25, fresh-context subagent, read-only. 618/618 entries read; tags match in all; all JSON
fields covered (8 names deliberately untranslated). Certain errors fixed: weapon pickup
("PODNIEŚ KOSA"), s2598 subject ("on chyba tu jest"), s1253 "Kiepska celność", m8 plural souls, s1227
"Straż!". Verdicts: all four user decisions **keep**; agent decisions keep, except "Stop suckin lmao!"
(changed). Discussion list applied (Styx song lines, "Przyprowadź... swoich...", "Nie wygląda
najlepiej.", "ODBLOKOWANO", "surowo", many low-priority fixes). After fixes: `review.py` 0 problems,
report clean (m22 "trupów" deliberate for rhyme), plugin test OK.

## Open

- Finale "grim and dim"; gender of the Candle in dia_lv3_7 (no context); pad button abbreviations
  ("L. bumper"/"L. spust" vs LB/RB/LT/RT).

## Check in game

1. Weapon pickup: which name gets appended, does the line fit.
2. Objectives with names: "Zabij: Timur Majsterkowicz", "Zabij: Amber & Evelyn" (does `&` show).
3. Charon screen: longest weapon names ("PISTOLET 9 mm Z TŁUMIKIEM", "KARABIN ZE STAREGO ŚWIATA").
4. fontTiny object hints: "WEJDŹ DO WENTYLACJI", "OTWÓRZ WYTRYCHEM", "ODETNIJ ZASILANIE (CHWILOWO)",
   "NASTAW MINUTNIK NA 3 S"; does "WEŹ NA CEL" (s1388) mean the sniper rifle.
5. Controls menu: "Strzel/zatwierdź" and column width.
6. Summary and achievements: "Naciśnij 'E', aby kontynuować", "NAGRODA W DUSZACH: n", longest descriptions.
7. Death tip "Liczba zgonów: 7. Spróbuj innej taktyki!".
8. Mission select: titles, descriptions.
9. Flames: `#` breaks, `&y&` color, fit in the folder (missions 16, 24).
10. Tapes: longest (s1759) and the song (s1766): blank lines, stanzas, scrolling.
11. Bubbles: is s2648 readable in time. 12. Warning (s1941) and credits fit the screen.
13. Main menu, tutorial and folder labels drawn by the plugin.
