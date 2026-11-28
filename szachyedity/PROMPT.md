# Prompt startowy: edity szachowe (podsumowanie sesji)

Jesteś kontynuacją wcześniejszej sesji z AI. Wszystko, co wtedy powstało (kod, plansza, czcionki, narzędzia, opis), jest w repozytorium GitHub `vSake-clean/xt` w folderze `szachyedity/`. Poza tym repo masz tylko to, co dostaniesz od użytkownika. Traktuj ten plik jak własną pamięć. Zadanie na teraz jest w sekcji 8: **film z matem zduszonym**.

## Jak zacząć

1. Sklonuj repo i wejdź do `szachyedity/`. Przeczytaj `README.md` (pliki, filmy, polecenia).
2. Uruchom `./ustaw.sh`: instaluje numpy, pillow, scipy i python-chess oraz sprawdza ffmpeg. Czcionki są w `fonty/`, plansza w `wejscie/plansza.jpg`.
3. `wejscie/alien.mp4` (klip „Willy alien”) i `wejscie/wzor1.mp4` (pierwszy wzór, z niego jest muzyka) są w repo, więc do maty zduszonego nie potrzebujesz nic od użytkownika. Pozostałe filmiki z TikToka (lista w `README.md`) dostaniesz od użytkownika, gdy będą potrzebne; zapisz je w `wejscie/` pod nazwami z listy i nie commituj ich.
4. Zrób zadanie z sekcji 8.

## 1. Cel

Użytkownik pisze po polsku, gra białymi i robi krótkie filmiki szachowe na TikToka. Wysyła filmiki-wzory z TikToka, a AI robi filmy z takim samym montażem, efektami, tempem i muzyką, ale na planszy z jego zrzutu chess.com i z partią, którą AI wymyśla albo odczytuje ze wzoru. Wszystko powstaje kodem, klatka po klatce (Python: numpy, Pillow, scipy, python-chess; ffmpeg), 30 kl./s. Nie używamy generatorów wideo AI.

## 2. Preferencje użytkownika (wszystko, co ustaliliśmy)

- Plansza zawsze ta sama: zielona plansza chess.com ze zrzutu `wejscie/plansza.jpg`, także gdy wzór ma inną (np. drewnianą). Cytat: „szachownica ma być ta, która jest na każdym filmie”.
- Wygrywają białe: „ja mam wygrywać, biały ma wygrać”.
- Każdy ruch legalny, sprawdzony w python-chess. Nie wolno pokazać nielegalnego ruchu.
- Gra szybka, filmy krótkie. Edit na 38 s był „o wiele za długi”; skróciliśmy go do 14,6 s.
- Muzyka i długość jak we wzorze. Mem (klip „Willy alien”) wchodzi od razu po ostatnim ruchu, w tej samej sekundzie co we wzorze.
- **NIGDY nie dodawaj napisów** (cytat: „nigdy nie dodawaj napisów, nikt nie czyta napisów”): żadnych podpisów, tytułów, imion, opisów fabuły, tekstów piosenek ani podpisów autorów zdjęć. Zostają tylko elementy interfejsu chess.com, które są częścią planszy: oceny ruchów (Brilliant, Blunder itd., po angielsku), stoper, współrzędne.
- Po macie bez dymków „Winner”/„Checkmate” i bez przewracania króla. Zostają: czerwone pole króla, przyciemnienie planszy, małe odznaki (zielona korona przy zwycięzcy, czerwona plakietka przy przegranym).
- „Dosłowna kopia” = odtworzyć wzór klatka w klatkę (czasy ruchów, zbliżenia, błyski, klip, muzyka). „Coś w takim stylu” = ten sam pomysł i efekty, ale własna partia lub pozycja.
- Gdy użytkownik mówi „nie wycinaj, ja wytnę”, nie wycinasz klipów ze wzoru, tylko czekasz na jego plik.
- Na GitHubie nigdy nie dopisujesz Claude ani AI jako współautora commitów.
- Raport krótki, po polsku.

## 3. Co jest w repo (`szachyedity/`)

| Plik | Do czego |
| --- | --- |
| `wejscie/plansza.jpg` | zrzut chess.com 1080×2460 z pozycją startową; plansza 1080×1080 od y = 754, pole 135 px |
| `src/assets.py` | wycina planszę i figury ze zrzutu, zamalowuje pasek przewijania (zasłaniał cyfrę „7”); używają go skrypty z `src/` |
| `src/*.py` | po jednym skrypcie na każdy zrobiony film (szablony do nowych, tabela w sekcji 4) |
| `mat_zduszony.py` | samodzielny skrypt maty zduszonego (bez `src/`) |
| `src/analiza_wzoru.py` | rozbiera wzór: plansza, cięcia i błyski, zmiany na polach (ruchy), kadry planszy po każdej zmianie, beat muzyki |
| `src/dopasuj_klip.py` | ustala, gdzie, od kiedy, jak przezroczyście i w jakim tempie we wzorze leci mem |
| `buduj.sh` | buduje wszystkie filmy do `build/` (`./buduj.sh zduszony` = jeden film) |
| `ustaw.sh`, `requirements.txt` | instalacja zależności |
| `fonty/` | Inter (Regular, SemiBold, Bold, ExtraBold, ExtraLight) i DejaVu Sans Bold z licencjami |
| `CLAUDE.md` | skrót zasad dla AI |

## 4. Jak zrobić nowy film na podstawie wzoru

1. `python3 src/analiza_wzoru.py WZOR.mp4`: wypisuje położenie planszy, cięcia i błyski, momenty zmian na polach (ruchy) i beat muzyki; zapisuje arkusze klatek i kadry planszy po każdej zmianie. Z kadrów odczytaj partię.
2. Gdy wzór ma mema: `python3 src/dopasuj_klip.py WZOR.mp4 wejscie/alien.mp4 T_PRZED T_PO` (sekunda bez klipu i sekunda z klipem). Wypisuje prostokąt klipu, start, tempo i krycie każdego odtworzenia.
3. Weź najbliższy szablon i zmień partię, czasy i efekty:

| Styl | Szablon |
| --- | --- |
| sama plansza, mem na pustych polach (ffmpeg overlay w `buduj.sh`) | `src/pierwsza_partia.py` |
| szybka partia, mem w innym miejscu | `src/mat_szewski_alien.py` |
| znaczek ?? i zwolniony mat | `src/mat_glupca_zwolnienie.py` |
| stoper i koniec partii jak w chess.com | `src/speedrun_stoper.py` |
| koniec partii jak w chess.com, bez stopera | `src/mat_szewski.py` |
| edit kinowy (szara plansza, kamera, poświata) | `src/edit_kinowy.py` |
| Game Review, 3 zbliżenia, biały błysk, mem na całą planszę, pionowo | `src/kopia_caro_kann.py` |
| pogoń wieżą, mem półprzezroczysty | `src/pogon_wieza.py` + `src/pogon_wieza_trasa.py` |
| Game Review, zoom, mem 3×3 pola, pionowo | `mat_zduszony.py` |
| stoper nad planszą, Game Review, mem 3×3 pola, pionowo, ruchy na bit muzyki | `src/speedrun_caro_kann.py` |
| stoper na polach a3–c3, smuga za ruchem, zbita figura gaśnie, przyciemnienie gradientem + duży napis, kwadrat | `src/kopia_fastest.py` |
| kinowy edit o graczu (kolaż ze wzoru 9/10, ale bez zdjęć ludzi): prawdziwa partia, kamera, gwiazdy, złota ramka, napisy na pasku, ziarno, winieta | `src/edit_magnus.py` |

4. Partię sprawdź w python-chess: każdy ruch przez `board.parse_san()`, na końcu `is_checkmate()`; dla memów dodatkowe asercje (np. „każdy ruch wieży daje szacha”, „każde zbicie wieży daje pata”).
5. Zbuduj film, zrób klatki kontrolne, porównaj je ze wzorem w tych samych sekundach i sprawdź `ffprobe` (wideo i audio mają długość wzoru).
6. Dopisz film do `buduj.sh` i tabeli w `README.md`. Commit: tylko kod i opis, bez nowych filmików z TikToka i gotowych `.mp4` (repo jest publiczne; wyjątkiem są tylko `alien.mp4` i `wzor1.mp4`), autor `vSake-clean <vSake-clean@users.noreply.github.com>`, bez współautora Claude/AI.

## 5. Techniki i parametry

- Figury wycinane z pozycji startowej: odległość koloru od koloru pola, największa spójna składowa z wypełnionymi dziurami, miękka krawędź przez „odmieszanie” koloru. Pusta plansza zachowuje etykiety współrzędnych. Pola: jasne (238, 238, 210), ciemne (118, 150, 85); a1 jest ciemne.
- Wygląd „Game Review” chess.com: podświetlenie pól ruchu w kolorze klasy (alfa 0,5), okrągła ikona w prawym górnym rogu pola, biały dymek z nazwą klasy (Great, Brilliant, Blunder). Kolory są w słowniku `CLS` w `mat_zduszony.py`.
- Efekty: ruch z wygładzeniem smoothstep; roszada (król i wieża jadą razem); skokowy zoom 1,75× → 2,2× → 2,7×; biały błysk (1 − t/0,35)²; przyciemnienie po macie (odbarwienie 55% + kontrast ×1,3); stoper (Inter ExtraLight, stała szerokość cyfr); edit kinowy (obrót kamery, poświata, wstrząsy na beat, błyski na dropach).
- Render: klatki RGB przez pipe do ffmpeg → H.264 CRF 17, yuv420p, `+faststart`, AAC 192 kb/s. Audio ze wzoru z `-t DŁUGOŚĆ` (nie `-shortest`, bo ucina wideo).

## 6. Co już zrobiliśmy

| Film (`buduj.sh`) | Partia lub pomysł | Długość |
| --- | --- | --- |
| `final` | 1. e4 b6 2. Nf3 Ba6 3. Ne5 Bxf1 4. Qh5 Bxg2 5. Qxf7#, od 12,1 s mem 3×3 pola na planszy | 18,7 s |
| `alien2` | 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6?? 4. Qxf7#, mem po prawej (f3–h5) | 11 s |
| `glupca` | 1. f3 e5 2. g4?? Qh4# ze znaczkiem ?? i zwolnionym matem | 7,5 s |
| `speedrun` | 1. e4 g5 2. d4 f6?? 3. Qh5#, stoper, czerwone pole, przyciemnienie, odznaki | 13,6 s |
| `szewczyk` | 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? 4. Qxf7#, mat w 5,13 s | 12,9 s |
| `edit` | mat szewski jako edit kinowy, muzyka 6,0–20,6 s wzoru | 14,6 s |
| `kopia` | 1. e4 c6 2. Nc3 d5 3. d4 dxe4 4. Nxe4 Nf6 5. Ng5?! Bf5 6. N1f3 h6 7. Nxf7?, 3 zbliżenia, błysk 8,3 s, mem od 8,6 s | 15,3 s |
| `wieza` | biały Ka1 bez ruchów, wieża szachuje króla dookoła planszy (96 półruchów), zbicie wieży = pat | 17,5 s |
| `zduszony` | mat zduszony (sekcja 8) | 18,7 s |
| `carokann` | 1. e4 c6 2. d4 d5 3. Nc3 dxe4 4. Nxe4 Nd7 5. Qe2 Ngf6?? 6. Nd6# (mat zduszony w 6 ruchach), stoper nad planszą; ruchy na basie wzoru 1, muzyka od 6,47 s, mat w 5,56 s na dropie, alien w a3–c5 od 5,63 s | 12,2 s |
| `fastest` | dosłowna kopia wzoru 8 „MY FASTEST CHECKMATE”: 1. e4 f5 2. Qh5+ g6 3. Be2 gxh5 4. Bxh5#, ruchy w klatkach wzoru (start 16/43/71/98/126/148/171, lądowanie +4), stoper od klatki 10,3, staje na 00:05.37; od 5,83 s przyciemnienie gradientem, duży napis „00:05.37 / MY FASTEST CHECKMATE”, odznaki zamiast dymków „Pemenang”/„Sekakmat” | 9,6 s |
| `legal` | mat Legala w przepisie viralowych filmów: 1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6? 5. Nxe5!! Bxd1?? 6. Bxf7+ Ke7 7. Nd5#, dymki Brilliant i Blunder, stoper staje na 00:06.84, muzyka `wzor1` od 5,19 s, mat na dropie, alien w a3–c5 od 6,91 s | 13,5 s |
| `magnus` | edit o Magnusie w stylu wzoru 9 (kolaż): zdjęcia z meczu z artykułów Chess.com (czarno-białe, najazdy kamery, wycinanka z białym obrysem przy zegarze, odbitka w złotej ramce, kolorowe zdjęcie z pucharem na końcu, podpis „Photos: Chess.com”); użytkownik chce prawdziwych editów ze zdjęciami, nie samej planszy; prawdziwa partia Carlsen – Karjakin, dogrywka MS 2016, partia 4, zapis z ChessBase, 99 półruchów, 50. Qh6+!! (Karjakin się poddał; po Kxh6 Rh8#, po gxh6 Rxf7#). Białe błyski w 0 / 3,67 / 5,0 / 7,2 / 16,0 s, zaciemnienie 3,8 s, zdjęcie w zamyśleniu 10,8–12,0 s, złota ramka 14,4–16,0 s, bez żadnych napisów (w kodzie `NAPISY = False`) | 19,2 s |

Opinie użytkownika: pierwsze filmy „piękne”, edit kinowy „super, ale o wiele za długi”. **Viral:** `zduszony` i `carokann` poszły w viral. Wspólny przepis: mat zduszony skoczkiem, pionowo 1080×1920, muzyka z `wzor1` z matem na dropie, alien w a3–c5 od razu po macie, czerwone pole króla, korona i plakietka; w `carokann` dodatkowo stoper nad planszą (zielony po macie). Nowe filmy rób najpierw według tego przepisu.

## 7. Błędy, które już naprawiliśmy (nie powtarzaj)

- Odwrócone kolory pól przy wycinaniu figur (a1 jest ciemne).
- Szary pasek przewijania na lewej krawędzi zrzutu i ucięta cyfra „7”.
- `pip install chess` się nie budował → `pip install --only-binary=:all: chess` (robi to `ustaw.sh`).
- Zbyt mała ikona w animacji „pop” wywracała PIL (`y1 must be greater than or equal to y0`) → minimalny rozmiar ikony.
- `-shortest` w ffmpeg ucinał wideo → używaj `-t`.
- Listy ruchów, klas i czasów muszą mieć tę samą długość (assert).
- Dymek przy krawędzi planszy zasłaniał króla → dymek nad polem (0,62 szerokości pola), dociśnięty do planszy.
- Cyfry stopera wychodziły poza ramkę → rozmiar czcionki dobierany do szerokości ramki.
- Za mocna poświata w edicie kinowym prześwietlała kolory → słabsza poświata.
- Edit 38 s był za długi → skracaj do ok. 15 s, wycinając fragment muzyki tak, żeby drop wypadł na macie.
- Automatyczne wykrywanie mema psuły kropki podpowiedzi ruchów → `dopasuj_klip.py` najpierw usuwa drobiazgi (otwarcie morfologiczne).

## 8. ZADANIE NA TERAZ: film z matem zduszonym

Zrób `szachy_mat_zduszony.mp4`: po instalacji (`./ustaw.sh`) uruchom `./buduj.sh zduszony` (`wejscie/alien.mp4` i `wejscie/wzor1.mp4` są w repo). Film pojawi się w `build/`. Skrypt `mat_zduszony.py` jest sprawdzony i daje dokładnie ten film:

- Partia (wygrywają białe, mat zduszony Philidora z poświęceniem hetmana): 1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. O-O Nxe4 5. Re1 Nd6 6. Nxe5 Be7 7. Bxc6 dxc6 8. c3 O-O 9. d4 Nf5 10. Nd2 f6?? 11. Qb3+ Kh8 12. Nf7+ Kg8?? 13. Nh6+ Kh8 14. Qg8+!! Rxg8 15. Nf7#. Po 13. Nh6+ i po 14. Qg8+ czarne mają tylko jeden legalny ruch.
- Format: pionowo 1080×1920, plansza 1080×1080 na środku (y 420–1500), czarne tło, 30 kl./s, 18,7 s, muzyka z `wzor1.mp4` od 0 s.
- Tempo: debiut co 0,24 s (1. e4 ląduje w 0,45 s), 10…f6?? w 5,25 s, potem 6,15 · 6,85 · 7,55 · 8,25 · 8,95 · 9,60 · 10,30 (Qg8+!!) · 11,45 · 12,03 s (Nf7#).
- Oceny: do 6…Be7 Book, potem Excellent/Best. Dymki: 10…f6 (Blunder), 11. Qb3+ (Great), 12…Kg8 (Blunder), 13. Nh6+ (Great), 14. Qg8+ (Brilliant) ze skokowym zoomem na g8 (1,75× w 10,48 s, 2,2× w 10,76 s, 2,7× w 11,04 s, powrót w 11,30 s).
- Mat: czerwone pole h8, przyciemnienie, po 0,12 s zielona korona przy g1 i czerwona plakietka przy h8.
- 12,1 s: klip z alienem w kwadracie 3×3 pola a3–c5 (405×405 px, w pełni kryjący) do końca filmu.
- Kontrola: `ffprobe` (wideo i audio po 18,7 s), klatki w 1,75 s, 5,6 s, 6,3 s, 11,2 s, 12,05 s i 13 s, partia jeszcze raz przez python-chess.
- Raport po polsku: ścieżka pliku, partia, potwierdzenie legalności i mata, czym film różni się od wzoru.
