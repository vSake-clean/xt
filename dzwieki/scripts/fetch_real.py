#!/usr/bin/env python3
"""Pobiera prawdziwe nagrania (licencja CC0) z Freesound i przycina je.

Każde nagranie jest na licencji Creative Commons 0 (domena publiczna).
Autorzy i linki są w zrodla/ZRODLA.md. Wynik: zrodla/<nazwa>.flac
(22 kHz, mono), z których scripts/gen_sounds.py robi pliki dla zegarka.

Pobierane są podglądy w jakości HQ (mp3 128 kb/s), bez logowania.
Wymaga: Python 3 z numpy, ffmpeg, curl.
Uruchom:  python3 scripts/fetch_real.py
"""

import os
import re
import subprocess
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "zrodla")
SR = 22050

# nazwa: (użytkownik, id, tytuł, od [s], do [s], wyciszenie końca [s], dodatkowe opcje)
REAL = {
    "kliker": ("dnewtonjr", 231559, "Metal Clicker, Dog Training, Mono, Clip", 1.35, 1.85, 0.05, {}),
    "wybuch": ("Deganoth", 165911, "Explosion 1", 0.6, 3.0, 0.9, {}),
    "boom": ("Kievinay", 512389, "Bass Impact - Ki_01", 0.0, 1.8, 0.6, {}),
    "smutna": ("kirbydx", 175409, "wah wah sad trombone", 0.05, 5.0, 0.4, {}),
    "badumtss": ("OverlookHotelRecords", 271208, "Baddum Tish - Comedy Rimshots", 1.92, 3.9, 0.5, {}),
    "trabka": ("mcpable", 131930, "Industrial Air Horn", 0.3, 2.2, 0.02, {"rytm": True}),
    "rura": ("RutgerMuller", 104355, "Metal Pipe Falling on Concrete in Basement", 2.45, 4.7, 0.7, {}),
    "swierszcze": ("Defelozedd94", 522299, "Crickets At Night - Raw sound", 2.5, 5.5, 0.6,
                   {"pasmo": (2500, 8000), "wejscie": 0.3}),
    "boing": ("magnuswaker", 540790, "Boing 2", 0.0, 0.85, 0.15, {}),
    "blad": ("-Andreas", 648462, "Wrong Answer", 0.0, 1.06, 0.04, {}),
    "pierd": ("bassimat", 840755, "Fart #005", 0.08, 1.85, 0.12, {}),
    "bruh": ("Autellaem", 534387, "Bruh Sound Effect #1", 0.08, 0.72, 0.06, {}),
    "zgrzyt": ("ludvique", 71853, "record_scratch", 0.0, 0.45, 0.03, {}),
    "smiech": ("Kinoton", 383207, "Sitcom Laughter 9x, Small Audience", 7.5, 10.4, 0.6, {"wejscie": 0.1}),
}


def page_url(user, sid):
    return "https://freesound.org/people/%s/sounds/%d/" % (user, sid)


def preview_url(user, sid):
    t = subprocess.run(["curl", "-sS", "-L", page_url(user, sid)], capture_output=True, text=True,
                       check=True).stdout
    if "Creative Commons 0" not in t:
        raise SystemExit("%s/%d: licencja inna niż CC0, przerywam" % (user, sid))
    m = re.search(r"https://cdn\.freesound\.org/previews/\d+/%d_\d+-[hl]q\.(?:mp3|ogg)" % sid, t)
    if not m:
        raise SystemExit("%s/%d: brak podglądu" % (user, sid))
    return re.sub(r"-lq\.(mp3|ogg)$", "-hq.mp3", m.group(0))


def decode(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768


def band(y, lo, hi):
    n = len(y)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(np.fft.rfft(y) * g, n)


def fade(y, fin, fout):
    y = y.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        y[:a] *= np.linspace(0, 1, a)
    if b:
        y[-b:] *= np.linspace(1, 0, b) ** 2
    return y


def horn_rhythm(y):
    """Prawdziwa syrena pocięta na rytm: krótko, krótko, krótko, długo."""
    env = np.abs(y)
    onset = int(np.argmax(env > 0.2 * env.max()))
    out = []
    for i, sec in enumerate((0.12, 0.12, 0.12, 0.62)):
        start = onset if i == 0 else onset + int(0.25 * SR) + i * int(0.2 * SR)
        seg = y[start:start + int(sec * SR)]
        out.append(fade(seg, 0.004 if i == 0 else 0.008, 0.02 if i < 3 else 0.12))
        out.append(np.zeros(int(0.06 * SR)))
    return np.concatenate(out)


def flac(path, y):
    pcm = np.clip(y * 32767, -32768, 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", "-", "-compression_level", "8", path], input=pcm, check=True)


def credits():
    rows = ["# Źródła prawdziwych nagrań", "",
            "Wszystkie nagrania pochodzą z [Freesound](https://freesound.org) i są na licencji",
            "**Creative Commons 0** (domena publiczna). Licencja nie wymaga podawania autorów,",
            "ale wymieniamy ich z wdzięczności. Nagrania zostały przycięte, a tam, gdzie",
            "zaznaczono, także przefiltrowane lub pocięte na rytm (`scripts/fetch_real.py`).", "",
            "| Plik | Nagranie | Autor | Licencja | Zmiany |", "|---|---|---|---|---|"]
    for name, (user, sid, title, a, b, fout, opt) in REAL.items():
        ch = ["fragment %.2f–%.2f s" % (a, b)]
        if "pasmo" in opt:
            ch.append("filtr %d–%d Hz" % opt["pasmo"])
        if opt.get("rytm"):
            ch.append("pocięte na rytm 3 krótkie + 1 długi")
        rows.append("| `%s` | [%s](%s) | %s | CC0 | %s |" % (name, title, page_url(user, sid), user, ", ".join(ch)))
    rows += ["", "Dźwięki bomby (`bomba_plant` i piknięcia w `bomba_tik`) oraz zwykłe dźwięki",
             "z kategorii Dźwięki są syntezowane w `scripts/gen_sounds.py`. Wybuch na końcu",
             "`bomba_tik` to nagranie `wybuch` z tabeli."]
    with open(os.path.join(OUT, "ZRODLA.md"), "w") as f:
        f.write("\n".join(rows) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, (user, sid, title, a, b, fout, opt) in REAL.items():
            src = os.path.join(tmp, "%d.mp3" % sid)
            subprocess.run(["curl", "-sS", "-f", "-o", src, preview_url(user, sid)], check=True)
            y = decode(src)[int(a * SR):int(b * SR)]
            if "pasmo" in opt:
                y = band(y, *opt["pasmo"])
            y = horn_rhythm(y) if opt.get("rytm") else fade(y, opt.get("wejscie", 0.003), fout)
            y = y / (np.max(np.abs(y)) + 1e-9) * 0.95
            flac(os.path.join(OUT, name + ".flac"), y)
            print("%-11s %5.2f s  %s/%d" % (name, len(y) / SR, user, sid))
    credits()


if __name__ == "__main__":
    main()
