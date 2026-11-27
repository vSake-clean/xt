# kopia_fastest.py  -  uzycie:
#   python3 src/kopia_fastest.py WZOR.mp4 szachy_fastest_checkmate.mp4
# Doslowna kopia wzoru 8 ("MY FASTEST CHECKMATE", 576x576, 9,6 s) na zielonej planszy ze zrzutu:
# te same klatki ruchow, stoper na polach a3-c3, zbicie z zanikajacym hetmanem, smuga za ruchem,
# po macie przyciemnienie z gradientem i duzy napis. Bez dymkow "Winner"/"Checkmate", tylko odznaki.
# Wymiary ze wzoru przeliczone x1,875 (576 -> 1080). Plansza z PLANSZA albo wejscie/plansza.jpg.
import os, sys, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import chess
from assets import S, LIGHT, DARK, empty, sprites as SPR, sq_xy, highlight

WZOR, OUT = sys.argv[1:3]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', '')
W = 8 * S                                   # 1080x1080, jak wzor (kwadrat)
FPS, NF = 30, 288                           # 9,6 s

# ---------------- 1. partia i klatki ruchow (odczytane ze wzoru) ----------------
SAN = "e4 f5 Qh5+ g6 Be2 gxh5 Bxh5#".split()
START_F = [16, 43, 71, 98, 126, 148, 171]   # klatka, w ktorej ruch rusza (pojawia sie podswietlenie)
SLIDE_F = 4                                 # laduje 4 klatki pozniej (ease-out)
assert len(SAN) == len(START_F)
b = chess.Board()
MOVES = []                                  # (start, land, skad, dokad, zbita figura albo None, szach)
for s, f0 in zip(SAN, START_F):
    mv = b.parse_san(s)                     # nielegalny ruch = wyjatek
    cap = b.piece_at(mv.to_square)
    b.push(mv)
    MOVES.append((f0, f0 + SLIDE_F, chess.square_name(mv.from_square), chess.square_name(mv.to_square),
                  ('w' if cap.color else 'b') + cap.symbol().upper() if cap else None, b.is_check()))
assert b.is_checkmate() and b.turn == chess.BLACK   # mat, wygraly biale
MATE_F = START_F[-1]
LOSER, WINNER = 'e8', 'e1'

T_START, T_STOP = 10.3, 171                 # stoper liczy od klatki 10,3 (jak we wzorze), od klatki 171 (start matujacego ruchu) stoi na 00:05.37
DIM_F, LINE2_F, LINE1_F, BADGE_F = 175, 177, 178, 178

START = {}
for i, f in enumerate('abcdefgh'):
    START[f + '1'], START[f + '2'] = 'w' + 'RNBQKBNR'[i], 'wP'
    START[f + '7'], START[f + '8'] = 'bP', 'b' + 'RNBQKBNR'[i]

def sq_color(n):
    return LIGHT if ((ord(n[0]) - 97) + int(n[1])) % 2 == 0 else DARK

def label(n):
    x, y = sq_xy(n)
    return (np.sqrt(((empty[y:y + S, x:x + S] - sq_color(n)) ** 2).sum(2)) > 35)[..., None]

def tint(img, n, col, a):                   # szach: plaski czerwony odcien, etykiety zostaja
    x, y = sq_xy(n)
    t = img[y:y + S, x:x + S]
    img[y:y + S, x:x + S] = np.where(label(n), t, t * (1 - a) + np.array(col, float) * a)

def blend_a(img, piece, x, y, k=1.0):       # figura z dodatkowym kryciem k
    rgb, a = SPR[piece]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + S, W), min(y + S, W)
    if x1 <= x0 or y1 <= y0: return
    aa = a[y0 - y:y1 - y, x0 - x:x1 - x, None] * k
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - aa) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * aa

def prog(f, m):                             # postep ruchu 0..1: we wzorze ok. 0,6 / 0,8 / 0,9 / 0,97 / 1
    u = min(max((f - (m[0] - 1)) / (m[1] - (m[0] - 1)), 0.0), 1.0)
    return 1 - (1 - u) ** 3

# ---------------- 2. przyciemnienie po macie: gradient zmierzony we wzorze ----------------
V = np.array([0.21, 0.32, 0.41, 0.475, 0.52, 0.55, 0.54, 0.51])   # srodki rzedow 8..1
yy = np.arange(W)
Vy = np.interp(yy, S / 2 + S * np.arange(8), V)
Hx = 1 - 0.2 * (np.arange(W) / W) ** 1.5                            # prawa strona ciemniejsza
DIM = (Vy[:, None] * Hx[None, :])[..., None]

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def pop(t, dur=0.2):
    if t <= 0: return 0.0
    if t >= dur: return 1.0
    u = t / dur
    return 1.15 * math.sin(u * math.pi / 2) if u < .75 else 1.15 - .15 * (u - .75) / .25

# ---------------- 3. napisy: stoper (Inter Regular, czarny) i duzy wynik (Inter ExtraBold, zwezony) ----------------
def text_img(txt, font_file, cap_h, width, color, fixed_digits=False):
    probe = ImageFont.truetype(FONT + font_file, 200)
    bb = probe.getbbox('0')
    f = ImageFont.truetype(FONT + font_file, max(8, int(round(200 * cap_h / (bb[3] - bb[1])))))
    adv = max(f.getlength(c) for c in '0123456789')
    ws = [adv if (fixed_digits and c.isdigit()) else f.getlength(c) for c in txt]
    ref = f.getbbox('0' if txt[0].isdigit() else 'M')
    im = Image.new('RGBA', (int(sum(ws)) + 4, ref[3] - ref[1] + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 2
    for c, w in zip(txt, ws):
        d.text((x + (w - f.getlength(c)) / 2, 2 - ref[1]), c, font=f, fill=color)
        x += w
    im = im.crop(im.getbbox())
    return im.resize((width, im.height), Image.LANCZOS)

def timer_txt(f):
    if f < T_START: v = 0
    elif f >= T_STOP: v = 537
    else: v = int(round((f - T_START) / FPS * 100))
    return f'{v // 6000:02d}:{(v // 100) % 60:02d}.{v % 100:02d}'

TIMER = {}                                  # pamiec podreczna: tekst -> obraz
def timer_img(txt):
    if txt not in TIMER:
        TIMER[txt] = text_img(txt, 'Inter-Regular.otf', 58, 323, (0, 0, 0, 255), fixed_digits=True)
    return TIMER[txt]

BIG1 = text_img('00:05.37', 'Inter-ExtraBold.otf', 116, 502, (255, 255, 255, 255), fixed_digits=True)
BIG2 = text_img('MY FASTEST CHECKMATE', 'Inter-ExtraBold.otf', 45, 566, (255, 255, 255, 255))
assert timer_txt(T_STOP) == '00:05.37'

def end_badge(kind, size=56):               # zielona korona (zwyciezca) / czerwona plakietka z krolem
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
    d.ellipse((0, 0, D - 1, D - 1), fill=(202, 52, 49, 255))
    im = im.resize((size, size), Image.LANCZOS)
    rgb, a = SPR['bK']
    k = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').rotate(-80, resample=Image.BICUBIC, expand=True)
    k = k.crop(k.getbbox()); k.thumbnail((int(size * .74),) * 2, Image.LANCZOS)
    im.alpha_composite(k, ((size - k.width) // 2, (size - k.height) // 2 + 2))
    return im

CROWN, MATE = end_badge('crown'), end_badge('mate')

def paste_badge(im, bdg, n, sc):            # odznaka na prawym gornym rogu pola (jak we wzorze)
    if sc <= 0: return
    x, y = sq_xy(n)
    bb = bdg.resize((max(2, int(bdg.width * sc)),) * 2, Image.LANCZOS)
    cx, cy = min(x + S - 10, W - bb.width / 2 - 2), max(y + 8, bb.height / 2 + 2)
    im.alpha_composite(bb, (int(cx - bb.width / 2), int(cy - bb.height / 2)))

# ---------------- 4. klatka ----------------
def frame(f):
    pos, last, moving, fading = dict(START), None, None, None
    for m in MOVES:
        if f >= m[0]:
            last = m
            if f >= m[1]:
                captured = pos.get(m[3])
                pos[m[3]] = pos.pop(m[2])
                if m[4] and f < m[1] + 9:                       # zbita figura gasnie 4-9 klatek po zbiciu
                    fading = (m[3], captured, 1 - min(max((f - (m[1] + 4)) / 5, 0.0), 1.0))
            else:
                moving = m
                if m[4]: fading = (m[3], pos[m[3]], 1.0)
    img = empty.copy()
    if last:
        highlight(img, last[2]); highlight(img, last[3])
        if last[5]:                                            # szach od chwili ruszenia figury
            tint(img, LOSER, (230, 100, 100), .72)
    for n, p in pos.items():
        if moving and n == moving[2]: continue
        if fading and n == fading[0]:
            if moving and moving[3] == n: continue
            blend_a(img, fading[1], *sq_xy(n), fading[2])     # zbita pod spodem, potem zwyciezca
        blend_a(img, p, *sq_xy(n))
    if moving:
        if fading: blend_a(img, fading[1], *sq_xy(fading[0]))
        piece = pos[moving[2]]
        (x0, y0), (x1, y1) = sq_xy(moving[2]), sq_xy(moving[3])
        e_prev, e = prog(f - 1.5, moving), prog(f, moving)
        acc = np.zeros_like(img)                               # smuga za figura: srednia z 24 polozen
        for t in np.linspace(e_prev, e, 24):
            tmp = img.copy()
            blend_a(tmp, piece, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            acc += tmp
        img = acc / 24
        blend_a(img, piece, x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)   # sama figura pelna, na czele smugi
    if f >= BADGE_F:                                           # odznaki pod przyciemnieniem, jak we wzorze
        bim = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
        sc = pop((f - BADGE_F) / FPS)
        paste_badge(bim, CROWN, WINNER, sc)
        paste_badge(bim, MATE, LOSER, sc)
        img = np.array(bim.convert('RGB')).astype(float)
    if f >= DIM_F:
        k = ease((f - DIM_F) / 6)
        img = img * (1 - k + k * DIM)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    t = timer_img(timer_txt(f))
    im.alpha_composite(t, (37, 711))
    if f >= LINE1_F:
        im.alpha_composite(BIG1, ((W - BIG1.width) // 2, 514))
    if f >= LINE2_F:
        im.alpha_composite(BIG2, ((W - BIG2.width) // 2, 649))
    return np.array(im.convert('RGB'))

# ---------------- 5. render -> ffmpeg, audio ze wzoru ----------------
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{W}',
                        '-r', str(FPS), '-i', '-', '-i', WZOR, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                        '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-t', f'{NF / FPS:.4f}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    enc.stdin.write(frame(fi).tobytes())
enc.stdin.close()
enc.wait()
print('gotowe:', OUT, f'| mat od klatki {MATE_F} ({MATE_F / FPS:.2f} s), stoper {timer_txt(T_STOP)}, {NF / FPS:.1f} s')
