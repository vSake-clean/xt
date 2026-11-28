# tweenslop.py  -  uzycie:
#   python3 src/tweenslop.py ZDJECIE.jpg wynik.mp4 [x0 y0 x1 y1]   (prostokat postaci w ulamkach zdjecia)
# Edit w stylu "tweenslop": jedno zdjecie (wycieta postac z bialym obrysem) najpierw spokojnie sie kolysze,
# a od dropu brazylijskiego funku przesadnie "tweenuje" na kazdy bit (zgniatanie/rozciaganie, obroty, skoki,
# odbicia, smugi). Muzyke (beat funk 130 BPM) generujemy sami kodem - bez cudzych utworow. Bez napisow.
import os, sys, math, subprocess, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kolaz

SRC, OUT = sys.argv[1:3]
RECT = [float(v) for v in sys.argv[3:7]] if len(sys.argv) >= 7 else [.03, .06, .78, 1.0]
W, H, FPS = 1080, 1920, 30
BPM = 130.0
BEAT = 60 / BPM
DROP = 3.0                                   # do dropu "moj tweening" (spokojnie), potem tweenslop
NBEATS = 20
DUR = DROP + NBEATS * BEAT + 0.35
NF = int(round(DUR * FPS))
SR = 44100

# ---------------- 1. muzyka: intro (pozytywka) + funk (tamborzao) ----------------
def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def kick(n=int(.4 * SR)):
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .001, .16) * 1.1

def bass808(freq, n=int(.42 * SR)):
    t = np.arange(n) / SR
    f = freq * (1 + .5 * np.exp(-t / .02))
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .003, .22) * .55

def clap(n=int(.2 * SR), rng=np.random.default_rng(1)):
    x = rng.normal(0, 1, n)
    x = x - np.concatenate([[0], x[:-1]]) * .9            # gora pasma
    e = np.zeros(n)
    for o in (0, .011, .022):
        k = int(o * SR); e[k:] += env(n - k, .0005, .012 if o < .02 else .07)
    return x * e * .35

def hat(n=int(.05 * SR), rng=np.random.default_rng(2)):
    x = rng.normal(0, 1, n); x = x - np.concatenate([[0], x[:-1]])
    return x * env(n, .0005, .012) * .12

def cowbell(freq, n=int(.28 * SR)):
    t = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * freq * t)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    return sq * env(n, .001, .09) * .11

def musicbox(freq, n=int(.9 * SR)):
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + .3 * np.sin(4 * np.pi * freq * t)) * env(n, .003, .35) * .22

N = int(DUR * SR) + SR
mix = np.zeros(N)
def put(x, t, g=1.0):
    i = int(t * SR); j = min(N, i + len(x)); mix[i:j] += x[:j - i] * g

notes = [659.3, 784.0, 880.0, 784.0, 659.3, 587.3, 523.3, 587.3]            # spokojne intro
for k in range(int(DROP / (BEAT / 2))):
    put(musicbox(notes[k % len(notes)]), k * BEAT / 2, .9 if k % 2 == 0 else .6)
S16 = BEAT / 4
KICK = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]                      # tamborzao 3-3-4-3-3
CLAP = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
BASS = [55.0, 55.0, 65.4, 49.0]                                               # A, A, C, G
BELL = [880, 0, 0, 1175, 0, 0, 988, 0, 880, 0, 0, 1175, 0, 1319, 0, 0]
for b in range(NBEATS // 4):                                                  # takty po 4 bity
    t0 = DROP + b * 4 * BEAT
    for s in range(16):
        ts = t0 + s * S16
        if KICK[s]: put(kick(), ts); put(bass808(BASS[b % 4]), ts)
        if CLAP[s]: put(clap(), ts)
        if s % 2 == 0: put(hat(), ts, 1.4 if s % 4 == 2 else .8)
        if BELL[s]: put(cowbell(BELL[s]), ts)
put(clap(), DROP - S16, .8); put(clap(), DROP - 2 * S16, .5)                   # podbicie przed dropem
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix[int((DUR - .3) * SR):] *= np.linspace(1, 0, len(mix) - int((DUR - .3) * SR))
WAV = OUT + '.wav'
with wave.open(WAV, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix[:int(DUR * SR)], -1, 1) * 27500).astype(np.int16).tobytes())

# ---------------- 2. postac: wycinanka w kolorze z bialym obrysem ----------------
im = Image.open(SRC).convert('RGB')
x0, y0, x1, y1 = RECT
FIG = kolaz.sticker(im, (int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1) - 1), outline=12)
FIG = FIG.resize((900, int(900 * FIG.height / FIG.width)), Image.LANCZOS)
if FIG.height > 1300: FIG = FIG.resize((int(FIG.width * 1300 / FIG.height), 1300), Image.LANCZOS)

# ---------------- 3. animacja: pozy na kazdy bit ----------------
def back(u, s=2.2):                                   # ease-out z przestrzeleniem (sprezyna)
    u = min(max(u, 0.0), 1.0) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2
def elastic(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - math.exp(-6 * u) * math.cos(14 * u)

# poza = (sx, sy, rot, dx, dy, flip); ruchy w cyklu na kolejne bity
POSES = [(1.35, .7, 0, 0, 120, 1), (.75, 1.35, -18, -60, -260, 1), (1.0, 1.0, 360, 0, -40, 1), (1.4, .75, 22, 160, 60, -1),
         (.8, 1.3, -30, -170, -200, -1), (1.6, 1.6, 8, 0, -100, 1), (1.0, 1.0, -360, 0, 0, 1), (1.25, .8, 0, 0, 140, 1),
         (.7, 1.45, 15, 120, -300, 1), (1.1, 1.1, 720, 0, -60, -1), (1.5, .65, -12, -140, 160, 1), (1.0, 1.0, 0, 0, -20, 1)]
REST = (1.0, 1.0, 0, 0, 0, 1)

def pose(t):
    if t < DROP:                                      # "moj tweening": lagodne kolysanie
        u = t / BEAT
        return (1 + .025 * math.sin(u * math.pi), 1 - .02 * math.sin(u * math.pi), 4 * math.sin(u * math.pi / 2),
                0, -18 * abs(math.sin(u * math.pi / 2)), 1)
    k = int((t - DROP) // BEAT); u = (t - DROP - k * BEAT) / BEAT
    a = POSES[(k - 1) % len(POSES)] if k > 0 else REST
    b = POSES[k % len(POSES)]
    e = back(u / .45) if abs(b[2] - a[2]) < 200 else elastic(u / .6)
    p = [a[i] + (b[i] - a[i]) * e for i in range(5)]
    if u > .55:                                       # w drugiej polowie bitu wraca do srodka (sprezyna)
        r = back((u - .55) / .45, 1.6)
        p = [p[i] + (REST[i] - p[i]) * r * (.85 if i < 2 else .7) for i in range(5)]
        p[2] = p[2] % 360 if abs(p[2]) > 300 else p[2]
    flip = b[5] if u < .55 else 1
    wob = 1 + .06 * math.sin(u * 2 * math.pi * 2) * (1 - u)   # drganie miedzy uderzeniami
    return (p[0] * wob, p[1] / wob, p[2], p[3], p[4], flip)

def draw_fig(base, ps, alpha=1.0):
    sx, sy, rot, dx, dy, flip = ps
    f = FIG.transpose(Image.FLIP_LEFT_RIGHT) if flip < 0 else FIG
    f = f.resize((max(2, int(f.width * sx)), max(2, int(f.height * sy))), Image.BICUBIC)
    f = f.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1: f.putalpha(f.getchannel('A').point(lambda v: int(v * alpha)))
    base.alpha_composite(f, (int(W / 2 + dx - f.width / 2), int(H * .56 + dy - f.height / 2)))

BG = [(255, 214, 0), (0, 200, 255), (255, 70, 160), (120, 255, 90), (160, 90, 255)]
yy, xx = np.mgrid[0:H, 0:W]
RAD = np.clip(1 - np.hypot((xx - W / 2) / W, (yy - H * .55) / H) * 1.5, 0, 1)[..., None]

def background(t):
    if t < DROP:                                      # spokojne, pastelowe
        c0, c1 = np.array([236, 230, 255.]), np.array([196, 214, 250.])
        return Image.fromarray((c1 + (c0 - c1) * RAD).astype(np.uint8)).convert('RGBA')
    k = int((t - DROP) // BEAT); bar = k // 4
    c = np.array(BG[bar % len(BG)], float)
    u = (t - DROP - k * BEAT) / BEAT
    pulse = max(0.0, 1 - u / .25)                     # rozblysk na uderzeniu
    img = c * (.55 + .45 * RAD) + (255 - c) * .5 * pulse
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

def frame(fi):
    t = fi / FPS
    base = background(t)
    if t >= DROP:                                     # smugi: poprzednie pozy jako duchy (slop)
        for lag, a in ((.07, .22), (.035, .38)):
            draw_fig(base, pose(t - lag), a)
    draw_fig(base, pose(t))
    if t >= DROP:                                     # zoom kamery na uderzenie
        u = ((t - DROP) % BEAT) / BEAT
        z = 1 + .07 * max(0.0, 1 - u / .2)
        if z > 1.001:
            bw_, bh_ = int(W * z), int(H * z)
            base = base.resize((bw_, bh_), Image.BILINEAR).crop(((bw_ - W) // 2, (bh_ - H) // 2, (bw_ - W) // 2 + W, (bh_ - H) // 2 + H))
    fr = np.array(base.convert('RGB'))
    if DROP <= t < DROP + .12:                        # bialy blysk na dropie
        fr = (fr + (255 - fr.astype(float)) * (1 - (t - DROP) / .12)).astype(np.uint8)
    return fr

if os.environ.get('PODGLAD'):
    for ts in os.environ['PODGLAD'].split(','):
        Image.fromarray(frame(int(round(float(ts) * FPS)))).save(f'{OUT}_{ts}.png')
    sys.exit(0)

enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                        '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-t', f'{NF / FPS:.4f}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    enc.stdin.write(frame(fi).tobytes())
enc.stdin.close(); enc.wait()
os.remove(WAV)
print('gotowe:', OUT, f'| drop {DROP} s, {NBEATS} bitow po {BEAT:.3f} s, {NF / FPS:.2f} s')
