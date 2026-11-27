# Szachy edity

Generator krótkich filmików szachowych na TikToka. Partia jest animowana na zielonej planszy chess.com wyciętej ze zrzutu ekranu, z ocenami ruchów jak w „Game Review” (Book, Best, Great, Brilliant, Blunder), zbliżeniami, błyskami, memem (klip z alienem) i muzyką z filmiku-wzoru. Każda partia jest sprawdzana w python-chess, więc w filmach nie ma nielegalnych ruchów.

## Wymagania

- Python 3 z `numpy`, `pillow`, `scipy` i `chess`: `pip install numpy pillow scipy` oraz `pip install --only-binary=:all: chess`
- ffmpeg i ffprobe
- czcionka Inter (Bold, SemiBold, ExtraLight) w `/usr/share/fonts/opentype/inter/`

## Pliki wejściowe (`wejscie/`)

| Plik | Co to jest | W repo |
| --- | --- | --- |
| `plansza.jpg` | zrzut chess.com 1080×2460 z pozycją startową (oryginalnie `1000187442.jpg`) | tak |
| `alien.mp4` | klip „Willy alien” 576×576, 6,6 s (`ssstik.io_1795725991721.mp4`) | nie |
| `wzor1.mp4` | pierwszy wzór z alienem, muzyka do filmów final, alien2, glupca i zduszony (`ssstik.io_1795725809290.mp4`) | nie |
| `wzor3_speedrun.mp4` | wzór ze stoperem (`ssstik.io_1795733422678.mp4`) | nie |
| `wzor4_szewczyk.mp4` | wzór z matem szewskim (`ssstik.io_1795737130909.mp4`) | nie |
| `wzor5_edit.mp4` | wzór editu kinowego (`ssstik.io_1795737267636.mp4`) | nie |
| `wzor6_kopia.mp4` | wzór Caro-Kann z zoomem (`ssstik.io_1795737810861.mp4`) | nie |
| `wzor7_wieza.mp4` | wzór z pogonią wieżą (`ssstik.io_1795738571009.mp4`) | nie |

Filmiki z TikToka zawierają cudzą muzykę i klipy, więc nie ma ich w tym publicznym repo (są w `.gitignore`). Przed budowaniem wrzuć je do `wejscie/` pod nazwami z tabeli.

## Budowanie

```bash
./buduj.sh            # wszystkie filmy do build/ (ok. 4 min)
./buduj.sh zduszony   # tylko jeden film
```

| Nazwa | Skrypt | Plik w `build/` | Partia | Długość |
| --- | --- | --- | --- | --- |
| `final` | `src/pierwsza_partia.py` | `szachy_final.mp4` | 1. e4 b6 2. Nf3 Ba6 3. Ne5 Bxf1 4. Qh5 Bxg2 5. Qxf7#, klip z alienem na planszy | 18,7 s |
| `alien2` | `src/mat_szewski_alien.py` | `szachy_alien2.mp4` | 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6?? 4. Qxf7#, klip po prawej | 11 s |
| `glupca` | `src/mat_glupca_zwolnienie.py` | `szachy_mat_glupca.mp4` | 1. f3 e5 2. g4?? Qh4#, znaczek ?? i zwolniony mat | 7,5 s |
| `speedrun` | `src/speedrun_stoper.py` | `szachy_bialy_wygrywa_v2.mp4` | 1. e4 g5 2. d4 f6?? 3. Qh5#, stoper i koniec partii jak w chess.com | 13,6 s |
| `szewczyk` | `src/mat_szewski.py` | `szachy_szewczyk.mp4` | 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? 4. Qxf7# | 12,9 s |
| `edit` | `src/edit_kinowy.py` | `szachy_edit_krotki.mp4` | mat szewski jako edit kinowy (szara plansza, kamera, poświata) | 14,6 s |
| `kopia` | `src/kopia_caro_kann.py` | `szachy_kopia.mp4` | 1. e4 c6 2. Nc3 d5 3. d4 dxe4 4. Nxe4 Nf6 5. Ng5?! Bf5 6. N1f3 h6 7. Nxf7?, pionowo | 15,3 s |
| `wieza` | `src/pogon_wieza.py` + `src/pogon_wieza_trasa.py` | `szachy_wieza.mp4` | wieża szachuje króla dookoła planszy, zbicie wieży = pat | 17,5 s |
| `zduszony` | `mat_zduszony.py` | `szachy_mat_zduszony.mp4` | mat zduszony Philidora: 14. Qg8+!! Rxg8 15. Nf7# | 18,7 s |

## Pozostałe pliki

- `src/assets.py` wycina planszę i figury ze zrzutu (zmienna `PLANSZA` albo `wejscie/plansza.jpg`) i zamalowuje pasek przewijania widoczny na zrzucie.
- `mat_zduszony.py` działa samodzielnie, bez `src/`: `python3 mat_zduszony.py PLANSZA.jpg MEM.mp4 MUZYKA.mp4 wynik.mp4`.
- `prompt_mat_zduszony.md` to prompt dla innego AI: podsumowanie całej pracy, zasady i zadanie „zrób film z matem zduszonym” z gotowym skryptem.
