# Szachy edity

Generator krótkich filmików szachowych na TikToka. Partia jest animowana na zielonej planszy chess.com wyciętej ze zrzutu ekranu, z ocenami ruchów jak w „Game Review” (Book, Best, Great, Brilliant, Blunder), zbliżeniami, błyskami, memem (klip z alienem) i muzyką z filmiku-wzoru. Każda partia jest sprawdzana w python-chess, więc w filmach nie ma nielegalnych ruchów.

Dla AI, które zaczyna od zera: najpierw `PROMPT.md` (pełny kontekst, zasady i zadanie), skrót zasad jest w `CLAUDE.md`.

## Instalacja

```bash
./ustaw.sh   # numpy, pillow, scipy, python-chess (requirements.txt) + sprawdzenie ffmpeg
```

Czcionki (Inter Regular, SemiBold, Bold, ExtraBold, ExtraLight i DejaVu Sans Bold, z licencjami) są w `fonty/`, więc nic więcej nie trzeba instalować.

## Pliki wejściowe (`wejscie/`)

| Plik | Co to jest | W repo |
| --- | --- | --- |
| `plansza.jpg` | zrzut chess.com 1080×2460 z pozycją startową (oryginalnie `1000187442.jpg`) | tak |
| `alien.mp4` | klip „Willy alien” 576×576, 6,6 s (`ssstik.io_1795725991721.mp4`) | tak |
| `wzor1.mp4` | pierwszy wzór z alienem, muzyka do filmów final, alien2, glupca, zduszony, carokann i legal (`ssstik.io_1795725809290.mp4`) | tak |
| `wzor3_speedrun.mp4` | wzór ze stoperem (`ssstik.io_1795733422678.mp4`) | nie |
| `wzor4_szewczyk.mp4` | wzór z matem szewskim (`ssstik.io_1795737130909.mp4`) | nie |
| `wzor5_edit.mp4` | wzór editu kinowego (`ssstik.io_1795737267636.mp4`) | nie |
| `wzor6_kopia.mp4` | wzór Caro-Kann z zoomem (`ssstik.io_1795737810861.mp4`) | nie |
| `wzor7_wieza.mp4` | wzór z pogonią wieżą (`ssstik.io_1795738571009.mp4`) | nie |
| `wzor8_fastest.mp4` | wzór „MY FASTEST CHECKMATE” ze stoperem (`ssstik.io_1795767131355.mp4`) | nie |
| `wzor9_magnus_a.mp4` | kinowy kolaż o Levym i Magnusie, muzyka do edytu `magnus` (`712eb9d795bdc06685490143b6eb28e8.mp4`) | nie |
| `wzor10_magnus_b.mp4` | kinowy kolaż o Fischerze (zimna wojna, lalkarze), muzyka do edytu `fischer` (`9e8d810080d92042a972cc3ff56606ad.mp4`) | nie |

`alien.mp4` i `wzor1.mp4` są w repo, więc mat zduszony (i filmy final, alien2, glupca, carokann) zbudujesz od razu. Pozostałych filmików z TikToka nie ma w repo (są w `.gitignore`); przed budowaniem innych filmów wrzuć je do `wejscie/` pod nazwami z tabeli.

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
| `carokann` | `src/speedrun_caro_kann.py` | `szachy_caro_kann_speedrun.mp4` | 1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Nd7 5. Qe2 Ngf6?? 6. Nd6#, stoper nad planszą, pionowo | 12,2 s |
| `fastest` | `src/kopia_fastest.py` | `szachy_fastest_checkmate.mp4` | 1. e4 f5 2. Qh5+ g6 3. Be2 gxh5 4. Bxh5#, dosłowna kopia wzoru 8, kwadrat | 9,6 s |
| `legal` | `src/speedrun_legal.py` | `szachy_mat_legala.mp4` | 1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6? 5. Nxe5!! Bxd1?? 6. Bxf7+ Ke7 7. Nd5#, stoper, pionowo | 13,5 s |
| `magnus` | `src/edit_magnus.py` | `szachy_edit_magnus.mp4` | Carlsen – Karjakin, dogrywka MS 2016, partia 4: 50. Qh6+!! 1-0, kinowy edit-kolaż ze zdjęciami z meczu (Chess.com), pionowo | 19,2 s |
| `fischer` | `src/edit_fischer.py` | `szachy_edit_fischer.mp4` | Fischer – Spasski, Reykjavik 1972, partia 6: 38. Rxf6!! … 41. Qf4 1-0, kinowy edit-kolaż (figury i zdjęcie na sznurkach, USA kontra ZSRR), pionowo | 19,4 s |

## Narzędzia do nowych filmów

- `python3 src/analiza_wzoru.py WZOR.mp4` rozbiera filmik-wzór: położenie planszy, cięcia i błyski, momenty zmian na polach (ruchy), beat muzyki. Zapisuje arkusze klatek, kadry planszy po każdej zmianie i `analiza.json`.
- `python3 src/dopasuj_klip.py WZOR.mp4 wejscie/alien.mp4 T_PRZED T_PO [x y w h]` ustala, gdzie, od kiedy, jak przezroczyście i w jakim tempie we wzorze leci mem. `T_PRZED` to sekunda bez klipu, `T_PO` sekunda z klipem.

## Pozostałe pliki

- `src/kolaz.py`: narzędzia do editów-kolaży (czarno-białe zdjęcie, najazd kamery, wycinanka z białym obrysem przez OpenCV, zegar).
- `src/pobierz_zdjecia.py`: pobiera zdjęcia z artykułów Chess.com o meczu 2016 do `wejscie/zdjecia/` (nie ma ich w repo). To zdjęcia prasowe z prawami autorskimi Chess.com: w filmie jest podpis „Photos: Chess.com”, a za publikację odpowiada autor filmu. Wikimedia Commons (wolne licencje) blokowało pobieranie z tego środowiska (błąd 429).

- `src/assets.py` wycina planszę i figury ze zrzutu (zmienna `PLANSZA` albo `wejscie/plansza.jpg`) i zamalowuje pasek przewijania widoczny na zrzucie.
- `mat_zduszony.py` działa samodzielnie, bez `src/`: `python3 mat_zduszony.py PLANSZA.jpg MEM.mp4 MUZYKA.mp4 wynik.mp4`.
- `PROMPT.md` to prompt startowy dla AI z dostępem tylko do GitHuba: podsumowanie całej pracy, zasady, sposób robienia nowych filmów i zadanie „zrób film z matem zduszonym”.
