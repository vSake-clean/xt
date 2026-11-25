# Tarcze na Redmi Watch 4

Własne, minimalistyczne tarcze `.bin` dla zegarka **Redmi Watch 4** (390×450): biel i szarości na czarnym tle. Grafika jest oryginalna, rysowana skryptami.

| Tarcza | Plik | Co pokazuje |
|---|---|---|
| **Nocna** | [`Nocna.bin`](Nocna.bin) | duża godzina 24h, dzień tygodnia po polsku, data, kroki, tętno, bateria |
| **Żółta** | [`Zolta.bin`](Zolta.bin) | duża godzina (godziny białe, minuty żółte), dzień tygodnia pisany odręcznie po polsku, data, bateria, kroki, kalorie, tętno, stres |
| **Pierścień** | [`Pierscien.bin`](Pierscien.bin) | godzina w środku pierścienia, który zapełnia się wraz z % dziennego celu kroków; data, kroki, tętno, bateria |
| **Analog** | [`Analog.bin`](Analog.bin) | wskazówki godzin, minut i sekund, kreski minut, dzień tygodnia i dzień miesiąca |

| Nocna | Żółta | Pierścień | Analog |
|---|---|---|---|
| ![Nocna](podglad.png) | ![Żółta](podglad-zolta.png) | ![Pierścień](podglad-pierscien.png) | ![Analog](podglad-analog.png) |

> **Uwaga (nietestowane, możliwy restart w kółko):** po wgraniu tarczy **Pierścień** lub **Analog** zegarek użytkownika zaczął się restartować w kółko (logo Xiaomi, logo HyperOS, czarny ekran). Przyczyna nie jest jeszcze ustalona. **Nie wgrywaj tych dwóch tarcz**, dopóki nie zostanie to wyjaśnione. Działanie „Nocnej” zostało potwierdzone.

Najbardziej prawdopodobna przyczyna przy Pierścieniu to pamięć: jego 21 obrazków 320×320 zajmuje po rozpakowaniu ok. 10 MB, a Nocna ok. 1,5 MB. **Żółta** jest zbudowana tylko z tych samych typów elementów co Nocna (obrazek, lista dnia tygodnia, liczby) i zajmuje ok. 1,9 MB. Nowe są w niej tylko dwie liczby: kalorie (źródło `0823`) i stres (`0826`). Nie była jeszcze sprawdzona na zegarku.

## Instalacja
W Notify for Xiaomi wybierz **Device → Watchface** i plik `.bin`. **Nie** używaj „Aktualizacji oprogramowania”, ta opcja służy do firmware'u.

## Budowanie
Wymaga Python 3 z Pillow i Node.js. Do pakowania `.bin` używany jest otwarty packer z projektu [Watchface Designer](https://github.com/calinhoria/watchface-designer) (czysty JS, bez dodatkowych pakietów).

```
git clone https://github.com/calinhoria/watchface-designer ../../watchface-designer
python3 scripts/gen_face.py      # Nocna -> build/face.json
python3 scripts/gen_extra.py     # Pierścień i Analog -> build/pierscien.json, build/analog.json
python3 scripts/gen_zolta.py     # Żółta -> build/zolta.json (pobiera czcionki Rubik i Dancing Script, licencja OFL)
node scripts/build.mjs ../../watchface-designer Nocna.bin
node scripts/build.mjs ../../watchface-designer Pierscien.bin build/pierscien.json
node scripts/build.mjs ../../watchface-designer Analog.bin build/analog.json
node scripts/build.mjs ../../watchface-designer Zolta.bin build/zolta.json
```

`build.mjs` po spakowaniu rozpakowuje wynik i sprawdza typ zegarka, tytuł oraz liczbę elementów.

Numery tarcz (`1672100xx`) mają ten sam format co tarcze z oficjalnego kompilatora Mi Create. Przy numerze w innym formacie Notify ostrzegał o niezgodności modelu. Każda tarcza ma własny numer: Nocna 088, Pierścień 089, Analog 090, Żółta 091.
