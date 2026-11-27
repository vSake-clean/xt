"""Cinematic chess edit of Scholar's mate (white wins), synced to the reference music."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from multiprocessing import Pool

import assets as A

S = A.S
BW = 8 * S                  # board size in board coords (1080)
OUT = 1080                  # output video size
FPS = 30
T0 = 6.0           # start of the music segment
END = 20.6         # end of the music segment
DUR = END - T0
NF = int(round(DUR * FPS))
AUDIO = sys.argv[2] if len(sys.argv) > 2 else None
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else 'edit.mp4'
import os
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', '')   # czcionki z repo (fonty/)

# ---------------------------------------------------------------- assets (grayscale look)
def gray3(a):
    g = (a * np.array([0.299, 0.587, 0.114])).sum(2, keepdims=True)
    return np.repeat(g, 3, 2)

_e = gray3(A.empty)
# map light squares ~232 -> 178, dark ~138 -> 92
GBOARD = np.clip(92 + (_e - 138) * (178 - 92) / (232 - 138), 0, 255)
GSPR = {k: (np.clip(gray3(F) * 1.0, 0, 255), al) for k, (F, al) in A.sprites.items()}

def spr_rgba(piece, size=None):
    F, al = GSPR[piece]
    im = Image.fromarray(np.dstack([F, al * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
    return im.resize((size, size), Image.LANCZOS) if size else im

def sqc(name):  # square centre in board coords
    x, y = A.sq_xy(name)
    return x + S / 2, y + S / 2

TEAL, RED, GREEN, BLUE, CYAN, WHITE = (32, 200, 170), (235, 40, 45), (70, 210, 70), (80, 110, 240), (60, 220, 235), (255, 255, 255)

# ---------------------------------------------------------------- badges
def _star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)

_badge_cache = {}
def badge(kind, size):
    size = max(int(size), 12)
    key = (kind, size)
    if key in _badge_cache:
        return _badge_cache[key]
    ss = 4; D = size * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = {'!!': (38, 194, 163), '??': (202, 52, 49), 'star': (129, 182, 76), '!': (92, 139, 176), '#': (202, 52, 49)}[kind]
    d.ellipse((ss, ss * 2, D - ss, D), fill=(0, 0, 0, 90))
    d.ellipse((ss, ss, D - ss, D - ss * 2), fill=col + (255,))
    if kind == 'star':
        _star(d, D / 2, D / 2 - ss * 0.5, D * 0.30, (255, 255, 255, 255))
    else:
        f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(D * (0.48 if len(kind) == 2 else 0.58)))
        bb = d.textbbox((0, 0), kind, font=f)
        d.text(((D - (bb[2] - bb[0])) / 2 - bb[0], (D - ss * 2 - (bb[3] - bb[1])) / 2 - bb[1]), kind, font=f, fill=(255, 255, 255, 255))
    im = im.resize((size, size), Image.LANCZOS)
    _badge_cache[key] = im
    return im

def pill(text, h=44):
    f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(h * 0.62) * 3)
    bb = f.getbbox(text)
    w = (bb[2] - bb[0]) + h * 3 * 0.9
    im = Image.new('RGBA', (int(w), h * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h * 3 - 1), radius=h * 1.5 * 0.6, fill=(245, 245, 245, 255))
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], (h * 3 - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=(20, 20, 20, 255))
    return im.resize((int(w / 3), h), Image.LANCZOS)

PILL_M1 = pill('M1')

# ---------------------------------------------------------------- game
START = dict(A.start)
GAME = [('e2', 'e4'), ('e7', 'e5'), ('f1', 'c4'), ('b8', 'c6'), ('d1', 'h5'), ('g8', 'f6'), ('h5', 'f7')]

def position(n):
    p = dict(START)
    for frm, to in GAME[:n]:
        p[to] = p.pop(frm)
    return p

POS = [position(n) for n in range(len(GAME) + 1)]
FINAL = POS[-1]

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3

def lerp(a, b, t):
    return a + (b - a) * t

# ---------------------------------------------------------------- board frame renderer
def render_board(st):
    """Returns (rgb float array BWxBW, glow float array BWxBW) in board coords."""
    img = GBOARD.copy()
    glow = np.zeros_like(img)
    for sq, col, a in st.get('fills', []):
        if a <= 0: continue
        x, y = A.sq_xy(sq)
        c = np.array(col, float)
        img[y:y + S, x:x + S] = img[y:y + S, x:x + S] * (1 - a * 0.8) + c * a * 0.8
        glow[y:y + S, x:x + S] += c * a * (0.25 if col == WHITE else 0.8)
    pos = st['pos']
    moving = st.get('moving')
    for name, p in pos.items():
        if moving and name == moving[0]:
            continue
        x, y = A.sq_xy(name)
        A.blend(img, *GSPR[p], x, y)
    if moving:
        frm, to, t = moving
        x0, y0 = A.sq_xy(frm); x1, y1 = A.sq_xy(to)
        F, al = GSPR[pos[frm]]
        trail = st.get('trail', 0)
        for k in range(trail, 0, -1):
            tt = max(0.0, t - k * 0.06)
            e = ease(tt)
            A.blend(img, F, al * (0.35 * (1 - k / (trail + 1))), x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
            gx, gy = int(x0 + (x1 - x0) * e), int(y0 + (y1 - y0) * e)
            glow[gy + 20:gy + S - 20, gx + 20:gx + S - 20] += np.array(WHITE) * 0.12 * (1 - k / (trail + 1))
        e = ease(t)
        A.blend(img, F, al, x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    # overlays (arrows, lines, badges) drawn with PIL
    if st.get('arrows') or st.get('badges') or st.get('pills') or st.get('lines'):
        base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
        gl = Image.new('L', (BW, BW), 0)
        ov = Image.new('RGBA', (BW, BW), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov); dg = ImageDraw.Draw(gl)
        for frm, to, a, col in st.get('lines', []):
            p0, p1 = sqc(frm), sqc(to)
            d.line([p0, p1], fill=col + (int(220 * a),), width=14)
            dg.line([p0, p1], fill=int(255 * a), width=30)
        for frm, to, a in st.get('arrows', []):
            (x0, y0), (x1, y1) = sqc(frm), sqc(to)
            ang = math.atan2(y1 - y0, x1 - x0)
            L = math.hypot(x1 - x0, y1 - y0) - 30
            ex, ey = x0 + L * math.cos(ang), y0 + L * math.sin(ang)
            hx, hy = ex - 46 * math.cos(ang), ey - 46 * math.sin(ang)
            nx, ny = -math.sin(ang), math.cos(ang)
            head = [(ex, ey), (hx + 34 * nx, hy + 34 * ny), (hx - 34 * nx, hy - 34 * ny)]
            dg.line([(x0, y0), (hx, hy)], fill=int(255 * a), width=48)
            dg.polygon(head, fill=int(255 * a))
            d.line([(x0, y0), (hx, hy)], fill=(15, 15, 15, int(255 * a)), width=22)
            d.polygon(head, fill=(15, 15, 15, int(255 * a)))
        for sq, kind, sc in st.get('badges', []):
            if sc <= 0: continue
            sz = max(2, int(54 * sc))
            b = badge(kind, sz)
            x, y = A.sq_xy(sq)
            cx, cy = x + S - 10, y + 12
            ov.alpha_composite(b, (int(cx - sz / 2), int(cy - sz / 2)))
        for sq, im, a in st.get('pills', []):
            if a <= 0: continue
            x, y = A.sq_xy(sq)
            pi = im.copy(); pi.putalpha(pi.getchannel('A').point(lambda v: int(v * a)))
            ov.alpha_composite(pi, (int(x + S / 2 - pi.width / 2), int(y - pi.height / 2 + 6)))
            dg.rounded_rectangle((x + S / 2 - pi.width / 2 - 6, y + 6 - pi.height / 2 - 6, x + S / 2 + pi.width / 2 + 6, y + 6 + pi.height / 2 + 6), radius=20, fill=int(200 * a))
        base.alpha_composite(ov)
        img = np.array(base.convert('RGB')).astype(float)
        glow += np.array(gl)[..., None].astype(float) * 0.30
    return img, glow

def camera_warp(arr, cx, cy, z, rot, fill=0):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    # output (u,v) -> board: p = C + R(-th) * ((u-OUT/2, v-OUT/2)/z)
    a, b = c / z, s / z
    d, e = -s / z, c / z
    cc = cx - a * OUT / 2 - b * OUT / 2
    f = cy - d * OUT / 2 - e * OUT / 2
    return np.array(im.transform((OUT, OUT), Image.AFFINE, (a, b, cc, d, e, f), resample=Image.BICUBIC, fillcolor=(fill, fill, fill))).astype(float)

def bloom(glow, strength):
    if strength <= 0 or glow.max() <= 0:
        return 0
    small = Image.fromarray(np.clip(glow, 0, 255).astype(np.uint8)).resize((OUT // 4, OUT // 4), Image.BILINEAR)
    b1 = np.array(small.filter(ImageFilter.GaussianBlur(4)).resize((OUT, OUT), Image.BILINEAR)).astype(float)
    b2 = np.array(small.filter(ImageFilter.GaussianBlur(12)).resize((OUT, OUT), Image.BILINEAR)).astype(float)
    return (b1 * 0.45 + b2 * 0.6) * strength

yy, xx = np.mgrid[0:OUT, 0:OUT]
VIGNETTE = (1 - 0.55 * np.clip((np.hypot(xx - OUT / 2, yy - OUT / 2) / (OUT * 0.72)) ** 2, 0, 1))[..., None]

# ---------------------------------------------------------------- timeline
BEAT = 0.6655
L = [6.45, 6.95, 7.45, 7.95, 8.5, 9.03, 10.63]   # landing times of the 7 half-moves
SLIDE = [0.22, 0.22, 0.22, 0.22, 0.26, 0.22, 0.2]
DROP = 10.63

CAM_INTRO = [  # t, cx, cy, zoom, rot
    (6.00, 540, 600, 0.80, -30), (6.95, 540, 560, 0.98, -20), (7.95, 430, 480, 1.12, -6),
    (8.50, 760, 440, 1.30, 8), (9.03, 760, 330, 1.55, 16), (9.60, 740, 250, 1.80, 20),
    (10.45, 742, 205, 2.9, 27), (10.63, 742, 205, 3.1, 28)]

def interp_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for k0, k1 in zip(keys, keys[1:]):
        if t <= k1[0]:
            u = ease((t - k0[0]) / (k1[0] - k0[0]))
            return tuple(lerp(a, b, u) for a, b in zip(k0[1:], k1[1:]))
    return keys[-1][1:]

def game_state(t):
    """position / moving piece / last move for the real-time game in the intro."""
    n = sum(1 for l in L if t >= l)
    st = {'pos': POS[n]}
    if n < len(GAME) and t > L[n] - SLIDE[n]:
        st['moving'] = (GAME[n][0], GAME[n][1], (t - (L[n] - SLIDE[n])) / SLIDE[n])
        st['pos'] = POS[n]
    return st, n

def pulse(t, period=BEAT, lo=0.55, hi=1.0, phase=0.0):
    return lo + (hi - lo) * (0.5 + 0.5 * math.cos(2 * math.pi * (t - phase) / period))

def pop(t, dur=0.18):
    if t <= 0: return 0.0
    if t >= dur: return 1.0
    u = t / dur
    return 1.18 * math.sin(u * math.pi / 2) if u < 0.75 else 1.18 - 0.18 * (u - 0.75) / 0.25

def final_decor(t, k_e8=1.0, k_f7=1.0, k_c4=0.0, badges=True):
    fills = [('f7', TEAL, 0.85 * k_f7), ('e8', RED, 0.85 * k_e8 * pulse(t, lo=0.65))]
    if k_c4: fills.append(('c4', CYAN, 0.6 * k_c4))
    b = [('f7', '!!', 1.0), ('e8', '#', 1.0)] if badges else []
    return {'pos': FINAL, 'fills': fills, 'badges': b}

# shot list after the drop: (start, type)
SHOTS = []
for i, kind in enumerate(['queen', 'wide', 'king', 'replay', 'void', 'bishop']):
    SHOTS.append((DROP + i * 2 * BEAT, kind))
ENDING = DROP + 6 * 2 * BEAT          # ~18.62
SHOTS.append((ENDING, 'ending'))
SECOND = 99.0
FLASHES = [DROP, DROP + 8 * BEAT, ENDING]
HITS = [DROP] + [DROP + i * 2 * BEAT for i in range(1, 7)]

def shot_at(t):
    cur = None
    for i, (s, k) in enumerate(SHOTS):
        if t >= s:
            cur = (i, s, k)
    return cur

def shake(t):
    amp = 0.0
    for h in HITS:
        if 0 <= t - h < 0.45:
            amp = max(amp, (1 - (t - h) / 0.45) ** 2 * (26 if h in (DROP, SECOND) else 12))
    return amp * math.sin(t * 91.0), amp * math.cos(t * 77.0), amp * 0.12 * math.sin(t * 53.0)

# ---------------------------------------------------------------- void scenes (piece on black)
QUEEN_BIG = spr_rgba('wQ', 520)
KING_BIG = spr_rgba('bK', 300).rotate(-80, resample=Image.BICUBIC, expand=True)

def void_scene(u, t, mode):
    """u: progress 0..1 inside the shot."""
    canvas = Image.new('RGB', (OUT, OUT), (0, 0, 0))
    glow = Image.new('RGB', (OUT, OUT), (0, 0, 0))
    if mode == 'void':
        z = lerp(1.0, 1.12, u)
        sz = int(520 * z)
        q = QUEEN_BIG.resize((sz, sz), Image.LANCZOS)
        bg = Image.new('RGB', (OUT, OUT), (16, 120, 104))
        canvas = Image.blend(canvas, bg, 0.9)
        canvas.paste(q, (OUT // 2 - sz // 2 - 60, OUT // 2 - sz // 2 + 40), q)
        b = badge('!!', int(260 * z * pop(u * 1.33, 0.25) if u < 0.75 else 260 * z))
        canvas.paste(b, (OUT // 2 + 140, OUT // 2 - 330), b)
        g = Image.new('L', (OUT, OUT), 0)
        g.paste(q.getchannel('A'), (OUT // 2 - sz // 2 - 60, OUT // 2 - sz // 2 + 40))
        glow = Image.merge('RGB', (g, g, g))
        return np.array(canvas).astype(float), np.array(glow).astype(float) * 0.25
    # ending: queen with a long light streak (blade) + fallen king
    ang = math.radians(lerp(-152, -146, u))     # streak direction (towards bottom-left)
    cx, cy = lerp(650, 610, u), lerp(400, 430, u)
    m = Image.new('L', (OUT, OUT), 0)
    dm = ImageDraw.Draw(m)
    Lmax = 1500
    for k in range(60):
        a0, a1 = k / 60, (k + 1) / 60
        p0 = (cx + 60 * math.cos(ang) + Lmax * a0 * math.cos(ang), cy + 120 - Lmax * a0 * math.sin(ang) * -1)
        p1 = (cx + 60 * math.cos(ang) + Lmax * a1 * math.cos(ang), cy + 120 - Lmax * a1 * math.sin(ang) * -1)
        dm.line([p0, p1], fill=int(235 * (1 - a0) ** 1.4), width=int(lerp(46, 18, a0)))
    m = m.filter(ImageFilter.GaussianBlur(5))
    white = Image.new('RGB', (OUT, OUT), (235, 238, 245))
    canvas.paste(white, (0, 0), m)
    king = KING_BIG.copy()
    king.putalpha(king.getchannel('A').point(lambda v: int(v * 0.6)))
    canvas.paste(king, (150, 600), king)
    q = spr_rgba('wQ', 420).rotate(lerp(-10, -6, u), resample=Image.BICUBIC, expand=True)
    canvas.paste(q, (int(cx - q.width / 2), int(cy - q.height / 2)), q)
    g = m.copy()
    g.paste(q.getchannel('A'), (int(cx - q.width / 2), int(cy - q.height / 2)), q.getchannel('A'))
    glow = Image.merge('RGB', (g, g, g))
    return np.array(canvas).astype(float), np.array(glow).astype(float) * 0.35

# ---------------------------------------------------------------- frame
def frame(fi):
    t = fi / FPS + T0
    bloom_k = 0.9
    dark = 1.0
    sh = shot_at(t)
    if t < DROP:
        st, n = game_state(t)
        cx, cy, z, rot = interp_keys(CAM_INTRO, t)
        fills, badges, arrows, pills = [], [], [], []
        last = GAME[n - 1] if n else None
        if last and n <= 4:
            fills += [(last[0], WHITE, 0.18), (last[1], WHITE, 0.30)]
        if n >= 3 and t < 8.03:
            fills.append(('c4', BLUE, 0.7)); badges.append(('c4', '!', pop(t - L[2])))
        if n >= 5:
            fills.append(('h5', GREEN, 0.75 if t < 9.6 else 0.45)); badges.append(('h5', 'star', pop(t - L[4])))
        if n >= 6:
            fills.append(('f6', RED, 0.8 * pulse(t, lo=0.7))); badges.append(('f6', '??', pop(t - L[5])))
        if t >= 9.6:
            a = ease((t - 9.6) / 0.2)
            arrows.append(('h5', 'f7', a)); pills.append(('f7', PILL_M1, a))
            fills.append(('e8', RED, 0.75 * a * pulse(t, lo=0.6)))
            fills.append(('f7', WHITE, 0.12 * a))
        st.update(fills=fills, badges=badges, arrows=arrows, pills=pills)
        if 'moving' in st:
            st['trail'] = 3
        if t > 10.0:
            dark = lerp(1.0, 0.75, (t - 10.0) / 0.63)
        img, glow = render_board(st)
        dx, dy, dr = 0, 0, 0
        fade_in = ease((t - T0) / 0.4)
        dark *= fade_in
    else:
        i, s0, kind = sh
        s1 = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else DUR
        u = (t - s0) / (s1 - s0)
        dx, dy, dr = shake(t)
        if kind in ('void', 'ending'):
            img, glow = void_scene(u, t, kind)
            out = img + bloom(glow, 0.8)
            if kind == 'ending':
                out = out * (1 - ease((t - (END - 0.9)) / 0.9))
            return finish(out, t)
        if kind in ('queen', 'queen2'):
            st = final_decor(t)
            sgn = 1 if kind == 'queen' else -1
            cx, cy, z, rot = 742, 220, lerp(2.7, 2.25, ease_out(u)), sgn * lerp(24, 16, u)
        elif kind in ('king', 'king2'):
            st = final_decor(t)
            sgn = -1 if kind == 'king' else 1
            cx, cy, z, rot = lerp(620, 640, u), lerp(90, 110, u), lerp(2.3, 2.6, u), sgn * lerp(10, 20, u)
        elif kind == 'wide':
            st = final_decor(t, k_c4=1.0)
            cx, cy, z, rot = 540, 540, lerp(0.92, 1.12, ease(u)), lerp(-22, -6, ease(u))
        elif kind == 'bishop':
            st = final_decor(t, k_c4=1.0)
            st['lines'] = [('c4', 'f7', 1.0, CYAN)]
            p0, p1 = sqc('c4'), sqc('f7')
            cx, cy = lerp(p0[0], p1[0], ease(u)), lerp(p0[1], p1[1], ease(u))
            z, rot = 1.9, 45 + lerp(-4, 4, u)
        elif kind in ('replay', 'replay_fast'):
            k = ease(min(u / 0.8, 1.0))
            st = {'pos': POS[6], 'moving': ('h5', 'f7', k), 'trail': 6,
                  'fills': [('h5', GREEN, 0.5), ('f6', RED, 0.6), ('e8', RED, 0.5 * k)],
                  'arrows': [('h5', 'f7', 0.6 * (1 - k))]}
            if u >= 0.8:
                st = final_decor(t)
            qx = lerp(sqc('h5')[0], sqc('f7')[0], k); qy = lerp(sqc('h5')[1], sqc('f7')[1], k)
            cx, cy = lerp(qx, 742, 0.3), lerp(qy, 202, 0.3)
            z, rot = lerp(1.8, 2.3, u), lerp(-10, 6, u) if kind == 'replay' else lerp(14, -4, u)
        elif kind == 'build':
            st = final_decor(t, k_c4=0.6)
            cx, cy, z, rot = lerp(540, 700, ease(u)), lerp(540, 260, ease(u)), lerp(1.0, 2.4, u ** 2), lerp(0, 70, u ** 2)
            dark = lerp(1.0, 0.45, u)
        elif kind == 'wide_end':
            st = final_decor(t, k_c4=0.8)
            cx, cy, z, rot = 540, 540, lerp(1.25, 0.95, ease_out(u)), lerp(25, -8, ease_out(u))
            dark = 1.0 - ease((t - 27.9) / 0.9)
        elif kind == 'dark':
            st = final_decor(t, k_e8=1.0, k_f7=0.6, badges=False)
            cx, cy, z, rot = lerp(700, 660, u), lerp(250, 140, u), lerp(1.6, 2.4, u), lerp(-12, -24, u)
            dark = 0.22 + 0.10 * pulse(t, lo=0, hi=1) * ease(u * 3)
            bloom_k = 1.3
        img, glow = render_board(st)
    img_t = camera_warp(img, cx + dx, cy + dy, z, rot + dr)
    glow_t = camera_warp(glow, cx + dx, cy + dy, z, rot + dr)
    out = img_t * dark + bloom(glow_t, bloom_k) * max(dark, 0.6 if t >= DROP else dark)
    return finish(out * VIGNETTE + 0 * out, t)

def finish(out, t):
    for f in FLASHES:
        if 0 <= t - f < 0.4:
            k = (1 - (t - f) / 0.4) ** 2
            out = out * (1 - k) + 255 * k
    return np.clip(out, 0, 255).astype(np.uint8)

def work(fi):
    return frame(fi).tobytes()

if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[3] == 'preview':
        ts = [float(x) for x in sys.argv[4].split(',')]
        tiles = [Image.fromarray(frame(int((tt - T0) * FPS))).resize((360, 360)) for tt in ts]
        cols = 6
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new('RGB', (360 * cols, 360 * rows))
        for k, im in enumerate(tiles):
            sheet.paste(im, ((k % cols) * 360, (k // cols) * 360))
        sheet.save(OUTFILE)
        sys.exit()
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OUT}x{OUT}',
           '-r', str(FPS), '-i', '-']
    if AUDIO:
        cmd += ['-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k']
    cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-t', f'{DUR}',
            '-movflags', '+faststart', OUTFILE]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, b in enumerate(pool.imap(work, range(NF), chunksize=4)):
            ff.stdin.write(b)
            if k % 150 == 0:
                print('frame', k, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', ff.returncode)
