# mat_zduszony.py  -  uzycie:
#   python3 mat_zduszony.py PLANSZA.jpg MEM.mp4 MUZYKA.mp4 szachy_mat_zduszony.mp4
# PLANSZA = zrzut chess.com 1080x2460 z pozycja startowa, MEM = klip z alienem (576x576, 6,6 s),
# MUZYKA = filmik, z ktorego bierzemy audio (pierwszy wzor z alienem, 18,7 s).
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import chess

PLANSZA, MEM, MUZYKA, OUT = sys.argv[1:5]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonty', '')   # czcionki z repo (fonty/)
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
