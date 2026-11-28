# tweenslop.py  -  uzycie:
#   python3 src/tweenslop.py POSTAC wynik.mp4        POSTAC: magnus | fischer (zdjecia z wejscie/zdjecia, src/pobierz_zdjecia.py)
# Edit "tweenslop" jak we wzorach z wejscie/tweenslop/ (t1-t6): spokojny wstep, drop brazylijskiego phonku/funku,
# potem co takt inne tlo (wzgorza, kalejdoskop z promieniami, korytarz z szachownica, plamy oleju, szybkie ciecia),
# wycinanki z bialym obrysem, ktore lataja, kreca sie, rozciagaja; kolorowe nakladki na bit, smugi, piksele, wielkie oczy.
# Muzyka i wszystkie tla generowane w tym skrypcie (wlasny utwor, bez cudzych nagran i grafik). Bez napisow.
import os, sys, math, subprocess, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from scipy import signal, ndimage
import kolaz
from assets import sprites as SPR

POSTAC, OUT = sys.argv[1:3]
ZDJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wejscie', 'zdjecia')
POSTACIE = {   # zdjecie, sposob wyciecia, oczy na ZDJECIU (ulamki), tempo i tonacja wlasnego utworu, tlo pierwszego taktu
    'magnus': dict(plik='magnus_usmiech.jpg', rect=(.03, .06, .78, 1.0), oczy=[(.517, .375), (.671, .373)],
                   bpm=130.0, rdzen=43.65, mel=[349.2, 415.3, 523.3, 466.2, 415.3, 349.2, 311.1, 349.2], tlo0='wzgorza'),
    'fischer': dict(plik='fischer_usmiech.jpg', oczy=[(.318, .312), (.386, .305)],
                    fg=[('e', .35, .33, .055, .10), ('r', .14, .66, .42, .99), ('r', .30, .45, .40, .6), ('r', .06, .68, .2, .99)],
                    bg=[('r', .56, 0, 1, 1), ('r', 0, 0, 1, .10), ('p', [(0, .10), (.25, .10), (.25, .46), (.12, .53), (0, .57)]),
                        ('r', .47, .13, .56, .55)],
                    bpm=140.0, rdzen=36.71, mel=[293.7, 349.2, 440.0, 392.0, 349.2, 293.7, 261.6, 293.7], tlo0='flaga'),
}
P = POSTACIE[POSTAC]
W, H, FPS, SR = 1080, 1920, 30, 44100
BPM = P['bpm']; B = 60 / BPM; S16 = B / 4
DROP = 6 * B                                 # 2,77 s spokojnego wstepu
SEC = [DROP + 4 * B * k for k in range(6)]   # poczatki taktow po dropie: wzgorza, kalejdoskop, korytarz, olej, ciecia
END_HITS = SEC[5]                            # 12,0 s: koncowka
DUR = END_HITS + 3 * B + .0
NF = int(round(DUR * FPS))
rng = np.random.default_rng(11)

# =============================== 1. MUZYKA ===============================
def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def sine_sweep(f0, f1, n, tau):
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / tau)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)

def kick():
    n = int(.35 * SR)
    return np.tanh(3 * sine_sweep(190, 48, n, .025) * env(n, .001, .14)) * .9

def bass808(f, dur, glide=None):
    n = int(dur * SR); t = np.arange(n) / SR
    ff = np.full(n, f) if glide is None else f * (glide / f) ** np.clip(t / dur * 1.6 - .4, 0, 1)
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR)
    return np.tanh(2.6 * x) * env(n, .004, dur * .7) * .5

def noise(n): return rng.normal(0, 1, n)
SOS_HP = signal.butter(2, 3000, 'hp', fs=SR, output='sos')
SOS_CL = signal.butter(2, [900, 3500], 'bp', fs=SR, output='sos')
def clap():
    n = int(.22 * SR); x = signal.sosfilt(SOS_CL, noise(n)); e = np.zeros(n)
    for o in (0, .009, .018):
        k = int(o * SR); e[k:] += env(n - k, .0004, .01 if o < .018 else .08)
    return x * e * .9
def hat(open_=False):
    n = int((.18 if open_ else .05) * SR)
    return signal.sosfilt(SOS_HP, noise(n)) * env(n, .0004, .06 if open_ else .012) * .35
def tom(f=230):
    n = int(.18 * SR)
    return sine_sweep(f * 1.6, f, n, .02) * env(n, .001, .06) * .45
def cowbell(f):
    n = int(.3 * SR); t = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    return signal.sosfilt(signal.butter(2, [f * .8, f * 3], 'bp', fs=SR, output='sos'), x) * env(n, .001, .1) * .35
def lead(f, dur, bend=-3.0):                 # "falujacy" lead automotivo: 3 pily, wibrato, zjazd na koncu
    n = int(dur * SR); t = np.arange(n) / SR
    semi = .45 * np.sin(2 * np.pi * 6.5 * t) + bend * np.clip((t / dur - .6) / .4, 0, 1) ** 2
    out = 0
    for det in (-.12, 0, .13):
        ph = np.cumsum(f * 2 ** ((semi + det) / 12)) / SR
        out = out + (2 * (ph % 1) - 1)
    out = signal.sosfilt(signal.butter(2, 2600, 'lp', fs=SR, output='sos'), out)
    return np.tanh(1.8 * out / 3) * env(n, .005, dur * .55) * .32
FORM = {'a': (800, 1150), 'o': (450, 800), 'e': (400, 2000), 'i': (300, 2300), 'u': (325, 700)}
def vox(vowel, f, dur):                      # "wokal" z syntezy formantowej (sieczka jak w montagem)
    n = int(dur * SR); t = np.arange(n) / SR
    ph = np.cumsum(f * 2 ** (.25 * np.sin(2 * np.pi * 5 * t) / 12)) / SR
    src = 2 * (ph % 1) - 1
    out = 0
    for fc, g in zip(FORM[vowel], (1.0, .6)):
        out = out + g * signal.sosfilt(signal.butter(2, [fc * .85, fc * 1.15], 'bp', fs=SR, output='sos'), src)
    return np.tanh(2.2 * out) * env(n, .008, dur * .45) * .5
def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = noise(n); out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        fc = 300 * (6000 / 300) ** (i / n)
        out[i:i + blk] = signal.sosfilt(signal.butter(2, [fc * .7, min(fc * 1.4, SR / 2 - 100)], 'bp', fs=SR, output='sos'), x[i:i + blk])
    return out * (t / dur) ** 2 * .5
def crash():
    n = int(1.2 * SR)
    return signal.sosfilt(signal.butter(2, 5000, 'hp', fs=SR, output='sos'), noise(n)) * env(n, .001, .35) * .35

N = int((DUR + 1) * SR); mix = np.zeros(N)
def put(x, t, g=1.0):
    i = int(t * SR)
    if i >= N: return
    j = min(N, i + len(x)); mix[i:j] += x[:j - i] * g

R = P['rdzen']                                                                # tonika basu (F1 albo D1)
F1, Ab1, C2, Db2, Eb2 = R, R * 2 ** (3 / 12), R * 2 ** (7 / 12), R * 2 ** (8 / 12), R * 2 ** (10 / 12)
MEL = P['mel']                                                                # mol (f albo d)
# wstep: siekane samogloski, przytlumione, + riser
for k in range(12):
    v = 'aoaeaoiu'[k % 8]
    put(vox(v, MEL[k % 8] / 2, B / 2 * .9), k * B / 2, .55 if k % 2 else .8)
put(riser(4 * B), DROP - 4 * B, .9)
KICK = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0]                        # tamborzao
TOM = [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
LEAD = [0, 3, 6, 10, 13]
VOXS = [2, 7, 11, 14]
BASS = [(F1, None), (F1, Ab1), (Db2, None), (Eb2, C2)]
BELL = [m * 2 if m else 0 for m in (MEL[0], 0, 0, MEL[1], 0, 0, MEL[3], 0, MEL[0], 0, 0, MEL[1], 0, MEL[2], 0, 0)]
for bar in range(5):
    t0 = SEC[bar]
    stop = bar == 2                                                           # przerwa przed drugim dropem
    put(crash(), t0, .9 if bar in (0, 3) else .4)
    for s in range(16):
        ts = t0 + s * S16
        if stop and s >= 12:
            continue
        if KICK[s]:
            put(kick(), ts); bn, gl = BASS[bar % 4]
            put(bass808(bn, S16 * 3.2, gl), ts)
        if TOM[s]: put(tom(230 if s < 8 else 260), ts)
        if s in (4, 12): put(clap(), ts)
        put(hat(open_=(s % 8 == 6)), ts, 1.0 if s % 4 == 2 else .55)
        if s in LEAD: put(lead(MEL[(s + bar * 3) % 8], S16 * 2.4, -4 if s == 13 else -1.5), ts)
        if s in VOXS: put(vox('aoea'[VOXS.index(s)], MEL[(s + bar) % 8], S16 * 1.6), ts, .8)
        if bar >= 3 and BELL[s]: put(cowbell(BELL[s]), ts)
    if stop:
        put(vox('o', 415.3, B * .9), t0 + 12 * S16, .9); put(riser(B), t0 + 12 * S16, .7)
for k, ts in enumerate([END_HITS, END_HITS + B, END_HITS + 1.5 * B]):        # koncowe uderzenia
    put(kick(), ts); put(bass808(F1, B * 1.5), ts); put(crash(), ts, .5); put(vox('a', MEL[k], B * .8), ts, .7)
mix = np.tanh(mix * 1.5)
mix = mix / (np.abs(mix).max() + 1e-9) * .89
mix[int((DUR - .25) * SR):int(DUR * SR)] *= np.linspace(1, 0, int(DUR * SR) - int((DUR - .25) * SR))
WAV = OUT + '.wav'
with wave.open(WAV, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix[:int(DUR * SR)] * 32767).astype(np.int16).tobytes())

# =============================== 2. POSTACIE ===============================
im = Image.open(os.path.join(ZDJ, P['plik'])).convert('RGB')
if 'fg' in P:
    FIG = kolaz.sticker_hints(im, P['fg'], P['bg'], outline=12)
else:
    x0, y0, x1, y1 = P['rect']
    FIG = kolaz.sticker(im, (int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1) - 1), outline=12)
bx0, by0 = FIG.info.get('bbox', (0, 0, 0, 0))[:2]
EYES = [((ex * im.width - bx0) / FIG.width, (ey * im.height - by0) / FIG.height) for ex, ey in P['oczy']]
FIG = FIG.resize((900, int(900 * FIG.height / FIG.width)), Image.LANCZOS)
if FIG.height > 1500: FIG = FIG.resize((int(FIG.width * 1500 / FIG.height), 1500), Image.LANCZOS)

def piece_sticker(p, size=420, outline=10):           # figura szachowa jako naklejka z bialym obrysem
    rgb, a = SPR[p]
    pim = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA').resize((size, size), Image.LANCZOS)
    al = np.asarray(pim.getchannel('A')) > 40
    ring = ndimage.binary_dilation(al, iterations=outline)
    out = Image.new('RGBA', pim.size, (0, 0, 0, 0))
    out.paste((255, 255, 255, 255), (0, 0), Image.fromarray((ring * 255).astype(np.uint8)))
    out.alpha_composite(pim)
    return out
PIECES = [piece_sticker(p) for p in ('wN', 'bQ', 'wK', 'bN', 'wQ', 'bK')]

def bulge(fig, k):                                    # "wielkie oczy": lokalne powiekszenie wokol oczu
    if k <= 0: return fig
    a = np.asarray(fig).astype(float); out = a.copy()
    R = int(fig.width * .085)
    for fx, fy in EYES:
        cx, cy = fx * fig.width, fy * fig.height
        xs, ys = int(cx - R), int(cy - R)
        yy, xx = np.mgrid[ys:ys + 2 * R, xs:xs + 2 * R].astype(float)
        dx, dy = xx - cx, yy - cy; r = np.hypot(dx, dy) / R
        f = np.where(r < 1, np.clip(r, 1e-3, 1) ** k, 1.0)          # probkuje blizej srodka -> powiekszenie
        sx, sy = cx + dx * f, cy + dy * f
        for c in range(4):
            out[ys:ys + 2 * R, xs:xs + 2 * R, c] = ndimage.map_coordinates(a[:, :, c], [sy, sx], order=1)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')

def place(base, fig, x, y, sx=1.0, sy=1.0, rot=0.0, alpha=1.0, flip=False):
    f = fig.transpose(Image.FLIP_LEFT_RIGHT) if flip else fig
    f = f.resize((max(2, int(f.width * sx)), max(2, int(f.height * sy))), Image.BICUBIC)
    if rot: f = f.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1: f.putalpha(f.getchannel('A').point(lambda v: int(v * alpha)))
    base.alpha_composite(f, (int(x - f.width / 2), int(y - f.height / 2)))

# =============================== 3. TLA (wlasne, z kodu) ===============================
hw, hh = W // 2, H // 2
YY, XX = np.mgrid[0:hh, 0:hw].astype(float)
def up(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert('RGBA')

def make_hills():
    sky = np.zeros((hh, hw, 3)); g = YY / hh
    sky[:] = (np.array([40, 110, 220.]) * (1 - g[..., None]) + np.array([170, 215, 255.]) * g[..., None])
    for _ in range(9):                                # chmury
        cx, cy, r = rng.uniform(0, hw), rng.uniform(0, hh * .45), rng.uniform(25, 70)
        m = np.exp(-(((XX - cx) / (r * 2.2)) ** 2 + ((YY - cy) / r) ** 2))
        sky = sky * (1 - m[..., None] * .8) + 255 * m[..., None] * .8
    for base_y, amp, col0, col1, ph in ((.62, 40, (70, 160, 40), (40, 120, 25), .3), (.74, 55, (90, 190, 50), (50, 140, 30), 2.1)):
        top = hh * base_y + amp * np.sin(XX[0] / hw * 3.1 + ph) + amp * .4 * np.sin(XX[0] / hw * 7 + ph * 2)
        m = YY > top[None, :]
        gg = np.clip((YY - top[None, :]) / (hh * .35), 0, 1)[..., None]
        sky = np.where(m[..., None], np.array(col0) * (1 - gg) + np.array(col1) * gg, sky)
    return up(sky)
HILLS = make_hills()

def make_flag():                                      # wlasna, rysowana flaga USA (13 pasow, kanton z gwiazdkami)
    from PIL import ImageDraw
    fw, fh = 1300, 2000
    f = Image.new('RGB', (fw, fh), (255, 255, 255)); d = ImageDraw.Draw(f)
    sh = fh / 13
    for i in range(0, 13, 2): d.rectangle((0, i * sh, fw, (i + 1) * sh), fill=(191, 13, 48))
    cw, ch = fw * .6, sh * 7
    d.rectangle((0, 0, cw, ch), fill=(10, 49, 97))
    for r in range(9):
        for c in range(6 if r % 2 == 0 else 5):
            x = cw / 12 * (2 * c + 1 + (r % 2)); y = ch / 10 * (r + 1); R_ = sh * .28
            pts = [(x + R_ * (1 if k % 2 == 0 else .4) * math.cos(-math.pi / 2 + k * math.pi / 5),
                    y + R_ * (1 if k % 2 == 0 else .4) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
            d.polygon(pts, fill=(255, 255, 255))
    return np.asarray(f.resize((hw + 80, hh + 80))).astype(float)
FLAG = make_flag()
def flag(t):                                          # falowanie: przesuniecie kolumn + cieniowanie fal
    xs = np.arange(hw)
    off = (22 * np.sin(xs / 55 - t * 5) + 10 * np.sin(xs / 23 - t * 7)).astype(int) + 40
    rows = np.clip(np.arange(hh)[:, None] + off[None, :], 0, hh + 79)
    img = FLAG[rows, xs[None, :] + 40]
    shade = 1 + .18 * np.cos(xs / 55 - t * 5)[None, :, None]
    return up(img * shade)

def rays(t, c1, c2):
    ang = np.arctan2(YY - hh * .5, XX - hw * .5)
    st = (np.sin(ang * 14 + t * 2.5) > 0)[..., None]
    r = np.hypot(XX - hw * .5, YY - hh * .5)[..., None] / (hh * .7)
    a = np.where(st, np.array(c1, float), np.array(c2, float)) * (1 - .35 * r) + 255 * np.clip(1 - r * 2.2, 0, 1) * .6
    return up(a)

def hallway(t):                                       # korytarz z szachownica w perspektywie (jak korytarze ze wzorow)
    hz = hh * .40
    img = np.zeros((hh, hw, 3))
    wall = np.array([236, 233, 226.]) - 30 * (np.abs(XX - hw / 2) / hw)[..., None]
    img[:] = wall
    floor = YY > hz
    z = 260.0 / np.maximum(YY - hz, 1)
    xw = (XX - hw / 2) * z / 90
    zw = z * 6 + t * 7
    chk = ((np.floor(xw) + np.floor(zw)) % 2 == 0)[..., None]
    fc = np.where(chk, np.array([238, 238, 210.]), np.array([118, 150, 85.]))
    fog = np.clip((YY - hz) / (hh - hz), 0, 1)[..., None] ** .5
    fc = fc * fog + wall * (1 - fog)
    img = np.where(floor[..., None], fc, img)
    for side in (-1, 1):                              # ciemniejsze sciany boczne
        edge = np.abs(XX - hw / 2) > (hw * .18 + (YY - hz) * .9 * (YY > hz))
        img = np.where((edge & (YY < hz + (np.abs(XX - hw / 2) - hw * .18) / .9))[..., None], img * .85, img)
    return up(img)

def oil(t):                                           # psychodeliczne plamy oleju (warping szumu)
    x, y = XX[::2, ::2] / 60, YY[::2, ::2] / 60
    for k in range(3):
        x, y = x + .8 * np.sin(y * 1.3 + t * .9 + k), y + .8 * np.sin(x * 1.1 - t * .7 + k * 2)
    v = np.sin(x * .9 + np.sin(y * .7)) + np.sin(y * 1.1 + t * .5)
    h = (v * .18 + t * .08) % 1
    rgb = np.stack([.5 + .5 * np.cos(2 * np.pi * (h + o)) for o in (0, .33, .67)], -1)
    rgb = .55 + .45 * rgb
    return Image.fromarray((rgb * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert('RGBA')

def mosaic(seed, white=0.0):
    r = np.random.default_rng(seed)
    blk = r.uniform(.55, 1, (H // 60 + 1, W // 60 + 1, 3)) * 255
    blk = blk * (1 - white) + 255 * white
    return Image.fromarray(blk.astype(np.uint8)).resize((blk.shape[1] * 60, blk.shape[0] * 60), Image.NEAREST).crop((0, 0, W, H)).convert('RGBA')

TINTS = [(255, 230, 40), (60, 255, 120), (80, 170, 255), (190, 90, 255), (255, 80, 90)]
def tint(img, col, a=.42):
    arr = np.asarray(img.convert('RGB')).astype(float)
    g = arr.mean(2, keepdims=True)
    t_ = g * np.array(col) / 255 * 1.25
    return Image.fromarray(np.clip(arr * (1 - a) + t_ * a, 0, 255).astype(np.uint8)).convert('RGBA')

# =============================== 4. ANIMACJA ===============================
def back(u, s=2.0):
    u = min(max(u, 0.0), 1.0) - 1
    return 1 + (s + 1) * u ** 3 + s * u ** 2
def beat_info(t):
    k = int(math.floor((t - DROP) / B)); u = (t - DROP - k * B) / B
    return k, u
def squash(u):                                        # zgniecenie na uderzeniu, potem sprezyna
    e = math.exp(-u * 7) * math.cos(u * 18)
    return 1 + .32 * e, 1 - .26 * e

def frame(fi):
    t = fi / FPS
    if t < DROP:                                      # "moj tweening": maly Magnus na bialym, spokojnie
        base = Image.new('RGBA', (W, H), (250, 250, 250, 255))
        u = t / B
        z = .42 + .05 * t / DROP
        sx, sy = 1 + .03 * math.sin(u * math.pi), 1 - .03 * math.sin(u * math.pi)
        place(base, FIG, W / 2, H * .55 - 20 * abs(math.sin(u * math.pi / 2)), z * sx, z * sy, 5 * math.sin(u * math.pi / 2))
        if t > DROP - B:                              # zapowiedz: nabiera powietrza
            v = (t - (DROP - B)) / B
            base = base.resize((int(W * (1 + .15 * v)), int(H * (1 + .15 * v))), Image.BICUBIC)
            base = base.crop(((base.width - W) // 2, (base.height - H) // 2, (base.width - W) // 2 + W, (base.height - H) // 2 + H))
        return np.array(base.convert('RGB'))
    k, u = beat_info(t)
    sec = min(int((t - DROP) // (4 * B)), 5)
    ssx, ssy = squash(u)
    if sec == 0:                                      # wzgorza / flaga: postac leci po okregu + latajace kopie
        base = flag(t) if P['tlo0'] == 'flaga' else HILLS.copy()
        for j in range(4):
            p = ((t - DROP) * .45 + j * .27) % 1.2 - .1
            place(base, FIG, W * (1.1 - p * 1.2), H * (.85 - p * .7) + 60 * math.sin(t * 3 + j), .22, .22, (t * 240 + j * 90) % 360, .95)
        a = (t - DROP) / (4 * B) * 2 * math.pi
        for lag, al in ((.12, .25), (.06, .45), (0, 1.0)):
            aa = a - lag * 3
            place(base, FIG, W / 2 + 260 * math.cos(aa), H * .5 + 380 * math.sin(aa), .55 * ssx, .55 * ssy, math.degrees(aa) * .6, al)
    elif sec == 1:                                    # kalejdoskop: 4 kopie na promieniach, kolor co bit
        col = TINTS[k % len(TINTS)]
        base = rays(t, col, tuple(int(c * .55) for c in col))
        grot = 45 * k + 45 * back(u / .4)
        for j in range(4):
            ang = math.radians(grot + 90 * j)
            place(base, FIG, W / 2 + 300 * math.cos(ang), H / 2 + 300 * math.sin(ang), .4 * ssx, .4 * ssy, -(grot + 90 * j) + 90)
        place(base, FIG, W / 2, H / 2, .32 * ssy, .32 * ssx, 20 * math.sin(t * 6))
    elif sec == 2:                                    # korytarz z szachownica: figury skacza, Magnus podskakuje
        base = hallway(t)
        for j, pc in enumerate(PIECES[:4]):
            ph = (u + j * .25) % 1
            jump = abs(math.sin(ph * math.pi))
            place(base, pc, W * (.2 + .2 * j), H * .78 - 420 * jump, .7, .7 * (1 + .25 * (1 - jump)), 25 * math.sin(t * 5 + j), flip=(k + j) % 2 == 1)
        hop = abs(math.sin(u * math.pi))
        place(base, FIG, W / 2, H * .62 - 260 * hop, .62 * ssx, .62 * ssy, 12 * math.sin(t * 8), flip=k % 2 == 1)
    elif sec == 3:                                    # plamy oleju + wielkie oczy, glitch pikseli
        base = oil(t)
        big = bulge(FIG, .7 + .5 * math.exp(-u * 5))
        shake = 18 * math.exp(-u * 6)
        place(base, big, W / 2 + shake * math.sin(t * 90), H * .52 + shake * math.cos(t * 70), 1.0 * ssx, 1.0 * ssy, 6 * math.sin(t * 9))
        for j, pc in enumerate(PIECES[4:]):
            place(base, pc, W * (.18 + .64 * j), H * (.2 + .05 * math.sin(t * 4 + j)), .55, .55, (t * 200 * (1 if j else -1)) % 360)
    elif sec == 4:                                    # szybkie ciecia: co bit inne tlo i poza
        kind = k % 4
        base = [flag(t) if P['tlo0'] == 'flaga' else HILLS.copy(), rays(t, (255, 120, 200), (120, 40, 160)), hallway(t), oil(t)][kind]
        poses = [(1.3, .7, 0, 0, 120), (.75, 1.35, -20, -80, -200), (1, 1, 360 * back(u / .5), 0, 0), (1.4, .75, 25, 120, 60)]
        sx, sy, rot, dx, dy = poses[kind]
        e = back(u / .35)
        sx, sy = 1 + (sx - 1) * e * (1 - u), 1 + (sy - 1) * e * (1 - u)
        for lag, al in ((.08, .3), (0, 1.0)):
            place(base, FIG, W / 2 + dx * (1 - u + lag), H * .55 + dy * (1 - u + lag), .7 * sx, .7 * sy, rot * (1 if lag == 0 else .7), al, flip=k % 2 == 1)
        base = tint(base, TINTS[(k + 2) % len(TINTS)], .35)
    else:                                             # koniec: rozpad na piksele do bialego, Magnus odlatuje krecac sie
        v = (t - END_HITS) / (DUR - END_HITS)
        base = mosaic(k, white=min(1.0, v * 1.3))
        place(base, FIG, W / 2, H * .55, .7 * (1 - v * .8), .7 * (1 - v * .8), 720 * v ** 1.5, 1 - v ** 3)
    # zoom kamery na uderzenie + bialy blysk na poczatku kazdego taktu
    z = 1 + .08 * math.exp(-u * 9)
    if z > 1.002:
        bw_, bh_ = int(W * z), int(H * z)
        base = base.resize((bw_, bh_), Image.BILINEAR).crop(((bw_ - W) // 2, (bh_ - H) // 2, (bw_ - W) // 2 + W, (bh_ - H) // 2 + H))
    fr = np.asarray(base.convert('RGB')).astype(float)
    if sec in (1, 3) and k % 2 == 1 and .45 < u < .58:   # glitch: pikselizacja na pol-bicie
        small = Image.fromarray(fr.astype(np.uint8)).resize((W // 28, H // 28), Image.NEAREST)
        fr = np.asarray(small.resize((W, H), Image.NEAREST)).astype(float)
    tb = (t - DROP) % (4 * B)
    if tb < .14: fr = fr + (255 - fr) * (1 - tb / .14)
    return np.clip(fr, 0, 255).astype(np.uint8)

if os.environ.get('PODGLAD'):
    for ts in os.environ['PODGLAD'].split(','):
        Image.fromarray(frame(int(round(float(ts) * FPS)))).save(f'{OUT}_{ts}.png')
    os.remove(WAV); sys.exit(0)

enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                        '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-t', f'{NF / FPS:.4f}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    enc.stdin.write(frame(fi).tobytes())
enc.stdin.close(); enc.wait()
os.remove(WAV)
print('gotowe:', OUT, f'| {BPM:.0f} BPM, drop {DROP:.2f} s, {NF / FPS:.2f} s')
