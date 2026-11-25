#!/usr/bin/env python3
"""Generuje grafiki i opis tarczy "Nocna" dla Redmi Watch 4 (390x450).

Wynik: build/face.json (widgety + obrazki jako surowe RGBA w base64)
oraz build/img/*.png i podglad.png. Kompilację do .bin robi build.mjs.
Wszystkie grafiki są oryginalne, rysowane tutaj kodem.
"""

import base64
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
IMG = os.path.join(BUILD, "img")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_COND = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 390, 450
SS = 4

WHITE = (245, 245, 245, 255)
ACCENT = (255, 149, 0, 255)
GRAY = (140, 140, 150, 255)
BG_TOP = (8, 10, 20)
BG_BOT = (0, 0, 0)
HEART = (255, 70, 90, 255)
GREEN = (80, 220, 120, 255)

BIG = (70, 116)
SMALL = (20, 32)
ICON = (30, 30)

images = {}


def font(path, size):
    return ImageFont.truetype(path, size)


def add(name, img):
    img = img.convert("RGBA")
    img.save(os.path.join(IMG, name))
    images[name] = {
        "width": img.width,
        "height": img.height,
        "rgba": base64.b64encode(img.tobytes()).decode("ascii"),
    }


def text_cell(name, ch, box, size, color, fnt=FONT):
    w, h = box[0] * SS, box[1] * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((w / 2, h / 2), ch, font=font(fnt, size * SS), fill=color, anchor="mm")
    add(name, img.resize(box, Image.LANCZOS))


def background():
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(BG_TOP[i] * (1 - t) + BG_BOT[i] * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c + (255,))
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    bd = ImageDraw.Draw(big)
    # cienki pomarańczowy łuk nad godziną i linia pod nią
    bd.arc([60 * SS, 40 * SS, 330 * SS, 330 * SS], start=200, end=340,
           fill=(255, 149, 0, 110), width=3 * SS)
    bd.line([(70 * SS, 272 * SS), (320 * SS, 272 * SS)], fill=(60, 60, 70, 255), width=2 * SS)
    # pionowe separatory między polami na dole
    for x in (135, 255):
        bd.line([(x * SS, 300 * SS), (x * SS, 370 * SS)], fill=(40, 40, 50, 255), width=2 * SS)
    img.alpha_composite(big.resize((W, H), Image.LANCZOS))
    add("bg.png", img)


def icon_steps():
    n = ICON[0] * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dwa ślady stóp
    d.ellipse([n * 0.10, n * 0.30, n * 0.40, n * 0.80], fill=ACCENT)
    d.ellipse([n * 0.16, n * 0.82, n * 0.36, n * 0.98], fill=ACCENT)
    d.ellipse([n * 0.58, n * 0.08, n * 0.88, n * 0.58], fill=ACCENT)
    d.ellipse([n * 0.64, n * 0.60, n * 0.84, n * 0.76], fill=ACCENT)
    add("i_steps.png", img.resize(ICON, Image.LANCZOS))


def icon_heart():
    n = ICON[0] * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = n * 0.25
    d.ellipse([n * 0.05, n * 0.10, n * 0.05 + 2 * r, n * 0.10 + 2 * r], fill=HEART)
    d.ellipse([n * 0.95 - 2 * r, n * 0.10, n * 0.95, n * 0.10 + 2 * r], fill=HEART)
    d.polygon([(n * 0.07, n * 0.42), (n * 0.93, n * 0.42), (n * 0.5, n * 0.92)], fill=HEART)
    add("i_heart.png", img.resize(ICON, Image.LANCZOS))


def icon_battery():
    n = ICON[0] * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([n * 0.08, n * 0.25, n * 0.84, n * 0.75], radius=n * 0.08,
                        outline=GREEN, width=int(n * 0.07))
    d.rectangle([n * 0.86, n * 0.40, n * 0.95, n * 0.60], fill=GREEN)
    d.rectangle([n * 0.18, n * 0.35, n * 0.60, n * 0.65], fill=GREEN)
    add("i_batt.png", img.resize(ICON, Image.LANCZOS))


def digits(prefix, box, size, color, fnt=FONT):
    names = []
    for i in range(10):
        nm = "%s_%d.png" % (prefix, i)
        text_cell(nm, str(i), box, size, color, fnt)
        names.append(nm)
    return names


def preview_png(widgets):
    """Podgląd: ręcznie złożony obraz z przykładowymi wartościami."""
    sample = {"1000911": 1, "0911": 0, "1211": 0, "1111": 9, "2012": 2,
              "1001912": 2, "1912": 5, "1212": 1, "1112": 1,
              "0821": 8432, "0822": 72, "0841": 86}
    canvas = Image.new("RGBA", (W, H))
    def img_of(n):
        im = images[n]
        return Image.frombytes("RGBA", (im["width"], im["height"]), base64.b64decode(im["rgba"]))
    for w in widgets:
        if w["Shape"] == 30:
            canvas.alpha_composite(img_of(w["Bitmap"]), (w["X"], w["Y"]))
        elif w["Shape"] == 31:
            names = w["BitmapList"].split("|")
            canvas.alpha_composite(img_of(names[sample[w["DataSrcIndex"]]]), (w["X"], w["Y"]))
        elif w["Shape"] == 32:
            names = w["BitmapList"].split("|")
            s = str(sample[w["DataSrcValue"]])
            if w["Digits"] == 1:
                s = s[-1]
            total = len(s) * w["Width"]
            x = w["_cx"] - total // 2 if "_cx" in w else w["X"]
            for i, ch in enumerate(s):
                canvas.alpha_composite(img_of(names[int(ch)]), (x + i * w["Width"], w["Y"]))
    return canvas


def main():
    os.makedirs(IMG, exist_ok=True)
    for f in os.listdir(IMG):
        os.remove(os.path.join(IMG, f))
    background()
    hour = digits("h", BIG, 96, WHITE, FONT_COND)
    minute = digits("m", BIG, 96, ACCENT, FONT_COND)
    small = digits("s", SMALL, 24, WHITE, FONT_COND)
    text_cell("colon.png", ":", (30, BIG[1]), 88, GRAY, FONT_COND)
    text_cell("dot.png", ".", (12, SMALL[1]), 26, WHITE, FONT_COND)
    days = ["NDZ", "PON", "WT", "ŚR", "CZW", "PT", "SOB"]  # 0 = niedziela
    wd = []
    for i, t in enumerate(days):
        nm = "wd_%d.png" % i
        text_cell(nm, t, (80, SMALL[1]), 22, ACCENT, FONT_COND)
        wd.append(nm)
    icon_steps()
    icon_heart()
    icon_battery()

    def num(name, src, x, y, lst, box, digits_n=1, align=0, blank=0):
        return {"Shape": 32, "Name": name, "X": x, "Y": y, "Width": box[0], "Height": box[1],
                "Alpha": 255, "Digits": digits_n, "Alignment": align, "Spacing": 0,
                "Blanking": blank, "DataSrcValue": src, "BitmapList": "|".join(lst)}

    def centered(name, src, cx, y, n_max, demo_len):
        # wyśrodkowane liczby (Alignment=1): packer liczy kotwicę od X
        maxlen = min(n_max, demo_len)
        x = cx - (SMALL[0] * maxlen) // 2
        w = num(name, src, x, y, small, SMALL, n_max, 1, 1)
        w["_cx"] = cx
        return w

    ty = 140
    widgets = [
        {"Shape": 30, "Name": "bg", "X": 0, "Y": 0, "Width": W, "Height": H, "Alpha": 255, "Bitmap": "bg.png"},
        # dzień tygodnia i data: "WT 25.11"
        {"Shape": 31, "Name": "weekday", "X": 92, "Y": 92, "Width": 80, "Height": SMALL[1], "Alpha": 255,
         "DataSrcIndex": "2012", "DefaultIndex": 0, "BitmapList": "|".join(wd)},
        num("day_h", "1001912", 186, 92, small, SMALL),
        num("day_l", "1912", 206, 92, small, SMALL),
        {"Shape": 30, "Name": "dot", "X": 226, "Y": 92, "Width": 12, "Height": SMALL[1], "Alpha": 255, "Bitmap": "dot.png"},
        num("mon_h", "1212", 238, 92, small, SMALL),
        num("mon_l", "1112", 258, 92, small, SMALL),
        # godzina HH:MM
        num("hour_h", "1000911", 27, ty, hour, BIG),
        num("hour_l", "0911", 101, ty, hour, BIG),
        {"Shape": 30, "Name": "colon", "X": 180, "Y": ty, "Width": 30, "Height": BIG[1], "Alpha": 255, "Bitmap": "colon.png"},
        num("min_h", "1211", 219, ty, minute, BIG),
        num("min_l", "1111", 293, ty, minute, BIG),
        # dół: kroki, tętno, bateria
        {"Shape": 30, "Name": "i_steps", "X": 60, "Y": 300, "Width": 30, "Height": 30, "Alpha": 255, "Bitmap": "i_steps.png"},
        {"Shape": 30, "Name": "i_heart", "X": 180, "Y": 300, "Width": 30, "Height": 30, "Alpha": 255, "Bitmap": "i_heart.png"},
        {"Shape": 30, "Name": "i_batt", "X": 300, "Y": 300, "Width": 30, "Height": 30, "Alpha": 255, "Bitmap": "i_batt.png"},
        centered("steps", "0821", 75, 338, 5, 5),
        centered("heart", "0822", 195, 338, 3, 3),
        centered("batt", "0841", 315, 338, 3, 3),
    ]
    prev = preview_png(widgets)
    prev.convert("RGB").save(os.path.join(ROOT, "podglad.png"))
    pv = prev.resize((234, 270), Image.LANCZOS).convert("RGBA")
    face = {
        "deviceType": 365,
        "title": "Nocna",
        "faceId": "365802511",
        "widgets": [{k: v for k, v in w.items() if not k.startswith("_")} for w in widgets],
        "images": images,
        "preview": {"width": pv.width, "height": pv.height,
                    "rgba": base64.b64encode(pv.tobytes()).decode("ascii")},
    }
    with open(os.path.join(BUILD, "face.json"), "w") as f:
        json.dump(face, f)
    print("OK:", len(images), "obrazków, widgetów:", len(widgets))


if __name__ == "__main__":
    main()
