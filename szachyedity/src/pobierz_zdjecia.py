# pobierz_zdjecia.py - pobiera zdjecia do editow-kolazy (src/edit_magnus.py, src/edit_fischer.py) do wejscie/zdjecia/.
# Zrodla: artykuly Chess.com i ChessBase (mecz o MS 2016 Carlsen - Karjakin; Fischer, Reykjavik 1972). To zdjecia prasowe z prawami autorskimi
# Chess.com (nie wolna licencja): nie trafiaja do repo, w filmie jest podpis "Photos: Chess.com", a za publikacje
# odpowiada autor filmu. Uzycie: python3 src/pobierz_zdjecia.py
import os, subprocess, time

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wejscie', 'zdjecia')
U = 'https://images.chesscomfiles.com/uploads/v1/'
ZDJECIA = {  # plik -> adres (artykul: chess.com/article/view/carlsen-karjakin-world-chess-championship-2016
             #                i chess.com/news/view/world-championship-playoff-live-update-4653)
    'magnus_ruch.jpg': U + 'images_users/tiny_mce/davidkaufmann/phpe8LlDI.jpeg',
    'magnus_portret.jpg': U + 'images_users/tiny_mce/davidkaufmann/phpN9XYJs.jpeg',
    'magnus_reka.jpg': U + 'images_users/tiny_mce/davidkaufmann/php3JYa5G.jpeg',
    'magnus_mysli.jpg': U + 'images_users/tiny_mce/davidkaufmann/phpfI8lUH.jpeg',
    'magnus_wdol.jpg': U + 'images_users/tiny_mce/davidkaufmann/phpumTPOO.jpeg',
    'oboje.jpg': U + 'news/365002.ea82d914.5000x5000o.dbeca1169d91.jpeg',
    'magnus_usmiech.jpg': U + 'images_users/tiny_mce/PeterDoggers/phpUFOw6M.jpeg',
    'puchar.jpg': U + 'images_users/tiny_mce/pete/phpJdpW2T.jpeg',
    # Fischer (chess.com/players/bobby-fischer, chess.com/article/view/50-year-anniversary-fischer-spassky-game-6,
    #          en.chessbase.com/post/50-years-ago-today-fischer-spassky-game-six)
    'fischer_rece.jpg': U + 'images_users/tiny_mce/NiiLoC/phpByWveT.jpeg',
    'fischer_tal_usa.jpg': U + 'images_users/tiny_mce/NiiLoC/phpk0ppHF.jpeg',
    'fischer_usmiech.jpg': U + 'images_users/tiny_mce/davidkaufmann/phphbOfs1.jpeg',
    'fischer_uscisk.jpg': U + 'images_users/tiny_mce/AnthonyLevin/php7UN4FE.jpeg',
    'fischer_autografy.jpg': U + 'images_users/tiny_mce/AnthonyLevin/phpm01TNB.jpeg',
    'fischer_spasski.jpg': 'https://en.chessbase.com/Portals/All/2017/_eng/ff/reykjavik51-fischer-spassky.jpg',
}

if __name__ == '__main__':
    os.makedirs(DIR, exist_ok=True)
    for name, url in ZDJECIA.items():
        out = os.path.join(DIR, name)
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            continue
        for k in range(4):
            r = subprocess.run(['curl', '-sS', '-m', '60', '-A', 'Mozilla/5.0', '-o', out, '-w', '%{http_code}', url],
                               capture_output=True, text=True)
            if r.stdout == '200': print('OK', name); break
            print('HTTP', r.stdout, name, '- ponawiam'); time.sleep(10 * (k + 1))
        time.sleep(1)
    print('Gotowe:', DIR)
