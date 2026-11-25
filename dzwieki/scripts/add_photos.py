#!/usr/bin/env python3
"""Wkłada zdjęcia do aplikacji (tylko do prywatnej paczki, nie do repo).

  python3 scripts/add_photos.py zdj1.jpg zdj2.png ...   # dodaje zdjęcia
  python3 scripts/add_photos.py --clear                 # usuwa je

Każde zdjęcie jest zmniejszane tak, by zmieściło się w polu 370x320
(proporcje bez zmian, czarne pasy), i zapisywane jako JPG (baseline,
jakość 80) w src/common/foto/<n>.jpg. Liczba trafia do src/common/fotos.js.
Folder src/common/foto/ jest w .gitignore.
"""

import os
import shutil
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOTO = os.path.join(ROOT, "src", "common", "foto")
JS = os.path.join(ROOT, "src", "common", "fotos.js")
BOX = (370, 320)
HEADER = ("// Liczba zdjęć w paczce. Ustawia ją scripts/add_photos.py.\n"
          "// W repozytorium zawsze 0: zdjęcia trafiają tylko do prywatnej paczki.\n")


def write_count(n):
    with open(JS, "w") as f:
        f.write(HEADER + "export const FOTO_COUNT = %d\n" % n)


def clear():
    shutil.rmtree(FOTO, ignore_errors=True)
    write_count(0)


def add(paths):
    clear()
    os.makedirs(FOTO)
    for i, p in enumerate(paths, 1):
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        im.thumbnail(BOX, Image.LANCZOS)
        out = Image.new("RGB", BOX, (0, 0, 0))
        out.paste(im, ((BOX[0] - im.width) // 2, (BOX[1] - im.height) // 2))
        out.save(os.path.join(FOTO, "%d.jpg" % i), "JPEG", quality=80, optimize=True,
                 progressive=False, subsampling=2)
    write_count(len(paths))
    size = sum(os.path.getsize(os.path.join(FOTO, f)) for f in os.listdir(FOTO))
    print("OK:", len(paths), "zdjęć,", size // 1024, "KB")


if __name__ == "__main__":
    if sys.argv[1:] == ["--clear"]:
        clear()
        print("usunięto zdjęcia")
    elif len(sys.argv) > 1:
        add(sys.argv[1:])
    else:
        print(__doc__)
