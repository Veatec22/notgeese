# Labyrinth of the Demon King PL

## Instalacja

1. Zamknij grę. Jeśli masz starsze spolszczenie, usuń z `Shinigami/Content/Paks` trzy pliki `pakchunk99-NieGesiPL_P` (`.pak`, `.utoc`, `.ucas`) — inaczej starsza wersja może przesłonić nowszą.
2. Wypakuj całą zawartość archiwum do katalogu gry, czyli tam, gdzie leży `Shinigami.exe`. W Steamie trafisz tam przez **Zarządzaj → Przeglądaj pliki lokalne**, w GOG Galaxy przez **Zarządzaj instalacją → Pokaż folder**. W `Shinigami/Content/Paks` pojawią się trzy pliki `pakchunk99-notgeesePL_P` (`.pak`, `.utoc` i `.ucas`), a w `Shinigami/Binaries/Win64` plik `dwmapi.dll` i folder `ue4ss` (UE4SS z naszym skryptem, który wyświetla polskie napisy pod tekstem filmu wprowadzającego i tłumaczy dodatkowe komunikaty oraz napisy interfejsu).
3. Uruchom grę i na ekranie wyboru języka wybierz **Polski**.

Spolszczenie nie podmienia żadnego pliku gry. Przy aktualizacji spolszczenia wypakuj nową paczkę i pozwól nadpisać pliki; zapisy gry zostają bez zmian. Żeby je usunąć, skasuj przy zamkniętej grze trzy pliki `pakchunk99-notgeesePL_P`, plik `Shinigami/Binaries/Win64/dwmapi.dll` i folder `Shinigami/Binaries/Win64/ue4ss`. Przy innych modach UE4SS usuń tylko `ue4ss/Mods/notgeesePL` i jego wpisy w `mods.txt` oraz `mods.json`.
