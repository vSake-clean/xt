"""Rook-chase meme on our green board, timings taken from the reference, alien clip overlay, reference music."""
import sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import assets as A
import pogon_wieza_trasa as route7

S = A.S
B = 8 * S
W, H = 1080, 1920
BY = (H - B) // 2
FPS = 30
DUR = 17.5
NF = int(round(DUR * FPS))
CLIP, AUDIO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FONT = '/usr/share/fonts/opentype/inter/'

COL = {'great': (116, 155, 191), 'brilliant': (38, 194, 163), 'best': (129, 182, 76)}
BADGE = {'great': (92, 139, 176), 'brilliant': (38, 194, 163), 'best': (129, 182, 76)}
TEXT = {'great': (92, 139, 176), 'brilliant': (27, 172, 140)}
NAME = {'great': 'Great', 'brilliant': 'Brilliant'}

# ---------------------------------------------------------------- icons & pills
def icon(cls, size=54):
    ss = 4; D = size * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((ss, ss * 2.5, D - ss, D - ss * 0.5), fill=(0, 0, 0, 60))
    d.ellipse((ss, ss, D - ss, D - ss * 2), fill=BADGE[cls] + (255,))
    cx, cy = D / 2, D / 2 - ss * 0.5
    w = (255, 255, 255, 255)
    if cls == 'best':
        import math
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = D * 0.30 if i % 2 == 0 else D * 0.13
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=w)
    else:
        txt = '!' if cls == 'great' else '!!'
        f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(D * (0.62 if cls == 'great' else 0.5)))
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=w)
    return im.resize((size, size), Image.LANCZOS)

def pill(cls, h=56):
    ss = 3
    f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(h * 0.58) * ss)
    txt = NAME[cls]
    bb = f.getbbox(txt)
    tw = bb[2] - bb[0]
    pw = tw + int(h * 0.95) * ss
    ph = h * ss
    im = Image.new('RGBA', (pw + 8 * ss, ph + 8 * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4 * ss, 6 * ss, 4 * ss + pw, 6 * ss + ph), radius=ph / 2, fill=(0, 0, 0, 45))
    d.rounded_rectangle((4 * ss, 4 * ss, 4 * ss + pw, 4 * ss + ph), radius=ph / 2, fill=(250, 250, 250, 255))
    d.text((4 * ss + (pw - tw) / 2 - bb[0], 4 * ss + (ph - (bb[3] - bb[1])) / 2 - bb[1]), txt, font=f, fill=TEXT[cls] + (255,))
    return im.resize((im.width // ss, im.height // ss), Image.LANCZOS)

ICONS = {c: icon(c) for c in BADGE}
PILLS = {c: pill(c) for c in NAME}

# ---------------------------------------------------------------- moves
start_fen, SEQ = route7.build()
import chess
board0 = chess.Board(start_fen)
POS0 = {}
for sq, pc in board0.piece_map().items():
    POS0[chess.square_name(sq)] = ('w' if pc.color else 'b') + pc.symbol().upper()
SLIDE = 3 / FPS
FIRST = ('h7', 'd7', 'great')

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def label_mask(name):
    x, y = A.sq_xy(name)
    c = ord(name[0]) - 97
    bg = A.LIGHT if (c + int(name[1])) % 2 == 0 else A.DARK
    return (np.sqrt(((A.empty[y:y + S, x:x + S] - bg) ** 2).sum(2)) > 35)[..., None]

MASKS = {chr(97 + c) + str(r): label_mask(chr(97 + c) + str(r)) for c in range(8) for r in range(1, 9)}

def tint(img, name, col, a):
    x, y = A.sq_xy(name)
    t = img[y:y + S, x:x + S]
    img[y:y + S, x:x + S] = np.where(MASKS[name], t, t * (1 - a) + np.array(col, float) * a)

def board_frame(t):
    pos = dict(POS0)
    last = FIRST
    last_t = -1.0
    next_t = SEQ[0][0]
    moving = None
    for k, (tm, frm, to, pc, cls) in enumerate(SEQ):
        if t >= tm:
            pos[to] = pos.pop(frm)
            last = (frm, to, cls); last_t = tm
            next_t = SEQ[k + 1][0] if k + 1 < len(SEQ) else 99
        else:
            if t > tm - SLIDE:
                moving = (frm, to, (t - (tm - SLIDE)) / SLIDE)
            break
    img = A.empty.copy()
    frm, to, cls = last
    tint(img, frm, COL[cls], 0.55)
    tint(img, to, COL[cls], 0.55)
    for name, p in pos.items():
        if moving and name == moving[0]:
            continue
        x, y = A.sq_xy(name)
        A.blend(img, *A.sprites[p], x, y)
    # classification colour also washes over the piece that just moved (as in the reference)
    if not moving or moving[0] != to:
        x, y = A.sq_xy(to)
        img[y:y + S, x:x + S] = img[y:y + S, x:x + S] * 0.72 + np.array(COL[cls], float) * 0.28
    if moving:
        f, tq, u = moving
        x0, y0 = A.sq_xy(f); x1, y1 = A.sq_xy(tq)
        e = ease(u)
        A.blend(img, *A.sprites[pos[f]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    x, y = A.sq_xy(to)
    ic = ICONS[cls]
    cx = min(x + S - 6, B - ic.width / 2 - 2); cy = max(y + 8, ic.height / 2 + 2)
    im.alpha_composite(ic, (int(cx - ic.width / 2), int(cy - ic.height / 2)))
    if cls in PILLS and last_t >= 0:
        a = min(1.0, (t - last_t) / 0.07) * min(1.0, max(0.0, (next_t - 0.02 - t) / 0.07))
        if a > 0:
            p = PILLS[cls].copy()
            if a < 1:
                p.putalpha(p.getchannel('A').point(lambda v: int(v * a)))
            px = min(max(x + S - 4, p.width / 2 + 2), B - p.width / 2 - 2)
            py = max(y + 10, p.height / 2 + 2)
            im.alpha_composite(p, (int(px - p.width / 2), int(py - p.height / 2)))
    return np.array(im.convert('RGB')).astype(float)

# ---------------------------------------------------------------- overlay clip (measured from the reference)
OV = 626
OVX, OVY = 0, 228
T_IN, T_LOOP = 3.63, 11.03
SPEED1 = 0.895

def main():
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', CLIP, '-vf', f'scale={OV}:{OV}:flags=lanczos',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    clip = np.frombuffer(raw, np.uint8).reshape(-1, OV, OV, 3)
    nclip = len(clip)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                            '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                            '-t', f'{DUR}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    frame = np.zeros((H, W, 3), np.uint8)
    snaps = {}
    for fi in range(NF):
        t = fi / FPS
        img = board_frame(t)
        if t >= T_IN:
            if t < T_LOOP:
                ct, alpha = (t - T_IN) * SPEED1, 0.69
            else:
                ct, alpha = t - T_LOOP, 0.57
            k = min(int(ct * FPS), nclip - 1)
            region = img[OVY:OVY + OV, OVX:OVX + OV]
            img[OVY:OVY + OV, OVX:OVX + OV] = region * (1 - alpha) + clip[k].astype(float) * alpha
        frame[:] = 0
        frame[BY:BY + B] = np.clip(img, 0, 255).astype(np.uint8)
        if fi in (2, 18, 60, 130, 142, 200, 212, 250, 340, 420, 480, NF - 1):
            snaps[fi] = Image.fromarray(frame[BY - 20:BY + B + 20]).resize((300, 311))
        enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait()
    sheet = Image.new('RGB', (300 * 6, 311 * 2))
    for k, (fi, im) in enumerate(sorted(snaps.items())):
        sheet.paste(im, ((k % 6) * 300, (k // 6) * 311))
    sheet.save('render7_sheet.png')
    print('done', enc.returncode)

if __name__ == '__main__':
    main()
