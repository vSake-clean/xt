# Edit – montaż ze zdjęć i klipów

Folder roboczy do montażu: wrzucasz zdjęcia i klipy do `materialy/`, skrypt `montaz.py` składa z nich jeden film do `gotowe/`.

## Jak to działa

- Kolejność ujęć = kolejność nazw plików, więc nazywaj je `01_...`, `02_...`, `03_...`.
- **Zdjęcia** (jpg, png, webp, heic…): domyślnie 3 s, z powolnym zoomem (efekt Ken Burns).
- **Klipy** (mp4, mov, mkv, webm…): skalowane i przycinane do wspólnego kadru, bez czarnych pasów.
- Między ujęciami płynne przejście, a na początku i końcu wyciemnienie.
- **Muzyka**: plik audio (np. `muzyka.mp3`) w `materialy/` zostaje podkładem. Dźwięk z klipów jest wtedy ściszony.

## Użycie

Wymaga `python3` i `ffmpeg`.

```bash
python3 montaz.py                         # pion 9:16 (Reels/TikTok/Shorts) → gotowe/edit.mp4
python3 montaz.py --format poziom         # 16:9 (YouTube)
python3 montaz.py --format kwadrat        # 1:1
python3 montaz.py --zdjecie 2 --klip-maks 4 --przejscie 0.3
python3 montaz.py --wyjscie gotowe/wakacje.mp4
```

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `--format` | `pion` | `pion` 1080×1920, `poziom` 1920×1080, `kwadrat` 1080×1080 |
| `--zdjecie` | `3` | czas jednego zdjęcia (s) |
| `--klip-maks` | `0` | maks. długość klipu (s), `0` = cały klip |
| `--przejscie` | `0.5` | długość przejścia (s) |
| `--glosnosc-klipow` | `0.3` | głośność dźwięku z klipów, gdy jest muzyka |
| `--wejscie` / `--wyjscie` | `materialy/` / `gotowe/edit.mp4` | foldery |

## Struktura

```
edit/
├── montaz.py     # skrypt montażowy (ffmpeg)
├── materialy/    # tu wrzucasz zdjęcia, klipy i muzykę
└── gotowe/       # tu trafia gotowy film
```
