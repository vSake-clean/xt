#!/usr/bin/env python3
"""Generator dźwięków dla aplikacji Dźwięki (Redmi Watch 4).

Zwykłe dźwięki (ping, dzwonek...) i piknięcia bomby są syntezowane tutaj.
Memy to prawdziwe nagrania na licencji CC0 z Freesound, pobrane i przycięte
przez scripts/fetch_real.py do folderu zrodla/ (autorzy: zrodla/ZRODLA.md).

Każdy dźwięk powstaje jako:
  <id>_0.mp3  pełna głośność (szczyt -1 dBFS)
  <id>_1.mp3  -20 dB
  <id>_2.mp3  -40 dB
  <id>.wav    zapasowy (pełna głośność, 11 kHz), gdyby zegarek nie grał mp3
Długości trafiają do src/common/durations.js.

Wymaga: Python 3 z numpy oraz ffmpeg (z libmp3lame).
Uruchom:  python3 scripts/gen_sounds.py
"""

import os
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "src", "common", "snd")
DUR_JS = os.path.join(ROOT, "src", "common", "durations.js")
ZRODLA = os.path.join(ROOT, "zrodla")
SR = 22050
WAV_SR = 11025
TIERS = [1.0, 0.1, 0.01]
PEAK = 10 ** (-1 / 20)
RNG = np.random.default_rng(2026)

NOTES = [523.25, 587.33, 659.26, 698.46, 783.99, 880.00, 987.77, 1046.50]  # c d e f g a h c'


# ---------------------------------------------------------------- narzędzia
def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def env(sec, attack=0.004, decay=0.3):
    t = t_axis(sec)
    e = np.clip(t / attack, 0, 1) * np.exp(-t / decay)
    fade = min(len(t), int(0.015 * SR))
    if fade:
        e[-fade:] *= np.linspace(1, 0, fade)
    return e


def tone(freq, sec, decay=0.3, partials=((1, 1.0),), attack=0.004):
    t = t_axis(sec)
    y = np.zeros_like(t)
    for ratio, amp in partials:
        y += amp * np.sin(2 * np.pi * freq * ratio * t)
    return y * env(sec, attack, decay)


def sweep(f, sec):
    """Sinus o zmiennej częstotliwości f (tablica albo funkcja czasu)."""
    t = t_axis(sec)
    ff = f(t) if callable(f) else f
    return np.sin(2 * np.pi * np.cumsum(ff) / SR)


def silence(sec):
    return np.zeros(int(SR * sec))


def cat(*parts):
    return np.concatenate(parts)


def noise(sec):
    return RNG.standard_normal(int(SR * sec))


def band(y, lo=0.0, hi=None):
    """Filtr pasmowy w dziedzinie częstotliwości (łagodne zbocza)."""
    n = len(y)
    spec = np.fft.rfft(y)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo > 0:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(spec * g, n)


def place(total_sec, events):
    """Składa dźwięk z kawałków: events = [(czas_startu_s, sygnał), ...]."""
    out = np.zeros(int(SR * total_sec))
    for start, y in events:
        i = int(SR * start)
        j = min(len(out), i + len(y))
        out[i:j] += y[: j - i]
    return out






# ---------------------------------------------------------------- zwykłe dźwięki
def ping():
    return tone(1568, 0.55, decay=0.16, partials=((1, 1.0), (2, 0.18), (3, 0.05)))


def kropla():
    sec = 0.22
    t = t_axis(sec)
    f = 1500 * np.exp(-t / 0.05) + 420
    y = sweep(f, sec) * env(sec, 0.002, 0.06)
    echo = 0.35 * sweep(f * 1.3, sec) * env(sec, 0.002, 0.04)
    return cat(y, silence(0.05), echo[: int(0.12 * SR)])


def dzwonek():
    partials = ((1, 1.0), (2.0, 0.55), (2.76, 0.42), (5.40, 0.22), (8.93, 0.10))
    return tone(880, 1.2, decay=0.38, partials=partials, attack=0.002)


def ptaszek():
    out = []
    for k, (f0, f1) in enumerate(((2600, 4100), (2900, 4400), (2500, 3900))):
        sec = 0.07
        t = t_axis(sec)
        y = sweep(f0 + (f1 - f0) * (t / sec) ** 0.7, sec) * np.sin(np.pi * t / sec) ** 2
        out.extend([y, silence(0.06 if k < 2 else 0.0)])
    return cat(*out)


def gong():
    partials = ((1, 1.0), (1.48, 0.6), (2.0, 0.5), (2.53, 0.35), (3.1, 0.25), (4.2, 0.12))
    t = t_axis(1.8)
    return tone(262, 1.8, decay=0.7, partials=partials, attack=0.01) * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))


def klik():
    sec = 0.06
    t = t_axis(sec)
    return 0.4 * noise(sec) * np.exp(-t / 0.004) + np.sin(2 * np.pi * 1300 * t) * np.exp(-t / 0.012)


def alarm():
    out = []
    for i in range(4):
        f = 988 if i % 2 == 0 else 784
        t = t_axis(0.13)
        y = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5)) * env(0.13, 0.004, 1.0)
        out.extend([y, silence(0.05)])
    return cat(*out)


def fanfara():
    out = []
    for f, sec in ((523.25, 0.12), (659.26, 0.12), (783.99, 0.12), (1046.5, 0.45)):
        out.append(tone(f, sec, decay=0.25 if sec > 0.2 else 0.12, partials=((1, 1.0), (2, 0.3), (3, 0.12))))
        out.append(silence(0.02))
    return cat(*out)


def note(f):
    return tone(f, 0.24, decay=0.11, partials=((1, 1.0), (2, 0.25), (3, 0.08)))


# ---------------------------------------------------------------- memy
# Memy to prawdziwe nagrania CC0 z Freesound (zrodla/*.flac, pobiera je
# scripts/fetch_real.py). Syntezowane są tylko piknięcia bomby.
REAL = ["wybuch", "kliker", "boom", "smutna", "badumtss", "trabka", "rura",
        "swierszcze", "boing", "blad", "pierd", "bruh", "zgrzyt", "smiech"]


def real(name):
    path = os.path.join(ZRODLA, name + ".flac")
    if not os.path.exists(path):
        raise SystemExit("brak %s, uruchom najpierw: python3 scripts/fetch_real.py" % path)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768


def bomb_beep(sec=0.075, f=1960):
    """Ostre, krótkie piknięcie zapalnika: prostokąt z kilku harmonicznych."""
    t = t_axis(sec)
    y = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5))
    return band(y * env(sec, 0.002, 1.0), 300, 7000)


def bomba_plant():
    # wpisywanie kodu: 7 piknięć w nierównym rytmie, potem uzbrojenie
    gaps = [0.0, 0.24, 0.19, 0.28, 0.21, 0.26, 0.2]
    ev = []
    t = 0.0
    for g in gaps:
        t += g
        ev.append((t, bomb_beep(0.06, 1960)))
    t += 0.35
    ev.append((t, bomb_beep(0.09, 1960)))
    ev.append((t + 0.13, bomb_beep(0.09, 1960)))
    ev.append((t + 0.30, 0.7 * tone(980, 0.35, decay=0.2, partials=((1, 1.0), (2, 0.4)))))
    return place(t + 0.7, ev)


def bomba_tik():
    # odliczanie coraz szybciej, długi pisk i prawdziwe nagranie wybuchu
    ev = []
    t, gap = 0.0, 0.9
    while gap > 0.1:
        ev.append((t, 0.6 * bomb_beep()))
        t += gap
        gap *= 0.8
    for _ in range(4):
        ev.append((t, 0.6 * bomb_beep(0.05)))
        t += 0.085
    ev.append((t, 0.6 * bomb_beep(0.45)))
    t += 0.5
    boom = real("wybuch")[: int(2.2 * SR)].copy()
    boom[-int(0.6 * SR):] *= np.linspace(1, 0, int(0.6 * SR)) ** 2
    ev.append((t, boom / np.max(np.abs(boom))))
    return place(t + len(boom) / SR, ev)


# ---------------------------------------------------------------- zapis
def write_wav(path, y, sr):
    pcm = np.clip(y * 32767, -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def resample(y, sr):
    n = int(len(y) * sr / SR)
    y = band(y, 0, sr * 0.45)
    return np.interp(np.linspace(0, len(y) - 1, n), np.arange(len(y)), y)


def write_all(name, y):
    y = np.asarray(y, dtype=np.float64)
    y = y / np.max(np.abs(y)) * PEAK
    y = cat(silence(0.01), y)  # odtwarzacz nie utnie ataku
    tmp = os.path.join(SND, "_tmp.wav")
    for i, g in enumerate(TIERS):
        write_wav(tmp, y * g, SR)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-codec:a", "libmp3lame",
                        "-b:a", "40k", "-ac", "1", "-ar", str(SR),
                        os.path.join(SND, "%s_%d.mp3" % (name, i))], check=True)
    os.remove(tmp)
    write_wav(os.path.join(SND, name + ".wav"), resample(y, WAV_SR), WAV_SR)
    return int(round(len(y) / SR * 1000))


SOUNDS = {
    "ping": ping, "kropla": kropla, "dzwonek": dzwonek, "ptaszek": ptaszek,
    "gong": gong, "klik": klik, "alarm": alarm, "fanfara": fanfara,
    "bomba_plant": bomba_plant, "bomba_tik": bomba_tik,
}
for _name in REAL:
    SOUNDS[_name] = (lambda n=_name: real(n))


def main():
    os.makedirs(SND, exist_ok=True)
    for f in os.listdir(SND):
        if f.endswith((".wav", ".mp3")):
            os.remove(os.path.join(SND, f))
    durations = {}
    for name, fn in SOUNDS.items():
        durations[name] = write_all(name, fn())
    for i, f in enumerate(NOTES):
        durations["n%d" % (i + 1)] = write_all("n%d" % (i + 1), note(f))
    with open(DUR_JS, "w") as f:
        f.write("// Wygenerowane przez scripts/gen_sounds.py: długości dźwięków w ms.\n")
        f.write("export const DURATIONS = {\n")
        f.write(",\n".join("  %s: %d" % (k, v) for k, v in durations.items()))
        f.write("\n}\n")
    total = sum(os.path.getsize(os.path.join(SND, f)) for f in os.listdir(SND))
    print("OK:", len(os.listdir(SND)), "plików,", total // 1024, "KB")
    for k, v in durations.items():
        if not k.startswith("n"):
            print("  %-12s %5d ms" % (k, v))


if __name__ == "__main__":
    main()
