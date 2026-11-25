#!/usr/bin/env python3
"""Generator grafik PNG dla kalkulatora na Redmi Watch 4.

Środowisko Vela na Redmi Watch 4 nie rysuje tekstu (<text>, <span>, <input>
wyświetlają puste pola), za to <image> działa. Dlatego każdy napis jest
gotowym obrazkiem PNG:
  - l_*.png   napisy na klawiszach (tło klawisza rysuje CSS)
  - o_*.png, sw_*.png, t_*.png  ekran ustawień, gear.png  ikona ustawień
  - b_<hex>.png  duże znaki wyświetlacza (26x44), nazwane kodem znaku
  - s_<hex>.png  małe znaki linii działania (13x22)
  - logo.png  ikona 96x96 (większa przesuwa nazwę aplikacji w launcherze)

Uruchom:  python3 scripts/gen_assets.py
"""

import math
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
SCI_BG = (40, 70, 110, 255)

LABEL = (56, 34)
BIG = (26, 44)
SMALL = (13, 22)

# Klawisze: tło rysuje <div> (kolor + zaokrąglenie w CSS), a PNG to tylko
# przezroczysty napis, więc przycisk może mieć dowolny rozmiar.
# nazwa pliku, napis, kolor tekstu, rozmiar czcionki
LABELS = [
    ("c", "C", BLACK, 24), ("back", "⌫", BLACK, 22),
    ("div", "÷", WHITE, 28), ("mul", "×", WHITE, 28),
    ("sub", "−", WHITE, 28), ("add", "+", WHITE, 28), ("eq", "=", WHITE, 28),
    ("dot", ".", WHITE, 28),
    ("lp", "(", WHITE, 24), ("rp", ")", WHITE, 24),
    ("sqrt", "√", WHITE, 24), ("sq", "x²", WHITE, 20), ("pow", "xʸ", WHITE, 20),
    ("pct", "%", WHITE, 22), ("fact", "n!", WHITE, 20), ("pi", "π", WHITE, 24),
    ("inv", "1/x", WHITE, 17), ("ans", "Ans", WHITE, 17),
] + [(str(d), str(d), WHITE, 24) for d in range(10)]

# Ekran ustawień
OPTIONS = [
    ("o_par", "Nawiasy ( )"), ("o_sqrt", "Pierwiastek √"),
    ("o_sq", "Kwadrat x²"), ("o_pow", "Potęga xʸ"),
    ("o_pct", "Procent %"), ("o_fact", "Silnia n!"),
    ("o_pi", "Liczba π"), ("o_inv", "Odwrotność 1/x"),
    ("o_ans", "Ans (ostatni wynik)"), ("o_prev", "Podgląd wyniku"),
    ("o_vib", "Wibracja"),
]
OPT_LABEL = (240, 40)
SWITCH = (64, 36)

BIG_CHARS = "0123456789.−+×÷^√²!%π()eEro "
SMALL_CHARS = BIG_CHARS + "="


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


def label(name, text, fg, size):
    w, h = LABEL[0] * SS, LABEL[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD if text in ("C", "%") else FONT, size * SS)
    d.text((w / 2, h / 2), text, font=f, fill=fg, anchor="mm")
    save(img.resize(LABEL, Image.LANCZOS), "l_%s.png" % name)


def text_left(name, text, box, size, color=WHITE, bold=False, center=False):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD if bold else FONT, size * SS)
    if center:
        d.text((w / 2, h / 2), text, font=f, fill=color, anchor="mm")
    else:
        d.text((4 * SS, h / 2), text, font=f, fill=color, anchor="lm")
    save(img.resize(box, Image.LANCZOS), name)


def switch(name, on):
    w, h = SWITCH[0] * SS, SWITCH[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h / 2,
                        fill=(52, 199, 89, 255) if on else (80, 80, 80, 255))
    r = h / 2 - 3 * SS
    cx = w - h / 2 if on else h / 2
    d.ellipse([cx - r, h / 2 - r, cx + r, h / 2 + r], fill=WHITE)
    save(img.resize(SWITCH, Image.LANCZOS), name)


def gear():
    n = 34 * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    col = (150, 150, 150, 255)
    for i in range(8):
        a = i * math.pi / 4
        x, y = c + math.cos(a) * n * 0.36, c + math.sin(a) * n * 0.36
        r = n * 0.09
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    r = n * 0.33
    d.ellipse([c - r, c - r, c + r, c + r], fill=col)
    r = n * 0.13
    d.ellipse([c - r, c - r, c + r, c + r], fill=(0, 0, 0, 0))
    save(img.resize((34, 34), Image.LANCZOS), "gear.png")


def glyph(prefix, ch, box, size, baseline, color):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if ch != " ":
        d = ImageDraw.Draw(img)
        fs = size
        # szerokie znaki (np. %) zmniejsz, żeby zmieściły się w komórce
        while fs > 8 and font(FONT, fs * SS).getlength(ch) > w * 0.96:
            fs -= 1
        d.text((w / 2, baseline * SS), ch, font=font(FONT, fs * SS),
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
    for l in LABELS:
        label(*l)
    for ch in BIG_CHARS:
        glyph("b", ch, BIG, 40, 38, WHITE)
    for ch in SMALL_CHARS:
        glyph("s", ch, SMALL, 18, 17, GRAY_TXT)
    for name, text in OPTIONS:
        text_left(name + ".png", text, OPT_LABEL, 21)
    switch("sw_on.png", True)
    switch("sw_off.png", False)
    text_left("t_settings.png", "Ustawienia", (300, 40), 28, color=OP_BG, bold=True, center=True)
    text_left("t_prev.png", "◀", (56, 34), 24, center=True)
    text_left("t_next.png", "▶", (56, 34), 24, center=True)
    text_left("t_done.png", "Gotowe", (110, 34), 22, bold=True, center=True)
    text_left("t_p1.png", "1/2", (50, 30), 18, color=GRAY_TXT, center=True)
    text_left("t_p2.png", "2/2", (50, 30), 18, color=GRAY_TXT, center=True)
    gear()
    logo()
    print("OK:", len(os.listdir(IMG)), "plików w src/common/img + logo.png")


if __name__ == "__main__":
    main()
