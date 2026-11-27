#!/usr/bin/env bash
# Instaluje wszystko, czego potrzebuja skrypty: numpy, pillow, scipy, python-chess i ffmpeg.
# Czcionki sa w fonty/, plansza w wejscie/plansza.jpg. Uzycie: ./ustaw.sh
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo "Instaluje ffmpeg..."
  if command -v apt-get >/dev/null; then
    (sudo apt-get install -y ffmpeg 2>/dev/null || apt-get install -y ffmpeg)
  elif command -v brew >/dev/null; then
    brew install ffmpeg
  else
    echo "Zainstaluj ffmpeg recznie (https://ffmpeg.org/download.html)"; exit 1
  fi
fi
python3 -m pip install numpy pillow scipy
# zwykla instalacja python-chess bywa zepsuta (blad przy budowaniu kola) - wtedy gotowe kolo
python3 -m pip install --only-binary=:all: chess || python3 -m pip install chess
python3 -c "import numpy, PIL, scipy, chess; print('OK: numpy, pillow, scipy, python-chess', chess.__version__)"
ffmpeg -version | head -1
echo "Gotowe. Teraz wrzuc filmiki z TikToka do wejscie/ (lista w README.md) i uruchom ./buduj.sh"
