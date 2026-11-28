# pobierz_zdjecia.py - pobiera zdjecia do editu o Magnusie z Wikimedia Commons do wejscie/zdjecia/.
# Wszystkie na licencji CC BY-SA: w opisie filmu trzeba podac autora, licencje i ze zdjecia sa przerobione.
# Pobiera powoli i ponawia po bledzie 429 (Wikimedia ogranicza liczbe zapytan). Uzycie: python3 src/pobierz_zdjecia.py
import os, subprocess, sys, time

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wejscie', 'zdjecia')
UA = 'szachyedity-video-tool/1.0 (personal, low-volume)'
C = 'https://upload.wikimedia.org/wikipedia/commons/'
ZDJECIA = [  # plik, adres, autor, licencja
    ('World_Chess_Championship_2016_tie-break_-_4.jpg', C + '4/48/World_Chess_Championship_2016_tie-break_-_4.jpg', 'Vladimir Barskij', 'CC BY-SA 3.0'),
    ('World_Chess_Championship_2016_tie-break_-_6.jpg', C + 'f/fb/World_Chess_Championship_2016_tie-break_-_6.jpg', 'Vladimir Barskij', 'CC BY-SA 3.0'),
    ('World_Chess_Championship_2016_tie-break_-_9.jpg', C + 'c/c7/World_Chess_Championship_2016_tie-break_-_9.jpg', 'Vladimir Barskij', 'CC BY-SA 3.0'),
    ('World_Chess_Championship_2016_tie-break_-_33.jpg', C + 'f/f1/World_Chess_Championship_2016_tie-break_-_33.jpg', 'Vladimir Barskij', 'CC BY-SA 3.0'),
    ('Carlsen_Magnus_BW_(30352212740).jpg', C + 'thumb/e/ee/Carlsen_Magnus_BW_%2830352212740%29.jpg/1280px-Carlsen_Magnus_BW_%2830352212740%29.jpg', 'Andreas Kontokanis', 'CC BY-SA 2.0'),
    ('Carlsen_Magnus_with_hood_(30251235731).jpg', C + 'thumb/1/13/Carlsen_Magnus_with_hood_%2830251235731%29.jpg/1280px-Carlsen_Magnus_with_hood_%2830251235731%29.jpg', 'Andreas Kontokanis', 'CC BY-SA 2.0'),
]

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    for name, url, autor, lic in ZDJECIA:
        out = os.path.join(DIR, name)
        if os.path.exists(out) and os.path.getsize(out) > 20000:
            continue
        wait = 45
        while True:
            r = subprocess.run(['curl', '-sS', '-m', '90', '-A', UA, '-o', out, '-w', '%{http_code}', url], capture_output=True, text=True)
            if r.stdout == '200':
                print('OK', name, '|', autor, '|', lic); break
            print('HTTP', r.stdout, name, f'- ponawiam za {wait} s', flush=True)
            time.sleep(wait); wait = min(wait * 1.6, 400)
        time.sleep(20)
    print('Gotowe:', DIR)
