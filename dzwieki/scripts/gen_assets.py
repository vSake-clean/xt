#!/usr/bin/env python3
"""Generator grafik PNG dla aplikacji Dźwięki na Redmi Watch 4.

Redmi Watch 4 nie rysuje tekstu w szybkich aplikacjach (<text> jest pusty),
dlatego każdy napis, cyfra i ikona to gotowy obrazek PNG. Tła przycisków
rysuje CSS (<div> z background-color), a PNG mają przezroczyste tło.

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
GRAY = (142, 142, 147, 255)
TEAL = (76, 215, 200, 255)
LAV = (179, 157, 250, 255)
AMBER = (255, 179, 64, 255)
PINK = (255, 120, 170, 255)
RED = (255, 105, 97, 255)
DARK = (0, 0, 0, 255)

SOUNDS = [
    ("ping", "Ping"), ("kropla", "Kropla"), ("dzwonek", "Dzwonek"),
    ("ptaszek", "Ptaszek"), ("gong", "Gong"), ("klik", "Klik"),
    ("alarm", "Alarm"), ("fanfara", "Fanfara"), ("wlasny", "Własny dźwięk"),
]
MEMES = [
    ("bomba_plant", "Bomba: podłożenie"), ("bomba_tik", "Bomba: odliczanie"),
    ("wybuch", "Wybuch"), ("kliker", "Kliker (pies)"), ("boom", "Boom"),
    ("smutna", "Smutna trąbka"), ("badumtss", "Ba dum tss"), ("trabka", "Trąbka MLG"),
    ("rura", "Metalowa rura"), ("swierszcze", "Świerszcze"), ("boing", "Boing"),
    ("blad", "Błąd"), ("pierd", "Pierd"), ("bruh", "Bruh"),
    ("zgrzyt", "Zgrzyt płyty"), ("smiech", "Śmiech publiczności"),
]
VIBES = [
    ("tik", "Tik"), ("podwojny", "Podwójny"), ("serce", "Serce"), ("fala", "Fala"),
    ("sos", "SOS"), ("alarm", "Alarm"), ("zegar", "Zegar"), ("wlasna", "Własna wibracja"),
]
NOTE_NAMES = ["·", "C", "D", "E", "F", "G", "A", "H", "C'"]

NAME = (230, 40)
DIG_BIG = (46, 80)
DIG_SMALL = (14, 24)
LABEL = (100, 34)
CELL = (60, 60)


def font(path, size):
    return ImageFont.truetype(path, size)


def canvas(box):
    img = Image.new("RGBA", (box[0] * SS, box[1] * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name, box):
    out = img.resize(box, Image.LANCZOS)
    path = os.path.join(COMMON if name == "logo.png" else IMG, name)
    out.save(path, optimize=True)
    chk = Image.open(path)
    chk.load()
    assert chk.size == box
    assert chk.getbbox() is not None, "pusty obrazek: " + name


def text(name, s, box, size, color=WHITE, bold=False, align="center"):
    img, d = canvas(box)
    fs = size
    f = font(FONT_BOLD if bold else FONT, fs * SS)
    while fs > 8 and f.getlength(s) > (box[0] - 8) * SS:
        fs -= 1
        f = font(FONT_BOLD if bold else FONT, fs * SS)
    w, h = box[0] * SS, box[1] * SS
    if align == "left":
        d.text((6 * SS, h / 2), s, font=f, fill=color, anchor="lm")
    else:
        d.text((w / 2, h / 2), s, font=f, fill=color, anchor="mm")
    save(img, name, box)


def digit(name, ch, box, size, color):
    img, d = canvas(box)
    w, h = box[0] * SS, box[1] * SS
    d.text((w / 2, h / 2), ch, font=font(FONT, size * SS), fill=color, anchor="mm")
    save(img, name, box)


# ---------------------------------------------------------------- ikony
def speaker(d, x, y, s, color, waves=1):
    """Głośnik o wysokości s w punkcie (x, y) = lewy górny róg."""
    d.rectangle([x, y + s * 0.32, x + s * 0.22, y + s * 0.68], fill=color)
    d.polygon([(x + s * 0.20, y + s * 0.32), (x + s * 0.48, y + s * 0.08),
               (x + s * 0.48, y + s * 0.92), (x + s * 0.20, y + s * 0.68)], fill=color)
    for i in range(waves):
        r = s * (0.22 + 0.17 * i)
        cx, cy = x + s * 0.52, y + s / 2
        d.arc([cx - r, cy - r, cx + r, cy + r], start=-50, end=50, fill=color,
              width=max(1, int(s * 0.07)))


def vibe_icon(d, x, y, s, color):
    """Zegarek z falkami po bokach."""
    bw, bh = s * 0.42, s * 0.72
    bx, by = x + (s - bw) / 2, y + (s - bh) / 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s * 0.1, outline=color,
                        width=int(s * 0.07))
    for side in (-1, 1):
        for k in range(2):
            ox = (bw / 2 + s * (0.1 + 0.12 * k)) * side
            cx = x + s / 2 + ox
            pts = []
            for j in range(9):
                yy = y + s * 0.3 + j * s * 0.05
                pts.append((cx + math.sin(j * math.pi / 2) * s * 0.025, yy))
            d.line(pts, fill=color, width=int(s * 0.05))


def bomb_icon(d, x, y, s, color):
    """Okrągła bomba z lontem i iskrą."""
    r = s * 0.33
    cx, cy = x + s * 0.42, y + s * 0.6
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.rectangle([cx + r * 0.35, cy - r * 1.18, cx + r * 0.85, cy - r * 0.72], fill=color)
    d.arc([cx + r * 0.55, cy - r * 1.9, cx + r * 1.55, cy - r * 0.9], start=180, end=300,
          fill=color, width=int(s * 0.05))
    sx, sy = cx + r * 1.32, cy - r * 1.75
    for k in range(8):
        a = k * math.pi / 4
        rr = s * (0.1 if k % 2 == 0 else 0.06)
        d.line([(sx, sy), (sx + math.cos(a) * rr, sy + math.sin(a) * rr)], fill=WHITE,
               width=int(s * 0.03))


def photo_icon(d, x, y, s, color):
    """Ramka zdjęcia z górami i słońcem."""
    w, h = s * 0.92, s * 0.72
    x0, y0 = x + (s - w) / 2, y + (s - h) / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=s * 0.08, outline=color, width=int(s * 0.07))
    d.polygon([(x0 + w * 0.1, y0 + h * 0.85), (x0 + w * 0.38, y0 + h * 0.4), (x0 + w * 0.6, y0 + h * 0.85)],
              fill=color)
    d.polygon([(x0 + w * 0.45, y0 + h * 0.85), (x0 + w * 0.66, y0 + h * 0.55), (x0 + w * 0.9, y0 + h * 0.85)],
              fill=color)
    r = s * 0.08
    d.ellipse([x0 + w * 0.72 - r, y0 + h * 0.3 - r, x0 + w * 0.72 + r, y0 + h * 0.3 + r], fill=color)


def menu_tile(name, label, color, kind):
    """Kafelek siatki 2x2: ikona na górze, napis pod spodem."""
    box = (150, 130)
    img, d = canvas(box)
    s = 66 * SS
    x, y = (box[0] * SS - s) / 2, 12 * SS
    {"s": lambda: speaker(d, x + 4 * SS, y, s, color, waves=2),
     "m": lambda: bomb_icon(d, x, y, s, color),
     "v": lambda: vibe_icon(d, x, y, s, color),
     "f": lambda: photo_icon(d, x, y, s, color)}[kind]()
    d.text((box[0] * SS / 2, 106 * SS), label, font=font(FONT_BOLD, 24 * SS), fill=WHITE, anchor="mm")
    save(img, name, box)


def arrow(name, direction, box=(40, 34), color=WHITE):
    img, d = canvas(box)
    w, h = box[0] * SS, box[1] * SS
    cx, cy, r = w / 2, h / 2, h * 0.28
    if direction == "left":
        pts = [(cx + r * 0.5, cy - r), (cx - r * 0.5, cy), (cx + r * 0.5, cy + r)]
    else:
        pts = [(cx - r * 0.5, cy - r), (cx + r * 0.5, cy), (cx - r * 0.5, cy + r)]
    d.line(pts, fill=color, width=int(3.2 * SS), joint="curve")
    for p in (pts[0], pts[2]):
        rr = 1.6 * SS
        d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=color)
    save(img, name, box)


def play_icon(name, box=(60, 40)):
    img, d = canvas(box)
    w, h = box[0] * SS, box[1] * SS
    r = h * 0.34
    d.polygon([(w / 2 - r * 0.7, h / 2 - r), (w / 2 + r * 0.9, h / 2),
               (w / 2 - r * 0.7, h / 2 + r)], fill=DARK)
    save(img, name, box)


def stop_icon(name, box=(60, 40)):
    img, d = canvas(box)
    w, h = box[0] * SS, box[1] * SS
    r = h * 0.26
    d.rounded_rectangle([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], radius=r * 0.25, fill=DARK)
    save(img, name, box)




def step_cell(name, kind, value):
    img, d = canvas(CELL)
    w, h = CELL[0] * SS, CELL[1] * SS
    if kind == "n":
        if value == 0:
            r = 4 * SS
            d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=GRAY)
        else:
            d.text((w / 2, h / 2), NOTE_NAMES[value], font=font(FONT_BOLD, 30 * SS),
                   fill=TEAL, anchor="mm")
    else:
        if value == 0:
            r = 4 * SS
            d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=GRAY)
        else:
            bw = (22 if value == 1 else 46) * SS
            bh = 14 * SS
            d.rounded_rectangle([w / 2 - bw / 2, h / 2 - bh / 2, w / 2 + bw / 2, h / 2 + bh / 2],
                                radius=bh / 2, fill=LAV)
    save(img, name, CELL)


def logo():
    n = 96
    img, d = canvas((n, n))
    N = n * SS
    d.ellipse([0, 0, N - 1, N - 1], fill=(24, 92, 88, 255))
    speaker(d, N * 0.2, N * 0.24, N * 0.52, TEAL, waves=1)
    # mała falka wibracji po prawej
    pts = []
    for j in range(9):
        pts.append((N * 0.76 + math.sin(j * math.pi / 2) * N * 0.03, N * 0.32 + j * N * 0.045))
    d.line(pts, fill=LAV, width=int(N * 0.04))
    save(img, "logo.png", (n, n))


def main():
    os.makedirs(IMG, exist_ok=True)
    for f in os.listdir(IMG):
        if f.endswith(".png"):
            os.remove(os.path.join(IMG, f))

    # menu
    text("t_title.png", "Ciche dźwięki", (300, 40), 28, TEAL, bold=True)
    menu_tile("m_snd.png", "Dźwięki", TEAL, "s")
    menu_tile("m_mem.png", "Memy", AMBER, "m")
    menu_tile("m_vib.png", "Wibracje", LAV, "v")
    menu_tile("m_foto.png", "Zdjęcia", PINK, "f")

    # zdjęcia
    text("h_f.png", "Zdjęcia", (230, 40), 28, PINK, bold=True, align="left")
    text("t_nofoto.png", "Brak zdjęć w tej paczce", (330, 34), 22, WHITE)
    text("t_nofoto2.png", "Zdjęcia dodaje się przy budowaniu", (330, 26), 17, GRAY)
    text("k_sl.png", "/", DIG_SMALL, 20, GRAY)

    # nagłówki list i nazwy
    text("h_s.png", "Dźwięki", (230, 40), 28, TEAL, bold=True, align="left")
    text("h_m.png", "Memy", (230, 40), 28, AMBER, bold=True, align="left")
    text("h_v.png", "Wibracje", (230, 40), 28, LAV, bold=True, align="left")
    for i, s in MEMES:
        text("n_m_%s.png" % i, s, NAME, 24, align="left")
    for i, s in SOUNDS:
        text("n_s_%s.png" % i, s, NAME, 24, align="left")
    for i, s in VIBES:
        text("n_v_%s.png" % i, s, NAME, 24, align="left")

    # cyfry
    for c in "0123456789":
        digit("d_%s.png" % c, c, DIG_BIG, 70, WHITE)
        digit("k_%s.png" % c, c, DIG_SMALL, 20, GRAY)

    # ekran poziomu
    text("t_of_s.png", "głośność (1–1000)", (300, 26), 17, GRAY)
    text("t_of_v.png", "siła wibracji (1–1000)", (300, 26), 17, GRAY)
    for name, s in (("m1", "−1"), ("p1", "+1"), ("m10", "−10"), ("p10", "+10"),
                    ("m100", "−100"), ("p100", "+100")):
        text("b_%s.png" % name, s, LABEL, 26, bold=True)
    text("b_min.png", "1", (60, 40), 26, bold=True)
    text("t_err.png", "Zegarek nie odtworzył dźwięku", (330, 26), 17, RED)
    play_icon("b_play.png")
    stop_icon("b_stop.png")
    text("b_edit.png", "✎", (60, 40), 30)

    # edytor
    for v in range(9):
        step_cell("e_%d.png" % v, "n", v)
    for v in range(3):
        step_cell("w_%d.png" % v, "w", v)
    text("t_hint.png", "Dotknij pola, aby zmienić", (300, 26), 17, GRAY)
    text("b_done.png", "Gotowe", (110, 34), 22, DARK, bold=True)

    # nawigacja
    arrow("i_back.png", "left")
    arrow("i_prev.png", "left")
    arrow("i_next.png", "right")
    arrow("i_more.png", "right", (20, 24), GRAY)
    for n in (2, 3, 4):
        for k in range(1, n + 1):
            text("p_%d_%d.png" % (k, n), "%d/%d" % (k, n), (50, 30), 18, GRAY)

    logo()
    print("OK:", len(os.listdir(IMG)), "plików w src/common/img + logo.png")


if __name__ == "__main__":
    main()
