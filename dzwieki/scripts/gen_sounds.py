#!/usr/bin/env python3
"""Generator dźwięków dla aplikacji Dźwięki (Redmi Watch 4).

Wszystkie dźwięki są oryginalne, syntezowane tutaj z fal i szumu (bez
żadnych nagrań z gier, filmów czy internetu). Memowe dźwięki tylko
naśladują znany klimat, np. pikanie bomby czy kliker dla psa.

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


def reverb(y, sec=0.6, mix=0.3):
    ir = noise(sec) * np.exp(-t_axis(sec) / (sec / 5))
    ir = band(ir, 200, 6000)
    ir /= np.sqrt(np.sum(ir ** 2))
    n = len(y) + len(ir)
    wet = np.fft.irfft(np.fft.rfft(y, n) * np.fft.rfft(ir, n), n)
    dry = np.concatenate([y, np.zeros(len(ir))])
    return dry + mix * wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(y))


def saw(f, sec, k_max=14, cutoff=None):
    """Piła z sumy harmonicznych; cutoff(t) przyciemnia barwę w czasie."""
    t = t_axis(sec)
    ff = f(t) if callable(f) else np.full_like(t, f)
    ph = 2 * np.pi * np.cumsum(ff) / SR
    y = np.zeros_like(t)
    for k in range(1, k_max + 1):
        g = 1.0 / k
        if cutoff is not None:
            fc = cutoff(t) if callable(cutoff) else cutoff
            g = g / (1 + (k * ff / fc) ** 4)
        y += g * np.sin(k * ph)
    return y


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
def bomb_beep(sec=0.075, f=1960):
    """Ostre, krótkie piknięcie zapalnika: prostokąt z kilku harmonicznych."""
    t = t_axis(sec)
    y = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5))
    return band(y * env(sec, 0.002, 1.0), 300, 7000)


def wybuch(sec=1.7):
    t = t_axis(sec)
    n = noise(sec)
    # szum przyciemniany w czasie: najpierw huk, potem dudnienie
    bright = band(n, 0, 2500) * np.exp(-t / 0.08)
    dark = band(n, 0, 500) * np.exp(-t / 0.45)
    thump = sweep(70 * np.exp(-t / 0.25) + 38, sec) * np.exp(-t / 0.35)
    y = 0.6 * bright + 1.2 * dark + 1.4 * thump
    y = np.tanh(2.2 * y / np.max(np.abs(y)))
    return y * env(sec, 0.003, 10.0)


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
    # odliczanie coraz szybciej, długi pisk i wybuch
    ev = []
    t, gap = 0.0, 0.9
    while gap > 0.1:
        ev.append((t, bomb_beep()))
        t += gap
        gap *= 0.8
    for _ in range(4):
        ev.append((t, bomb_beep(0.05)))
        t += 0.085
    ev.append((t, bomb_beep(0.45)))
    t += 0.5
    boom = wybuch(1.5)
    ev.append((t, 1.6 * boom))
    return place(t + len(boom) / SR, ev)


def kliker():
    # metalowy języczek: "klik" przy wciśnięciu i cichsze "klak" przy puszczeniu
    def snap(f1, f2, amp):
        sec = 0.05
        t = t_axis(sec)
        y = 0.5 * noise(sec) * np.exp(-t / 0.0008)
        y += np.sin(2 * np.pi * f1 * t) * np.exp(-t / 0.006)
        y += 0.6 * np.sin(2 * np.pi * f2 * t) * np.exp(-t / 0.004)
        return amp * band(y, 900, 9000)
    return place(0.26, [(0.0, snap(3300, 5200, 1.0)), (0.12, snap(2800, 4700, 0.55))])


def boom():
    sec = 1.1
    t = t_axis(sec)
    y = sweep(115 * np.exp(-t / 0.06) + 48, sec) * np.exp(-t / 0.42)
    y += 0.25 * band(noise(sec), 0, 900) * np.exp(-t / 0.05)
    # przester dodaje harmoniczne, żeby mały głośnik zegarka coś zagrał
    y = np.tanh(4.0 * y / np.max(np.abs(y)))
    y *= env(sec, 0.002, 10.0)
    y[-int(0.25 * SR):] *= np.linspace(1, 0, int(0.25 * SR)) ** 2  # bez trzasku na końcu
    return reverb(y, 0.8, 0.35)


def smutna_trabka():
    seq = ((392.0, 0.36), (369.99, 0.36), (349.23, 0.36), (329.63, 1.25))
    out = []
    for i, (f, sec) in enumerate(seq):
        last = i == len(seq) - 1
        fn = (lambda tt, f=f: f * (1 + 0.014 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.25, 0, 1))) if last else f
        # "wah": barwa otwiera się i zamyka w każdej nucie
        cut = (lambda tt, s=sec: 700 + 1500 * np.sin(np.pi * np.clip(tt / s, 0, 1)) ** 0.8)
        y = saw(fn, sec, 12, cut)
        y *= np.clip(t_axis(sec) / 0.03, 0, 1) * np.linspace(1, 0.75 if not last else 0.6, len(y))
        fade = int(0.03 * SR)
        y[-fade:] *= np.linspace(1, 0, fade)
        out.extend([y, silence(0.03)])
    return cat(*out)


def ba_dum_tss():
    def tom(f0, f1, sec=0.22):
        t = t_axis(sec)
        y = sweep(f1 + (f0 - f1) * np.exp(-t / 0.04), sec) * np.exp(-t / 0.09)
        return y + 0.2 * band(noise(sec), 0, 3000) * np.exp(-t / 0.015)

    def cymbal(sec=0.9):
        t = t_axis(sec)
        y = band(noise(sec), 4500, None) * np.exp(-t / 0.28)
        for f in (5230, 6870, 8110):
            y += 0.15 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.2)
        return 0.8 * y
    return place(1.35, [(0.0, tom(210, 140)), (0.2, tom(170, 105)), (0.44, cymbal())])


def trabka_mlg():
    def blast(sec):
        t = t_axis(sec)
        f = lambda tt: 466 * (1 - 0.04 * np.exp(-tt / 0.03))
        y = saw(f, sec, 14) + 0.8 * saw(lambda tt: f(tt) * 1.26, sec, 12) + 0.6 * saw(lambda tt: f(tt) * 1.5, sec, 10)
        y = np.tanh(1.8 * y / np.max(np.abs(y)))
        a = np.clip(t / 0.012, 0, 1)
        fade = int(0.025 * SR)
        a[-fade:] *= np.linspace(1, 0, fade)
        return y * a
    ev, t = [], 0.0
    for sec in (0.11, 0.11, 0.11, 0.62):
        ev.append((t, blast(sec)))
        t += sec + 0.05
    return place(t, ev)


def metalowa_rura():
    def clang(sec, amp):
        t = t_axis(sec)
        y = 0.4 * band(noise(sec), 1500, None) * np.exp(-t / 0.01)
        for f, d, a in ((523, 1.1, 1.0), (1371, 0.8, 0.8), (2412, 0.5, 0.6), (3787, 0.35, 0.4), (5321, 0.22, 0.3)):
            y += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
        return amp * y * env(sec, 0.001, 10.0)
    return place(2.2, [(0.0, clang(2.1, 1.0)), (0.34, clang(1.6, 0.45)),
                       (0.56, clang(1.2, 0.25)), (0.70, clang(0.9, 0.12))])


def swierszcze():
    def chirp(f, amp):
        out = []
        for _ in range(3):
            t = t_axis(0.014)
            out.extend([np.sin(2 * np.pi * f * t) * np.sin(np.pi * t / 0.014), silence(0.016)])
        return amp * cat(*out)
    ev = []
    for i in range(5):
        ev.append((0.05 + i * 0.42, chirp(4650, 1.0)))
        ev.append((0.27 + i * 0.42, chirp(4250, 0.45)))
    return place(2.25, ev)


def boing():
    sec = 0.95
    t = t_axis(sec)
    f = 380 + 240 * t + 280 * np.exp(-t / 0.35) * np.sin(2 * np.pi * 11 * t)
    y = sweep(f, sec) + 0.35 * sweep(2 * f, sec)
    return y * env(sec, 0.003, 0.4)


def blad():
    def buzz(f, sec):
        t = t_axis(sec)
        y = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5, 7, 9))
        return band(y, 0, 3500) * env(sec, 0.004, 10.0)
    return cat(buzz(190, 0.16), silence(0.05), buzz(140, 0.32))


def pierd():
    sec = 0.85
    t = t_axis(sec)
    # drgający, nieregularny bas: impulsy o pływającej częstotliwości
    walk = np.cumsum(RNG.standard_normal(len(t))) / SR * 40
    f = 140 + 30 * np.sin(2 * np.pi * 2.3 * t) + walk - np.linspace(0, 35, len(t))
    ph = np.cumsum(f) / SR
    pulses = np.maximum(0, np.sin(2 * np.pi * ph)) ** 6
    y = band(pulses + 0.08 * noise(sec), 90, 2000)
    flutter = 1 + 0.35 * np.sin(2 * np.pi * 9 * t + 2 * np.sin(2 * np.pi * 1.7 * t))
    return y * flutter * env(sec, 0.02, 0.9)


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
    "bomba_plant": bomba_plant, "bomba_tik": bomba_tik, "wybuch": wybuch,
    "kliker": kliker, "boom": boom, "smutna": smutna_trabka, "badumtss": ba_dum_tss,
    "trabka": trabka_mlg, "rura": metalowa_rura, "swierszcze": swierszcze,
    "boing": boing, "blad": blad, "pierd": pierd,
}


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
