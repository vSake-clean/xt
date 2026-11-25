#!/usr/bin/env python3
"""Generator grafik PNG dla kalkulatora na Redmi Watch 4.

Środowisko Vela na Redmi Watch 4 nie rysuje tekstu (<text>, <span>, <input>
wyświetlają puste pola), za to <image> działa. Dlatego każdy napis jest
gotowym obrazkiem PNG:
  - k_*.png   przyciski klawiatury (84x58)
  - b_<hex>.png  duże znaki wyświetlacza (26x44), nazwane kodem znaku
  - s_<hex>.png  małe znaki linii działania (13x22)
  - logo.png  ikona 96x96 (większa przesuwa nazwę aplikacji w launcherze)

Uruchom:  python3 scripts/gen_assets.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(ROOT, "src", "common")
IMG = os.path.join(COMMON, "img")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SS = 4

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
GRAY_TXT = (150, 150, 150, 255)
DIGIT_BG = (51, 51, 51, 255)
FUNC_BG = (165, 165, 165, 255)
OP_BG = (255, 149, 0, 255)

KEY = (84, 58)
BIG = (26, 44)
SMALL = (13, 22)

# nazwa pliku, napis, tło, kolor tekstu, rozmiar czcionki
KEYS = [
    ("c", "C", FUNC_BG, BLACK, 30),
    ("neg", "±", FUNC_BG, BLACK, 32),
    ("pct", "%", FUNC_BG, BLACK, 28),
    ("div", "÷", OP_BG, WHITE, 36),
    ("7", "7", DIGIT_BG, WHITE, 30),
    ("8", "8", DIGIT_BG, WHITE, 30),
    ("9", "9", DIGIT_BG, WHITE, 30),
    ("mul", "×", OP_BG, WHITE, 36),
    ("4", "4", DIGIT_BG, WHITE, 30),
    ("5", "5", DIGIT_BG, WHITE, 30),
    ("6", "6", DIGIT_BG, WHITE, 30),
    ("sub", "−", OP_BG, WHITE, 36),
    ("1", "1", DIGIT_BG, WHITE, 30),
    ("2", "2", DIGIT_BG, WHITE, 30),
    ("3", "3", DIGIT_BG, WHITE, 30),
    ("add", "+", OP_BG, WHITE, 36),
    ("0", "0", DIGIT_BG, WHITE, 30),
    ("dot", ".", DIGIT_BG, WHITE, 34),
    ("back", "⌫", FUNC_BG, BLACK, 28),
    ("eq", "=", OP_BG, WHITE, 36),
]

BIG_CHARS = "0123456789.-eEro "
SMALL_CHARS = "0123456789.-e+×÷= "


def font(path, size):
    return ImageFont.truetype(path, size)


def save(img, name, allow_blank=False):
    path = os.path.join(IMG if name != "logo.png" else COMMON, name)
    img.save(path, optimize=True)
    chk = Image.open(path)
    chk.load()
    assert chk.size == img.size
    if not allow_blank:
        assert chk.getbbox() is not None, "pusty obrazek: " + name


def key(name, label, bg, fg, size):
    w, h = KEY[0] * SS, KEY[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h * 0.45, fill=bg)
    f = font(FONT_BOLD if label in "C%" else FONT, size * SS)
    d.text((w / 2, h / 2), label, font=f, fill=fg, anchor="mm")
    save(img.resize(KEY, Image.LANCZOS), "k_%s.png" % name)


def glyph(prefix, ch, box, size, baseline, color):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if ch != " ":
        d = ImageDraw.Draw(img)
        d.text((w / 2, baseline * SS), ch, font=font(FONT, size * SS),
               fill=color, anchor="ms")
    save(img.resize(box, Image.LANCZOS), "%s_%x.png" % (prefix, ord(ch)),
         allow_blank=(ch == " "))


def logo():
    n = 96 * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, n - 1, n - 1], fill=OP_BG)
    # mała klawiatura 2x2 na pomarańczowym kółku
    cell = n * 0.22
    gap = n * 0.06
    x0 = (n - 2 * cell - gap) / 2
    y0 = (n - 2 * cell - gap) / 2
    f = font(FONT_BOLD, int(cell * 0.8))
    for i, ch in enumerate(["+", "−", "×", "="]):
        x = x0 + (i % 2) * (cell + gap)
        y = y0 + (i // 2) * (cell + gap)
        d.rounded_rectangle([x, y, x + cell, y + cell], radius=cell * 0.25,
                            fill=WHITE)
        d.text((x + cell / 2, y + cell / 2), ch, font=f, fill=OP_BG,
               anchor="mm")
    save(img.resize((96, 96), Image.LANCZOS), "logo.png")


def main():
    os.makedirs(IMG, exist_ok=True)
    for f in os.listdir(IMG):
        if f.endswith(".png"):
            os.remove(os.path.join(IMG, f))
    for k in KEYS:
        key(*k)
    for ch in BIG_CHARS:
        glyph("b", ch, BIG, 40, 38, WHITE)
    for ch in SMALL_CHARS:
        glyph("s", ch, SMALL, 18, 17, GRAY_TXT)
    logo()
    print("OK:", len(os.listdir(IMG)), "plików w src/common/img + logo.png")


if __name__ == "__main__":
    main()
