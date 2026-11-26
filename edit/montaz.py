#!/usr/bin/env python3
"""Montaż: składa zdjęcia i klipy z folderu materialy/ w jeden film (ffmpeg).

Kolejność = kolejność nazw plików (np. 01_..., 02_...).
Zdjęcia dostają powolny zoom (Ken Burns), klipy są skalowane i przycinane
do wspólnego kadru, między ujęciami jest płynne przejście.
Plik muzyka.* (mp3/m4a/wav/aac/ogg) w materialy/ zostaje podkładem.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMG = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic"}
VID = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}
AUD = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"}
FORMATY = {"pion": (1080, 1920), "poziom": (1920, 1080), "kwadrat": (1080, 1080)}
FPS = 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Błąd ffmpeg:\n{' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(out)


def duration(path):
    return float(probe(path)["format"]["duration"])


def has_audio(path):
    return any(s["codec_type"] == "audio" for s in probe(path)["streams"])


def kadr(w, h):
    # wypełnij kadr i przytnij nadmiar (bez czarnych pasów)
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1,fps={FPS},format=yuv420p")


def segment_zdjecie(src, dst, w, h, czas, idx):
    klatki = int(czas * FPS)
    # skaluj z zapasem, potem zoompan (naprzemiennie zoom in / zoom out)
    if idx % 2 == 0:
        z = "min(zoom+0.0010,1.15)"
    else:
        z = "if(eq(on,0),1.15,max(zoom-0.0010,1.0))"
    vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={klatki}:s={w}x{h}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-vf", vf, "-t", f"{czas}", "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(dst)])


def segment_klip(src, dst, w, h, maks):
    d = duration(src)
    t = min(d, maks) if maks else d
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if has_audio(src):
        mapa = ["-map", "0:v:0", "-map", "0:a:0"]
        af = ["-af", "aresample=48000,aformat=channel_layouts=stereo"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        mapa = ["-map", "0:v:0", "-map", "1:a"]
        af = []
    cmd += ["-t", f"{t}", "-vf", kadr(w, h), *mapa, *af,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", str(dst)]
    run(cmd)


def sklej(segmenty, dst, przejscie, muzyka, glosnosc_klipow):
    dl = [duration(s) for s in segmenty]
    n = len(segmenty)
    T = min([przejscie] + [d / 2 for d in dl]) if n > 1 else 0
    cmd = ["ffmpeg", "-y"]
    for s in segmenty:
        cmd += ["-i", str(s)]
    f = []
    if n == 1:
        f.append("[0:v]null[v];[0:a]anull[a]")
        total = dl[0]
    else:
        v, a, off = "[0:v]", "[0:a]", 0.0
        for i in range(1, n):
            off += dl[i - 1] - T
            f.append(f"{v}[{i}:v]xfade=transition=fade:duration={T}:offset={off:.3f}[v{i}]")
            f.append(f"{a}[{i}:a]acrossfade=d={T}[a{i}]")
            v, a = f"[v{i}]", f"[a{i}]"
        f.append(f"{v}null[v];{a}anull[a]")
        total = sum(dl) - T * (n - 1)
    fo = max(total - 1.0, 0)
    f.append(f"[v]fade=t=in:d=0.5,fade=t=out:st={fo:.3f}:d=1[vo]")
    if muzyka:
        cmd += ["-stream_loop", "-1", "-i", str(muzyka)]
        f.append(f"[a]volume={glosnosc_klipow}[ak];"
                 f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f}[m];"
                 f"[ak][m]amix=inputs=2:duration=first:normalize=0[mx];"
                 f"[mx]afade=t=out:st={fo:.3f}:d=1[ao]")
    else:
        f.append(f"[a]afade=t=out:st={fo:.3f}:d=1[ao]")
    cmd += ["-filter_complex", ";".join(f), "-map", "[vo]", "-map", "[ao]",
            "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)]
    run(cmd)
    return total


def main():
    p = argparse.ArgumentParser(description="Montaż zdjęć i klipów w jeden film.")
    p.add_argument("--wejscie", default=HERE / "materialy", type=Path, help="folder z materiałami")
    p.add_argument("--wyjscie", default=HERE / "gotowe" / "edit.mp4", type=Path, help="plik wynikowy")
    p.add_argument("--format", choices=FORMATY, default="pion", help="pion 9:16 (domyślnie), poziom 16:9, kwadrat 1:1")
    p.add_argument("--zdjecie", type=float, default=3.0, help="ile sekund trwa zdjęcie")
    p.add_argument("--klip-maks", type=float, default=0, help="maks. długość klipu w s (0 = cały)")
    p.add_argument("--przejscie", type=float, default=0.5, help="długość przejścia w s")
    p.add_argument("--glosnosc-klipow", type=float, default=0.3, help="głośność dźwięku z klipów, gdy jest muzyka")
    a = p.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("Brak ffmpeg w systemie.")
    pliki = sorted(x for x in a.wejscie.iterdir() if x.is_file() and not x.name.startswith("."))
    muzyka = next((x for x in pliki if x.suffix.lower() in AUD), None)
    media = [x for x in pliki if x.suffix.lower() in IMG | VID]
    if not media:
        sys.exit(f"Brak zdjęć/klipów w {a.wejscie}")

    w, h = FORMATY[a.format]
    a.wyjscie.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segmenty = []
        for i, src in enumerate(media):
            dst = Path(tmp) / f"{i:03d}.mp4"
            print(f"[{i+1}/{len(media)}] {src.name}")
            if src.suffix.lower() in IMG:
                segment_zdjecie(src, dst, w, h, a.zdjecie, i)
            else:
                segment_klip(src, dst, w, h, a.klip_maks)
            segmenty.append(dst)
        print("Sklejanie" + (f" z muzyką {muzyka.name}" if muzyka else "") + "...")
        total = sklej(segmenty, a.wyjscie, a.przejscie, muzyka, a.glosnosc_klipow)
    print(f"Gotowe: {a.wyjscie} ({total:.1f} s, {w}x{h})")


if __name__ == "__main__":
    main()
