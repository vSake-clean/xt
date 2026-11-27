import os
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

moves = [('e2', 'e4'), ('b7', 'b6'), ('g1', 'f3'), ('c8', 'a6'), ('f3', 'e5'),
         ('a6', 'f1'), ('d1', 'h5'), ('f1', 'g2'), ('h5', 'f7')]

FPS = 30
pos = dict(start)
frames_spec = []  # (pos, last_move, moving)

def render(pos, last, moving=None):
    img = empty.copy()
    if last:
        highlight(img, last[0]); highlight(img, last[1])
    for name, p in pos.items():
        if moving and name == moving[0]:
            continue
        x, y = sq_xy(name)
        blend(img, *sprites[p], x, y)
    if moving:
        frm, to, t = moving
        x0, y0 = sq_xy(frm); x1, y1 = sq_xy(to)
        e = t * t * (3 - 2 * t)
        blend(img, *sprites[pos[frm]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    return np.clip(img, 0, 255).astype(np.uint8)

ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                       '-s', f'{8*S}x{8*S}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264',
                       '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT],
                      stdin=subprocess.PIPE)

written=[0]
def emit(frame, n):
    written[0]+=n
    b = frame.tobytes()
    for _ in range(n):
        ff.stdin.write(b)

from PIL import ImageDraw, ImageFont

# chess.com-style "??" blunder badge, supersampled for smooth edges
def make_badge(d=62):
    ss = 4
    D = d * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse((ss * 2, ss * 3, D - ss * 2, D - ss * 1), fill=(0, 0, 0, 70))      # soft shadow
    dr.ellipse((ss * 2, ss * 1, D - ss * 2, D - ss * 3), fill=(202, 52, 49, 255))  # red disc
    f = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonty', 'DejaVuSans-Bold.ttf'), int(D * 0.5))
    bb = dr.textbbox((0, 0), '??', font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    dr.text(((D - tw) / 2 - bb[0], (D - ss * 2 - th) / 2 - bb[1]), '??', font=f, fill=(255, 255, 255, 255))
    return im.resize((d, d), Image.LANCZOS)

BADGE = make_badge()

def with_badge(frame, square, scale):
    if scale <= 0:
        return frame
    im = Image.fromarray(frame)
    d = max(1, int(round(BADGE.width * scale)))
    b = BADGE.resize((d, d), Image.LANCZOS)
    x, y = sq_xy(square)
    cx, cy = x + S - 12, y + 12          # badge centre at top-right corner of the square
    im.paste(b, (int(cx - d / 2), int(cy - d / 2)), b)
    return np.array(im)

def pop(t):  # 0..1 -> scale with small overshoot
    if t >= 1:
        return 1.0
    return 1.15 * np.sin(t * np.pi / 2) if t < 0.7 else 1.15 - 0.15 * (t - 0.7) / 0.3

moves = [('f2', 'f3', 8), ('e7', 'e5', 8), ('g2', 'g4', 8), ('d8', 'h4', 54)]
PAUSE = 10
last = None
emit(render(pos, None), 15)
badge_sq = None
for k, (frm, to, anim) in enumerate(moves):
    for i in range(1, anim + 1):
        fr = render(pos, last, (frm, to, i / anim))
        if badge_sq and i < anim:
            fr = with_badge(fr, badge_sq, 1.0)
        emit(fr, 1)
    pos[to] = pos.pop(frm)
    last = (frm, to)
    badge_sq = None
    if (frm, to) == ('g2', 'g4'):
        badge_sq = 'g4'
        base = render(pos, last)
        for i in range(1, 9):
            emit(with_badge(base, 'g4', pop(i / 8)), 1)
        emit(with_badge(base, 'g4', 1.0), 30)
    elif k < len(moves) - 1:
        emit(render(pos, last), PAUSE)
print('mate lands at frame', written[0] - 1)
final = render(pos, last)
Image.fromarray(final).save('check_end3.png')
emit(final, 75)
ff.stdin.close()
ff.wait()
print('done', ff.returncode, 'frames', written[0])
