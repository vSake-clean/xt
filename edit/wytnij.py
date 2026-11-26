#!/usr/bin/env python3
"""Wycina ten sam prostokąt z wielu screenów (np. podgląd zdjęcia w czacie).

Przykład (podgląd w okienku "Remiks", screen 1080x2460):
  python3 wytnij.py --ramka 308,1576,463,463 screeny/*.jpg --do materialy/
"""
import argparse
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("pliki", nargs="+", type=Path)
p.add_argument("--ramka", required=True, help="x,y,szerokosc,wysokosc w pikselach")
p.add_argument("--do", required=True, type=Path, help="folder docelowy")
p.add_argument("--prefiks", default="", help="początek nazw plików wynikowych")
a = p.parse_args()

x, y, w, h = (int(v) for v in a.ramka.split(","))
a.do.mkdir(parents=True, exist_ok=True)
for i, src in enumerate(a.pliki, 1):
    dst = a.do / f"{a.prefiks}{i:02d}.png"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                        "-vf", f"crop={w}:{h}:{x}:{y}", "-frames:v", "1", str(dst)])
    if r.returncode:
        sys.exit(f"Nie udało się: {src}")
    print(f"{src.name} -> {dst}")
