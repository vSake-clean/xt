#!/usr/bin/env python3
"""Generator dźwięków dla aplikacji Dźwięki (Redmi Watch 4).

Wszystkie dźwięki są oryginalne, syntezowane tutaj z fal sinusoidalnych
i szumu. Każdy dźwięk powstaje w trzech wersjach głośności:
  <id>_0  pełna (szczyt -1 dBFS)
  <id>_1  -20 dB
  <id>_2  -40 dB
oraz w dwóch formatach: .mp3 (używany najpierw) i .wav (zapasowy, gdyby
zegarek nie odtworzył mp3). Pliki trafiają do src/common/snd/.

Wymaga: Python 3 z numpy oraz ffmpeg (z libmp3lame).
Uruchom:  python3 scripts/gen_sounds.py
"""

import os
import subprocess
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "src", "common", "snd")
SR = 22050
TIERS = [1.0, 0.1, 0.01]
PEAK = 10 ** (-1 / 20)

NOTES = [523.25, 587.33, 659.26, 698.46, 783.99, 880.00, 987.77, 1046.50]  # c d e f g a h c'


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def env(sec, attack=0.004, decay=0.3):
    t = t_axis(sec)
    a = np.clip(t / attack, 0, 1)
    d = np.exp(-t / decay)
    e = a * d
    # łagodne wyciszenie ostatnich 15 ms, bez trzasku na końcu
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


def silence(sec):
    return np.zeros(int(SR * sec))


def cat(*parts):
    return np.concatenate(parts)


def ping():
    return tone(1568, 0.55, decay=0.16, partials=((1, 1.0), (2, 0.18), (3, 0.05)))


def kropla():
    sec = 0.22
    t = t_axis(sec)
    f = 1500 * np.exp(-t / 0.05) + 420
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * env(sec, 0.002, 0.06)
    echo = 0.35 * np.sin(2 * np.pi * np.cumsum(f * 1.3) / SR) * env(sec, 0.002, 0.04)
    return cat(y, silence(0.05), echo[: int(0.12 * SR)])


def dzwonek():
    partials = ((1, 1.0), (2.0, 0.55), (2.76, 0.42), (5.40, 0.22), (8.93, 0.10))
    return tone(880, 1.2, decay=0.38, partials=partials, attack=0.002)


def ptaszek():
    out = []
    for k, (f0, f1) in enumerate(((2600, 4100), (2900, 4400), (2500, 3900))):
        sec = 0.07
        t = t_axis(sec)
        f = f0 + (f1 - f0) * (t / sec) ** 0.7
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / sec) ** 2
        out.append(y)
        out.append(silence(0.06 if k < 2 else 0.0))
    return cat(*out)


def gong():
    partials = ((1, 1.0), (1.48, 0.6), (2.0, 0.5), (2.53, 0.35), (3.1, 0.25), (4.2, 0.12))
    t = t_axis(1.8)
    y = tone(262, 1.8, decay=0.7, partials=partials, attack=0.01)
    return y * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))


def klik():
    rng = np.random.default_rng(7)
    sec = 0.06
    t = t_axis(sec)
    noise = rng.standard_normal(len(t)) * np.exp(-t / 0.004)
    body = np.sin(2 * np.pi * 1300 * t) * np.exp(-t / 0.012)
    return 0.4 * noise + body


def alarm():
    out = []
    for i in range(4):
        f = 988 if i % 2 == 0 else 784
        sec = 0.13
        t = t_axis(sec)
        # łagodna "kwadratowa" fala: kilka nieparzystych harmonicznych
        y = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 3, 5))
        y = y * env(sec, 0.004, 1.0)
        out.extend([y, silence(0.05)])
    return cat(*out)


def fanfara():
    out = []
    seq = ((523.25, 0.12), (659.26, 0.12), (783.99, 0.12), (1046.5, 0.45))
    for f, sec in seq:
        out.append(tone(f, sec, decay=0.25 if sec > 0.2 else 0.12,
                        partials=((1, 1.0), (2, 0.3), (3, 0.12))))
        out.append(silence(0.02))
    return cat(*out)


def note(f):
    return tone(f, 0.24, decay=0.11, partials=((1, 1.0), (2, 0.25), (3, 0.08)))


def write_wav(path, y):
    pcm = np.clip(y * 32767, -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def write_all(name, y):
    y = np.asarray(y, dtype=np.float64)
    y = y / np.max(np.abs(y)) * PEAK
    # krótka cisza na początku, żeby odtwarzacz nie uciął ataku
    y = cat(silence(0.01), y)
    for i, g in enumerate(TIERS):
        base = os.path.join(SND, "%s_%d" % (name, i))
        write_wav(base + ".wav", y * g)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", base + ".wav",
                        "-codec:a", "libmp3lame", "-b:a", "48k", "-ac", "1",
                        "-ar", str(SR), base + ".mp3"], check=True)


def main():
    os.makedirs(SND, exist_ok=True)
    for f in os.listdir(SND):
        if f.endswith((".wav", ".mp3")):
            os.remove(os.path.join(SND, f))
    sounds = {
        "ping": ping(), "kropla": kropla(), "dzwonek": dzwonek(), "ptaszek": ptaszek(),
        "gong": gong(), "klik": klik(), "alarm": alarm(), "fanfara": fanfara(),
    }
    for i, f in enumerate(NOTES):
        sounds["n%d" % (i + 1)] = note(f)
    for name, y in sounds.items():
        write_all(name, y)
    total = sum(os.path.getsize(os.path.join(SND, f)) for f in os.listdir(SND))
    print("OK:", len(os.listdir(SND)), "plików,", total // 1024, "KB")


if __name__ == "__main__":
    main()
