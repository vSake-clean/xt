"""Frame-accurate remake of the reference: Caro-Kann with 7.Nxf7?, zooms, then the alien clip."""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import assets as A

S = A.S
B = 8 * S                       # 1080 board
W, H = 1080, 2322               # same aspect as the reference (576x1238)
BY = (H - B) // 2               # board top in the frame
FPS = 30
DUR = 15.333333
NF = int(round(DUR * FPS))
CLIP = sys.argv[1]
AUDIO = sys.argv[2]
OUT = sys.argv[3]
FONT = '/usr/share/fonts/opentype/inter/'

# ---------------------------------------------------------------- classification look (chess.com review)
HL = {'book': (213, 164, 125), 'inacc': (247, 198, 49), 'exc': (150, 188, 75), 'best': (129, 182, 76), 'mist': (255, 164, 89)}
BADGE_COL = {'book': (168, 136, 101), 'inacc': (247, 198, 49), 'exc': (150, 188, 75), 'best': (129, 182, 76), 'mist': (255, 164, 89)}

def draw_icon(kind, size):
    ss = 4; D = size * ss
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((ss, ss * 2.5, D - ss, D - ss * 0.5), fill=(0, 0, 0, 55))
    d.ellipse((ss, ss, D - ss, D - ss * 2), fill=BADGE_COL[kind] + (255,))
    w = (255, 255, 255, 255)
    cx, cy = D / 2, D / 2 - ss * 0.5
    if kind in ('inacc', 'mist'):
        txt = '?!' if kind == 'inacc' else '?'
        f = ImageFont.truetype(FONT + 'Inter-Bold.otf', int(D * (0.52 if kind == 'inacc' else 0.62)))
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=w)
    elif kind == 'best':
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = D * 0.30 if i % 2 == 0 else D * 0.13
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=w)
    elif kind == 'book':
        u = D / 100
        d.polygon([(cx - 30 * u, cy - 18 * u), (cx - 3 * u, cy - 13 * u), (cx - 3 * u, cy + 24 * u), (cx - 30 * u, cy + 19 * u)], fill=w)
        d.polygon([(cx + 30 * u, cy - 18 * u), (cx + 3 * u, cy - 13 * u), (cx + 3 * u, cy + 24 * u), (cx + 30 * u, cy + 19 * u)], fill=w)
    elif kind == 'exc':
        u = D / 100
        d.rounded_rectangle((cx - 28 * u, cy - 4 * u, cx - 16 * u, cy + 26 * u), radius=2 * u, fill=w)       # cuff
        d.rounded_rectangle((cx - 12 * u, cy - 6 * u, cx + 26 * u, cy + 26 * u), radius=7 * u, fill=w)       # palm
        d.polygon([(cx - 12 * u, cy - 2 * u), (cx - 2 * u, cy - 28 * u), (cx + 8 * u, cy - 26 * u), (cx + 6 * u, cy - 4 * u)], fill=w)  # thumb
        d.ellipse((cx - 6 * u, cy - 34 * u, cx + 10 * u, cy - 20 * u), fill=w)
    return im.resize((size, size), Image.LANCZOS)

ICON = {k: draw_icon(k, 74) for k in BADGE_COL}

# ---------------------------------------------------------------- game (timings measured from the reference)
#            from  to    start  land   class
MOVES = [('c7', 'c6', 0.33, 0.50, 'book'), ('b1', 'c3', 1.10, 1.30, 'book'), ('d7', 'd5', 1.57, 1.77, 'book'),
         ('d2', 'd4', 2.03, 2.27, 'book'), ('d5', 'e4', 2.60, 2.83, 'book'), ('c3', 'e4', 3.13, 3.40, 'book'),
         ('g8', 'f6', 3.63, 3.87, 'book'), ('e4', 'g5', 4.03, 4.30, 'inacc'), ('c8', 'f5', 4.53, 4.80, 'exc'),
         ('g1', 'f3', 5.07, 5.27, 'exc'), ('h7', 'h6', 5.67, 5.85, 'best'), ('g5', 'f7', 6.07, 6.27, 'mist')]
pos0 = dict(A.start)
pos0['e4'] = pos0.pop('e2')     # 1.e4 is already on the board when the video starts
FIRST = ('e2', 'e4', 'book')

def label_mask(name):
    x, y = A.sq_xy(name)
    c = ord(name[0]) - 97
    bg = A.LIGHT if (c + int(name[1])) % 2 == 0 else A.DARK
    return (np.sqrt(((A.empty[y:y + S, x:x + S] - bg) ** 2).sum(2)) > 35)[..., None]

def tint(img, name, col, a=0.5):
    x, y = A.sq_xy(name)
    t = img[y:y + S, x:x + S]
    img[y:y + S, x:x + S] = np.where(label_mask(name), t, t * (1 - a) + np.array(col) * a)

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def board_at(t):
    pos = dict(pos0)
    last = FIRST
    moving = None
    for frm, to, s0, s1, cl in MOVES:
        if t >= s1:
            pos[to] = pos.pop(frm); last = (frm, to, cl)
        elif t > s0:
            moving = (frm, to, (t - s0) / (s1 - s0))
            break
        else:
            break
    img = A.empty.copy()
    frm, to, cl = last
    tint(img, frm, HL[cl]); tint(img, to, HL[cl])
    for name, p in pos.items():
        if moving and name == moving[0]:
            continue
        x, y = A.sq_xy(name)
        A.blend(img, *A.sprites[p], x, y)
    if moving:
        f, tq, u = moving
        x0, y0 = A.sq_xy(f); x1, y1 = A.sq_xy(tq)
        e = ease(u)
        A.blend(img, *A.sprites[pos[f]], x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    if not moving:   # badge on the destination square of the last move
        x, y = A.sq_xy(to)
        b = ICON[cl]
        im.alpha_composite(b, (int(min(x + S - b.width / 2 - 2, B - b.width)), int(max(y - b.height / 2 + 8, 0))))
    return im.convert('RGB')

# ---------------------------------------------------------------- zooms on the knight (measured from the reference)
ZOOMS = [(6.73, 1.75, 0.716), (7.10, 1.94, 0.6875), (7.57, 2.64, 0.6875)]   # start, zoom, centre-x (board fraction)
ZOOM_END = 7.93
FLASH = 8.30
CLIP_START = 8.60

def zoomed(img, z, cxf, cyf=0.1875):
    half = 0.5 / z
    cx = min(max(cxf, half), 1 - half)
    cy = min(max(cyf, half), 1 - half)
    box = ((cx - half) * B, (cy - half) * B, (cx + half) * B, (cy + half) * B)
    return img.resize((B, B), Image.BICUBIC, box=box)

def main():
    clip = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', CLIP, '-vf', f'scale={B}:{B}:flags=lanczos',
                             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    fsz = B * B * 3
    first = np.frombuffer(clip.stdout.read(fsz), np.uint8).reshape(B, B, 3)
    clip_used_first = False
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                            '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                            '-t', f'{DUR}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    frame = np.zeros((H, W, 3), np.uint8)
    snaps = {}
    for fi in range(NF):
        t = fi / FPS
        if t < FLASH:
            img = board_at(t)
            z = None
            for s, zz, cx in ZOOMS:
                if s <= t < ZOOM_END:
                    z = (zz, cx)
            if z:
                img = zoomed(img, *z)
            sq = np.array(img).astype(float)
            if t < 0.53:
                sq *= t / 0.53
        elif t < CLIP_START:
            k = 1 - (t - FLASH) / (CLIP_START + 0.03 - FLASH)
            sq = first.astype(float) * (1 - k) + 255 * k
        else:
            if not clip_used_first:
                cur = first; clip_used_first = True
            else:
                buf = clip.stdout.read(fsz)
                cur = np.frombuffer(buf, np.uint8).reshape(B, B, 3) if len(buf) == fsz else None
            if cur is None:
                sq = np.zeros((B, B, 3))
            else:
                sq = cur.astype(float)
        frame[:] = 0
        frame[BY:BY + B] = np.clip(sq, 0, 255).astype(np.uint8)
        if fi in (5, 45, 130, 190, 210, 222, 236, 245, 255, 300, 400, NF - 1):
            snaps[fi] = Image.fromarray(frame.copy()).resize((180, 387))
        enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait(); clip.kill()
    sheet = Image.new('RGB', (180 * 6, 387 * 2))
    for k, (fi, im) in enumerate(sorted(snaps.items())):
        sheet.paste(im, ((k % 6) * 180, (k // 6) * 387))
    sheet.save('copy6_sheet.png')
    print('done', enc.returncode)

if __name__ == '__main__':
    main()
