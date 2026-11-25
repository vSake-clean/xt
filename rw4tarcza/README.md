# Nocna: tarcza na Redmi Watch 4

Własna tarcza `.bin` dla zegarka **Redmi Watch 4** (390×450).

![Podgląd tarczy](podglad.png)

**Gotowy plik:** [`Nocna.bin`](Nocna.bin)

## Co pokazuje
- godzinę w formacie 24h: godziny białe, minuty pomarańczowe;
- dzień tygodnia po polsku (PON, WT, ŚR…) i datę;
- kroki, tętno i baterię z ikonami.

Grafika jest oryginalna, rysowana skryptem.

## Budowanie
Wymaga Python 3 z Pillow i Node.js. Do pakowania `.bin` używany jest otwarty packer z projektu [Watchface Designer](https://github.com/calinhoria/watchface-designer) (czysty JS, bez dodatkowych pakietów).

```
git clone https://github.com/calinhoria/watchface-designer ../../watchface-designer
python3 scripts/gen_face.py
node scripts/build.mjs ../../watchface-designer Nocna.bin
```

`gen_face.py` tworzy grafiki w `build/img/`, podgląd `podglad.png` i opis `build/face.json`. `build.mjs` pakuje to do `Nocna.bin`, a potem rozpakowuje wynik, żeby go sprawdzić.

Zamiast `build.mjs` możesz złożyć tarczę w Mi Create (Windows) z gotowych grafik z `build/img/`.

## Instalacja
W Notify for Xiaomi wybierz **Device → Watchface** i plik `.bin`. **Nie** używaj „Aktualizacji oprogramowania”, ta opcja służy do firmware'u.
