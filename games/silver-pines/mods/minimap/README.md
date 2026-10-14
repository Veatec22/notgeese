# Silver Pines: Minimapa

## Instalacja

1. Zamknij grę.
2. Rozpakuj całe archiwum ZIP do folderu gry, tego z plikiem `Carpenter.exe`. Na Steamie:
   prawy przycisk na Silver Pines → Zarządzaj → Przeglądaj pliki lokalne.
3. Uruchom grę. Pierwsze uruchomienie trwa 1–3 minuty i przez ten czas nic nie widać na ekranie:
   BepInEx przygotowuje się do pracy (raz potrzebuje internetu). Kolejne starty są normalne.

Steam Deck i Linux (Proton): w opcjach uruchamiania gry wpisz
`WINEDLLOVERRIDES="winhttp=n,b" %command%`.

## Obsługa

Minimapa pokazuje się w prawym górnym rogu, gdy sterujesz postacią, i znika przy rozmowach,
telefonach, przerywnikach, oglądaniu przedmiotów i notatek. Przytrzymanie klawisza szybkiej mapy
(domyślnie Caps Lock albo RB na padzie) nadal otwiera pełną szybką mapę. **F7** włącza i wyłącza
minimapę.

Róg ekranu, rozmiar, przybliżenie, czas zanikania i ramkę zmienisz po pierwszym uruchomieniu w
`BepInEx\config\pl.notgeese.silverpines.minimap.cfg` (potem uruchom grę ponownie).

Żeby usunąć mod, skasuj z folderu gry `winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`,
`changelog.txt` oraz foldery `BepInEx` i `dotnet`. Jeśli po aktualizacji gry mod przestanie
pasować, wyłączy się sam i zapisze to w `BepInEx\LogOutput.log`, a gra działa dalej bez niego.
