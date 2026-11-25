#!/usr/bin/env python3
"""Minimalistyczne tła 390x390 do "Własnej tarczy" w FitCloudPro (Maxcom FW58).

Środek zostaje spokojny i ciemny, bo zegarek rysuje na nim godzinę.
Wszystkie wzory są oryginalne, rysowane kodem.
Uruchom:  python3 scripts/gen_tla.py
"""

import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tla")
N = 390
SS = 4
C = N * SS / 2


def canvas(color=(0, 0, 0)):
    return Image.new("RGB", (N * SS, N * SS), color)


def finish(img, name):
    img = img.resize((N, N), Image.LANCZOS)
    img.save(os.path.join(OUT, name), optimize=True)
    return img


def radial(inner, outer, power=1.6):
    img = Image.new("RGB", (N, N))
    px = img.load()
    for y in range(N):
        for x in range(N):
            r = min(1.0, math.hypot(x - N / 2, y - N / 2) / (N / 2 * 1.05))
            t = r ** power
            px[x, y] = tuple(int(inner[i] * (1 - t) + outer[i] * t) for i in range(3))
    return img


def grafit():
    """Czerń z cienkimi kreskami minut na krawędzi."""
    img = canvas()
    d = ImageDraw.Draw(img)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        big = i % 5 == 0
        r0 = C - (26 if big else 16) * SS
        r1 = C - 6 * SS
        col = (150, 154, 160) if big else (55, 57, 62)
        d.line([(C + r0 * math.cos(a), C + r0 * math.sin(a)),
                (C + r1 * math.cos(a), C + r1 * math.sin(a))],
               fill=col, width=(3 if big else 2) * SS)
    return finish(img, "01-grafit-kreski.png")


def mgla():
    """Grafitowy gradient od środka do krawędzi."""
    img = radial((4, 4, 6), (52, 55, 62), 2.2)
    img.save(os.path.join(OUT, "02-grafitowa-mgla.png"), optimize=True)
    return img


def noc():
    """Granatowa noc z kilkoma gwiazdami przy krawędziach."""
    img = radial((2, 3, 10), (14, 20, 46), 1.8)
    d = ImageDraw.Draw(img)
    rnd = random.Random(58)
    placed = 0
    while placed < 38:
        x, y = rnd.randrange(N), rnd.randrange(N)
        if math.hypot(x - N / 2, y - N / 2) < 120:  # środek zostaje czysty
            continue
        b = rnd.randint(110, 230)
        r = rnd.choice([0, 0, 0, 1])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 15)))
        placed += 1
    img.save(os.path.join(OUT, "03-granatowa-noc.png"), optimize=True)
    return img


def okregi():
    """Cienkie współśrodkowe okręgi, coraz jaśniejsze ku krawędzi."""
    img = canvas()
    d = ImageDraw.Draw(img)
    for k, r in enumerate(range(130, 196, 9)):
        v = 22 + k * 7
        rr = r * SS
        d.ellipse([C - rr, C - rr, C + rr, C + rr], outline=(v, v, v + 4), width=SS)
    return finish(img, "04-okregi.png")


def las():
    """Głęboka zieleń, bardzo ciemna w środku."""
    img = radial((2, 6, 4), (16, 46, 34), 2.0)
    img.save(os.path.join(OUT, "05-ciemny-las.png"), optimize=True)
    return img


def poziomice():
    """Delikatne linie jak na mapie poziomicowej, tylko przy krawędziach."""
    img = canvas()
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    phases = [rnd.uniform(0, 6.28) for _ in range(4)]
    for k in range(9):
        base = 120 + k * 9
        pts = []
        for i in range(0, 361, 3):
            a = math.radians(i)
            wob = (6 * math.sin(3 * a + phases[0] + k * 0.3)
                   + 4 * math.sin(5 * a + phases[1])
                   + 3 * math.sin(7 * a + phases[2] - k * 0.2))
            r = (base + wob) * SS
            pts.append((C + r * math.cos(a), C + r * math.sin(a)))
        v = 26 + k * 6
        d.line(pts, fill=(v, v + 2, v + 6), width=SS, joint="curve")
    return finish(img, "06-poziomice.png")


def swit():
    """Ciepły, przygaszony gradient od dołu (jak świt), góra i środek ciemne."""
    img = Image.new("RGB", (N, N))
    px = img.load()
    for y in range(N):
        for x in range(N):
            t = max(0.0, (y - N * 0.45) / (N * 0.55)) ** 1.8
            px[x, y] = (int(6 + 70 * t), int(5 + 34 * t), int(10 + 22 * t))
    img.save(os.path.join(OUT, "07-swit.png"), optimize=True)
    return img


def kropki():
    """Siatka małych kropek wygaszana ku środkowi."""
    img = canvas()
    d = ImageDraw.Draw(img)
    step = 18
    for gy in range(step // 2, N, step):
        for gx in range(step // 2, N, step):
            r = math.hypot(gx - N / 2, gy - N / 2)
            if r > N / 2 - 4:
                continue
            t = max(0.0, (r - 95) / (N / 2 - 95))
            v = int(14 + 60 * t)
            if v <= 16:
                continue
            x, y, rr = gx * SS, gy * SS, 1.6 * SS
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(v, v, v))
    return finish(img, "08-kropki.png")


def sheet(imgs):
    """Arkusz z podglądem wszystkich teł w okrągłej masce."""
    cols, pad, s = 4, 20, 180
    rows = (len(imgs) + cols - 1) // cols
    out = Image.new("RGB", (cols * (s + pad) + pad, rows * (s + pad) + pad), (235, 235, 238))
    mask = Image.new("L", (s * SS, s * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, s * SS - 1, s * SS - 1], fill=255)
    mask = mask.resize((s, s), Image.LANCZOS)
    for i, im in enumerate(imgs):
        x = pad + (i % cols) * (s + pad)
        y = pad + (i // cols) * (s + pad)
        out.paste(im.resize((s, s), Image.LANCZOS), (x, y), mask)
    out.save(os.path.join(ROOT, "podglad.png"), optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    imgs = [grafit(), mgla(), noc(), okregi(), las(), poziomice(), swit(), kropki()]
    sheet(imgs)
    print("OK:", len(imgs), "teł w", OUT)


if __name__ == "__main__":
    main()
