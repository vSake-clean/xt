# edit_magnus.py  -  uzycie:
#   python3 src/edit_magnus.py WZOR.mp4 szachy_edit_magnus.mp4
# Kinowy edit w stylu wzoru 9 (kolaz o Magnusie, 576x576, muzyka do ok. 19,2 s), ale bez zdjec ludzi:
# prawdziwa partia Carlsen - Karjakin, dogrywka MS 2016, partia 4 (Nowy Jork, 30.11.2016), 50. Qh6+!! 1-0.
# Zapis z ChessBase (newsblog-wcc-carlsen-karjakin-2016-11-30), sprawdzony w python-chess.
# Ciecia, bialy blysk i zaciemnienia w tych samych sekundach co we wzorze; plansza zielona ze zrzutu.
import os, sys, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import chess
from assets import S, empty, sprites as SPR, sq_xy, highlight, LIGHT, DARK

WZOR, OUT = sys.argv[1:3]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', '')
B = 8 * S
W, H, FPS = 1080, 1920, 30
DUR = 19.2                                   # we wzorze od 19,2 s jest juz plansza koncowa TikToka
NF = int(round(DUR * FPS))

# ---------------- 1. partia (prawdziwa, z zapisu) ----------------
PGN = """1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. f3 e5 6. Nb3 Be7 7. c4 a5 8. Be3 a4 9. Nc1 O-O 10. Nc3 Qa5
11. Qd2 Na6 12. Be2 Nc5 13. O-O Bd7 14. Rb1 Rfc8 15. b4 axb3 16. axb3 Qd8 17. Nd3 Ne6 18. Nb4 Bc6 19. Rfd1 h5
20. Bf1 h4 21. Qf2 Nd7 22. g3 Ra3 23. Bh3 Rca8 24. Nc2 R3a6 25. Nb4 Ra5 26. Nc2 b6 27. Rd2 Qc7 28. Rbd1 Bf8
29. gxh4 Nf4 30. Bxf4 exf4 31. Bxd7 Qxd7 32. Nb4 Ra3 33. Nxc6 Qxc6 34. Nb5 Rxb3 35. Nd4 Qxc4 36. Nxb3 Qxb3
37. Qe2 Be7 38. Kg2 Qe6 39. h5 Ra3 40. Rd3 Ra2 41. R3d2 Ra3 42. Rd3 Ra7 43. Rd5 Rc7 44. Qd2 Qf6 45. Rf5 Qh4
46. Rc1 Ra7 47. Qxf4 Ra2+ 48. Kh1 Qf2 49. Rc8+ Kh7 50. Qh6+"""
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
assert len(SAN) == 99 and SAN[-1] == 'Qh6+'
assert sorted(b.san(m) for m in b.legal_moves) == ['Kxh6', 'gxh6']          # obie odpowiedzi daja mata w 1
for r, m in (('Kxh6', 'Rh8#'), ('gxh6', 'Rxf7#')):
    c = b.copy(); c.push_san(r); c.push_san(m); assert c.is_checkmate()

# czasy wyladowania polruchow: 92 szybko (0,25-12,6 s), koncowka na basie, 50. Qh6+ na cieciu w 16,0 s
LAND = list(np.linspace(0.25, 12.6, 92)) + [12.9, 13.2, 13.5, 13.84, 14.12, 14.28, 16.0]
assert len(LAND) == len(SAN)
SLIDE = [0.1] * 92 + [0.18] * 6 + [0.3]
QH6 = LAND[-1]

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

def arrow(im, fr, to, col=(255, 170, 0, 205), w=26):     # strzalka jak w chess.com (na planszy, przed kamera)
    (x0, y0), (x1, y1) = [(sq_xy(n)[0] + S / 2, sq_xy(n)[1] + S / 2) for n in (fr, to)]
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    hx, hy = x1 - ux * 52, y1 - uy * 52
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.line((x0 + ux * 30, y0 + uy * 30, hx, hy), fill=col, width=w)
    d.polygon([(x1 - ux * 8, y1 - uy * 8), (hx - uy * 34, hy + ux * 34), (hx + uy * 34, hy - ux * 34)], fill=col)
    im.alpha_composite(lay)

def board_img(t, arrows=0.0):
    k = sum(1 for L in LAND if t >= L)                   # ile polruchow juz wyladowalo
    moving = k if k < len(SAN) and t > LAND[k] - SLIDE[k] else None
    pos = POS[k]
    img = empty.copy()
    if k:
        if k == len(SAN):
            for n in PAIRS[k - 1][0]: tint(img, n, (38, 194, 163), .55)   # Qh6+ w kolorze Brilliant
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
    if t >= QH6:
        u = t - QH6
        sc = 1.15 * math.sin(min(u / .14, 1) * math.pi / 2) if u < .14 else max(1.0, 1.15 - (u - .14))
        ic = ICON.resize((max(2, int(ICON.width * sc)),) * 2, Image.LANCZOS)
        x, y = sq_xy('h6')
        im.alpha_composite(ic, (int(min(x + S - 8, B - ic.width / 2 - 2) - ic.width / 2), int(y + 8 - ic.height / 2 + 6)))
        if u > .25:
            p = PILL.copy(); a = min(1.0, (u - .25) / .1)
            p.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
            im.alpha_composite(p, (int(x - p.width - 4), int(y + S / 2 - p.height / 2)))   # na f6-g6, nie na krolu
    if arrows > 0:
        lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
        arrow(lay, 'c8', 'h8'); arrow(lay, 'f5', 'f7')
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * arrows)))
        im.alpha_composite(lay)
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
SHOTS = [  # od, do, klatki kluczowe kamery, tlo
    (0.00, 1.93, [(0.0, 470, 640, 2.9, -8), (1.93, 540, 560, 2.3, -3)], 'black'),
    (1.93, 3.80, [(1.93, 300, 700, 2.2, 6), (3.8, 340, 520, 1.85, 2)], 'black'),
    (3.80, 5.00, [(3.8, C, C, 0.42, -18), (5.0, C, C, 0.62, 4)], 'stars'),
    (5.00, 7.20, [(5.0, C, C, 1.02, 0), (7.2, C, C, 1.1, -2)], 'black'),
    (7.20, 10.80, [(7.2, 700, 380, 1.75, -28), (9.0, 600, 560, 1.45, 10), (10.8, C, C, 1.25, 22)], 'black'),
    (10.80, 12.00, [(10.8, C, C, 1.0, 0), (12.0, C, C, 0.96, 0)], 'black'),
    (12.00, 14.40, [(12.0, 820, 420, 2.0, 0), (14.4, 840, 430, 2.35, 0)], 'black'),
    (14.40, 16.00, [(14.4, C, C, 0.64, 0), (16.0, C, C, 0.7, 0)], 'frame'),
    (16.00, 17.10, [(16.0, 945, 335, 2.6, -4), (17.1, 900, 360, 2.25, 0)], 'black'),
    (17.10, 19.20, [(17.1, C, C, 1.0, 0), (19.2, C, C, 1.04, 0)], 'black'),
]
FLASH = [(0.0, 0.3, 1.0), (3.67, 0.15, 0.95), (5.0, 0.22, 1.0), (7.2, 0.22, 1.0), (16.0, 0.4, 1.0)]   # bialy: start, czas, sila
DARK_AT = [(3.80, 0.22)]                              # zaciemnienie jak we wzorze
HITS = [1.9, 4.34, 4.64, 4.83, 10.24, 13.84, 14.12, 14.28, 14.98, 16.0]   # bas: wstrzas kamery

CAPS = [  # od, do, tekst (napis na dole, jak we wzorze, tylko wlasny)
    (0.25, 1.85, 'NEW YORK. 30.11.2016'),
    (2.00, 3.60, 'WORLD CHAMPIONSHIP'),
    (3.90, 4.95, 'TIEBREAK. GAME 4.'),
    (5.10, 7.10, 'CARLSEN  vs  KARJAKIN'),
    (7.30, 10.70, '25 MINUTES ON THE CLOCK'),
    (12.10, 14.30, 'HE ONLY NEEDED A DRAW.'),
    (14.50, 15.95, 'HIS BIRTHDAY.'),
    (16.25, 17.05, '50. Qh6+!!'),
    (17.25, 18.10, 'KARJAKIN RESIGNED.'),
    (18.15, 19.20, 'WORLD CHAMPION.'),
]
CAP_FONT = font('Inter-SemiBold.otf', 44)

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
    for txt, f, y, col in (('MAGNUS', BIG1, 820, (255, 214, 74, 255)), ('C A R L S E N', BIG2, 1030, (255, 255, 255, 255))):
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((W / 2 - (bb[2] - bb[0]) / 2 - bb[0] + 4, y + 6), txt, font=f, fill=(0, 0, 0, 170))
        d.text((W / 2 - (bb[2] - bb[0]) / 2 - bb[0], y), txt, font=f, fill=col)
    if scale != 1:
        lay = lay.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
        lay = lay.crop(((lay.width - W) // 2, (lay.height - H) // 2, (lay.width - W) // 2 + W, (lay.height - H) // 2 + H))
    lay.putalpha(lay.getchannel('A').point(lambda v: int(v * a)))
    im.alpha_composite(lay)

def frame(fi):
    t = fi / FPS
    shot = next(s for s in SHOTS if s[0] <= t < s[1] or s is SHOTS[-1])
    cx, cy, z, rot = keys(t, shot[2])
    for h in HITS:                                    # wstrzas na basie
        u = t - h
        if 0 <= u < .3:
            k = (1 - u / .3) ** 2
            cx += 14 * k * math.sin(u * 90); cy += 10 * k * math.cos(u * 70); z *= 1 + .05 * k
    bimg = board_img(t, arrows=ease((t - 17.4) / .3) if t >= 17.4 else 0.0)
    if shot[3] == 'frame':                            # plansza jak portret w zlotej ramce (wzor: zdjecie w ramce)
        fr = Image.new('RGBA', (B + 60, B + 60), (0, 0, 0, 0))
        dd = ImageDraw.Draw(fr)
        dd.rectangle((0, 0, B + 59, B + 59), outline=(196, 158, 74, 255), width=9)
        fr.alpha_composite(bimg, (30, 30))
        bimg = fr; cx += 30; cy += 30
    cam = camera(bimg, cx, cy, z, rot)
    base = Image.fromarray(STARS if shot[3] == 'stars' else np.zeros((H, W, 3), np.uint8)).convert('RGBA')
    base.alpha_composite(cam)
    if 10.8 <= t < 12.0:                              # "MAGNUS": plansza przygaszona, duzy napis
        base = Image.blend(base, Image.new('RGBA', (W, H), (0, 0, 0, 255)), .62)
        title(base, min(1.0, (t - 10.8) / .12), 1.06 - .06 * ease((t - 10.8) / .4))
    for a0, a1, txt in CAPS:
        if a0 <= t < a1:
            caption(base, txt, min(1.0, (t - a0) / .1, (a1 - t) / .1))
    fr = np.array(base.convert('RGB')).astype(float)
    fr = fr * VIGN + GRAIN[fi % len(GRAIN)]
    for s0, d, k in FLASH:
        if s0 <= t < s0 + d: fr = fr + (255 - fr) * k * (1 - (t - s0) / d) ** 2
    for s0, d in DARK_AT:
        if s0 <= t < s0 + d: fr = fr * ((t - s0) / d)
    if t > DUR - .35: fr = fr * max(0.0, (DUR - t) / .35)
    return np.clip(fr, 0, 255).astype(np.uint8)

# ---------------- 4. render, audio ze wzoru (do 19,2 s, wyciszenie na koncu) ----------------
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', WZOR, '-map', '0:v', '-map', '1:a',
                        '-af', f'afade=t=out:st={DUR - 0.5:.2f}:d=0.5', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', f'{NF / FPS:.4f}',
                        '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    enc.stdin.write(frame(fi).tobytes())
enc.stdin.close()
enc.wait()
print('gotowe:', OUT, f'| {len(SAN)} polruchow, 50. Qh6+ w {QH6:.2f} s, {NF / FPS:.1f} s')
