#!/usr/bin/env python3
"""Generator grafik PNG dla gry "Świetlik" (Redmi Watch 4).

Zegarek nie rysuje tekstu w szybkich aplikacjach, więc napisy i cyfry to
obrazki. Wszystkie grafiki są oryginalne i rysowane tutaj kodem.
Uruchom:  python3 scripts/gen_assets.py
"""

import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(ROOT, "src", "common")
IMG = os.path.join(COMMON, "img")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SS = 4
W, H = 390, 450
COL_W, COL_H = 64, 450
BIRD = (40, 32)
DIGIT = (30, 48)

SKY_TOP = (6, 10, 32)
SKY_BOT = (18, 14, 52)
GLOW = (190, 255, 90)
CRYSTAL = (120, 90, 230)
CRYSTAL_LIGHT = (190, 170, 255)
CRYSTAL_DARK = (60, 40, 140)
WHITE = (255, 255, 255, 255)


def font(path, size):
    return ImageFont.truetype(path, size)


def save(img, name, folder=IMG):
    path = os.path.join(folder, name)
    img.save(path, optimize=True)
    chk = Image.open(path)
    chk.load()
    assert chk.getbbox() is not None, "pusty obrazek: " + name


def background():
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(SKY_TOP[i] * (1 - t) + SKY_BOT[i] * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c + (255,))
    rnd = random.Random(7)
    for _ in range(45):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.75))
        b = rnd.randint(90, 220)
        r = rnd.choice([0, 0, 0, 1])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b + 20 if b < 235 else 255, 255))
    # księżyc (sierp)
    moon = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    cx, cy, r = 300 * SS, 70 * SS, 26 * SS
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 240, 210, 255))
    md.ellipse([cx - r + 12 * SS, cy - r - 6 * SS, cx + r + 12 * SS, cy + r - 6 * SS],
               fill=(0, 0, 0, 0))
    moon = moon.resize((W, H), Image.LANCZOS)
    img.alpha_composite(moon)
    # sylwetka trawy na dole
    grass = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grass)
    pts = [(0, H * SS)]
    for i in range(0, W + 1, 6):
        h = 18 + 10 * math.sin(i * 0.11) + rnd.randint(0, 10)
        pts.append((i * SS, (H - h) * SS))
    pts.append((W * SS, H * SS))
    gd.polygon(pts, fill=(4, 8, 18, 255))
    img.alpha_composite(grass.resize((W, H), Image.LANCZOS))
    save(img.convert("RGB"), "bg.png")


def column(name, cap_at_bottom):
    w, h = COL_W * SS, COL_H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # trzon kryształu: pas z jaśniejszą krawędzią
    m = 6 * SS
    d.rectangle([m, 0, w - m, h], fill=CRYSTAL + (255,))
    d.rectangle([m, 0, m + 10 * SS, h], fill=CRYSTAL_LIGHT + (255,))
    d.rectangle([w - m - 12 * SS, 0, w - m, h], fill=CRYSTAL_DARK + (255,))
    # poziome pęknięcia
    for y in range(40, COL_H, 70):
        yy = y * SS
        d.line([(m, yy), (w - m, yy + 8 * SS)], fill=CRYSTAL_DARK + (255,), width=2 * SS)
    # zakończenie: szpic kryształu
    tip = 34 * SS
    if cap_at_bottom:
        d.rectangle([m, h - tip, w - m, h], fill=(0, 0, 0, 0))
        d.polygon([(0, h - tip), (w, h - tip), (w / 2, h)], fill=CRYSTAL + (255,))
        d.polygon([(0, h - tip), (w / 2, h - tip), (w / 2, h)], fill=CRYSTAL_LIGHT + (255,))
    else:
        d.rectangle([m, 0, w - m, tip], fill=(0, 0, 0, 0))
        d.polygon([(0, tip), (w, tip), (w / 2, 0)], fill=CRYSTAL + (255,))
        d.polygon([(0, tip), (w / 2, tip), (w / 2, 0)], fill=CRYSTAL_LIGHT + (255,))
    save(img.resize((COL_W, COL_H), Image.LANCZOS), name)


def firefly(size, name, folder=IMG, scale=1.0):
    w, h = size[0] * SS, size[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # poświata
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = w * 0.42, h * 0.58
    r = h * 0.40
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GLOW + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(h * 0.10))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    # świecący odwłok
    r2 = h * 0.24
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(230, 255, 140, 255))
    # tułów i głowa
    d.ellipse([w * 0.48, h * 0.34, w * 0.80, h * 0.66], fill=(70, 50, 40, 255))
    d.ellipse([w * 0.70, h * 0.36, w * 0.94, h * 0.60], fill=(90, 65, 50, 255))
    d.ellipse([w * 0.80, h * 0.40, w * 0.87, h * 0.49], fill=(255, 255, 255, 255))
    d.ellipse([w * 0.83, h * 0.42, w * 0.87, h * 0.47], fill=(0, 0, 0, 255))
    # czułki
    d.line([(w * 0.86, h * 0.38), (w * 0.97, h * 0.12)], fill=(90, 65, 50, 255), width=int(1.5 * SS * scale))
    # skrzydło półprzezroczyste
    d.ellipse([w * 0.40, h * 0.02, w * 0.72, h * 0.42], fill=(200, 230, 255, 150))
    save(img.resize(size, Image.LANCZOS), name, folder)


def text_img(name, text, size, box, color=WHITE, fnt=FONT):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(fnt, size * SS)
    d.text((w / 2, h / 2), text, font=f, fill=color, anchor="mm",
           stroke_width=int(size * SS * 0.08), stroke_fill=(0, 0, 0, 255))
    save(img.resize(box, Image.LANCZOS), name)


def digits():
    for ch in "0123456789":
        text_img("d_%s.png" % ch, ch, 42, DIGIT)
    blank = Image.new("RGBA", DIGIT, (0, 0, 0, 0))
    blank.save(os.path.join(IMG, "d_blank.png"))
    for ch in "0123456789":
        text_img("m_%s.png" % ch, ch, 26, (18, 30), color=GLOW + (255,))
    Image.new("RGBA", (18, 30), (0, 0, 0, 0)).save(os.path.join(IMG, "m_blank.png"))


def logo():
    n = 96 * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, n - 1, n - 1], fill=SKY_BOT + (255,))
    img = img.resize((96, 96), Image.LANCZOS)
    bug = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    firefly((76, 60), "_tmp_logo.png", folder=COMMON, scale=2)
    f = Image.open(os.path.join(COMMON, "_tmp_logo.png")).convert("RGBA")
    os.remove(os.path.join(COMMON, "_tmp_logo.png"))
    bug.alpha_composite(f, (10, 18))
    img.alpha_composite(bug)
    save(img, "logo.png", COMMON)


def main():
    os.makedirs(IMG, exist_ok=True)
    for fn in os.listdir(IMG):
        if fn.endswith(".png"):
            os.remove(os.path.join(IMG, fn))
    background()
    column("col_top.png", cap_at_bottom=True)
    column("col_bot.png", cap_at_bottom=False)
    firefly(BIRD, "bug.png")
    text_img("title.png", "ŚWIETLIK", 40, (330, 60), color=GLOW + (255,))
    text_img("hint.png", "Dotknij, aby lecieć", 22, (330, 36))
    text_img("over.png", "KONIEC GRY", 38, (330, 56), color=(255, 120, 120, 255))
    text_img("best.png", "Rekord:", 22, (110, 30), color=GLOW + (255,))
    text_img("again.png", "Dotknij, aby zagrać", 22, (330, 36))
    digits()
    logo()
    print("OK:", len(os.listdir(IMG)), "plików w src/common/img + logo.png")


if __name__ == "__main__":
    main()
