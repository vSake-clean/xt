"""Rozbiera filmik-wzor na liczby: plansza, ciecia i blyski, momenty ruchow na polach, muzyka.

Uzycie:  python3 src/analiza_wzoru.py WZOR.mp4 [katalog_wyniku]
Wynik:   katalog (domyslnie analiza_<nazwa>/) z arkuszami klatek (arkusz*.png), klatkami po kazdej
         zmianie na planszy (plansza_*.png) i podsumowaniem analiza.json; najwazniejsze rzeczy idzie tez na ekran.
"""
import os, sys, json, subprocess
import numpy as np
from PIL import Image

def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate',
                          '-show_entries', 'format=duration', '-of', 'json', path], capture_output=True, text=True).stdout
    j = json.loads(out)
    v = [s for s in j['streams'] if s['codec_type'] == 'video'][0]
    num, den = v['r_frame_rate'].split('/')
    return dict(w=int(v['width']), h=int(v['height']), fps=float(num) / float(den),
                duration=float(j['format']['duration']), audio=any(s['codec_type'] == 'audio' for s in j['streams']))

def frames(path, w, h, gray=False):
    fmt, ch = ('gray', 1) if gray else ('rgb24', 3)
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-vf', f'scale={w}:{h}', '-f', 'rawvideo',
                          '-pix_fmt', fmt, '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8)
    return a.reshape(-1, h, w) if gray else a.reshape(-1, h, w, ch)

def find_board(rgb):
    """Prostokat planszy: wiersze i kolumny wyraznie jasniejsze od czarnego tla."""
    g = rgb.mean(2)
    rows = np.nonzero(g.mean(1) > 40)[0]
    if len(rows) == 0:
        return 0, 0, rgb.shape[1], rgb.shape[0]
    y0, y1 = rows.min(), rows.max() + 1
    cols = np.nonzero(g[y0:y1].mean(0) > 40)[0]
    return int(cols.min()), int(y0), int(cols.max() + 1), int(y1)

def audio_stats(path, sr=22050):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float)
    if len(a) < sr:
        return None
    loud = [round(float(np.sqrt((a[i:i + sr // 2] ** 2).mean())), 0) for i in range(0, len(a) - sr // 2, sr // 2)]
    hop, n = 512, 2048
    fr = np.lib.stride_tricks.sliding_window_view(a, n)[::hop] * np.hanning(n)
    spec = np.abs(np.fft.rfft(fr, axis=1))
    low = spec[:, 1:12].sum(1)                                   # bas < ~120 Hz
    flux = np.maximum(np.diff(np.log1p(low)), 0)
    t = np.arange(len(flux)) * hop / sr
    thr = flux.mean() + 2 * flux.std()
    onsets = []
    for i in range(1, len(flux) - 1):
        if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1] and (not onsets or t[i] - onsets[-1] > 0.15):
            onsets.append(round(float(t[i]), 2))
    f = flux - flux.mean()
    ac = np.correlate(f, f, 'full')[len(f) - 1:]
    lags = np.arange(len(ac)) * hop / sr
    m = (lags > 0.25) & (lags < 1.5)
    beat = float(lags[m][np.argmax(ac[m])]) if m.any() else None
    return dict(glosnosc_co_0_5s=loud, onsety_basu=onsets, okres_beatu_s=round(beat, 4) if beat else None,
                bpm=round(60 / beat, 1) if beat else None)

def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'analiza_' + os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out, exist_ok=True)
    info = probe(path)
    fps = info['fps']
    print(f"Plik: {path}\n  {info['w']}x{info['h']}, {fps:.2f} kl./s, {info['duration']:.2f} s, audio: {info['audio']}")

    # arkusz podgladu: 2 klatki na sekunde
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', path, '-vf', 'fps=2,scale=160:-1,tile=10x6',
                    os.path.join(out, 'arkusz%d.png')])

    # klatki w malej rozdzielczosci (szybko), plansza z klatki ze srodka filmu
    sw = 288
    sh = int(round(info['h'] * sw / info['w'] / 2) * 2)
    small = frames(path, sw, sh).astype(float)
    n = len(small)
    bright = small.mean((1, 2, 3))
    ref = int(np.argmax(bright[: max(1, n // 2)] > 30)) if (bright > 30).any() else n // 2
    full = frames(path, info['w'], info['h'])[min(ref + 5, n - 1)]
    x0, y0, x1, y1 = find_board(full)
    print(f"  plansza: x {x0}-{x1}, y {y0}-{y1} (pole ok. {(x1 - x0) / 8:.1f} x {(y1 - y0) / 8:.1f} px)")

    # ciecia, blyski, wyciemnienia
    g = small.mean(3)
    d = np.abs(np.diff(g, axis=0)).mean((1, 2))
    events = []
    for i in np.nonzero(d > 12)[0]:
        kind = 'blysk' if bright[i + 1] - bright[i] > 40 else ('wyciemnienie' if bright[i] - bright[i + 1] > 40 else 'ciecie')
        events.append(dict(t=round((i + 1) / fps, 2), typ=kind, roznica=round(float(d[i]), 1)))
    print('  ciecia/blyski:', ', '.join(f"{e['t']} s {e['typ']}" for e in events) or 'brak')

    # zmiany na polach planszy (ruchy): odchylenie standardowe srodka kazdego pola
    sx, sy = sw / info['w'], sh / info['h']
    bx0, by0, bx1, by1 = x0 * sx, y0 * sy, x1 * sx, y1 * sy
    cw, chh = (bx1 - bx0) / 8, (by1 - by0) / 8
    sig = np.zeros((n, 8, 8))
    for r in range(8):
        for c in range(8):
            ya, yb = int(by0 + (r + .2) * chh), int(by0 + (r + .8) * chh)
            xa, xb = int(bx0 + (c + .2) * cw), int(bx0 + (c + .8) * cw)
            sig[:, r, c] = g[:, ya:yb, xa:xb].std((1, 2))
    ds = np.abs(np.diff(sig, axis=0))
    moves = []
    for i in range(len(ds)):
        sq = [chr(97 + c) + str(8 - r) for r in range(8) for c in range(8) if ds[i, r, c] > 8]
        if 1 <= len(sq) <= 4:
            moves.append(dict(t=round((i + 1) / fps, 2), pola=sq))
    merged = []
    for mv in moves:                      # sklejamy zmiany z sasiednich klatek (animacja ruchu)
        if merged and mv['t'] - merged[-1]['t_koniec'] <= 0.1:
            merged[-1]['pola'] = sorted(set(merged[-1]['pola']) | set(mv['pola']))
            merged[-1]['t_koniec'] = mv['t']
        else:
            merged.append(dict(t=mv['t'], t_koniec=mv['t'], pola=mv['pola']))
    print(f'  zmiany na planszy ({len(merged)}; to zwykle ruchy, czasem ikony lub dymki):')
    for mv in merged:
        print(f"    {mv['t']:6.2f}-{mv['t_koniec']:.2f} s: {' '.join(mv['pola'])}")
    # kadr planszy po kazdej zmianie, zeby odczytac partie
    full_all = None
    for k, mv in enumerate(merged[:60]):
        fi = min(int(round((mv['t_koniec'] + 0.15) * fps)), n - 1)
        if full_all is None:
            full_all = frames(path, info['w'], info['h'])
        Image.fromarray(full_all[fi][y0:y1, x0:x1]).resize((288, 288)).save(os.path.join(out, f'plansza_{k:02d}_{mv["t"]:.2f}s.png'))

    au = audio_stats(path) if info['audio'] else None
    if au:
        print(f"  muzyka: beat co {au['okres_beatu_s']} s (~{au['bpm']} BPM), onsety basu: {au['onsety_basu'][:30]}")
    json.dump(dict(plik=path, info=info, plansza=[x0, y0, x1, y1], zdarzenia=events, zmiany_na_planszy=merged, audio=au),
              open(os.path.join(out, 'analiza.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'  zapisano: {out}/analiza.json, arkusze i kadry planszy')

if __name__ == '__main__':
    main()
