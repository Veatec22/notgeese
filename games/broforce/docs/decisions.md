# Broforce: translation decisions

Facts and sources: `translations/bible.yaml`.

## Addressing the player

- **"Ty", masculine.** Menus, hints, messages ("Wyrzucono cię z gry", "Nie masz ich dość, co?").
  Personal forms avoided where free ("Połączenie zostało przerwane" instead of "Zostałeś
  rozłączony", "W KTÓRYCH JESZCZE CIĘ NIE BYŁO").
- **World-map orders in the infinitive, military style:** "UZIEMIĆ ICH!", "ODOBCOWIĆ ICH!",
  "DO ROBOTY!", "ODNALEŹĆ ICH I URATOWAĆ!". The original says "Broforce" or "Bros"; the
  infinitive skips "ty" vs "wy" and sounds like HQ orders.
- **Finale: President and Jesus use "ty"** ("DOKONAŁEŚ NIEMOŻLIWEGO", "OBRALI CIĘ WIELKIM
  CESARZEM"): "Hello, friend", "High five me, Bro!", singular "emperor". "Gentlemen…" and "How did
  you know…" stay plural ("PANOWIE", "SKĄD WIEDZIELIŚCIE").

## Terms

| EN | PL | Why | Source |
| --- | --- | --- | --- |
| bro | bro (indeclinable) | core of every pun; Polish slang knows "bro" | decision |
| IRONBRO | unchanged | mode name | decision |
| Brotality | Brotalność | brutality → brutalność, pun kept | decision |
| Brodown (tie-breaker) | BROJEDYNEK | showdown → pojedynek, with "bro" | decision |
| Covert Operation | TAJNA OPERACJA | | decision |
| Workshop | Warsztat | official Polish Steam name | decision |
| dash | sprint | a faster run here, not a dodge | decision |
| Fire (button) | STRZAŁ | "NACIŚNIJ STRZAŁ, BY DOŁĄCZYĆ" | decision |
| custom campaign / map | WŁASNE KAMPANIE / mapy graczy | main menu vs messages | decision |
| Deathmatch, Versus, Host | unchanged | established in Polish games | decision |
| gyming (boss captions) | koksowanie | gym slang | decision |

## Opportunities taken

- Country parodies stay parodies: Veetman → Wietman, Cambodium – soon to be Cam*BRO*dium →
  KAMBODIUM – WKRÓTCE KAM*BRO*DIUM, Youkraine? More like our kraine! → TWUKRAINA? RACZEJ
  NASZKRAINA! Irakistan, Jalpin, Mookgolia, Afreeka, Arstotzka, Val Verde unchanged.
- Threat levels as foods and colors: CZARNY BEZ, MARMOLADA, MORELA, CHEDDAR, BAKŁAŻAN,
  KANTALUPA, BATAT; muscle temples: BRĄZOWA OPALENIZNA, SAMOOPALACZ, MASŁO KAKAOWE,
  NAPOMPOWANE ŻELAZO.
- Boss captions: TACO HELL → TACO Z PIEKŁA RODEM, OVERCOMPENSATE MUCH? → COŚ SOBIE
  REKOMPENSUJEMY?, gyming technology → SZCZYTOWE OSIĄGNIĘCIE TERRORYSTYCZNEGO / NIEUMARŁEGO
  KOKSOWANIA.
- Freedominate them! → ZDOMINOWAĆ ICH WOLNOŚCIĄ!, Terrestrialize them! → UZIEMIĆ ICH!,
  De-alienate them! → ODOBCOWIĆ ICH!, 'Murica → MERYKA.

## Deliberate departures

- **Post-mission counter "4 DO URATOWANIA I NOWY BRO ODBLOKOWANY!"**: the game glues
  "{n} {MORE} {RESCUE|RESCUES} {UNTIL NEXT UNLOCK}" with only 1 vs rest; no noun that would need
  three forms.
- "ZWYCIĘSTWA Z RZĘDU: {0}!", "POZOSTAŁO SEKUND: {0}": number after a colon.
- Region descriptions and cutscene captions in caps (caps-only fonts, see technical).
- Kept English: "WHAT IS LOVE?" (Terrorbot, song quote), "BLRRGGGGG", contest "Weekend Workshop
  Brodown", bro names (Rambro, Ellen Ripbro, MacBrover, Time Bro…).
- Dash hint shortened to "KIERUNEK DWA RAZY = SPRINT!" (literal was 60% longer in a tight box).

## Review

No independent full review yet. Check report after full: 0 hits in all sections (9 deliberate
English leftovers moved to `keep_english`, contest name silenced, "Warsztat" stem fixed to
"warszta").

## Check in game

- Map region descriptions: dynamic font, Windows substitutes Ą Ć Ę Ń Ś Ź Ż in another face. Bad
  enough to move them to the bitmap Hudson?
- Finale (President, Jesus): some lines in 04B_11 without Polish letters (substituted) and with
  manual line breaks; longest may clip.
- Mission results: "4 DO URATOWANIA I NOWY BRO / ODBLOKOWANY!" fits?
- Boss captions before fights, e.g. "UKORONOWANIE ZAGROŻENIA TERRORYSTYCZNEGO I KOSMICZNEGO".
- Red "POZOSTAŁO SEKUND" counter (timed campaigns): HudsonOutline with composed letters, unseen.
- Versus and custom campaign menus: long labels ("WYBIERZ SPOŚRÓD ZAPISANYCH LOKALNIE KAMPANII…").
