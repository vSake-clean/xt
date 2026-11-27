#!/usr/bin/env bash
# Buduje wszystkie filmy do katalogu build/.
# Wymaga plikow w wejscie/ (opis w README.md): plansza.jpg (jest w repo) + filmiki z TikToka (nie ma ich w repo).
# Uzycie:  ./buduj.sh            - wszystkie filmy
#          ./buduj.sh zduszony   - tylko jeden (nazwy: final alien2 glupca speedrun szewczyk edit kopia wieza zduszony carokann)
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(pwd)
IN=$ROOT/wejscie
SRC=$ROOT/src
export PLANSZA=$IN/plansza.jpg
mkdir -p build && cd build

need() { for f in "$@"; do [ -f "$IN/$f" ] || { echo "Brak pliku wejscie/$f (patrz README.md)"; exit 1; }; done; }
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
want() { [ $# -eq 0 ] || [ -z "${ONLY:-}" ] || [ "$ONLY" = "$1" ]; }
ONLY=${1:-}

# 1. Pierwsza partia (1. e4 b6 ... 5. Qxf7#), mat w 12,07 s, od 12,1 s klip z alienem na b3-d5, muzyka wzoru 1 (18,7 s)
if want final; then
  need alien.mp4 wzor1.mp4
  TOTAL_FRAMES=561 python3 "$SRC/pierwsza_partia.py" "$PLANSZA" baza_final.mp4
  ffmpeg -loglevel error -y -i baza_final.mp4 -i "$IN/alien.mp4" -i "$IN/wzor1.mp4" -filter_complex \
    "[1:v]scale=414:414:flags=lanczos,setpts=PTS-STARTPTS+12.1/TB[ov];[0:v][ov]overlay=133:394:eof_action=pass,format=yuv420p[v]" \
    -map "[v]" -map 2:a -c:v libx264 -preset slow -crf 17 -r 30 -c:a aac -b:a 192k -movflags +faststart szachy_final.mp4
fi

# 2. Mat szewski na szybko, klip z alienem po prawej (f3-h5), muzyka wzoru 1 od 7,73 s (11 s)
if want alien2; then
  need alien.mp4 wzor1.mp4
  TOTAL_FRAMES=330 python3 "$SRC/mat_szewski_alien.py" "$PLANSZA" baza_alien2.mp4
  ffmpeg -loglevel error -y -i baza_alien2.mp4 -i "$IN/alien.mp4" -ss 7.733333 -i "$IN/wzor1.mp4" -filter_complex \
    "[1:v]scale=405:405:flags=lanczos,setpts=PTS-STARTPTS+4.366667/TB[ov];[0:v][ov]overlay=675:405:eof_action=pass,format=yuv420p[v];[2:a]asetpts=PTS-STARTPTS,afade=t=out:st=10.6:d=0.4[a]" \
    -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 17 -r 30 -c:a aac -b:a 192k -t 11.0 -movflags +faststart szachy_alien2.mp4
fi

# 3. Mat glupca 1. f3 e5 2. g4?? Qh4# ze znaczkiem ?? i zwolnionym matem (7,5 s)
if want glupca; then
  need wzor1.mp4
  python3 "$SRC/mat_glupca_zwolnienie.py" "$PLANSZA" baza_glupca.mp4
  D=$(dur baza_glupca.mp4); ST=$(python3 -c "print($D-0.6)")
  ffmpeg -loglevel error -y -i baza_glupca.mp4 -i "$IN/wzor1.mp4" -filter_complex "[1:a]atrim=0:$D,afade=t=out:st=$ST:d=0.6[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart szachy_mat_glupca.mp4
fi

# 4. Speedrun: 1. e4 g5 2. d4 f6?? 3. Qh5#, stoper, czerwone pole, przyciemnienie, odznaki (13,6 s)
if want speedrun; then
  need wzor3_speedrun.mp4
  python3 "$SRC/speedrun_stoper.py" "$PLANSZA" baza_speedrun.mp4 407
  ffmpeg -loglevel error -y -i baza_speedrun.mp4 -i "$IN/wzor3_speedrun.mp4" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
    -movflags +faststart szachy_bialy_wygrywa_v2.mp4
fi

# 5. Szewczyk: 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6?? 4. Qxf7#, mat w 5,13 s (12,9 s)
if want szewczyk; then
  need wzor4_szewczyk.mp4
  python3 "$SRC/mat_szewski.py" "$PLANSZA" baza_szewczyk.mp4 387
  ffmpeg -loglevel error -y -i baza_szewczyk.mp4 -i "$IN/wzor4_szewczyk.mp4" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
    -movflags +faststart szachy_szewczyk.mp4
fi

# 6. Edit kinowy (krotka wersja): fragment muzyki 6,0-20,6 s, drop na macie (14,6 s)
if want edit; then
  need wzor5_edit.mp4
  python3 "$SRC/edit_kinowy.py" baza_edit.mp4
  ffmpeg -loglevel error -y -i baza_edit.mp4 -ss 6.0 -t 14.6 -i "$IN/wzor5_edit.mp4" -filter_complex \
    "[1:a]asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.15,afade=t=out:st=13.7:d=0.9[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart szachy_edit_krotki.mp4
fi

# 7. Doslowna kopia wzoru 6 (Caro-Kann, 7. Nxf7?), pionowo 1080x2322 (15,3 s)
if want kopia; then
  need alien.mp4 wzor6_kopia.mp4
  python3 "$SRC/kopia_caro_kann.py" "$IN/alien.mp4" "$IN/wzor6_kopia.mp4" szachy_kopia.mp4
fi

# 8. Pogon wieza: wieza szachuje krola dookola planszy, zbicie = pat, mem polprzezroczysty (17,5 s)
if want wieza; then
  need alien.mp4 wzor7_wieza.mp4
  python3 "$SRC/pogon_wieza.py" "$IN/alien.mp4" "$IN/wzor7_wieza.mp4" szachy_wieza.mp4
fi

# 9. Mat zduszony Philidora: 14. Qg8+!! Rxg8 15. Nf7#, zoom, klip z alienem po macie (18,7 s)
if want zduszony; then
  need alien.mp4 wzor1.mp4
  python3 "$ROOT/mat_zduszony.py" "$PLANSZA" "$IN/alien.mp4" "$IN/wzor1.mp4" szachy_mat_zduszony.mp4
fi

# 10. Speedrun Caro-Kann: 5...Ngf6?? 6. Nd6#, stoper nad plansza, muzyka wzoru 1 od 6,47 s, mat na dropie (12,2 s)
if want carokann; then
  need alien.mp4 wzor1.mp4
  python3 "$SRC/speedrun_caro_kann.py" "$PLANSZA" "$IN/alien.mp4" "$IN/wzor1.mp4" szachy_caro_kann_speedrun.mp4
fi

rm -f baza_*.mp4
echo "Gotowe. Filmy sa w: $ROOT/build"
ls -la "$ROOT/build"/*.mp4
