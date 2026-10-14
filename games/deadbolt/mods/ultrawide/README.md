# DEADBOLT: Szeroki ekran

## Instalacja

1. Zamknij grę.
2. W Steamie wybierz DEADBOLT → **Zarządzaj → Przeglądaj pliki lokalne**.
3. Wypakuj zawartość archiwum obok `deadbolt_game.exe`: plik `d3d9.dll` i folder `ultrawide`.
4. Uruchom grę normalnie.

Mod używa tego samego `d3d9.dll` co nasze spolszczenie, więc obie paczki możesz wypakować w
dowolnej kolejności i mieć jedno i drugie. Używaj najnowszych wersji obu. Innego moda z własnym
`d3d9.dll` nie da się używać razem z tym.

## Ustawienia

W `ultrawide\settings.ini` (po zmianie uruchom grę ponownie):

- `Enabled=0` wyłącza szeroki ekran,
- `VirtualWidth=0` dopasowuje szerokość do głównego monitora; liczba (parzysta, 961–3840)
  wymusza szerokość przy wysokości 540, np. 1280 dla 21:9 albo 1920 dla 32:9.

Sprawdzone w grze na 32:9 (5120×1440). 21:9 liczy się tak samo, ale nie było testowane w grze.
Na ekranach 16:9 i węższych mod nic nie zmienia.

Żeby usunąć mod, przy zamkniętej grze skasuj `d3d9.dll` i folder `ultrawide`. Jeśli używasz też
spolszczenia, zostaw `d3d9.dll` i skasuj tylko folder `ultrawide`.
