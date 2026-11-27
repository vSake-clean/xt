"""Ustala, gdzie, kiedy, jak przezroczyscie i w jakim tempie we wzorze leci klip (np. mem z alienem).

Uzycie:
  python3 src/dopasuj_klip.py WZOR.mp4 KLIP.mp4 T_BEZ_KLIPU T_Z_KLIPEM [x y w h]
    T_BEZ_KLIPU - sekunda wzoru, w ktorej klipu jeszcze nie ma (tlo),
    T_Z_KLIPEM  - sekunda, w ktorej klip juz jest (do wykrycia prostokata),
    x y w h     - prostokat klipu w pikselach wzoru (gdy pominiesz, wykrywa go sam).
Model dla kazdej probki:  wzor = a * klatka_klipu + b * tlo  (najmniejsze kwadraty).
a ~ 1, b ~ 0 -> klip kryjacy; a ~ 0,6 -> polprzezroczysty. Z par (czas wzoru, czas klipu) wychodzi
przesuniecie i predkosc kazdego odtworzenia klipu (klip moze leciec wolniej albo zaczac sie od nowa).
"""
import sys, json, subprocess
import numpy as np

def probe(path):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate',
                                   '-show_entries', 'format=duration', '-select_streams', 'v:0', '-of', 'json', path],
                                  capture_output=True, text=True).stdout)
    s = j['streams'][0]
    num, den = s['r_frame_rate'].split('/')
    return int(s['width']), int(s['height']), float(num) / float(den), float(j['format']['duration'])

def frame_at(path, t, w, h):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8)[: w * h * 3].reshape(h, w, 3).astype(float)

def main():
    wzor, klip = sys.argv[1], sys.argv[2]
    t_bg, t_on = float(sys.argv[3]), float(sys.argv[4])
    W, H, fps, dur = probe(wzor)
    bg = frame_at(wzor, t_bg, W, H)
    if len(sys.argv) >= 9:
        x, y, w, h = map(int, sys.argv[5:9])
    else:
        # obszar, ktory rozni sie od tla na kilku klatkach naraz (ruchy figur go nie psuja)
        ch = None
        for dt in (0.0, 0.7, 1.4, 2.1):
            if t_on + dt < dur - 0.05:
                m = np.abs(frame_at(wzor, t_on + dt, W, H) - bg).sum(2) > 40
                ch = m if ch is None else (ch & m)
        # usun drobiazgi (np. kropki podpowiedzi ruchow), potem wiersze i kolumny zmienione w wiekszosci
        from scipy import ndimage
        ch = ndimage.binary_opening(ch, iterations=3)
        rows = np.nonzero(ch.mean(1) > 0.35)[0]
        if len(rows) == 0:
            sys.exit('Nie znalazlem klipu: podaj prostokat recznie (x y w h).')
        cols = np.nonzero(ch[rows.min():rows.max() + 1].mean(0) > 0.35)[0]
        x, w = int(cols.min()), int(cols.max() - cols.min() + 1)
        rows = np.nonzero(ch[:, x:x + w].mean(1) > 0.5)[0]
        y, h = int(rows.min()), int(rows.max() - rows.min() + 1)
    print(f'Prostokat klipu we wzorze: x={x} y={y} w={w} h={h}  (wzor {W}x{H})')

    _, _, cfps, cdur = probe(klip)
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', klip, '-vf', f'scale={w}:{h}', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    C = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(float)
    Bd = bg[y:y + h, x:x + w].ravel()[::7]
    Cs = C.reshape(len(C), -1)[:, ::7]

    times = np.arange(t_on, dur - 0.05, 0.5)
    pts = []
    print(' czas wzoru | klatka klipu (s) | przesuniecie | a (klip) | b (tlo) | blad')
    for t in times:
        R = frame_at(wzor, t, W, H)[y:y + h, x:x + w].ravel()[::7]
        best = None
        for k in range(len(Cs)):
            A = np.stack([Cs[k], Bd], 1)
            coef = np.linalg.lstsq(A, R, rcond=None)[0]
            err = np.abs(A @ coef - R).mean()
            if best is None or err < best[0]:
                best = (err, k, coef)
        err, k, (a, b) = best
        pts.append((t, k / cfps, a, b, err))
        print(f'  {t:8.2f} s | {k / cfps:9.2f} s     | {t - k / cfps:9.2f} s | {a:6.2f}   | {b:6.2f}  | {err:5.1f}')

    # podzial na odtworzenia (czas klipu spada = klip zaczal sie od nowa) i dopasowanie prostej
    segs, cur = [], [pts[0]]
    for p in pts[1:]:
        if p[1] + 0.2 < cur[-1][1]:
            segs.append(cur); cur = [p]
        else:
            cur.append(p)
    segs.append(cur)
    print('Odtworzenia klipu:')
    for s in segs:
        T = np.array([p[0] for p in s]); K = np.array([p[1] for p in s])
        if len(s) >= 2 and np.ptp(T) > 0:
            v, c = np.polyfit(T, K, 1)
        else:
            v, c = 1.0, K[0] - T[0]
        start = -c / v
        a = np.median([p[2] for p in s])
        print(f'  od {start:.2f} s wzoru: predkosc {v:.3f}x, krycie a={a:.2f} '
              f'(czas_klipu = (t - {start:.2f}) * {v:.3f})')

if __name__ == '__main__':
    main()
