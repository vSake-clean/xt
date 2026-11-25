#!/usr/bin/env python3
"""Dwie kolejne tarcze dla Redmi Watch 4 w stylu "Nocnej":

  Pierścień  - godzina w środku, pierścień zapełnia się wraz z % celu kroków
  Analog     - wskazówki na czarnym tle, kreski godzin, dzień i data

Używa funkcji z gen_face.py. Wynik: build/<nazwa>.json + podglad-<nazwa>.png.
Uruchom:  python3 scripts/gen_extra.py
"""

import base64
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_face as F  # noqa: E402

W, H, SS = F.W, F.H, F.SS
LIGHT = (200, 204, 210, 255)
TRACK = (30, 31, 36, 255)
DAYS = ["NDZ", "PON", "WT", "ŚR", "CZW", "PT", "SOB"]


def reset():
    F.images.clear()
    os.makedirs(F.IMG, exist_ok=True)


def img_of(name):
    im = F.images[name]
    return Image.frombytes("RGBA", (im["width"], im["height"]), base64.b64decode(im["rgba"]))


def write(name, title, face_id, widgets, preview):
    preview.convert("RGB").save(os.path.join(F.ROOT, "podglad-%s.png" % name))
    pv = preview.resize((234, 270), Image.LANCZOS).convert("RGBA")
    face = {
        "deviceType": 365, "title": title, "faceId": face_id,
        "widgets": [{k: v for k, v in w.items() if not k.startswith("_")} for w in widgets],
        "images": dict(F.images),
        "preview": {"width": pv.width, "height": pv.height,
                    "rgba": base64.b64encode(pv.tobytes()).decode("ascii")},
    }
    with open(os.path.join(F.BUILD, name + ".json"), "w") as f:
        json.dump(face, f)
    print(name, "OK:", len(F.images), "obrazków,", len(widgets), "widgetów")


def num(name, src, x, y, lst, box, n=1, align=0, blank=0):
    return {"Shape": 32, "Name": name, "X": x, "Y": y, "Width": box[0], "Height": box[1],
            "Alpha": 255, "Digits": n, "Alignment": align, "Spacing": 0, "Blanking": blank,
            "DataSrcValue": src, "BitmapList": "|".join(lst)}


def image(name, bmp, x, y):
    im = F.images[bmp]
    return {"Shape": 30, "Name": name, "X": x, "Y": y, "Width": im["width"],
            "Height": im["height"], "Alpha": 255, "Bitmap": bmp}


def draw_digits(canvas, lst, value, x, y, w, center=False):
    s = str(value)
    if center:
        x = x - len(s) * w // 2
    for i, ch in enumerate(s):
        canvas.alpha_composite(img_of(lst[int(ch)]), (x + i * w, y))


# ---------------------------------------------------------------- Pierścień
def ring():
    reset()
    cx, cy, R, RW = 195, 210, 150, 10
    box = 2 * R + 2 * RW  # 320
    # tło z ciemnym torem pierścienia
    bg = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 255))
    d = ImageDraw.Draw(bg)
    # środek grubości toru leży na promieniu R (tak samo jak pasek postępu)
    ro = R + RW / 2
    d.ellipse([(cx - ro) * SS, (cy - ro) * SS, (cx + ro) * SS, (cy + ro) * SS],
              outline=TRACK, width=RW * SS)
    F.add("bg.png", bg.resize((W, H), Image.LANCZOS))

    # klatki postępu: 0, 5, ..., 100 %
    steps_pct = list(range(0, 101, 5))
    frames = []
    for p in steps_pct:
        im = Image.new("RGBA", (box * SS, box * SS), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        o = RW * SS
        rect = [o, o, (box - RW) * SS, (box - RW) * SS]
        if p > 0:
            end = -90 + 360 * p / 100.0
            dd.arc([rect[0] - o / 2, rect[1] - o / 2, rect[2] + o / 2, rect[3] + o / 2],
                   start=-90, end=end, fill=LIGHT, width=RW * SS)
            # zaokrąglone końce
            for ang in (-90, end):
                a = math.radians(ang)
                rr = (box / 2 - RW) * SS  # = R, środek grubości paska
                px, py = box * SS / 2 + rr * math.cos(a), box * SS / 2 + rr * math.sin(a)
                dd.ellipse([px - o / 2, py - o / 2, px + o / 2, py + o / 2], fill=LIGHT)
        nm = "ring_%03d.png" % p
        F.add(nm, im.resize((box, box), Image.LANCZOS))
        frames.append("(%d):%s" % (p, nm))

    hour = F.digits("h", (52, 88), 72, F.WHITE, F.FONT_LIGHT)
    minute = F.digits("m", (52, 88), 72, F.ACCENT, F.FONT_LIGHT)
    small = F.digits("s", F.SMALL, 24, LIGHT, F.FONT_LIGHT)
    tiny = F.digits("t", (16, 26), 19, LIGHT, F.FONT_LIGHT)
    F.text_cell("colon.png", ":", (22, 88), 66, F.GRAY, F.FONT_LIGHT)
    F.text_cell("dot.png", ".", (12, F.SMALL[1]), 24, LIGHT, F.FONT_LIGHT)
    wd = []
    for i, t in enumerate(DAYS):
        nm = "wd_%d.png" % i
        F.text_cell(nm, t, (70, F.SMALL[1]), 20, F.ACCENT, F.FONT_COND)
        wd.append(nm)
    F.icon_steps()
    F.icon_heart()
    F.icon_battery()

    ty = 168
    tx = cx - (4 * 52 + 22) // 2  # 80
    widgets = [
        image("bg", "bg.png", 0, 0),
        {"Shape": 31, "Name": "ring", "X": cx - box // 2, "Y": cy - box // 2,
         "Width": box, "Height": box, "Alpha": 255, "DataSrcIndex": "1021",
         "DefaultIndex": 0, "BitmapList": "|".join(frames)},
        {"Shape": 31, "Name": "weekday", "X": 100, "Y": 118, "Width": 70, "Height": F.SMALL[1],
         "Alpha": 255, "DataSrcIndex": "2012", "DefaultIndex": 0, "BitmapList": "|".join(wd)},
        num("day_h", "1001912", 178, 118, small, F.SMALL),
        num("day_l", "1912", 198, 118, small, F.SMALL),
        image("dot", "dot.png", 218, 118),
        num("mon_h", "1212", 230, 118, small, F.SMALL),
        num("mon_l", "1112", 250, 118, small, F.SMALL),
        num("hour_h", "1000911", tx, ty, hour, (52, 88)),
        num("hour_l", "0911", tx + 52, ty, hour, (52, 88)),
        image("colon", "colon.png", tx + 104, ty),
        num("min_h", "1211", tx + 126, ty, minute, (52, 88)),
        num("min_l", "1111", tx + 178, ty, minute, (52, 88)),
        image("i_steps", "i_steps.png", cx - 15, 266),
        num("steps", "0821", cx - 50, 300, small, F.SMALL, 5, 1, 1),
        image("i_heart", "i_heart.png", 70, 392),
        num("heart", "0822", 106, 394, tiny, (16, 26), 3, 1, 1),
        image("i_batt", "i_batt.png", 230, 392),
        num("batt", "0841", 266, 394, tiny, (16, 26), 3, 1, 1),
    ]
    # podgląd: 10:09, 64% kroków
    pv = img_of("bg.png").copy()
    pv.alpha_composite(img_of("ring_065.png"), (cx - box // 2, cy - box // 2))
    pv.alpha_composite(img_of("wd_2.png"), (100, 118))
    draw_digits(pv, small, "25", 178, 118, 20)
    pv.alpha_composite(img_of("dot.png"), (218, 118))
    draw_digits(pv, small, "11", 230, 118, 20)
    draw_digits(pv, hour, "10", tx, ty, 52)
    pv.alpha_composite(img_of("colon.png"), (tx + 104, ty))
    draw_digits(pv, minute, "09", tx + 126, ty, 52)
    pv.alpha_composite(img_of("i_steps.png"), (cx - 15, 266))
    draw_digits(pv, small, 6432, cx, 300, 20, center=True)
    pv.alpha_composite(img_of("i_heart.png"), (70, 392))
    draw_digits(pv, tiny, 72, 106 + 24, 394, 16, center=True)
    pv.alpha_composite(img_of("i_batt.png"), (230, 392))
    draw_digits(pv, tiny, 86, 266 + 24, 394, 16, center=True)
    write("pierscien", "Pierscien", "167210089", widgets, pv)


# ---------------------------------------------------------------- Analog
def hand(name, w, length, tail, color, tip_round=True):
    """Wskazówka skierowana w górę; punkt obrotu = (w/2, length)."""
    hgt = length + tail
    im = Image.new("RGBA", (w * SS, hgt * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, hgt * SS - 1], radius=w * SS / 2 if tip_round else 0,
                        fill=color)
    F.add(name, im.resize((w, hgt), Image.LANCZOS))
    return (w // 2, length)


def analog():
    reset()
    cx, cy = 195, 225
    bg = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 255))
    d = ImageDraw.Draw(bg)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        if i % 5 == 0:
            main = i % 15 == 0
            r0, r1 = (150, 182) if main else (160, 180)
            col = (235, 235, 235, 255) if main else (120, 124, 132, 255)
            wdt = 5 if main else 3
        else:
            r0, r1, col, wdt = 174, 180, (45, 47, 52, 255), 2
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        d.line([(x0 * SS, y0 * SS), (x1 * SS, y1 * SS)], fill=col, width=wdt * SS)
    F.add("bg.png", bg.resize((W, H), Image.LANCZOS))

    hp = hand("hour.png", 10, 95, 18, F.WHITE)
    mp = hand("minute.png", 8, 140, 20, LIGHT)
    sp = hand("second.png", 3, 155, 30, (130, 134, 142, 255))
    cap = Image.new("RGBA", (16 * SS, 16 * SS), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cap)
    cd.ellipse([0, 0, 16 * SS - 1, 16 * SS - 1], fill=F.WHITE)
    cd.ellipse([5 * SS, 5 * SS, 11 * SS, 11 * SS], fill=(0, 0, 0, 255))
    F.add("cap.png", cap.resize((16, 16), Image.LANCZOS))

    small = F.digits("s", F.SMALL, 24, LIGHT, F.FONT_LIGHT)
    wd = []
    for i, t in enumerate(DAYS):
        nm = "wd_%d.png" % i
        F.text_cell(nm, t, (70, F.SMALL[1]), 20, F.ACCENT, F.FONT_COND)
        wd.append(nm)

    dy = 290
    widgets = [
        image("bg", "bg.png", 0, 0),
        {"Shape": 31, "Name": "weekday", "X": 128, "Y": dy, "Width": 70, "Height": F.SMALL[1],
         "Alpha": 255, "DataSrcIndex": "2012", "DefaultIndex": 0, "BitmapList": "|".join(wd)},
        num("day_h", "1001912", 204, dy, small, F.SMALL),
        num("day_l", "1912", 224, dy, small, F.SMALL),
        {"Shape": 27, "Name": "clock", "X": 0, "Y": 0, "Width": W, "Height": H, "Alpha": 255,
         "BackgroundImage": "",
         "HourHandImage": "hour.png", "HourImageRotateX": hp[0], "HourImageRotateY": hp[1],
         "MinuteHandImage": "minute.png", "MinuteImageRotateX": mp[0], "MinuteImageRotateY": mp[1],
         "SecondHandImage": "second.png", "SecondImageRotateX": sp[0], "SecondImageRotateY": sp[1]},
        image("cap", "cap.png", cx - 8, cy - 8),
    ]
    # podgląd: 10:09:30
    pv = img_of("bg.png").copy()
    pv.alpha_composite(img_of("wd_2.png"), (128, dy))
    draw_digits(pv, small, "25", 204, dy, 20)
    for nm, piv, ang in (("hour.png", hp, (10 + 9 / 60) * 30), ("minute.png", mp, 9.5 * 6),
                         ("second.png", sp, 30 * 6)):
        im = img_of(nm)
        # rozszerz tak, by punkt obrotu był w środku, i obróć
        big = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        big.alpha_composite(im, (200 - piv[0], 200 - piv[1]))
        big = big.rotate(-ang, resample=Image.BICUBIC, center=(200, 200))
        pv.alpha_composite(big, (cx - 200, cy - 200))
    pv.alpha_composite(img_of("cap.png"), (cx - 8, cy - 8))
    write("analog", "Analog", "167210090", widgets, pv)


if __name__ == "__main__":
    ring()
    analog()
