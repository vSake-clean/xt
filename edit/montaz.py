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
PRZEJSCIA = ["fade", "slideleft", "circleopen", "smoothup", "zoomin", "wiperight",
             "dissolve", "slideup", "radial", "smoothleft", "pixelize", "circleclose"]
# szybkie, "rwane" przejścia do energicznych editów
ENERGIA = ["slideleft", "zoomin", "slideup", "hblur", "slideright", "circleopen",
           "slidedown", "squeezeh", "wipeleft", "radial", "squeezev", "smoothright"]


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


def segment_zdjecie(src, dst, w, h, czas, idx, tlo, zoom=0.15, tryb="plynny"):
    klatki = int(round(czas * FPS)) + 1
    krok = zoom / klatki  # zoom zawsze o tyle samo, niezależnie od długości ujęcia
    # skaluj z zapasem, potem zoompan (naprzemiennie zoom in / zoom out)
    if tryb == "punch":
        # uderzenie: start mocno przybliżony, szybki odjazd do pełnego kadru
        z = f"1+{zoom}*pow(max(0,1-on/{max(klatki * 0.6, 1):.1f}),2)"
    elif idx % 2 == 0:
        z = f"min(zoom+{krok:.5f},{1+zoom})"
    else:
        z = f"if(eq(on,0),{1+zoom},max(zoom-{krok:.5f},1.0))"
    if tlo == "rozmyte":
        # całe zdjęcie na środku, w tle jego rozmyta i przyciemniona kopia
        baza = (f"split[a][b];[a]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
                f"crop={w*2}:{h*2},boxblur=40:4,eq=brightness=-0.12[bg];"
                f"[b]scale={w*2}:{h*2}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,")
    else:
        baza = f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
    vf = (baza +
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={klatki}:s={w}x{h}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"[0:v]{vf}[v]", "-t", f"{czas}", "-map", "[v]", "-map", "1:a",
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


def efekty_ciec(ciecia, w, h, jakie):
    """Filtry wideo odpalane na każdym cięciu: błysk, trzęsienie, przesunięcie RGB."""
    def okno(d, zanik=True):
        if zanik:
            return "+".join(f"between(t,{c:.3f},{c + d:.3f})*(1-(t-{c:.3f})/{d})" for c in ciecia)
        return "+".join(f"between(t,{c:.3f},{c + d:.3f})" for c in ciecia)
    fl = []
    if "shake" in jakie:
        A = int(w * 0.03)
        env = okno(0.22)
        fl.append(f"scale={int(w * 1.08) // 2 * 2}:{int(h * 1.08) // 2 * 2},"
                  f"crop={w}:{h}:x='(iw-ow)/2+{A}*({env})*sin(t*91)':y='(ih-oh)/2+{A}*({env})*cos(t*67)'")
    if "rgb" in jakie:
        fl.append(f"rgbashift=rh=-{w // 60}:bh={w // 60}:enable='{okno(0.07, False)}'")
    if "flash" in jakie:
        fl.append(f"eq=brightness='0.6*({okno(0.08)})':eval=frame")
    if "kolor" in jakie:
        fl.append("eq=contrast=1.08:saturation=1.3")
    return fl


def sklej(segmenty, dst, przejscie, muzyka, glosnosc_klipow, rodzaj, muzyka_od=0.0, efekty=(), wh=(1080, 1920)):
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
        ciecia = []
        for i in range(1, n):
            off += dl[i - 1] - T
            ciecia.append(off + T / 2)
            lista = {"mix": PRZEJSCIA, "energia": ENERGIA}.get(rodzaj)
            tr = lista[(i - 1) % len(lista)] if lista else rodzaj
            f.append(f"{v}[{i}:v]xfade=transition={tr}:duration={T}:offset={off:.3f}[v{i}]")
            f.append(f"{a}[{i}:a]acrossfade=d={T}[a{i}]")
            v, a = f"[v{i}]", f"[a{i}]"
        fx = efekty_ciec(ciecia, *wh, efekty) if efekty else []
        f.append(f"{v}{','.join(fx) or 'null'}[v];{a}anull[a]")
        total = sum(dl) - T * (n - 1)
    dz = min(1.0, total * 0.06)  # wyciemnienie na końcu, krótsze przy krótkich filmach
    fo = max(total - dz, 0)
    f.append(f"[v]fade=t=in:d={min(0.5, dz / 2):.3f},fade=t=out:st={fo:.3f}:d={dz:.3f}[vo]")
    if muzyka:
        cmd += ["-stream_loop", "-1", "-ss", f"{muzyka_od:.3f}", "-i", str(muzyka)]
        f.append(f"[a]volume={glosnosc_klipow}[ak];"
                 f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f}[m];"
                 f"[ak][m]amix=inputs=2:duration=first:normalize=0[mx];"
                 f"[mx]afade=t=out:st={fo:.3f}:d={dz:.3f}[ao]")
    else:
        f.append(f"[a]afade=t=out:st={fo:.3f}:d={dz:.3f}[ao]")
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
    p.add_argument("--tlo", choices=["przyciete", "rozmyte"], default="przyciete",
                   help="zdjęcia: przyciete = wypełnij kadr, rozmyte = całe zdjęcie na rozmytym tle")
    p.add_argument("--przejscia", default="fade",
                   help="rodzaj przejścia ffmpeg xfade, 'mix' (różne po kolei) albo 'energia' (szybkie, rwane)")
    p.add_argument("--efekty", default="",
                   help="efekty na cięciach, po przecinku: flash, shake, rgb, kolor (albo 'wszystkie')")
    p.add_argument("--zoom-tryb", choices=["plynny", "punch"], default="plynny",
                   help="plynny = powolny zoom, punch = mocne uderzenie zoomem na starcie ujęcia")
    p.add_argument("--fps", type=int, default=30, help="klatki na sekundę (60 = płynniej przy szybkich editach)")
    p.add_argument("--bpm", type=float, default=0,
                   help="tempo muzyki: zdjęcia zmieniają się co --takty uderzeń (nadpisuje --zdjecie)")
    p.add_argument("--takty", type=float, default=4, help="co ile uderzeń zmiana zdjęcia (z --bpm)")
    p.add_argument("--final", type=float, default=0,
                   help="ostatnie zdjęcie trwa tyle uderzeń (z --bpm) albo sekund (bez --bpm); 0 = jak inne")
    p.add_argument("--beat", type=float, default=None,
                   help="moment (s) jakiegoś uderzenia w utworze: muzyka startuje tak, by cięcia trafiały w rytm")
    p.add_argument("--muzyka-od", type=float, default=0, help="od której sekundy utworu zacząć (bez --beat)")
    p.add_argument("--zoom", type=float, default=0.15, help="siła zoomu na zdjęciach (0 = bez)")
    p.add_argument("--glosnosc-klipow", type=float, default=0.3, help="głośność dźwięku z klipów, gdy jest muzyka")
    a = p.parse_args()
    global FPS
    FPS = a.fps
    efekty = {"flash", "shake", "rgb", "kolor"} if a.efekty == "wszystkie" else \
        {e.strip() for e in a.efekty.split(",") if e.strip()}

    if not shutil.which("ffmpeg"):
        sys.exit("Brak ffmpeg w systemie.")
    pliki = sorted(x for x in a.wejscie.iterdir() if x.is_file() and not x.name.startswith("."))
    muzyka = next((x for x in pliki if x.suffix.lower() in AUD), None)
    media = [x for x in pliki if x.suffix.lower() in IMG | VID]
    if not media:
        sys.exit(f"Brak zdjęć/klipów w {a.wejscie}")

    w, h = FORMATY[a.format]
    if a.bpm:
        # cięcie co N uderzeń: długość ujęcia = N * beat + przejście
        beat = 60 / a.bpm
        a.zdjecie = round(a.takty * beat + a.przejscie, 3)
        if a.final:
            a.final = round(a.final * beat + a.przejscie, 3)
        if a.beat is not None:
            # środek przejścia ma wypaść na uderzeniu
            od = a.beat - a.przejscie / 2
            while od < 0:
                od += beat
            a.muzyka_od = od
        print(f"Tempo {a.bpm} BPM -> zdjęcie {a.zdjecie} s, muzyka od {a.muzyka_od:.3f} s")
    a.wyjscie.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        segmenty = []
        for i, src in enumerate(media):
            dst = Path(tmp) / f"{i:03d}.mp4"
            print(f"[{i+1}/{len(media)}] {src.name}")
            if src.suffix.lower() in IMG:
                czas = a.final if (a.final and i == len(media) - 1) else a.zdjecie
                segment_zdjecie(src, dst, w, h, czas, i, a.tlo, a.zoom, a.zoom_tryb)
            else:
                segment_klip(src, dst, w, h, a.klip_maks)
            segmenty.append(dst)
        print("Sklejanie" + (f" z muzyką {muzyka.name}" if muzyka else "") + "...")
        total = sklej(segmenty, a.wyjscie, a.przejscie, muzyka, a.glosnosc_klipow, a.przejscia, a.muzyka_od,
                      efekty, (w, h))
    print(f"Gotowe: {a.wyjscie} ({total:.1f} s, {w}x{h})")


if __name__ == "__main__":
    main()
