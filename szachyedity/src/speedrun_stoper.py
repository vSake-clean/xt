import sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SRC = sys.argv[1]
OUT = sys.argv[2]
S = 135
TOP = 754
LIGHT = np.array([238, 238, 210.])
DARK = np.array([118, 150, 85.])
HL = np.array([247, 248, 131.])

board = np.array(Image.open(SRC).convert('RGB').crop((0, TOP, 8 * S, TOP + 8 * S))).astype(float)

# remove the app's grey scrollbar (x 17..24, y 94..275) and repair the "7" label under it
board[94:135, 15:27] = LIGHT
board[135:270, 15:27] = DARK
board[270:280, 15:27] = LIGHT
t = board[135:180, 0:45]
keep = t.sum(2) > 500
t[:, 15:27][~keep[:, 15:27]] = DARK
SS = 8
mask = Image.new('L', (45 * SS, 45 * SS), 0)
d = ImageDraw.Draw(mask)
d.polygon([(p[0] * SS, p[1] * SS) for p in [(9, 13.6), (22.6, 13.6), (22.6, 17), (9, 17)]], fill=255)
d.polygon([(p[0] * SS, p[1] * SS) for p in [(18.4, 16), (22.6, 16), (15.6, 33), (11.2, 33)]], fill=255)
mask = np.array(mask.resize((45, 45), Image.LANCZOS)).astype(float)[..., None] / 255
LABEL_ON_DARK = np.array([192, 207, 164.])
board[135:180, 0:45] = np.maximum(t * (1 - mask) + LABEL_ON_DARK * mask, t * keep[..., None])

def sq_xy(name):
    c = ord(name[0]) - 97
    r = int(name[1])
    return c * S, (8 - r) * S

start = {}
for i, f in enumerate('abcdefgh'):
    back = 'RNBQKBNR'[i]
    start[f + '1'] = 'w' + back
    start[f + '2'] = 'wP'
    start[f + '7'] = 'bP'
    start[f + '8'] = 'b' + back

empty = board.copy()
sprites = {}  # piece -> (rgb, alpha) arrays SxS
for name, piece in start.items():
    x, y = sq_xy(name)
    tile = board[y:y + S, x:x + S]
    bgc = LIGHT if ((ord(name[0]) - 97) + int(name[1])) % 2 == 0 else DARK
    dist = np.sqrt(((tile - bgc) ** 2).sum(2))
    fg = dist > 35
    lab, n = ndimage.label(fg)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    piece_mask = lab == (np.argmax(sizes) + 1)
    piece_mask = ndimage.binary_fill_holes(piece_mask)
    # alpha: solid inside, soft edge by unmixing against background colour
    O = np.array([55, 55, 55.])
    od = np.linalg.norm(O - bgc)
    inner = ndimage.binary_erosion(piece_mask, iterations=2)
    band = ndimage.binary_dilation(piece_mask, iterations=2) & ~inner
    alpha = np.where(inner, 1.0, 0.0)
    a_band = np.clip(dist / od, 0, 1)
    alpha = np.where(band, a_band, alpha)
    alpha = np.where(piece_mask & band, np.maximum(alpha, 0.0), alpha)
    with np.errstate(divide='ignore', invalid='ignore'):
        F = bgc + (tile - bgc) / np.maximum(alpha, 1e-3)[..., None]
    F = np.clip(F, 0, 255)
    F = np.where(inner[..., None], tile, F)
    if piece not in sprites:
        sprites[piece] = (F, alpha)
    # clear the square on the empty board, keep coordinate labels
    clear = ndimage.binary_dilation(piece_mask, iterations=3)
    empty[y:y + S, x:x + S][clear] = bgc

def blend(img, rgb, alpha, x, y):
    x, y = int(round(x)), int(round(y))
    region = img[y:y + S, x:x + S]
    a = alpha[..., None]
    img[y:y + S, x:x + S] = region * (1 - a) + rgb * a

def highlight(img, name):
    x, y = sq_xy(name)
    tile = empty[y:y + S, x:x + S]
    c = ord(name[0]) - 97
    bgc = LIGHT if (c + int(name[1])) % 2 == 0 else DARK
    dist = np.sqrt(((tile - bgc) ** 2).sum(2))
    labelmask = (dist > 35)[..., None]
    img[y:y + S, x:x + S] = np.where(labelmask, tile, HL)

from PIL import ImageDraw, ImageFont
import math
FPS = 30
TOTAL = int(sys.argv[3]) if len(sys.argv) > 3 else 407
W = 8 * S
FONT = '/usr/share/fonts/opentype/inter/'

def to_rgba(piece):
    F, a = sprites[piece]
    return Image.fromarray(np.dstack([F, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA')

def lerp(a, b, t):
    return a + (b - a) * t

def ease(t):
    t = min(max(t, 0), 1)
    return t * t * (3 - 2 * t)

def pop(t):  # scale 0 -> 1 with overshoot
    if t <= 0: return 0.0
    if t >= 1: return 1.0
    return 1.12 * math.sin(t * math.pi / 2) if t < 0.7 else 1.12 - 0.12 * (t - 0.7) / 0.3

def tile_color(name):
    return LIGHT if ((ord(name[0]) - 97) + int(name[1])) % 2 == 0 else DARK

def render2(pos, last, moving=None, tints=None, hide=()):
    img = empty.copy()
    if last:
        highlight(img, last[0]); highlight(img, last[1])
    for sq, (col, al) in (tints or {}).items():
        if al <= 0: continue
        x, y = sq_xy(sq)
        tile = img[y:y + S, x:x + S]
        dist = np.sqrt(((empty[y:y + S, x:x + S] - tile_color(sq)) ** 2).sum(2))
        lab = (dist > 35)[..., None]       # keep coordinate labels
        img[y:y + S, x:x + S] = np.where(lab, tile, tile * (1 - al) + np.array(col) * al)
    for name, p in pos.items():
        if (moving and name == moving[0]) or name in hide:
            continue
        x, y = sq_xy(name)
        blend(img, *sprites[p], x, y)
    if moving:
        frm, to, t = moving
        x0, y0 = sq_xy(frm); x1, y1 = sq_xy(to)
        e = ease(t)
        blend(img, *sprites[pos[frm]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    return img

def dim(img, k):
    # chess.com game-over look: desaturate + contrast around 200
    if k <= 0: return img
    g = (img * np.array([0.299, 0.587, 0.114])).sum(2, keepdims=True)
    d = g + (img - g) * 0.45
    d = 200 + (d - 200) * 1.3
    return img * (1 - k) + d * k

# ---------- overlay drawing (supersampled RGBA layers) ----------
def crown(draw, cx, cy, w, fill):
    h = w * 0.72
    x0, x1 = cx - w / 2, cx + w / 2
    yb, yt = cy + h * 0.42, cy - h * 0.30
    pts = [(x0 + w * 0.06, yb - h * 0.16), (x0, yt), (x0 + w * 0.30, cy + h * 0.02), (cx, yt - h * 0.12),
           (x1 - w * 0.30, cy + h * 0.02), (x1, yt), (x1 - w * 0.06, yb - h * 0.16)]
    draw.polygon(pts, fill=fill)
    draw.rounded_rectangle((x0 + w * 0.06, yb - h * 0.20, x1 - w * 0.06, yb), radius=w * 0.05, fill=fill)
    r = w * 0.075
    for px, py in [(x0, yt), (cx, yt - h * 0.12), (x1, yt)]:
        draw.ellipse((px - r, py - r, px + r, py + r), fill=fill)

PILL_FONT = ImageFont.truetype(FONT + 'Inter-SemiBold.otf', 40 * 2)
def pill(layer, cx, cy, text, color, scale, alpha):
    if scale <= 0 or alpha <= 0: return
    ss = 2
    bb = PILL_FONT.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = tw + 44 * ss, 62 * ss
    im = Image.new('RGBA', (pw + 12 * ss, ph + 12 * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6 * ss, 9 * ss, 6 * ss + pw, 9 * ss + ph), radius=ph / 2, fill=(0, 0, 0, 60))
    d.rounded_rectangle((6 * ss, 6 * ss, 6 * ss + pw, 6 * ss + ph), radius=ph / 2, fill=(255, 255, 255, 255))
    d.text((6 * ss + (pw - tw) / 2 - bb[0], 6 * ss + (ph - th) / 2 - bb[1]), text, font=PILL_FONT, fill=color)
    w = max(1, int(im.width / ss * scale)); h = max(1, int(im.height / ss * scale))
    im = im.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    layer.alpha_composite(im, (int(cx - w / 2), int(cy - h / 2)))

def circle_icon(kind, d):
    ss = 4
    D = d * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if kind == 'win':
        dr.ellipse((0, 0, D - 1, D - 1), fill=(129, 182, 76, 255))
        crown(dr, D / 2, D / 2 + D * 0.02, D * 0.58, (255, 255, 255, 255))
        return im.resize((d, d), Image.LANCZOS)
    dr.ellipse((0, 0, D - 1, D - 1), fill=(222, 108, 118, 255))
    im = im.resize((d, d), Image.LANCZOS)
    k = TOPPLED.resize((int(d * 0.78), int(d * 0.78)), Image.LANCZOS)
    im.alpha_composite(k, ((d - k.width) // 2, (d - k.height) // 2 + 2))
    return im

def big_win_icon(d):
    ss = 4
    D = d * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, D - 1, D - 1), fill=(150, 196, 104, 235))
    crown(dr, D / 2, D / 2 + D * 0.03, D * 0.62, (255, 255, 255, 255))
    return im.resize((d, d), Image.LANCZOS)

def _tf(sz):
    f = ImageFont.truetype(FONT + 'Inter-ExtraLight.otf', sz)
    a = max(f.getlength(c) for c in '0123456789')
    return f, a, 6 * a + f.getlength(':') + f.getlength('.')
for _sz in range(100, 20, -1):
    TIMER_FONT, ADV, _w = _tf(_sz)
    if _w <= 285: break
def timer(layer, secs):
    cs = int(round(secs * 100))
    txt = f'{cs // 6000:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}'
    bx0, by0, bx1, by1 = 206, 369, 535, 497
    d = ImageDraw.Draw(layer)
    d.rectangle((bx0, by0, bx1, by1), fill=(18, 18, 18, 255))
    widths = [ADV if c.isdigit() else TIMER_FONT.getlength(c) for c in txt]
    x = (bx0 + bx1) / 2 - sum(widths) / 2
    asc = TIMER_FONT.getbbox('0')
    y = (by0 + by1) / 2 - (asc[1] + asc[3]) / 2
    for c, w in zip(txt, widths):
        cw = TIMER_FONT.getlength(c)
        d.text((x + (w - cw) / 2, y), c, font=TIMER_FONT, fill=(255, 255, 255, 255))
        x += w

# ---------- game: fool's mate ----------
LOSER, WINNER = 'e8', 'e1'
TOPPLED = to_rgba('bK').rotate(-80, resample=Image.BICUBIC, expand=True)
TOPPLED = TOPPLED.crop(TOPPLED.getbbox())
side = max(TOPPLED.size); tmp = Image.new('RGBA', (side, side), (0, 0, 0, 0))
tmp.alpha_composite(TOPPLED, ((side - TOPPLED.width) // 2, (side - TOPPLED.height) // 2)); TOPPLED = tmp

SLIDE = 6
moves = [('e2', 'e4', 20), ('g7', 'g5', 48), ('d2', 'd4', 76), ('f7', 'f6', 104), ('d1', 'h5', 133)]  # landing frames
M = moves[-1][2]
RED = (214, 82, 88)

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                       '-s', f'{W}x{W}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264',
                       '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                      stdin=subprocess.PIPE)

pos = dict(start)
last = None
mi = 0
snap = {}
for f in range(TOTAL):
    moving = None
    while mi < len(moves) and f >= moves[mi][2]:
        frm, to, _ = moves[mi]
        pos[to] = pos.pop(frm); last = (frm, to); mi += 1
    if mi < len(moves) and f > moves[mi][2] - SLIDE:
        frm, to, land = moves[mi]
        moving = (frm, to, (f - (land - SLIDE)) / SLIDE)
    r = f - M
    tints, hide = {}, set()
    if r >= 0:
        a = 0.78 if r < 20 else 0.78 * (1 - ease((r - 20) / 8))
        tints[LOSER] = (RED, a)
    topple_phase = False
    if topple_phase:
        hide = {LOSER, WINNER}
    img = render2(pos, last, moving, tints, hide)
    img = dim(img, ease(r / 3) if r >= 0 else 0)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    if topple_phase:
        lx, ly = sq_xy(LOSER); wx, wy = sq_xy(WINNER)
        k = TOPPLED.resize((S - 14, S - 14), Image.LANCZOS)
        layer.alpha_composite(k, (lx + 7, ly + 12))
        sc = pop((r - 5) / 6)
        d = max(1, int((S - 20) * sc))
        layer.alpha_composite(big_win_icon(d), (int(wx + S / 2 - d / 2), int(wy + S / 2 - d / 2)))
    if False:
        sc = pop((r - 5) / 6)
        al = 1 - ease((r - 19) / 7)
        wx, wy = sq_xy(WINNER); lx, ly = sq_xy(LOSER)
        pill(layer, wx + S / 2, wy + 34, 'Winner', (93, 153, 72, 255), sc, al)
        pill(layer, lx + S / 2, ly + 30, 'Checkmate', (196, 64, 78, 255), sc, al)
    if r >= 5:
        sc = pop((r - 5) / 7)
        d = int(48 * sc)
        if d > 0:
            for sq, kind in ((WINNER, 'win'), (LOSER, 'lose')):
                x, y = sq_xy(sq)
                ic = circle_icon(kind, 48).resize((d, d), Image.LANCZOS)
                cx, cy = x + S - 14, y + 14
                cx = min(cx, W - 26)
                layer.alpha_composite(ic, (int(cx - d / 2), int(cy - d / 2)))
    timer(layer, min(f, M) / FPS)
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    base.alpha_composite(layer)
    fr = np.array(base.convert('RGB'))
    if f in (40, M, M + 8, M + 14, M + 22, M + 28, M + 40, TOTAL - 1):
        snap[f] = fr
    ff.stdin.write(fr.tobytes())
ff.stdin.close(); ff.wait()
keys = sorted(snap)
sheet = Image.new('RGB', (360 * 4, 360 * 2))
for i, k in enumerate(keys):
    sheet.paste(Image.fromarray(snap[k]).resize((360, 360)), ((i % 4) * 360, (i // 4) * 360))
sheet.save('sheet4.png')
print('done', ff.returncode, 'mate frame', M, keys)
