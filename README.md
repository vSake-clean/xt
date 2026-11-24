# xt – zbiór aplikacji

Jedno repozytorium, wiele aplikacji. **Każda aplikacja ma własny folder w głównym katalogu (gałąź `main`), a nazwa folderu = nazwa aplikacji.** Cały kod, pliki budowania i gotowe paczki (APK, CRX itp.) danej aplikacji trzymamy wyłącznie w jej folderze.

## Zasady dodawania nowej aplikacji

1. Utwórz folder w katalogu głównym: `<nazwa-aplikacji>/` (małe litery, bez spacji, np. `keycopier`).
2. Cały kod i konfiguracja budowania tylko w tym folderze. Niczego nie dodawaj do katalogu głównego.
3. Gotowy plik do instalacji (np. `.apk`) zapisz w tym samym folderze, np. `keycopier/KeyCopier.apk`.
4. W folderze dodaj krótki `README.md`: co robi aplikacja, jak ją zbudować i zainstalować.
5. Dopisz aplikację do tabeli poniżej.
6. Commity bez dopisywania Claude jako współautora (bez `Co-Authored-By: Claude`).

## Aplikacje

| Folder | Aplikacja | Typ | Gotowa paczka |
|---|---|---|---|
| [`keycopier/`](keycopier/) | Key Copier: odczyt kodu klucza z ekranu telefonu (jak Flipper Zero) | Android (Java) | [`keycopier/KeyCopier.apk`](keycopier/KeyCopier.apk) |
| [`eszkola-ext/`](eszkola-ext/) | eSzkoła: rozszerzenie przeglądarki | Chrome / Firefox | `eszkola.crx`, `eszkola.xpi` (w katalogu głównym, patrz niżej) |

### Wyjątek: eSzkoła

Pliki `eszkola.crx`, `eszkola.xpi` i `eszkola_update.xml` muszą zostać w katalogu głównym. Zainstalowane rozszerzenie pobiera aktualizacje z adresu `https://cdn.jsdelivr.net/gh/vSake-clean/xt@main/eszkola.crx`, więc przeniesienie ich zepsułoby aktualizacje. Nowe aplikacje tego wyjątku nie powielają.
