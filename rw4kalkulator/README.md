# Kalkulator na Redmi Watch 4

Kalkulator naukowy jako „szybka aplikacja” (quick app, plik `.rpk`) dla zegarka **Redmi Watch 4** z HyperOS (Xiaomi Vela).

![Podgląd: wszystkie klawisze, tylko √ i %, ustawienia](podglad.png)

**Gotowa paczka:** [`Kalkulator.rpk`](Kalkulator.rpk)

## Funkcje (wersja 2.0)
Kalkulator liczy **całe wyrażenia** z zachowaniem kolejności działań, a nie tylko po jednym kroku.

| Klawisz | Działanie | Przykład |
|---|---|---|
| `+ − × ÷` | cztery działania, mnożenie i dzielenie przed dodawaniem | `2+3×4` = 14 |
| `( )` | nawiasy, brakujące `)` domyka się samo przy `=` | `(2+3)×4` = 20 |
| `√` | pierwiastek kwadratowy, wstawia `√(` | `√(16)` = 4 |
| `x²` | kwadrat | `3²` = 9 |
| `xʸ` | dowolna potęga `^` | `2^10` = 1024 |
| `%` | procent; po `+`/`−` liczy procent poprzedniej liczby | `200+10%` = 220, `50%` = 0.5 |
| `n!` | silnia | `5!` = 120 |
| `π` | liczba pi | `2π` = 6.283… |
| `1/x` | odwrotność, wstawia `1÷(` | `1÷(4)` = 0.25 |
| `Ans` | wstawia ostatni wynik | |
| `⌫` / `C` | kasowanie ostatniego elementu / wszystkiego | |

- Działa mnożenie domyślne: `2π`, `3(4+1)`, `2√(9)`.
- Liczby ujemne wpisuje się klawiszem `−`, np. `(−2)^2` = 4, a `−2^2` = −4.
- Mała szara linia na górze pokazuje **wynik na żywo** podczas wpisywania, a po `=` całe działanie.
- Po `=` naciśnięcie operatora liczy dalej od wyniku, a cyfra zaczyna nowe działanie.
- Niepoprawne wyrażenie, dzielenie przez zero albo pierwiastek z liczby ujemnej wyświetla `Error`.
- Krótka wibracja przy każdym naciśnięciu.

## Ustawienia (wersja 2.1)
Ikona zębatki w lewym górnym rogu otwiera ustawienia. Na dwóch stronach (przyciski `◀` `▶`) można włączać i wyłączać:

- klawisze naukowe: nawiasy `( )`, `√`, `x²`, `xʸ`, `%`, `n!`, `π`, `1/x`, `Ans`;
- **Podgląd wyniku**, czyli wynik na żywo w szarej linii;
- **Wibrację** przy naciśnięciu.

Przycisk **Gotowe** zapisuje wybór w pamięci zegarka i wraca do kalkulatora. Klawiatura sama się przebudowuje: bez klawiszy naukowych zostaje sama podstawowa klawiatura z dużymi przyciskami. Cyfry, `+ − × ÷`, `=`, `.`, `C` i `⌫` są zawsze widoczne.

**Aktualizacja ze starszej wersji:** najpierw usuń stary Kalkulator z zegarka, potem wgraj nowy plik. Notify nie nadpisuje zainstalowanej aplikacji.

## Instalacja (Notify for Xiaomi)
Potrzebny jest **telefon z Androidem**, bo z iPhone'a nie da się wgrać pliku `.rpk`.

1. Pobierz `Kalkulator.rpk` na telefon.
2. Zainstaluj **Notify for Xiaomi** ze Sklepu Play i przejdź kreator. Zaloguje się na Twoje konto Xiaomi i pobierze klucz zegarka.
3. Wymuś zatrzymanie **Mi Fitness** w ustawieniach aplikacji. Tylko jedna aplikacja może być połączona z zegarkiem. **Nie rozparowuj zegarka.**
4. W Notify wejdź w **Device → Third party app**, wybierz `Kalkulator.rpk` i postępuj zgodnie z instrukcjami.
5. Aplikacja „Kalkulator” pojawi się na liście aplikacji na zegarku.

Ograniczenia zegarka: najwyżej około 20 szybkich aplikacji i około 87 MB wolnego miejsca potrzebnego do instalacji.

## Budowanie
Wymagany Node.js 18+ (Python 3 z Pillow tylko do generowania grafik).

```
npm install
npm test                  # testy logiki kalkulatora
python3 scripts/gen_assets.py   # tylko gdy zmieniasz wygląd
npm run build             # paczka trafia do dist/
cp dist/*.rpk Kalkulator.rpk
```

Przy każdej nowej wersji zwiększ `versionName` i `versionCode` w `src/manifest.json`. Inaczej zegarek może zostawić starą wersję.

## Jak to działa
- Redmi Watch 4 nie rysuje tekstu w szybkich aplikacjach (`<text>` jest pusty), więc przyciski i cyfry na wyświetlaczu to gotowe obrazki PNG z `scripts/gen_assets.py`.
- Logika jest w `src/common/calc.js` (czysty JS, testy w `test/`), a ekran w `src/pages/index/index.ux`.
- Paczka jest podpisana kluczem debug z `aiot-toolkit`, co wystarcza do instalacji przez Notify.

## Pliki
| Plik | Opis |
|---|---|
| `Kalkulator.rpk` | gotowa paczka do instalacji |
| `src/manifest.json` | nazwa, pakiet `com.xt.rw4kalkulator`, wersja |
| `src/pages/index/index.ux` | ekran i obsługa dotyku |
| `src/common/calc.js` | logika kalkulatora |
| `src/common/layout.js` | układ klawiatury zależny od ustawień |
| `src/common/img/` | grafiki przycisków i znaków |
| `scripts/gen_assets.py` | generator grafik |
| `test/*.test.mjs` | testy (`npm test`) |
