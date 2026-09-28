# Heat Signature: translation decisions

Facts and sources: `translations/bible.yaml`.

## Direction

- **Practice terminal speaks correctly** (user: "smooth it anyway"): caps, over-the-top enthusiasm,
  the "magic reality" joke kept ("TRENING ROZPOCZĘTY", "TERMINAL TRENINGOWY POZWALA ĆWICZYĆ WALKĘ Z
  WIRTUALNYMI LUDŹMI W MAGICZNEJ RZECZYWISTOŚCI"). *Rejected:* keeping broken grammar ("TRENING SIĘ
  ZACZĄĆ", "ROBIĆ PRZEMOC"). Don't restore errors during review.
- **Other dialogue: dry humor and swearing of the same strength** (agent). The terminal ruling is not
  censorship ("Nie tak wyobrażałam sobie emeryturę", "Teraz wyskoczę w kosmos. Jeśli nie zginę,
  widzimy się w barze").
- UI and instructions short and direct; no hard-coded keys next to control icons; trailing spaces of
  fragments kept. "Wrench" = klucz francuski (melee), "keycard" = karta dostępu.

## Characters

- **Fiasco is a woman** (Breaker: "she", "this white haired woman"); the vertical's masculine forms
  were fixed ("wyobrażałam", "Dostałam dziesięć kulek", "Rozniosłabyś"). **Asli Sixty female.**
- **Breaker, Geneva, Mirfak and the random player: neutral** (agent): present tense and impersonal
  constructions ("Czemu cię tam już nie ma?", "Ja stoję za barem", "Kieruję ochroną"). Traits as
  genderless nouns (Słabość, Technofobia, Duma, Kruchość, Szczęście).

## Terms

Swapper → Zamieniacz, Visitor → Wizytator, Sidewinder → Omijacz, Slipstream → Poślizg, Crashbeam →
Zawieszacz, Subverter → Przeprogramator, Key Cloner → Kopiarka kart, crash → zawiesić, Glory →
chwała, clause → klauzula, vow → przysięga, Defector → dezerter, Contractor → najemnik, Drift → Dryf,
Voidmother → Matka Pustki, Facebreaker → Gębołamacz. Factions, special pods (Offworld Angel,
Sovereign Coldfire, Glitchers Tick, Foundry Brick) and names stay; Sovereign/Foundry/Offworld are
neuter ("Sovereign zjawiło się"), Glitchers plural. Breacher stays (pod name).

## Item names and numbers

- Game builds "[modifiers] Noun"; Polish: noun first, adjectives after in reverse order agreeing in
  gender, "o dużej pojemności"/"dalekiego zasięgu" last ("Zamieniacz ładowalny o dużej pojemności");
  truncation keeps the key word. *Rejected:* adjectives before the noun.
- Weapon trait labels as nouns/phrases (Tłumik, Cichy strzał, Szybki ogień, Przebija pancerz,
  Zapalnik czasowy); same words in item names are adjectives ("Pistolet wytłumiony").
- Numbers from holes without declension: "Liczba użyć: 3.", "Zabójstwa: 12". "Zabij 3 oficerów
  Glitchers" is right for 2+.
- Personal missions: own templates per relative with the right case and gender ("Uratuj moją mamę z
  rąk Glitchers"); "Partner" → "moja druga połówka". Foundry "Better." → "Bywało lepiej." keeps
  Breaker's double-meaning joke.
- Opening narration uses the station as a variable name: "<nazwa> — ta stacja już cztery razy
  zmieniała właściciela w tym roku" (no guessing the name's gender).

## User rulings after the review

| Topic | Was | Is |
| --- | --- | --- |
| Player reply "Yep." | No. / Aha. No. | No tak. / Aha. No tak.; Mirfak "No jasne." |
| "Holy shit you're alive." (Breaker) | O kurwa, żyjesz. | Jasna cholera, żyjesz. |
| "Yeah, you stole a station!" | No właśnie, stacja ukradziona! | No właśnie, ukradliście stację! |
| Mission grade PACIFIST, trait Liberator | PACYFISTA, Wyzwoliciel | PACYFIZM, Wyzwolenie (dostępne) |
| Shiplocked | przypisany do statku | pokładowy/-a/-e; "Sprzęt pokładowy" |
| missions/jobs board, listings | mixed | "tablica zleceń", "Oferty zleceń" (user chose zlecenia over the reviewer's "tablica misji") |

Rejected, don't propose again without new evidence: "No." as yes, "O kurwa", "stacja ukradziona",
"przypisany do statku", "tablica misji".

## Review

2026-09-25, fresh-context subagent; 2704/2704 rows read (522 dialogue lines by scene, 1578 EXE
literals, 550 templates, 54 item grammar rows, ~40 composed names simulated with a Python port of
`Translate.h`). 28 certain issues applied, incl.: gender leaks for the player in UI (status labels
"Bez przytomności", "Nie żyje", "W niewoli", "Do wyboru"; death causes as nouns "Śmierć w
tajemniczych… okolicznościach", "Obrócenie w pył"; "Nie daj się zobaczyć"), grammar ("Liczba
wykryć", "Najbardziej zabójczy", "nie naładowano", "skuteczny przeciw"), sense ("Chwalebni rywale",
"Gdy skończysz grać"), and a template bug: adjacent holes `{0}{9}` produced "z rąk the Glitchers";
fixed with one template per clause `{0}, <clause>` and removal of `{0}'s {1}` (it split "Castor's
Rest"); added "poza celem nikogo nie zabijaj". All low-cost edits accepted (incl. Eks-Glitcher…).
Verdicts: all early decisions **keep**.

## Check in game

1. Personal mission with "the Glitchers" and a clause: no "the" left.
2. Station names with "'s" in holes.
3. Mission offers with bloodless/pacifist clause ("poza celem nikogo nie zabijaj").
4. Inventory with a damaged pod: "[uszkodzona]" refers to the pod.
5. Guard description with Defender (`#Chroniony: … sprzęt: {0}`).
6. Stronghold names on the map ("Twierdza Foundry").
7. Long item names in inventory and shop: "..." truncation.
8. `[Continue]`, `[Something else]` in TutorialEnd and FiascoEndGame: Polish and working.
9. Tutorial "Pause a lot!" header with three labels.
10. Character select and HUD after being knocked out: status labels.
11. Bar conversation, inventory, jobs board, log under B; then the "Untranslated" log for missing templates.
