# Kontekst sesji (podsumowanie po kompaktowaniu): edity szachowe na TikToka

Jesteś kontynuacją wcześniejszej sesji z AI. Poniżej jest pełne podsumowanie tego, co ustaliliśmy i zrobiliśmy. Traktuj je jak własną pamięć. Na końcu jest zadanie na teraz: **film z matem zduszonym** (sekcja 7).

## 1. Główna prośba i cel

Użytkownik pisze po polsku, gra białymi i robi krótkie filmiki szachowe na TikToka. Wysyła zrzut planszy z chess.com i filmiki-wzory z TikToka. AI robi filmy z takim samym montażem, efektami, tempem i muzyką jak wzór, ale na planszy ze zrzutu i z partią, którą wymyśla albo odczytuje ze wzoru. Wszystko powstaje kodem, klatka po klatce (Python: numpy, Pillow, scipy, python-chess; ffmpeg), 30 kl./s. Nie używamy generatorów wideo AI.

## 2. Preferencje użytkownika (wszystko, co ustaliliśmy)

- Plansza zawsze ta sama: zielona plansza chess.com ze zrzutu (figury „neo”, współrzędne a–h i 1–8), także gdy wzór ma inną, np. drewnianą. Cytat: „szachownica ma być ta, która jest na każdym filmie”.
- Wygrywają białe: „ja mam wygrywać, biały ma wygrać”.
- Każdy ruch legalny, sprawdzony w python-chess. Nie wolno pokazać nielegalnego ruchu.
- Gra szybka, filmy krótkie. Edit na 38 s był „o wiele za długi”; skróciliśmy go do 14,6 s.
- Muzyka i długość jak we wzorze. Mem (klip „Willy alien”) wchodzi od razu po ostatnim ruchu, w tej samej sekundzie co we wzorze.
- Napisy po angielsku (Great, Brilliant, Best, Blunder itd.).
- Po macie bez dymków „Winner”/„Checkmate” i bez przewracania króla (użytkownik kazał usunąć tę półsekundową animację). Zostają: czerwone pole króla, przyciemnienie planszy, małe odznaki (zielona korona przy zwycięzcy, czerwona plakietka przy przegranym).
- „Dosłowna kopia” = odtworzyć wzór klatka w klatkę (czasy ruchów, zbliżenia, błyski, klip, muzyka). „Coś w takim stylu” = ten sam pomysł i efekty, ale własna partia lub pozycja.
- Gdy użytkownik mówi „nie wycinaj, ja wytnę”, nie wycinasz klipów ze wzoru, tylko czekasz na jego plik.
- Na GitHubie nigdy nie dopisujesz Claude ani AI jako współautora commitów.
- Raport krótki, po polsku.

## 3. Pliki dołączone do tej wiadomości

- `1000187442.jpg` (PLANSZA): zrzut chess.com 1080×2460 z pozycją startową. Plansza 1080×1080 zaczyna się na y = 754, pole ma 135 px. Przy lewej krawędzi szary pasek przewijania aplikacji (x 17–24, y 94–275 w układzie planszy) zasłania cyfrę „7”: trzeba go zamalować i dorysować cyfrę (robi to skrypt).
- `ssstik.io_1795725991721.mp4` (MEM): klip „Willy alien” 576×576, 6,63 s, z cięciem w 3,03 s.
- `ssstik.io_1795725809290.mp4` (wzór 1): 576×1024, 18,7 s; partia, mat, w 12,1 s klip z alienem w kwadracie 3×3 pola na planszy. Z niego bierzemy muzykę do maty zduszonego.

## 4. Kluczowe techniki

- Figury wycinamy z pozycji startowej: odległość koloru od koloru pola, największa spójna składowa z wypełnionymi dziurami, miękka krawędź przez „odmieszanie” koloru. Pusta plansza zachowuje etykiety współrzędnych. Kolory pól: jasne (238, 238, 210), ciemne (118, 150, 85); a1 jest ciemne.
- Analiza wzoru: `ffprobe`; arkusz klatek (`fps=2,scale=160:-1,tile=10x5`); wszystkie klatki. Różnica sąsiednich klatek pokazuje cięcia i błyski, zmiana odchylenia w środku każdego pola pokazuje moment ruchu, piksele w kolorze klasy pokazują dymki. Klip mema dopasowujemy najmniejszymi kwadratami (`wynik = a·klip + b·plansza`): wychodzi pozycja, krycie, przesunięcie i prędkość. Muzyka: onsety basu, beat z autokorelacji.
- Wygląd „Game Review” chess.com: podświetlenie pól ruchu w kolorze klasy (alfa 0,5), okrągła ikona w prawym górnym rogu pola, biały dymek z nazwą klasy (słownik `CLS` w skrypcie).
- Efekty: ruch z wygładzeniem smoothstep; roszada (król i wieża jadą razem); skokowy zoom 1,75× → 2,2× → 2,7× (wycinek planszy dociśnięty do krawędzi); biały błysk (1 − t/0,35)²; przyciemnienie po macie; stoper (Inter ExtraLight, stała szerokość cyfr); edit kinowy (szara plansza, obrót kamery, poświata, wstrząsy na beat, błyski na dropach).
- Render: klatki RGB idą przez pipe do ffmpeg → H.264 CRF 17, yuv420p, `+faststart`, AAC 192 kb/s. Audio ze wzoru z `-t DŁUGOŚĆ` (nie `-shortest`, bo ucina wideo).
- Legalność: każdy ruch przez `board.parse_san()`, na końcu `is_checkmate()`. Dla memów dodatkowe asercje, np. „każdy ruch wieży daje szacha”, „każde zbicie wieży daje pata”.

## 5. Co już zrobiliśmy (seria)

| Film | Partia lub pomysł | Styl | Długość |
| --- | --- | --- | --- |
| 1 | 1. e4 b6 2. Nf3 Ba6 3. Ne5 Bxf1 4. Qh5 Bxg2 5. Qxf7# | sama plansza i animacje ruchów | 13,7 s |
| 2 | ta sama partia + mem 3×3 pola od 12,1 s + muzyka wzoru 1 | klip na planszy | 18,7 s |
| 3 | mat szewski, szybko; mem po prawej (f3–h5) | klip na planszy | 11 s |
| 4 | 1. f3 e5 2. g4?? Qh4# ze znaczkiem ?? i zwolnionym matem | prosty | 7,5 s |
| 5 | 1. e4 g5 2. d4 f6?? 3. Qh5# (odwrócony mat głupca) | stoper, czerwone pole, przyciemnienie, odznaki | 13,6 s |
| 6 | 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? 4. Qxf7#, mat w 5,13 s | jak wyżej, bez stopera | 12,9 s |
| 7 | mat szewski jako edit kinowy (szara plansza, kamera, poświata, M1) | edit kinowy | 38,4 → 14,6 s |
| 8 | 1. e4 c6 2. Nc3 d5 3. d4 dxe4 4. Nxe4 Nf6 5. Ng5?! Bf5 6. N1f3 h6 7. Nxf7?; 3 zbliżenia na skoczka, błysk 8,3 s, mem od 8,6 s | dosłowna kopia, pionowo 1080×2322 | 15,3 s |
| 9 | biały Ka1 bez ruchów, wieża szachuje króla dookoła planszy (96 półruchów), zbicie wieży = pat; mem półprzezroczysty od 3,63 s | Great / Brilliant / Best, pionowo 1080×1920 | 17,5 s |
| 10 | mat zduszony (zadanie niżej) | klip na planszy, Game Review, zoom | 18,7 s |

Opinie użytkownika: filmy 1–2 „piękne”, edit kinowy „super, ale o wiele za długi”.

## 6. Błędy, które już naprawiliśmy (nie powtarzaj)

- Odwrócone kolory pól przy wycinaniu figur (a1 jest ciemne).
- Szary pasek przewijania na lewej krawędzi zrzutu i ucięta cyfra „7”.
- `pip install chess` się nie budował → `pip install --only-binary=:all: chess`.
- Zbyt mała ikona w animacji „pop” wywracała PIL (`y1 must be greater than or equal to y0`) → minimalny rozmiar ikony.
- `-shortest` w ffmpeg ucinał wideo przed końcem → używaj `-t`.
- Listy ruchów, klas i czasów muszą mieć tę samą długość (assert).
- Dymek przy krawędzi planszy zasłaniał króla → dymek nad polem (0,62 szerokości pola), dociśnięty do planszy.
- Cyfry stopera wychodziły poza ramkę → rozmiar czcionki dobierany do szerokości ramki.
- Za mocna poświata w edicie kinowym prześwietlała kolory → słabsza poświata.
- Edit 38 s był za długi → skracaj do ~15 s, wycinając fragment muzyki tak, żeby drop wypadł na macie.

## 7. ZADANIE NA TERAZ: film z matem zduszonym

Zrób `szachy_mat_zduszony.mp4`:

- Partia (wygrywają białe, mat zduszony Philidora z poświęceniem hetmana): 1. e4 e5 2. Nf3 Nc6 3. Bb5 Nf6 4. O-O Nxe4 5. Re1 Nd6 6. Nxe5 Be7 7. Bxc6 dxc6 8. c3 O-O 9. d4 Nf5 10. Nd2 f6?? 11. Qb3+ Kh8 12. Nf7+ Kg8?? 13. Nh6+ Kh8 14. Qg8+!! Rxg8 15. Nf7#. Po 13. Nh6+ i po 14. Qg8+ czarne mają tylko jeden legalny ruch.
- Format: pionowo 1080×1920, plansza 1080×1080 na środku (y 420–1500), czarne tło, 30 kl./s, 18,7 s. Muzyka: audio z `ssstik.io_1795725809290.mp4` od 0 s.
- Tempo: debiut co 0,24 s (1. e4 ląduje w 0,45 s), 10…f6?? w 5,25 s, potem kolejne półruchy w 6,15 · 6,85 · 7,55 · 8,25 · 8,95 · 9,60 · 10,30 (Qg8+!!) · 11,45 · 12,03 s (Nf7#).
- Oceny: ruchy do 6…Be7 to Book, potem Excellent/Best. Dymki mają: 10…f6 (Blunder), 11. Qb3+ (Great), 12…Kg8 (Blunder), 13. Nh6+ (Great), 14. Qg8+ (Brilliant). 11…Kh8 to Mistake, 12. Nf7+ to Best. Po 14. Qg8+ skokowy zoom na g8: 1,75× w 10,48 s, 2,2× w 10,76 s, 2,7× w 11,04 s, powrót w 11,30 s.
- Mat: czerwone pole h8, przyciemnienie planszy, po 0,12 s zielona korona przy g1 i czerwona plakietka przy h8.
- 12,1 s: klip z alienem w kwadracie 3×3 pola a3–c5 (405×405 px, w pełni kryjący) do końca filmu.
- Uruchom skrypt poniżej. Jest sprawdzony i daje dokładnie ten film. Przygotowanie: `pip install numpy pillow scipy` i `pip install --only-binary=:all: chess`. Skrypt używa czcionki Inter z `/usr/share/fonts/opentype/inter/`; jeśli jej nie ma, podmień `FONT` i nazwy plików czcionki (np. na DejaVuSans-Bold.ttf).
- Kontrola: `ffprobe` (wideo i audio po 18,7 s), klatki kontrolne w 1,75 s, 5,6 s, 6,3 s, 11,2 s, 12,05 s i 13 s, partia jeszcze raz przez python-chess.
- Raport po polsku: ścieżka pliku, partia, potwierdzenie legalności i mata, czym film różni się od wzoru.

Uruchomienie: `python3 mat_zduszony.py 1000187442.jpg ssstik.io_1795725991721.mp4 ssstik.io_1795725809290.mp4 szachy_mat_zduszony.mp4`

```python
# mat_zduszony.py  -  uzycie:
#   python3 mat_zduszony.py PLANSZA.jpg MEM.mp4 MUZYKA.mp4 szachy_mat_zduszony.mp4
# PLANSZA = zrzut chess.com 1080x2460 z pozycja startowa, MEM = klip z alienem (576x576, 6,6 s),
# MUZYKA = filmik, z ktorego bierzemy audio (pierwszy wzor z alienem, 18,7 s).
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import chess

PLANSZA, MEM, MUZYKA, OUT = sys.argv[1:5]
FONT = '/usr/share/fonts/opentype/inter/'          # Inter Bold / SemiBold / ExtraLight
S, TOP = 135, 754                                  # pole 135 px; plansza 1080x1080 od y=754 na zrzucie
LIGHT, DARK = np.array([238, 238, 210.]), np.array([118, 150, 85.])
B = 8 * S
W, H, FPS, DUR = 1080, 1920, 30, 18.7
BY = (H - B) // 2

# ---------------- 1. plansza ze zrzutu + naprawa paska przewijania (zaslanial cyfre 7) ----------------
board = np.array(Image.open(PLANSZA).convert('RGB').crop((0, TOP, B, TOP + B))).astype(float)
board[94:135, 15:27] = LIGHT
board[135:270, 15:27] = DARK
board[270:280, 15:27] = LIGHT
t7 = board[135:180, 0:45]
keep = t7.sum(2) > 500
t7[:, 15:27][~keep[:, 15:27]] = DARK
m = Image.new('L', (360, 360), 0)
dm = ImageDraw.Draw(m)
dm.polygon([(x * 8, y * 8) for x, y in [(9, 13.6), (22.6, 13.6), (22.6, 17), (9, 17)]], fill=255)
dm.polygon([(x * 8, y * 8) for x, y in [(18.4, 16), (22.6, 16), (15.6, 33), (11.2, 33)]], fill=255)
m = np.array(m.resize((45, 45), Image.LANCZOS)).astype(float)[..., None] / 255
board[135:180, 0:45] = np.maximum(t7 * (1 - m) + np.array([192, 207, 164.]) * m, t7 * keep[..., None])

def sq_xy(n):
    return (ord(n[0]) - 97) * S, (8 - int(n[1])) * S

def sq_color(n):            # a1 ciemne: jasne gdy (kolumna 0-7 + rzad 1-8) parzyste
    return LIGHT if ((ord(n[0]) - 97) + int(n[1])) % 2 == 0 else DARK

START = {}
for i, f in enumerate('abcdefgh'):
    START[f + '1'], START[f + '2'] = 'w' + 'RNBQKBNR'[i], 'wP'
    START[f + '7'], START[f + '8'] = 'bP', 'b' + 'RNBQKBNR'[i]

# ---------------- 2. wyciecie figur (matting) + pusta plansza z etykietami ----------------
empty, SPR = board.copy(), {}
for n, p in START.items():
    x, y = sq_xy(n)
    tile, bg = board[y:y + S, x:x + S], sq_color(n)
    d = np.sqrt(((tile - bg) ** 2).sum(2))
    lab, k = ndimage.label(d > 35)
    piece = ndimage.binary_fill_holes(lab == np.argmax(ndimage.sum(d > 35, lab, range(1, k + 1))) + 1)
    inner = ndimage.binary_erosion(piece, iterations=2)
    band = ndimage.binary_dilation(piece, iterations=2) & ~inner
    a = np.where(inner, 1.0, np.where(band, np.clip(d / np.linalg.norm(np.array([55, 55, 55.]) - bg), 0, 1), 0.0))
    rgb = np.where(inner[..., None], tile, np.clip(bg + (tile - bg) / np.maximum(a, 1e-3)[..., None], 0, 255))
    SPR.setdefault(p, (rgb, a))
    empty[y:y + S, x:x + S][ndimage.binary_dilation(piece, iterations=3)] = bg
LABEL = {f + str(r): (np.sqrt(((empty[sq_xy(f + str(r))[1]:sq_xy(f + str(r))[1] + S, sq_xy(f + str(r))[0]:sq_xy(f + str(r))[0] + S]
                               - sq_color(f + str(r))) ** 2).sum(2)) > 35)[..., None] for f in 'abcdefgh' for r in range(1, 9)}

def blend(img, sprite, x, y):
    rgb, a = sprite
    x, y = int(round(x)), int(round(y))
    img[y:y + S, x:x + S] = img[y:y + S, x:x + S] * (1 - a[..., None]) + rgb * a[..., None]

def tint(img, n, col, a):     # podswietlenie pola bez zamalowania etykiet wspolrzednych
    x, y = sq_xy(n)
    t = img[y:y + S, x:x + S]
    img[y:y + S, x:x + S] = np.where(LABEL[n], t, t * (1 - a) + np.array(col, float) * a)

# ---------------- 3. wyglad ocen chess.com (podswietlenie, ikona, dymek) ----------------
CLS = {'book': ((213, 164, 125), (168, 136, 101), None), 'best': ((129, 182, 76), (129, 182, 76), None),
       'exc': ((150, 188, 75), (150, 188, 75), None), 'mist': ((255, 164, 89), (255, 164, 89), None),
       'great': ((116, 155, 191), (92, 139, 176), ('Great', (92, 139, 176))),
       'brilliant': ((38, 194, 163), (38, 194, 163), ('Brilliant', (27, 172, 140))),
       'blunder': ((250, 82, 60), (202, 52, 49), ('Blunder', (202, 52, 49)))}

def icon(kind, size=58):
    D, u = size * 4, size * 4 / 100
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 10, D - 4, D - 2), fill=(0, 0, 0, 60))
    d.ellipse((4, 4, D - 4, D - 8), fill=CLS[kind][1] + (255,))
    cx, cy, w = D / 2, D / 2 - 2, (255, 255, 255, 255)
    if kind == 'best':
        d.polygon([(cx + (30 if i % 2 == 0 else 13) * u * math.cos(-math.pi / 2 + i * math.pi / 5),
                    cy + (30 if i % 2 == 0 else 13) * u * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)], fill=w)
    elif kind == 'book':
        for s in (-1, 1):
            d.polygon([(cx + s * 30 * u, cy - 18 * u), (cx + s * 3 * u, cy - 13 * u), (cx + s * 3 * u, cy + 24 * u), (cx + s * 30 * u, cy + 19 * u)], fill=w)
    elif kind == 'exc':
        d.rounded_rectangle((cx - 28 * u, cy - 4 * u, cx - 16 * u, cy + 26 * u), radius=2 * u, fill=w)
        d.rounded_rectangle((cx - 12 * u, cy - 6 * u, cx + 26 * u, cy + 26 * u), radius=7 * u, fill=w)
        d.polygon([(cx - 12 * u, cy - 2 * u), (cx - 2 * u, cy - 28 * u), (cx + 8 * u, cy - 26 * u), (cx + 6 * u, cy - 4 * u)], fill=w)
        d.ellipse((cx - 6 * u, cy - 34 * u, cx + 10 * u, cy - 20 * u), fill=w)
    else:
        txt = {'great': '!', 'brilliant': '!!', 'mist': '?', 'blunder': '??'}[kind]
        f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(D * (0.62 if len(txt) == 1 else 0.5)))
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=w)
    return im.resize((size, size), Image.LANCZOS)

def pill(kind, h=58):
    name, col = CLS[kind][2]
    f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(h * 0.58) * 3)
    bb = f.getbbox(name)
    pw, ph = bb[2] - bb[0] + int(h * 0.95) * 3, h * 3
    im = Image.new('RGBA', (pw + 24, ph + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12, 18, 12 + pw, 18 + ph), radius=ph / 2, fill=(0, 0, 0, 45))
    d.rounded_rectangle((12, 12, 12 + pw, 12 + ph), radius=ph / 2, fill=(250, 250, 250, 255))
    d.text((12 + (pw - (bb[2] - bb[0])) / 2 - bb[0], 12 + (ph - (bb[3] - bb[1])) / 2 - bb[1]), name, font=f, fill=col + (255,))
    return im.resize((im.width // 3, im.height // 3), Image.LANCZOS)

ICON = {k: icon(k) for k in CLS}
PILL = {k: pill(k) for k in CLS if CLS[k][2]}

def end_badge(kind, size=58):     # zielona korona (zwyciezca) / czerwona plakietka z przewroconym krolem
    im = Image.new('RGBA', (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == 'crown':
        D = size * 4
        d.ellipse((0, 0, D - 1, D - 1), fill=(129, 182, 76, 255))
        w = D * .58; cx, cy = D / 2, D / 2 + D * .02; h = w * .72
        x0, x1, yb, yt = cx - w / 2, cx + w / 2, cy + h * .42, cy - h * .30
        d.polygon([(x0 + w * .06, yb - h * .16), (x0, yt), (x0 + w * .3, cy + h * .02), (cx, yt - h * .12),
                   (x1 - w * .3, cy + h * .02), (x1, yt), (x1 - w * .06, yb - h * .16)], fill=(255, 255, 255, 255))
        d.rounded_rectangle((x0 + w * .06, yb - h * .2, x1 - w * .06, yb), radius=w * .05, fill=(255, 255, 255, 255))
        return im.resize((size, size), Image.LANCZOS)
    d.ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=(222, 108, 118, 255))
    im = im.resize((size, size), Image.LANCZOS)
    rgb, a = SPR['bK']
    k = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').rotate(-80, resample=Image.BICUBIC, expand=True)
    k = k.crop(k.getbbox()); k.thumbnail((int(size * .74),) * 2, Image.LANCZOS)
    im.alpha_composite(k, ((size - k.width) // 2, (size - k.height) // 2 + 2))
    return im

CROWN, MATE = end_badge('crown'), end_badge('mate')

# ---------------- 4. partia + os czasu (sekunda wyladowania kazdego polruchu) ----------------
SAN = ("e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 Re1 Nd6 Nxe5 Be7 Bxc6 dxc6 c3 O-O d4 Nf5 Nd2 f6 "
       "Qb3+ Kh8 Nf7+ Kg8 Nh6+ Kh8 Qg8+ Rxg8 Nf7#").split()
KIND = ['book'] * 12 + ['exc', 'best', 'exc', 'best', 'best', 'exc', 'best', 'blunder',
                       'great', 'mist', 'best', 'blunder', 'great', 'best', 'brilliant', 'best', 'best']
LAND = [0.45 + 0.24 * i for i in range(19)] + [5.25, 6.15, 6.85, 7.55, 8.25, 8.95, 9.60, 10.30, 11.45, 12.03]
SLIDE = [0.14] * 19 + [0.2] * 5 + [0.18, 0.18, 0.26, 0.2, 0.2]
PILL_ON = {19, 20, 23, 24, 26}                       # f6?? Qb3+ Kg8?? Nh6+ Qg8+!!
ZOOMS, ZOOM_END, ZOOM_C = [(10.48, 1.75), (10.76, 2.2), (11.04, 2.7)], 11.30, (0.8125, 0.0625)   # zoom na g8
MATE_T, CLIP_T, CLIP_SQ = LAND[-1], 12.10, 'a5'     # mem 3x3 pola a3-c5, od 12,1 s (jak we wzorze)

b = chess.Board()
EV = []                                             # (wyladowanie, animacja, [(skad, dokad)], pole docelowe, klasa, nr)
for i, s in enumerate(SAN):
    mv = b.parse_san(s)                             # nielegalny ruch = wyjatek
    fr, to = chess.square_name(mv.from_square), chess.square_name(mv.to_square)
    pairs = [(fr, to)]
    if b.is_castling(mv):                            # roszada: krol i wieza jada naraz
        r = to[1]
        pairs.append(('h' + r, 'f' + r) if to[0] == 'g' else ('a' + r, 'd' + r))
    b.push(mv)
    EV.append((LAND[i], SLIDE[i], pairs, to, KIND[i], i))
assert b.is_checkmate() and b.turn == chess.BLACK   # mat, wygraly biale
assert chess.Board(b.fen()).is_valid()

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def pop(t, dur=0.16):
    if t <= 0: return 0.0
    if t >= dur: return 1.0
    u = t / dur
    return 1.15 * math.sin(u * math.pi / 2) if u < .75 else 1.15 - .15 * (u - .75) / .25

def dim(img, k):            # przyciemnienie po macie: odbarwienie 55% + kontrast x1,3 wokol 200
    g = (img * np.array([.299, .587, .114])).sum(2, keepdims=True)
    d = 200 + (g + (img - g) * .45 - 200) * 1.3
    return img * (1 - k) + d * k

def paste_badge(im, bdg, n, sc):
    if sc <= 0: return
    x, y = sq_xy(n)
    bb = bdg.resize((max(2, int(bdg.width * sc)),) * 2, Image.LANCZOS)
    cx, cy = min(x + S - 6, B - bb.width / 2 - 2), max(y + 8, bb.height / 2 + 2)
    im.alpha_composite(bb, (int(cx - bb.width / 2), int(cy - bb.height / 2)))

def frame_board(t):
    pos, last, moving = dict(START), None, None
    for ev in EV:
        if t >= ev[0]:
            for f, q in ev[2]:
                pos[q] = pos.pop(f)
            last = ev
        else:
            if t > ev[0] - ev[1]:
                moving = (ev, (t - (ev[0] - ev[1])) / ev[1])
            break
    img = empty.copy()
    if last:
        tint(img, last[2][0][0], CLS[last[4]][0], .5)
        tint(img, last[2][0][1], CLS[last[4]][0], .5)
    if t >= MATE_T:
        tint(img, 'h8', (214, 82, 88), .78)
    hidden = {f for f, _ in moving[0][2]} if moving else set()
    for n, p in pos.items():
        if n not in hidden:
            blend(img, SPR[p], *sq_xy(n))
    if moving:
        e = ease(moving[1])
        for f, q in moving[0][2]:
            (x0, y0), (x1, y1) = sq_xy(f), sq_xy(q)
            blend(img, SPR[pos[f]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    if t >= MATE_T:
        img = dim(img, ease((t - MATE_T) / .25) * .85)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    if last and (not moving or moving[0][5] != last[5]):
        land, _, _, to, kind, idx = last
        if idx != len(EV) - 1:
            paste_badge(im, ICON[kind], to, pop(t - land))
        if idx in PILL_ON:
            nxt = EV[idx + 1][0] - EV[idx + 1][1]
            a = min(1.0, (t - land) / .08) * min(1.0, max(0.0, (nxt - t) / .08))
            if a > 0:
                p = PILL[kind].copy()
                p.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
                x, y = sq_xy(to)
                px = min(max(x + S * .62, p.width / 2 + 2), B - p.width / 2 - 2)
                py = max(y + 4, p.height / 2 + 2)
                im.alpha_composite(p, (int(px - p.width / 2), int(py - p.height / 2)))
    if t >= MATE_T + .12:
        sc = pop(t - MATE_T - .12, .2)
        paste_badge(im, CROWN, 'g1', sc)
        paste_badge(im, MATE, 'h8', sc)
    return im.convert('RGB')

def zoomed(im, z, cx, cy):   # skokowy zoom: wycinek planszy -> cala plansza, docisniety do krawedzi
    h = .5 / z
    cx, cy = min(max(cx, h), 1 - h), min(max(cy, h), 1 - h)
    return im.resize((B, B), Image.BICUBIC, box=((cx - h) * B, (cy - h) * B, (cx + h) * B, (cy + h) * B))

# ---------------- 5. render -> ffmpeg (pipe), audio z MUZYKI ----------------
cs = 3 * S
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', MEM, '-vf', f'scale={cs}:{cs}:flags=lanczos',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
clip = np.frombuffer(raw, np.uint8).reshape(-1, cs, cs, 3)
ccx, ccy = sq_xy(CLIP_SQ)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', MUZYKA, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                        '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR),
                        '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
frame = np.zeros((H, W, 3), np.uint8)
for fi in range(int(round(DUR * FPS))):
    t = fi / FPS
    im = frame_board(t)
    z = [zz for s0, zz in ZOOMS if s0 <= t < ZOOM_END]
    if z:
        im = zoomed(im, z[-1], *ZOOM_C)
    sq = np.array(im)
    if t < .3:                                         # wejscie z czerni
        sq = (sq * (t / .3)).astype(np.uint8)
    if t >= CLIP_T:                                    # mem od razu po macie
        sq[ccy:ccy + cs, ccx:ccx + cs] = clip[min(int((t - CLIP_T) * FPS), len(clip) - 1)]
    frame[:] = 0
    frame[BY:BY + B] = sq
    enc.stdin.write(frame.tobytes())
enc.stdin.close()
enc.wait()
print('gotowe:', OUT)
```
