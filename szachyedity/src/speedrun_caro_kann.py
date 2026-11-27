# speedrun_caro_kann.py  -  uzycie:
#   python3 src/speedrun_caro_kann.py PLANSZA.jpg MEM.mp4 MUZYKA.mp4 szachy_caro_kann_speedrun.mp4
# Mat w 6 ruchach w Caro-Kann (mat zduszony skoczkiem na d6), stoper nad plansza, oceny jak w Game Review,
# klip z alienem po macie. Muzyka z pierwszego wzoru od 6,47 s, tak zeby mat wypadl na dropie (12,07 s wzoru),
# a alien wszedl w tej samej chwili muzyki co we wzorze (12,1 s). Pionowo 1080x1920, 30 kl./s.
import os, sys, math, subprocess
PLANSZA, MEM, MUZYKA, OUT = sys.argv[1:5]
os.environ['PLANSZA'] = PLANSZA
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import chess
from assets import S, LIGHT, DARK, empty, sprites as SPR, sq_xy, blend

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', '')
B = 8 * S
W, H, FPS = 1080, 1920, 30
BY = (H - B) // 2                                   # plansza y 420-1500

# ---------------- 1. partia i os czasu ----------------
SAN = "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Nd7 Qe2 Ngf6 Nd6#".split()
KIND = ['book'] * 9 + ['blunder', 'best']
WZ = [6.92, 7.36, 7.78, 8.22, 8.64, 9.07, 9.50, 9.93, 10.36, 11.05, 12.03]   # wyladowania w czasie wzoru (bas)
OFF = 6.47                                          # od tej sekundy wzoru leci muzyka
LAND = [round(w - OFF, 3) for w in WZ]              # 0.45 ... 5.56 s filmu
SLIDE = [0.14] * 9 + [0.2, 0.22]
PILL_ON = {9}                                       # Ngf6??
MATE_T = LAND[-1]
CLIP_T = round(12.10 - OFF, 3)                      # 5.63 s: alien w tej samej chwili muzyki co we wzorze
CLIP_SQ = 'a5'                                      # 3x3 pola a3-c5 (puste w pozycji koncowej)
DUR = round(18.70 - OFF, 3)                         # do konca wzoru = do konca klipu (12,23 s)
assert len(SAN) == len(KIND) == len(LAND) == len(SLIDE)

b = chess.Board()
EV = []
for i, s in enumerate(SAN):
    mv = b.parse_san(s)                             # nielegalny ruch = wyjatek
    fr, to = chess.square_name(mv.from_square), chess.square_name(mv.to_square)
    b.push(mv)
    EV.append((LAND[i], SLIDE[i], fr, to, KIND[i], i))
assert b.is_checkmate() and b.turn == chess.BLACK   # mat, wygraly biale
assert b.king(chess.BLACK) == chess.E8 and b.piece_at(chess.D6) == chess.Piece(chess.KNIGHT, chess.WHITE)
assert all(b.piece_at(chess.parse_square(f + r)) is None for f in 'abc' for r in '345')   # miejsce na klip
LOSER, WINNER = 'e8', 'e1'

START = {}
for i, f in enumerate('abcdefgh'):
    START[f + '1'], START[f + '2'] = 'w' + 'RNBQKBNR'[i], 'wP'
    START[f + '7'], START[f + '8'] = 'bP', 'b' + 'RNBQKBNR'[i]

def sq_color(n):
    return LIGHT if ((ord(n[0]) - 97) + int(n[1])) % 2 == 0 else DARK

LABEL = {}
for f in 'abcdefgh':
    for r in range(1, 9):
        n = f + str(r); x, y = sq_xy(n)
        LABEL[n] = (np.sqrt(((empty[y:y + S, x:x + S] - sq_color(n)) ** 2).sum(2)) > 35)[..., None]

def tint(img, n, col, a):     # podswietlenie pola bez zamalowania etykiet wspolrzednych
    x, y = sq_xy(n)
    t = img[y:y + S, x:x + S]
    img[y:y + S, x:x + S] = np.where(LABEL[n], t, t * (1 - a) + np.array(col, float) * a)

# ---------------- 2. wyglad Game Review (jak w mat_zduszony.py) ----------------
CLS = {'book': ((213, 164, 125), (168, 136, 101), None), 'best': ((129, 182, 76), (129, 182, 76), None),
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
    else:
        f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(D * 0.5))
        bb = d.textbbox((0, 0), '??', font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), '??', font=f, fill=w)
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

def end_badge(kind, size=58):     # zielona korona (zwyciezca) / czerwona plakietka z krolem
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

CROWN, MATE = end_badge('crown'), end_badge('mate')

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
            pos[ev[3]] = pos.pop(ev[2])
            last = ev
        else:
            if t > ev[0] - ev[1]:
                moving = (ev, (t - (ev[0] - ev[1])) / ev[1])
            break
    img = empty.copy()
    if last:
        tint(img, last[2], CLS[last[4]][0], .5)
        tint(img, last[3], CLS[last[4]][0], .5)
    if t >= MATE_T:
        tint(img, LOSER, (214, 82, 88), .78)
    hidden = {moving[0][2]} if moving else set()
    for n, p in pos.items():
        if n not in hidden:
            blend(img, *SPR[p], *sq_xy(n))
    if moving:
        e = ease(moving[1])
        (x0, y0), (x1, y1) = sq_xy(moving[0][2]), sq_xy(moving[0][3])
        blend(img, *SPR[pos[moving[0][2]]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
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
        paste_badge(im, CROWN, WINNER, sc)
        paste_badge(im, MATE, LOSER, sc)
    return im.convert('RGB')

# ---------------- 3. stoper nad plansza (Inter ExtraLight, cyfry o stalej szerokosci) ----------------
TW, TH, TCY = 470, 150, 290                          # ramka 470x150, srodek y=290 (nad plansza)
def _tf(sz):
    f = ImageFont.truetype(FONT + 'Inter-ExtraLight.otf', sz)
    a = max(f.getlength(c) for c in '0123456789')
    return f, a, 6 * a + f.getlength(':') + f.getlength('.')
for _sz in range(160, 20, -1):
    TFONT, ADV, _w = _tf(_sz)
    if _w <= TW - 70: break
GREY, GREEN = np.array([38, 37, 34.]), np.array([129, 182, 76.])

def timer_img(secs, k):                             # k: 0 = szary, 1 = zielony (po macie)
    ss = 2
    im = Image.new('RGBA', (TW * ss, TH * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = tuple(int(v) for v in GREY * (1 - k) + GREEN * k) + (255,)
    d.rounded_rectangle((0, 0, TW * ss - 1, TH * ss - 1), radius=22 * ss, fill=col)
    im = im.resize((TW, TH), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    cs = int(secs * 100)
    txt = f'{cs // 6000:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}'
    widths = [ADV if c.isdigit() else TFONT.getlength(c) for c in txt]
    x = TW / 2 - sum(widths) / 2
    bb = TFONT.getbbox('0')
    y = TH / 2 - (bb[1] + bb[3]) / 2
    for c, w in zip(txt, widths):
        d.text((x + (w - TFONT.getlength(c)) / 2, y), c, font=TFONT, fill=(255, 255, 255, 255))
        x += w
    return im

# ---------------- 4. render -> ffmpeg (pipe), audio z MUZYKI od OFF ----------------
cs = 3 * S
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', MEM, '-vf', f'scale={cs}:{cs}:flags=lanczos',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
clip = np.frombuffer(raw, np.uint8).reshape(-1, cs, cs, 3)
ccx, ccy = sq_xy(CLIP_SQ)
NF = int(round(DUR * FPS))
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-ss', str(OFF), '-i', MUZYKA, '-map', '0:v', '-map', '1:a',
                        '-af', 'afade=t=in:st=0:d=0.12', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{NF / FPS:.4f}',
                        '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    t = fi / FPS
    frame = Image.new('RGB', (W, H), (0, 0, 0))
    frame.paste(frame_board(t), (0, BY))
    k = ease((t - MATE_T) / .15) if t >= MATE_T else 0.0
    tm = timer_img(min(t, MATE_T), k)
    sc = 1 + .08 * math.sin(math.pi * min(1.0, (t - MATE_T) / .3)) if t >= MATE_T else 1.0
    if sc != 1.0:
        tm = tm.resize((int(TW * sc), int(TH * sc)), Image.LANCZOS)
    frame.paste(tm, ((W - tm.width) // 2, TCY - tm.height // 2), tm)
    fr = np.array(frame)
    if t >= CLIP_T:                                   # mem od razu po macie, do konca filmu
        fr[BY + ccy:BY + ccy + cs, ccx:ccx + cs] = clip[min(int((t - CLIP_T) * FPS), len(clip) - 1)]
    if t < .3:                                        # wejscie z czerni
        fr = (fr * (t / .3)).astype(np.uint8)
    enc.stdin.write(fr.tobytes())
enc.stdin.close()
enc.wait()
print('gotowe:', OUT, f'| mat {MATE_T:.2f} s, klip {CLIP_T:.2f} s, dlugosc {NF / FPS:.2f} s')
