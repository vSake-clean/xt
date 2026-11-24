# Key Copier (Android)

Odczyt kodu klucza z ekranu telefonu (działanie jak Key Copier na Flipper Zero) i generowanie pasujących modeli 3D.

Gotowe APK: `KeyCopier.apk` (w tym folderze), Android 5.0+.

## Funkcje
- **Kalibracja ekranu** kartą płatniczą (85,60 × 53,98 mm). Klucz rysowany jest w skali 1:1.
- **Profile:** Europrofil 5/6/7 pin, Europrofil 6 pin dwustronny (ogólne, przybliżone), Kwikset KW1/KW10, Schlage SC1/SC4, Yale Y1, Master M1, własne profile. Profile można udostępniać i importować jako JSON.
- **Odczyt ręczny:** klucz kładziesz na ekranie, ramię przy czerwonej linii; głębokość ustawiasz ▲▼ albo przeciągając palcem. Przy dotyku pojawia się lupa.
- **Klucze dwustronne:** osobny kod dla górnej i dolnej krawędzi (⇵, kopiowanie góra→dół).
- **Zdjęcie klucza 📷:** zdjęcie pod obrysem, dopasowanie palcami (przesuń, powiększ, obróć), a potem ✨ Auto odczytuje nacięcia.
- **Eksport 📤:** model 3D (STL z podglądem 3D), PDF 1:1 do druku z linijką kontrolną, SVG (laser / ploter), tekst.
- **Model 3D:** główka z otworem na kółko, ostrze z nacięciami, rowki profilu (przybliżone, edytowalne w profilu: `F/B:wysokość:szerokość:głębokość`), grubość ostrza.

## Budowanie
- Debug: `./gradlew assembleDebug`
- Release (stały podpis): plik `signing.properties` (poza repo) z `storeFile`, `storePassword`, `keyAlias`, `keyPassword`, potem `./gradlew assembleRelease`.
