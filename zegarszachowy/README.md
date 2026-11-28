# Zegar szachowy (Android)

Telefon jako zegar szachowy na turniej: kładziesz go między graczami, każdy dotyka swojej połowy ekranu po ruchu.

- Górna połowa jest obrócona do przeciwnika, a ekran nie gaśnie i działa na pełnym ekranie.
- Start: gracz z czarnymi dotyka swojej strony, co uruchamia zegar białych.
- Gotowe tempa: bullet, blitz, rapid, klasyczne, FIDE 90'/40 ruchów + 30' z dodatkiem 30".
- Własne tempo: minuty i sekundy, dodatek Fischera, Bronstein lub opóźnienie (delay), opcjonalny drugi okres po X ruchach.
- Licznik ruchów, dziesiąte części sekundy poniżej 20 s, kolor ostrzegawczy poniżej 10 s, sygnał przy upadku flagi.
- ⏸ pauza (np. dla sędziego), ± korekta czasu i liczby ruchów, ↺ nowa partia, ⚙ tempo, 🔊 dźwięk.
- Czas liczy się od zegara systemowego, więc nie gubi się, gdy aplikacja zostanie zamknięta lub zminimalizowana.

Gotowe APK: `ZegarSzachowy.apk` (w tym folderze). Instalacja: skopiuj na telefon, otwórz i zezwól na instalację z nieznanych źródeł.

Build: `./gradlew assembleDebug` → `app/build/outputs/apk/debug/app-debug.apk` (wymaga Android SDK, ścieżka w `local.properties`: `sdk.dir=...`).
