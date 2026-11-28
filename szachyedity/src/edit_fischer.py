# edit_fischer.py  -  uzycie:
#   python3 src/edit_fischer.py WZOR.mp4 szachy_edit_fischer.mp4 [katalog_zdjec]
# Kinowy edit-kolaz o Bobbym Fischerze w stylu wzoru 10 (zimna wojna, lalkarze; muzyka do ok. 19,4 s, potem plansza TikToka).
# Partia: Fischer - Spasski, Reykjavik 1972, partia 6 (zapis z ChessBase), 38. Rxf6!! ... 41. Qf4 1-0, sprawdzona w python-chess.
# Bez napisow (zasada uzytkownika). Zdjecia z artykulow ChessBase/Chess.com (prasowe, nie do repo; src/pobierz_zdjecia.py).
import os, sys, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import chess
from assets import S, empty, sprites as SPR, sq_xy, highlight, LIGHT, DARK

WZOR, OUT = sys.argv[1:3]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', '')
B = 8 * S
W, H, FPS = 1080, 1920, 30
DUR = 19.4                                   # we wzorze od ok. 19,47 s jest juz plansza koncowa TikToka
NF = int(round(DUR * FPS))

# ---------------- 1. partia (prawdziwa, z zapisu) ----------------
PGN = """1. c4 e6 2. Nf3 d5 3. d4 Nf6 4. Nc3 Be7 5. Bg5 O-O 6. e3 h6 7. Bh4 b6 8. cxd5 Nxd5 9. Bxe7 Qxe7 10. Nxd5 exd5
11. Rc1 Be6 12. Qa4 c5 13. Qa3 Rc8 14. Bb5 a6 15. dxc5 bxc5 16. O-O Ra7 17. Be2 Nd7 18. Nd4 Qf8 19. Nxe6 fxe6 20. e4 d4
21. f4 Qe7 22. e5 Rb8 23. Bc4 Kh8 24. Qh3 Nf8 25. b3 a5 26. f5 exf5 27. Rxf5 Nh7 28. Rcf1 Qd8 29. Qg3 Re7 30. h4 Rbb7
31. e6 Rbc7 32. Qe5 Qe8 33. a4 Qd8 34. R1f2 Qe8 35. R2f3 Qd8 36. Bd3 Qe8 37. Qe4 Nf6 38. Rxf6 gxf6 39. Rxf6 Kg8
40. Bc4 Kh8 41. Qf4"""
SAN = [t for t in PGN.split() if not t[0].isdigit()]
b = chess.Board()

def as_dict(bd):
    return {chess.square_name(s): ('w' if p.color else 'b') + p.symbol().upper() for s, p in bd.piece_map().items()}

POS, PAIRS, CHECK = [as_dict(b)], [], [None]
for s in SAN:
    mv = b.parse_san(s)                      # nielegalny ruch = wyjatek
    fr, to = chess.square_name(mv.from_square), chess.square_name(mv.to_square)
    pr = [(fr, to)]
    if b.is_castling(mv):
        r = to[1]
        pr.append(('h' + r, 'f' + r) if to[0] == 'g' else ('a' + r, 'd' + r))
    assert not mv.promotion                  # bicie w przelocie (15...axb3) obsluguja pelne pozycje z POS
    b.push(mv)
    POS.append(as_dict(b)); PAIRS.append(pr)
    CHECK.append(chess.square_name(b.king(b.turn)) if b.is_check() else None)
assert len(SAN) == 81 and SAN[74] == 'Rxf6' and SAN[-1] == 'Qf4'   # 41. Qf4, Spasski sie poddal
assert b.king(chess.WHITE) == chess.G1 and b.king(chess.BLACK) == chess.H8

# 74 polruchy szybko (0,25-14,2 s), 38. Rxf6!! na bialym blysku wzoru (14,53 s), koncowka na basie
LAND = list(np.linspace(0.25, 14.2, 74)) + [14.53, 15.17, 15.88, 16.23, 16.67, 17.0, 17.27]
assert len(LAND) == len(SAN)
SLIDE = [0.12] * 74 + [0.28, 0.2, 0.22, 0.18, 0.2, 0.18, 0.22]
BRIL = 74                                            # indeks 38. Rxf6!! (Brilliant)
END_T = LAND[-1]
WINNER, LOSER = 'g1', 'h8'

# ---------------- 2. wyglad ----------------
def font(name, px):
    return ImageFont.truetype(FONT + name, px)

def tint(img, n, col, a):
    x, y = sq_xy(n)
    t = img[y:y + S, x:x + S]
    sc = LIGHT if ((ord(n[0]) - 97) + int(n[1])) % 2 == 0 else DARK
    lab = (np.sqrt(((empty[y:y + S, x:x + S] - sc) ** 2).sum(2)) > 35)[..., None]
    img[y:y + S, x:x + S] = np.where(lab, t, t * (1 - a) + np.array(col, float) * a)

def blend(img, piece, x, y):
    rgb, a = SPR[piece]
    x, y = int(round(x)), int(round(y))
    img[y:y + S, x:x + S] = img[y:y + S, x:x + S] * (1 - a[..., None]) + rgb * a[..., None]

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3

def brilliant_icon(size=70):
    D = size * 4
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 10, D - 4, D - 2), fill=(0, 0, 0, 60))
    d.ellipse((4, 4, D - 4, D - 8), fill=(38, 194, 163, 255))
    f = font('Inter-Bold.otf', int(D * 0.5))
    bb = d.textbbox((0, 0), '!!', font=f)
    d.text((D / 2 - (bb[2] - bb[0]) / 2 - bb[0], D / 2 - 2 - (bb[3] - bb[1]) / 2 - bb[1]), '!!', font=f, fill=(255, 255, 255, 255))
    return im.resize((size, size), Image.LANCZOS)

def pill(text, col, h=62):
    f = font('Inter-Bold.otf', int(h * 0.58) * 3)
    bb = f.getbbox(text)
    pw, ph = bb[2] - bb[0] + int(h * 0.95) * 3, h * 3
    im = Image.new('RGBA', (pw + 24, ph + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12, 18, 12 + pw, 18 + ph), radius=ph / 2, fill=(0, 0, 0, 45))
    d.rounded_rectangle((12, 12, 12 + pw, 12 + ph), radius=ph / 2, fill=(250, 250, 250, 255))
    d.text((12 + (pw - (bb[2] - bb[0])) / 2 - bb[0], 12 + (ph - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=col + (255,))
    return im.resize((im.width // 3, im.height // 3), Image.LANCZOS)

ICON, PILL = brilliant_icon(), pill('Brilliant', (27, 172, 140))

def end_badge(kind, size=64):                         # zielona korona / czerwona plakietka (jak w chess.com)
    D = size * 4
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == 'crown':
        d.ellipse((0, 0, D - 1, D - 1), fill=(129, 182, 76, 255))
        w = D * .58; cx, cy = D / 2, D / 2 + D * .02; h = w * .72
        x0, x1, yb, yt = cx - w / 2, cx + w / 2, cy + h * .42, cy - h * .30
        d.polygon([(x0 + w * .06, yb - h * .16), (x0, yt), (x0 + w * .3, cy + h * .02), (cx, yt - h * .12),
                   (x1 - w * .3, cy + h * .02), (x1, yt), (x1 - w * .06, yb - h * .16)], fill=(255, 255, 255, 255))
        d.rounded_rectangle((x0 + w * .06, yb - h * .2, x1 - w * .06, yb), radius=w * .05, fill=(255, 255, 255, 255))
        return im.resize((size, size), Image.LANCZOS)
    d.ellipse((0, 0, D - 1, D - 1), fill=(222, 108, 118, 255))
    im = im.resize((size, size), Image.LANCZOS)
    rgb, a = SPR['bK']
    k = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').rotate(-80, resample=Image.BICUBIC, expand=True)
    k = k.crop(k.getbbox()); k.thumbnail((int(size * .74),) * 2, Image.LANCZOS)
    im.alpha_composite(k, ((size - k.width) // 2, (size - k.height) // 2 + 2))
    return im
CROWN, MATEB = end_badge('crown'), end_badge('mate')

def arrow(im, fr, to, col=(255, 170, 0, 205), w=26):     # strzalka jak w chess.com (na planszy, przed kamera)
    (x0, y0), (x1, y1) = [(sq_xy(n)[0] + S / 2, sq_xy(n)[1] + S / 2) for n in (fr, to)]
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    hx, hy = x1 - ux * 52, y1 - uy * 52
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.line((x0 + ux * 30, y0 + uy * 30, hx, hy), fill=col, width=w)
    d.polygon([(x1 - ux * 8, y1 - uy * 8), (hx - uy * 34, hy + ux * 34), (hx + uy * 34, hy - ux * 34)], fill=col)
    im.alpha_composite(lay)

def board_img(t):
    k = sum(1 for L in LAND if t >= L)                   # ile polruchow juz wyladowalo
    moving = k if k < len(SAN) and t > LAND[k] - SLIDE[k] else None
    pos = POS[k]
    img = empty.copy()
    if k:
        if k == BRIL + 1:
            for n in PAIRS[k - 1][0]: tint(img, n, (38, 194, 163), .55)   # Rxf6!! w kolorze Brilliant
        else:
            for n in PAIRS[k - 1][0]: highlight(img, n)
    if CHECK[k]: tint(img, CHECK[k], (214, 82, 88), .78)                 # szach: czerwone pole krola
    hidden = {f for f, _ in PAIRS[moving]} if moving is not None else set()
    for n, p in pos.items():
        if n not in hidden: blend(img, p, *sq_xy(n))
    if moving is not None:
        e = ease_out((t - (LAND[moving] - SLIDE[moving])) / SLIDE[moving])
        for f, q in PAIRS[moving]:
            (x0, y0), (x1, y1) = sq_xy(f), sq_xy(q)
            blend(img, pos[f], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    if LAND[BRIL] <= t < LAND[BRIL + 1] - SLIDE[BRIL + 1]:
        u = t - LAND[BRIL]
        sc = 1.15 * math.sin(min(u / .14, 1) * math.pi / 2) if u < .14 else max(1.0, 1.15 - (u - .14))
        ic = ICON.resize((max(2, int(ICON.width * sc)),) * 2, Image.LANCZOS)
        x, y = sq_xy('f6')
        im.alpha_composite(ic, (int(min(x + S - 8, B - ic.width / 2 - 2) - ic.width / 2), int(y + 8 - ic.height / 2 + 6)))
        if u > .25:
            p = PILL.copy(); a = min(1.0, (u - .25) / .1)
            p.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
            im.alpha_composite(p, (int(x - p.width - 4), int(y + S / 2 - p.height / 2)))   # na f6-g6, nie na krolu
    if t >= END_T + .1:                               # koniec: korona przy Fischerze, czerwona plakietka przy Spasskim
        sc = min(1.0, (t - END_T - .1) / .15)
        for sq, bd in ((WINNER, CROWN), (LOSER, MATEB)):
            bb = bd.resize((max(2, int(bd.width * sc)),) * 2, Image.LANCZOS)
            x, y = sq_xy(sq)
            im.alpha_composite(bb, (int(min(x + S - 8, B - bb.width / 2 - 2) - bb.width / 2), int(max(y + 8, bb.height / 2 + 2) - bb.height / 2)))
    return im

# ---------------- 3. kamera, tlo, ziarno ----------------
rng = np.random.default_rng(7)
STARS = np.zeros((H, W, 3), np.uint8)
for _ in range(900):
    x, y = rng.integers(0, W), rng.integers(0, H)
    v = int(rng.integers(90, 256)); r = int(rng.integers(1, 3))
    STARS[max(0, y - r // 2):y + r, max(0, x - r // 2):x + r] = v
GRAIN = [rng.normal(0, 7, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1) for _ in range(6)]
yy, xx = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.6 * np.clip((np.hypot((xx - W / 2) / W, (yy - H / 2) / H) / 0.62) ** 2.2, 0, 1))[..., None]

def camera(board, cx, cy, z, rot):                   # wycinek planszy -> klatka 1080x1920 (obrot, zoom)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, bb_, d, e = c / z, s / z, -s / z, c / z
    data = (a, bb_, cx - a * W / 2 - bb_ * H / 2, d, e, cy - d * W / 2 - e * H / 2)
    return board.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))

def keys(t, ks):                                     # interpolacja klatek kluczowych (t, cx, cy, z, rot)
    if t <= ks[0][0]: return ks[0][1:]
    for k0, k1 in zip(ks, ks[1:]):
        if t <= k1[0]:
            u = ease((t - k0[0]) / (k1[0] - k0[0]))
            return tuple(a + (bq - a) * u for a, bq in zip(k0[1:], k1[1:]))
    return ks[-1][1:]

C = B / 2
# ---------------- 4. zdjecia (Wikimedia Commons, CC BY-SA; autorzy w ZDJECIA_ZRODLA i w opisie filmu) ----------------
ZDJ = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wejscie', 'zdjecia')
PH = {  # klucz -> plik w wejscie/zdjecia (pobiera src/pobierz_zdjecia.py)
    'rece': 'fischer_rece.jpg', 'usa': 'fischer_tal_usa.jpg', 'spasski': 'fischer_spasski.jpg',
    'autografy': 'fischer_autografy.jpg', 'uscisk': 'fischer_uscisk.jpg', 'usmiech': 'fischer_usmiech.jpg',
    'mlody': 'fischer_mlody.jpg', 'reykjavik': 'fischer_reykjavik_kolor.jpg', 'geller': 'geller_spasski.jpg',
    'idzie': 'fischer_idzie.jpg',
}
import kolaz
def load_ph(key):
    f = os.path.join(ZDJ, PH[key])
    if os.path.exists(f):
        im = Image.open(f).convert('RGB')
        rows = np.nonzero(np.asarray(im.convert('L')).mean(1) > 14)[0]      # obcina czarne pasy (kadr z filmu)
        return im.crop((0, int(rows[0]), im.width, int(rows[-1]) + 1)) if len(rows) else im
    im = Image.new('RGB', (1200, 800), (90, 90, 90)); ImageDraw.Draw(im).text((40, 40), 'BRAK ' + PH[key], fill=(255, 255, 255))
    return im
COLOR = {k: load_ph(k) for k in PH}
PHOTO = {k: kolaz.bw(v, gamma=1.05) for k, v in COLOR.items()}
STICK = None                                           # spadajaca odbitka (usmiechniety Fischer); wycinanka GrabCut
def sticker():                                         # na tych zdjeciach (kurtyna, polki) wychodzila zle
    global STICK
    if STICK is None:
        STICK = kolaz.card(PHOTO['usmiech'], 540, border=16)
    return STICK
HANDS = [(.585, .27), (.665, .30), (.62, .2)]           # dlonie i czolo Fischera na zdjeciu 'rece' (ulamki)

def marionette(base, t, cx, cy, z, rot):              # figury na sznurkach: od gory klatki do czubka kazdej figury
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    k = sum(1 for L in LAND if t >= L)
    d = ImageDraw.Draw(base)
    for i, n in enumerate(sorted(POS[k])):
        bx, by = sq_xy(n); bx += S / 2; by += S * .16
        X = W / 2 + z * (c * (bx - cx) - s_ * (by - cy)); Y = H / 2 + z * (s_ * (bx - cx) + c * (by - cy))
        if not (0 <= X < W and 0 < Y < H): continue
        top = X + 26 * math.sin(t * 1.5 + i * .9)
        d.line((top, 0, X, Y), fill=(245, 245, 240, 215), width=3)

CLOCK_FONT = FONT + 'Inter-SemiBold.otf'

# kinds: board (kamera na planszy), stars (plansza wsrod gwiazd), photo (najazd na zdjecie na caly ekran), clock (zegar +
# plansza-karta + spadajaca wycinanka), title (zdjecie + MAGNUS CARLSEN), framed (odbitka w zlotej ramce),
# card (kolorowa odbitka na rozmytym tle)
PLANSZA_W_EDYCIE = False                               # uzytkownik: edity nie musza miec szachownicy
SHOTS = [  # od, do, rodzaj, parametry (bez planszy: same zdjecia, sznurki, gwiazdy, zegar)
    (0.00, 2.40, 'photostr', ('mlody', [(0.0, .77, .5, 1.0, 0), (2.4, .76, .45, 1.1, 0)], [(.86, .3), (.71, .56), (.93, .52)])),
    (2.40, 4.97, 'cardstr', ('rece', [(2.4, 0, 0, 1.0, -3), (4.97, 0, 0, 1.08, 2)])),
    (5.00, 6.83, 'photo', ('usa', [(5.0, .33, .36, 1.05, 0), (6.83, .42, .68, 1.15, 0)])),
    (6.83, 8.03, 'starcard', ('geller', [(6.83, 0, 0, .7, -16), (8.03, 0, 0, .85, 8)])),
    (8.03, 9.60, 'card', ('spasski', [(8.03, 0, 0, 1.0, 2), (9.6, 0, 0, 1.07, -1)])),
    (9.60, 11.20, 'photo', ('autografy', [(9.6, .4, .45, 1.0, 0), (11.2, .38, .38, 1.15, 0)])),
    (11.20, 12.00, 'photo', ('idzie', [(11.2, .55, .5, 1.0, 0), (12.0, .55, .42, 1.1, 0)])),
    (12.00, 14.53, 'clock', None),
    (14.53, 15.10, 'photo', ('autografy', [(14.53, .43, .27, 2.0, -3), (15.1, .43, .28, 1.8, 0)])),
    (15.10, 17.83, 'card', ('reykjavik', [(15.1, 0, 0, 1.0, -2), (17.83, 0, 0, 1.12, 1)])),
    (17.83, 19.40, 'photo', ('uscisk', [(17.83, .24, .3, 1.12, 0), (18.7, .47, .5, 1.0, 0), (19.4, .5, .52, .98, 0)])),
]
FLASH = [(0.0, 0.3, 1.0), (14.53, 0.45, 1.0), (17.83, 0.18, 0.7)]   # bialy blysk wzoru w 14,53 s
DARK_AT = [(4.97, 0.2), (8.03, 0.15)]                 # ciecia przez czern jak we wzorze
HITS = [1.43, 2.4, 3.87, 4.8, 6.3, 6.93, 8.73, 10.13, 11.17, 12.4, 13.6, 14.53, 15.17, 15.88, 16.67, 17.27]   # akcenty: wstrzas

NAPISY = False                                         # uzytkownik: nigdy nie dodawaj napisow (nikt ich nie czyta)
CAPS = []                                              # zadnych napisow
CREDIT = 'Photos: Chess.com'
CAP_FONT, CRED_FONT = font('Inter-SemiBold.otf', 44), font('Inter-SemiBold.otf', 22)

def caption(im, text, a):
    lay = Image.new('RGBA', (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    sp = 6
    ws = [CAP_FONT.getlength(ch) + sp for ch in text]
    x = W / 2 - (sum(ws) - sp) / 2
    d.rounded_rectangle((x - 26, 26, x + sum(ws) - sp + 26, 110), radius=10, fill=(0, 0, 0, 175))   # pasek jak we wzorze
    for ch, w in zip(text, ws):
        d.text((x + 3, 43), ch, font=CAP_FONT, fill=(0, 0, 0, 200))
        d.text((x, 40), ch, font=CAP_FONT, fill=(255, 255, 255, 255))
        x += w
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    im.alpha_composite(lay, (0, 1600))

BIG1, BIG2 = font('Inter-ExtraBold.otf', 190), font('Inter-SemiBold.otf', 70)
def title(im, a, scale):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for txt, f, y, col in (('MAGNUS', BIG1, 1180, (255, 214, 74, 255)), ('C A R L S E N', BIG2, 1390, (255, 255, 255, 255))):
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((W / 2 - (bb[2] - bb[0]) / 2 - bb[0] + 4, y + 6), txt, font=f, fill=(0, 0, 0, 170))
        d.text((W / 2 - (bb[2] - bb[0]) / 2 - bb[0], y), txt, font=f, fill=col)
    if scale != 1:
        lay = lay.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
        lay = lay.crop(((lay.width - W) // 2, (lay.height - H) // 2, (lay.width - W) // 2 + W, (lay.height - H) // 2 + H))
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    im.alpha_composite(lay)

def shake_cam(t, cx, cy, z, k_px=14):
    for h in HITS:                                    # wstrzas na basie
        u = t - h
        if 0 <= u < .3:
            k = (1 - u / .3) ** 2
            cx += k_px * k * math.sin(u * 90); cy += k_px * .7 * k * math.cos(u * 70); z *= 1 + .05 * k
    return cx, cy, z

def frame(fi):
    t = fi / FPS
    s0, s1, kind, prm = next(s for s in SHOTS if s[0] <= t < s[1] or s is SHOTS[-1])
    base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    if kind in ('board', 'stars', 'strings'):
        cx, cy, z, rot = keys(t, prm)
        cx, cy, z = shake_cam(t, cx, cy, z)
        if kind == 'stars': base = Image.fromarray(STARS).convert('RGBA')
        base.alpha_composite(camera(board_img(t), cx, cy, z, rot))
        if kind == 'strings': marionette(base, t, cx, cy, z, rot)
    elif kind in ('photo', 'title'):
        key, ks = prm
        cx, cy, z, rot = keys(t, ks)
        _, _, z = shake_cam(t, 0, 0, z)
        base = kolaz.cover(PHOTO[key], W, H, cx, cy, z, rot)
        if kind == 'title':
            base = Image.blend(base, Image.new('RGBA', (W, H), (0, 0, 0, 255)), .35)
            if NAPISY: title(base, min(1.0, (t - s0) / .12), 1.06 - .06 * ease((t - s0) / .4))
    elif kind in ('framed', 'card'):                  # odbitka (zlota ramka / kolor) na rozmytym, ciemnym tle
        key, ks = prm
        _, _, z, rot = keys(t, ks)
        src = PHOTO[key] if kind == 'framed' else COLOR[key]
        bg = kolaz.cover(PHOTO[key], W, H, .5, .5, 1.1).filter(ImageFilter.GaussianBlur(18))
        base = Image.blend(bg, Image.new('RGBA', (W, H), (0, 0, 0, 255)), .55)
        c = kolaz.card(src, int(1010 * z), border=14 if kind == 'framed' else 20,
                       col=(196, 158, 74, 255) if kind == 'framed' else (245, 244, 238, 255), rot=rot)
        base.alpha_composite(c, ((W - c.width) // 2, (H - c.height) // 2 - 80))
    elif kind == 'photostr':                          # zdjecie na caly ekran + sznurki od gory do wskazanych punktow
        key, ks, pts = prm
        cx, cy, z, rot = keys(t, ks)
        _, _, z = shake_cam(t, 0, 0, z)
        ph = PHOTO[key]; base = kolaz.cover(ph, W, H, cx, cy, z)
        sc = max(W / ph.width, H / ph.height) * z
        d = ImageDraw.Draw(base)
        for i, (fx, fy) in enumerate(pts):
            X, Y = W / 2 + (fx - cx) * ph.width * sc, H / 2 + (fy - cy) * ph.height * sc
            d.line((X + 40 * math.sin(t * 1.6 + i * 1.4), 0, X, Y), fill=(245, 245, 240, 235), width=5)
            d.ellipse((X - 8, Y - 8, X + 8, Y + 8), fill=(245, 245, 240, 255))
    elif kind == 'starcard':                          # odbitka obracajaca sie wsrod gwiazd (zamiast Ziemi ze wzoru)
        key, ks = prm
        _, _, z, rot = keys(t, ks)
        base = Image.fromarray(STARS).convert('RGBA')
        c = kolaz.card(PHOTO[key], int(900 * z), border=16, rot=rot)
        base.alpha_composite(c, ((W - c.width) // 2, (H - c.height) // 2))
    elif kind == 'cardstr':                           # zdjecie-odbitka zawieszona na sznurkach (lalkarz ze wzoru)
        key, ks = prm
        _, _, z, rot = keys(t, ks)
        bg = kolaz.cover(PHOTO[key], W, H, .5, .5, 1.1).filter(ImageFilter.GaussianBlur(18))
        base = Image.blend(bg, Image.new('RGBA', (W, H), (0, 0, 0, 255)), .6)
        M = 700; lay = Image.new('RGBA', (W, H + M), (0, 0, 0, 0))
        wph = int(1000 * z); c = kolaz.card(PHOTO[key], wph, border=20)
        x0, y0 = (W - c.width) // 2, M + (H - c.height) // 2 - 40
        lay.alpha_composite(c, (x0, y0))
        hph = int(wph * PHOTO[key].height / PHOTO[key].width); px, py = x0 + 50, y0 + 50
        pts = [(px + 10, y0 + 32), (px + wph - 10, y0 + 32)] + [(px + fx * wph, py + fy * hph) for fx, fy in HANDS]
        d = ImageDraw.Draw(lay)
        for i, (qx, qy) in enumerate(pts):
            top = qx + 40 * math.sin(t * 1.7 + i * 1.3)
            d.line((top, 0, qx, qy), fill=(245, 245, 240, 240), width=5)
            d.ellipse((qx - 7, qy - 7, qx + 7, qy + 7), fill=(240, 240, 235, 255))
        lay = lay.rotate(rot + 2.5 * math.sin(t * 2.1), center=(W / 2, y0 + c.height / 2), resample=Image.BICUBIC)
        base.alpha_composite(lay.crop((0, M, W, H + M)))
    elif kind == 'clock':                             # zegar sie kreci, plansza-karta (partia leci), wycinanka spada
        u = (t - s0) / (s1 - s0)
        ck = kolaz.clock_face(1040, t_spin=u * 6, font_file=CLOCK_FONT).rotate(-u * 40, resample=Image.BICUBIC)
        base.alpha_composite(ck, ((W - ck.width) // 2, (H - ck.height) // 2 - 120))
        base = Image.blend(base, Image.new('RGBA', (W, H), (0, 0, 0, 255)), .25)
        if PLANSZA_W_EDYCIE:
            card = Image.new('RGBA', (B + 40, B + 40), (245, 244, 238, 255)); card.alpha_composite(board_img(t), (20, 20))
            card = card.resize((620, 620), Image.LANCZOS).rotate(12 - 24 * ease(u), resample=Image.BICUBIC, expand=True)
            base.alpha_composite(card, ((W - card.width) // 2 + 190, 900 - card.height // 2))
        st = sticker().rotate(-25 + 55 * u, resample=Image.BICUBIC, expand=True)
        base.alpha_composite(st, (int((W - st.width) / 2 - 200 + 330 * u), int(120 + 520 * ease(u))))
    for a0, a1, txt in (CAPS if NAPISY else []):
        if a0 <= t < a1:
            caption(base, txt, min(1.0, (t - a0) / .1, (a1 - t) / .1))
    if NAPISY and t >= 18.3:                          # podpis zrodla zdjec (wylaczony razem z napisami)
        d = ImageDraw.Draw(base); bb = d.textbbox((0, 0), CREDIT, font=CRED_FONT)
        d.text(((W - bb[2]) / 2, 1800), CREDIT, font=CRED_FONT, fill=(220, 220, 220, 255))
    fr = np.array(base.convert('RGB')).astype(float)
    fr = fr * VIGN + GRAIN[fi % len(GRAIN)]
    for f0, d, k in FLASH:
        if f0 <= t < f0 + d: fr = fr + (255 - fr) * k * (1 - (t - f0) / d) ** 2
    for f0, d in DARK_AT:
        if f0 <= t < f0 + d: fr = fr * ((t - f0) / d)
    if t > DUR - .35: fr = fr * max(0.0, (DUR - t) / .35)
    return np.clip(fr, 0, 255).astype(np.uint8)

# ---------------- 5. render, audio ze wzoru (do 19,2 s, wyciszenie na koncu) ----------------
if os.environ.get('PODGLAD'):                          # PODGLAD="1.0,8.5" -> tylko klatki PNG do sprawdzenia
    for ts in os.environ['PODGLAD'].split(','):
        Image.fromarray(frame(int(round(float(ts) * FPS)))).save(f'{OUT}_{ts}.png')
    sys.exit(0)
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', WZOR, '-map', '0:v', '-map', '1:a',
                        '-af', f'afade=t=out:st={DUR - 0.5:.2f}:d=0.5', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{NF / FPS:.4f}',
                        '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    enc.stdin.write(frame(fi).tobytes())
enc.stdin.close()
enc.wait()
print('gotowe:', OUT, f'| {len(SAN)} polruchow, 38. Rxf6!! w {LAND[BRIL]:.2f} s, 41. Qf4 w {END_T:.2f} s, {NF / FPS:.1f} s')
