#!/usr/bin/env python3
"""Tarcza "Żółta" dla Redmi Watch 4 (390x450), po polsku.

Duża godzina (godziny białe, minuty w kolorze akcentu), dzień tygodnia
(zmienia się sam: 7 obrazków, źródło 2012), data, bateria oraz cztery
statystyki: kroki, kalorie, tętno i stres.

  python3 scripts/gen_zolta.py [kolor]          # kolor: zolty (domyślny),
                                                # pomaranczowy, niebieski,
                                                # zielony, czerwony, bialy
  python3 scripts/gen_zolta.py --warianty X.png # podgląd wszystkich kolorów
  python3 scripts/gen_zolta.py --dni X.png      # podgląd 7 dni tygodnia

Bezpieczeństwo: tarcza używa tylko tych samych typów elementów co "Nocna",
która działa na zegarku: obrazek (Shape 30), lista dnia tygodnia (Shape 31,
źródło 2012) i liczby (Shape 32). Nie ma tu pierścieni postępu ani wskazówek,
a obrazki są małe (Pierścień miał 21 obrazków 320x320 i zawieszał zegarek).

Czcionka Rubik (licencja SIL OFL, pobierana do build/fonts/):
  https://github.com/google/fonts/tree/main/ofl/rubik

Wynik: build/zolta.json + podglad-zolta.png. Kompilacja:
  node scripts/build.mjs <watchface-designer> Zolta.bin build/zolta.json
"""

import base64
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
IMG = os.path.join(BUILD, "img_zolta")
FONTS = os.path.join(BUILD, "fonts")
FONT_URLS = {
    "Rubik[wght].ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/rubik/Rubik%5Bwght%5D.ttf",
}
W, H, SS = 390, 450, 4

WHITE = (246, 246, 246, 255)
DIM = (150, 150, 150, 255)
# kolor akcentu: minuty, dzień tygodnia, napisy statystyk, błyskawica baterii
SCHEMES = {
    "zolty": (250, 224, 32, 255),
    "pomaranczowy": (255, 149, 0, 255),
    "niebieski": (90, 200, 250, 255),
    "zielony": (60, 210, 100, 255),
    "czerwony": (255, 69, 58, 255),
    "bialy": (170, 170, 175, 255),
}
ACCENT = SCHEMES["zolty"]

BIG = (80, 110)        # cyfry godziny
SMALL = (18, 32)       # cyfry daty i statystyk
DAYS = ["Niedziela", "Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"]
# długość przykładowej wartości w packerze (do wyśrodkowania liczb)
DEMO_LEN = {"0821": 5, "0823": 5, "0822": 3, "0826": 2, "0841": 3}

images = {}


def fonts():
    os.makedirs(FONTS, exist_ok=True)
    for name, url in FONT_URLS.items():
        path = os.path.join(FONTS, name)
        if not os.path.exists(path):
            subprocess.run(["curl", "-sSL", "-f", "-o", path, url], check=True)


def font(name, size, style):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_name(style)
    return f


def add(name, img):
    img = img.convert("RGBA")
    img.save(os.path.join(IMG, name))
    images[name] = {"width": img.width, "height": img.height,
                    "rgba": base64.b64encode(img.tobytes()).decode("ascii")}


def cell(name, text, box, fnt, color, anchor="mm", x=None):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((w / 2 if x is None else x * SS, h / 2), text, font=fnt, fill=color, anchor=anchor)
    add(name, img.resize(box, Image.LANCZOS))


def digits(prefix, box, fnt, color):
    names = []
    for i in range(10):
        nm = "%s_%d.png" % (prefix, i)
        cell(nm, str(i), box, fnt, color)
        names.append(nm)
    return names


def fit(name, style, text, max_w, max_h, start):
    """Największy rozmiar czcionki, przy którym tekst mieści się w polu."""
    size = start
    while size > 8:
        f = font(name, size * SS, style)
        l, t, r, b = f.getbbox(text)
        if r - l <= max_w * SS and b - t <= max_h * SS:
            return f
        size -= 1
    return font(name, 8 * SS, style)


def weekday(i, text):
    box = (290, 56)
    f = fit("Rubik[wght].ttf", "Bold", text, 270, 44, 40)
    nm = "wd_%d.png" % i
    cell(nm, text, box, f, ACCENT)
    return nm


def label(name, text):
    cell(name, text, (150, 26), font("Rubik[wght].ttf", 19 * SS, "SemiBold"), ACCENT)


def battery_icon():
    n = 28 * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([n * 0.06, n * 0.26, n * 0.84, n * 0.74], radius=n * 0.1, outline=WHITE,
                        width=int(n * 0.08))
    d.rectangle([n * 0.86, n * 0.40, n * 0.96, n * 0.60], fill=WHITE)
    # błyskawica w środku
    d.polygon([(n * 0.50, n * 0.30), (n * 0.30, n * 0.53), (n * 0.45, n * 0.53),
               (n * 0.38, n * 0.72), (n * 0.60, n * 0.46), (n * 0.46, n * 0.46)], fill=ACCENT)
    add("i_batt.png", img.resize((28, 28), Image.LANCZOS))


def background():
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    # cienkie linie oddzielające godzinę od statystyk i kolumny statystyk
    d.line([(60 * SS, 282 * SS), (330 * SS, 282 * SS)], fill=(40, 40, 40, 255), width=2 * SS)
    d.line([(195 * SS, 296 * SS), (195 * SS, 412 * SS)], fill=(30, 30, 30, 255), width=2 * SS)
    add("bg.png", img.resize((W, H), Image.LANCZOS))


def num(name, src, x, y, lst, box, n=1, align=0, blank=0):
    return {"Shape": 32, "Name": name, "X": x, "Y": y, "Width": box[0], "Height": box[1],
            "Alpha": 255, "Digits": n, "Alignment": align, "Spacing": 0, "Blanking": blank,
            "DataSrcValue": src, "BitmapList": "|".join(lst)}


def centered(name, src, cx, y, lst, n_max):
    # wyśrodkowana liczba, tak samo jak w "Nocnej" (Alignment=1, bez zer z przodu)
    maxlen = min(n_max, DEMO_LEN[src])
    w = num(name, src, cx - SMALL[0] * maxlen // 2, y, lst, SMALL, n_max, 1, 1)
    w["_cx"] = cx
    return w


def image(name, bmp, x, y):
    im = images[bmp]
    return {"Shape": 30, "Name": name, "X": x, "Y": y, "Width": im["width"], "Height": im["height"],
            "Alpha": 255, "Bitmap": bmp}


def preview(widgets, sample):
    canvas = Image.new("RGBA", (W, H))

    def img_of(n):
        im = images[n]
        return Image.frombytes("RGBA", (im["width"], im["height"]), base64.b64decode(im["rgba"]))
    for w in widgets:
        if w["Shape"] == 30:
            canvas.alpha_composite(img_of(w["Bitmap"]), (w["X"], w["Y"]))
        elif w["Shape"] == 31:
            canvas.alpha_composite(img_of(w["BitmapList"].split("|")[sample[w["DataSrcIndex"]]]), (w["X"], w["Y"]))
        elif w["Shape"] == 32:
            names = w["BitmapList"].split("|")
            s = str(sample[w["DataSrcValue"]])
            if w["Digits"] == 1:
                s = s[-1]
            x = w["_cx"] - len(s) * w["Width"] // 2 if "_cx" in w else w["X"]
            for i, ch in enumerate(s):
                canvas.alpha_composite(img_of(names[int(ch)]), (x + i * w["Width"], w["Y"]))
    return canvas


SAMPLE = {"1001912": 2, "1912": 5, "1212": 1, "1112": 1, "0841": 67, "2012": 3,
          "1000911": 2, "0911": 1, "1211": 0, "1111": 3,
          "0821": 1392, "0823": 382, "0822": 72, "0826": 28}


def build(scheme):
    """Rysuje wszystkie obrazki w danym kolorze i zwraca listę widgetów."""
    global ACCENT
    ACCENT = SCHEMES[scheme]
    fonts()
    images.clear()
    os.makedirs(IMG, exist_ok=True)
    for f in os.listdir(IMG):
        os.remove(os.path.join(IMG, f))

    background()
    big = fit("Rubik[wght].ttf", "Black", "0", BIG[0] - 4, BIG[1] - 6, 140)
    hour = digits("h", BIG, big, WHITE)
    minute = digits("m", BIG, big, ACCENT)
    small = digits("s", SMALL, font("Rubik[wght].ttf", 26 * SS, "Medium"), WHITE)
    cell("dot.png", ".", (10, SMALL[1]), font("Rubik[wght].ttf", 26 * SS, "Medium"), WHITE)
    cell("pct.png", "%", (18, SMALL[1]), font("Rubik[wght].ttf", 20 * SS, "Medium"), DIM)
    wd = [weekday(i, t) for i, t in enumerate(DAYS)]
    label("l_kroki.png", "Kroki")
    label("l_kalorie.png", "Kalorie")
    label("l_tetno.png", "Tętno")
    label("l_stres.png", "Stres")
    battery_icon()

    ty, gap = 158, 14
    x0 = (W - 4 * BIG[0] - gap) // 2
    c1, c2 = 110, 280
    return [
        image("bg", "bg.png", 0, 0),
        # data "25.11" w lewym górnym rogu
        num("day_h", "1001912", 44, 30, small, SMALL),
        num("day_l", "1912", 62, 30, small, SMALL),
        image("dot", "dot.png", 80, 30),
        num("mon_h", "1212", 90, 30, small, SMALL),
        num("mon_l", "1112", 108, 30, small, SMALL),
        # bateria w prawym górnym rogu
        image("i_batt", "i_batt.png", 240, 32),
        centered("batt", "0841", 300, 30, small, 3),
        image("pct", "pct.png", 330, 30),
        # dzień tygodnia: zegarek sam wybiera jeden z 7 obrazków (0 = niedziela)
        {"Shape": 31, "Name": "weekday", "X": (W - 290) // 2, "Y": 88, "Width": 290, "Height": 56,
         "Alpha": 255, "DataSrcIndex": "2012", "DefaultIndex": 0, "BitmapList": "|".join(wd)},
        # duża godzina: HH białe, MM w kolorze akcentu
        num("hour_h", "1000911", x0, ty, hour, BIG),
        num("hour_l", "0911", x0 + BIG[0], ty, hour, BIG),
        num("min_h", "1211", x0 + 2 * BIG[0] + gap, ty, minute, BIG),
        num("min_l", "1111", x0 + 3 * BIG[0] + gap, ty, minute, BIG),
        # statystyki 2x2
        image("l_kroki", "l_kroki.png", c1 - 75, 296),
        centered("steps", "0821", c1, 322, small, 5),
        image("l_kalorie", "l_kalorie.png", c2 - 75, 296),
        centered("kcal", "0823", c2, 322, small, 4),
        image("l_tetno", "l_tetno.png", c1 - 75, 360),
        centered("heart", "0822", c1, 386, small, 3),
        image("l_stres", "l_stres.png", c2 - 75, 360),
        centered("stress", "0826", c2, 386, small, 3),
    ]


def sheet(panels, cols, path):
    w, h = panels[0].size
    out = Image.new("RGB", (cols * (w + 12) + 12, ((len(panels) + cols - 1) // cols) * (h + 12) + 12), (60, 60, 60))
    for i, p in enumerate(panels):
        out.paste(p.convert("RGB"), (12 + (i % cols) * (w + 12), 12 + (i // cols) * (h + 12)))
    out.save(path)


def main(scheme="zolty"):
    widgets = build(scheme)
    pv = preview(widgets, SAMPLE)
    pv.convert("RGB").save(os.path.join(ROOT, "podglad-zolta.png"))
    small_pv = pv.resize((234, 270), Image.LANCZOS).convert("RGBA")
    face = {
        "deviceType": 365, "title": "Zolta", "faceId": "167210091",
        "widgets": [{k: v for k, v in w.items() if not k.startswith("_")} for w in widgets],
        "images": images,
        "preview": {"width": small_pv.width, "height": small_pv.height,
                    "rgba": base64.b64encode(small_pv.tobytes()).decode("ascii")},
    }
    with open(os.path.join(BUILD, "zolta.json"), "w") as f:
        json.dump(face, f)
    mem = sum(im["width"] * im["height"] * 4 for im in images.values())
    print("OK (%s):" % scheme, len(images), "obrazków,", len(widgets), "widgetów, pamięć obrazków ok.",
          mem // 1024, "KB")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--warianty"]:
        sheet([preview(build(k), SAMPLE) for k in SCHEMES], 3, args[1])
    elif args[:1] == ["--dni"]:
        widgets = build(args[2] if len(args) > 2 else "zolty")
        # poniedziałek ... niedziela
        sheet([preview(widgets, dict(SAMPLE, **{"2012": d % 7})) for d in range(1, 8)], 4, args[1])
    else:
        main(args[0] if args else "zolty")
