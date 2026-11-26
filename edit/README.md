# Edit – montaż ze zdjęć i klipów

Folder roboczy do montażu: wrzucasz zdjęcia i klipy do `materialy/`, skrypt `montaz.py` składa z nich jeden film do `gotowe/`.

## Jak to działa

- Kolejność ujęć = kolejność nazw plików, więc nazywaj je `01_...`, `02_...`, `03_...`.
- **Zdjęcia** (jpg, png, webp, heic…): domyślnie 3 s, z powolnym zoomem (efekt Ken Burns).
- **Klipy** (mp4, mov, mkv, webm…): skalowane i przycinane do wspólnego kadru, bez czarnych pasów.
- Między ujęciami płynne przejście, a na początku i końcu wyciemnienie.
- **Muzyka**: plik audio (np. `muzyka.mp3`) w `materialy/` zostaje podkładem. Dźwięk z klipów jest wtedy ściszony.

## Użycie

Wymaga `python3` i `ffmpeg`.

```bash
python3 montaz.py                         # pion 9:16 (Reels/TikTok/Shorts) → gotowe/edit.mp4
python3 montaz.py --format poziom         # 16:9 (YouTube)
python3 montaz.py --format kwadrat        # 1:1
python3 montaz.py --zdjecie 2 --klip-maks 4 --przejscie 0.3
python3 montaz.py --wyjscie gotowe/wakacje.mp4
```

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `--format` | `pion` | `pion` 1080×1920, `poziom` 1920×1080, `kwadrat` 1080×1080 |
| `--zdjecie` | `3` | czas jednego zdjęcia (s) |
| `--klip-maks` | `0` | maks. długość klipu (s), `0` = cały klip |
| `--przejscie` | `0.5` | długość przejścia (s) |
| `--tlo` | `przyciete` | `przyciete` = zdjęcie wypełnia kadr, `rozmyte` = całe zdjęcie na rozmytym tle (dobre do kwadratowych/małych zdjęć) |
| `--przejscia` | `fade` | rodzaj przejścia (`fade`, `slideleft`, `circleopen`, `zoomin`…) albo `mix` = różne po kolei |
| `--bpm` / `--takty` | `0` / `4` | cięcie do rytmu: zmiana zdjęcia co N uderzeń muzyki |
| `--beat` | — | moment (s) dowolnego uderzenia w utworze: muzyka startuje tak, żeby cięcia trafiały w rytm |
| `--muzyka-od` | `0` | od której sekundy utworu zacząć (gdy nie podano `--beat`) |
| `--final` | `0` | ostatnie zdjęcie trwa tyle uderzeń (z `--bpm`) albo sekund; `0` = jak inne |
| `--zoom` | `0.15` | siła zoomu na zdjęciach (`0` = bez zoomu) |
| `--zoom-tryb` | `plynny` | `plynny` = powolny zoom, `punch` = mocne uderzenie zoomem na starcie każdego ujęcia |
| `--efekty` | — | efekty na każdym cięciu: `flash` (biały błysk), `shake` (trzęsienie), `rgb` (przesunięcie kolorów), `kolor` (mocniejsze kolory) albo `wszystkie` |
| `--fps` | `30` | klatki na sekundę, `60` = płynniej przy bardzo szybkich editach |
| `--glosnosc-klipow` | `0.3` | głośność dźwięku z klipów, gdy jest muzyka |
| `--wejscie` / `--wyjscie` | `materialy/` / `gotowe/edit.mp4` | foldery |

## Wycinanie zdjęć ze screenów

Jeśli zdjęcia są screenami (np. podgląd w czacie), `wytnij.py` wycina z każdego ten sam prostokąt:

```bash
python3 wytnij.py --ramka 308,1576,463,463 screeny/*.jpg --do materialy/
```

## Przykłady: edit do rytmu

Spokojny (zmiana co 4 uderzenia, długie przejścia):

```bash
python3 montaz.py --tlo rozmyte --przejscia mix --bpm 143.55 --takty 4 --przejscie 0.4
```

Szybki i energiczny (20 zdjęć w ok. 10 s, cięcie na każde uderzenie, ostatnie zdjęcie trzymane 2 uderzenia):

```bash
python3 montaz.py --tlo rozmyte --przejscia mix --bpm 120.14 --takty 1 --final 2 \
  --beat 0.035 --przejscie 0.12 --zoom 0.12
```

Przy „Electrodoodle” tempo wynosi 120,14 BPM, a pierwsze uderzenie wypada w 0,035 s.

Super energiczny (20 zdjęć w < 5 s, cięcie co pół uderzenia, błyski, trzęsienie, RGB, zoom-punch, 60 fps):

```bash
python3 montaz.py --tlo rozmyte --przejscia energia --efekty wszystkie --zoom-tryb punch --zoom 0.3 \
  --fps 60 --bpm 160.2 --takty 0.5 --final 3 --beat 130.032 --przejscie 0.0627
```

Tu muzyka startuje od 130 s utworu „Electrodoodle” (najmocniejszy fragment, 160 BPM).
Przy 60 fps przejście 0,0627 s sprawia, że każde ujęcie ma równo 15 klatek, więc cięcia nie rozjeżdżają się z bitem.

## Muzyka

Używamy tylko muzyki na wolnej licencji, np. Kevin MacLeod (incompetech.com, CC BY 4.0).
Przy publikacji podpisz utwór, np.: *"Electrodoodle" Kevin MacLeod (incompetech.com), licencja CC BY 4.0*.
Popularny utwór z TikToka/Instagrama najlepiej dodać już w aplikacji przy publikacji.

## Prywatność

`materialy/` i `gotowe/` są w `.gitignore`: zdjęcia i filmy zostają tylko lokalnie i nie trafiają na GitHuba.

## Struktura

```
edit/
├── montaz.py     # skrypt montażowy (ffmpeg)
├── wytnij.py     # wycinanie tego samego fragmentu z wielu screenów
├── materialy/    # tu wrzucasz zdjęcia, klipy i muzykę
└── gotowe/       # tu trafia gotowy film
```
