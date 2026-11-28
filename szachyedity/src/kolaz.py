# kolaz.py - narzedzia do kinowych editow-kolazy (jak wzory 9 i 10): zdjecie czarno-biale z ziarnem,
# powolny najazd kamery (Ken Burns), wycinanka postaci z bialym obrysem (OpenCV GrabCut), zegar z cyframi rzymskimi.
# Zdjecia: najlepiej z wolnymi licencjami (Wikimedia Commons, CC BY-SA); inne (np. prasowe) na odpowiedzialnosc autora filmu.
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

def bw(img, lo=2, hi=98, gamma=1.0, warm=0.0):
    """Zdjecie -> czarno-biale RGB z rozciagnietym kontrastem (percentyle lo/hi) i lekkim tonem."""
    g = np.asarray(img.convert('L')).astype(float)
    a, b = np.percentile(g, lo), np.percentile(g, hi)
    g = np.clip((g - a) / max(b - a, 1), 0, 1) ** gamma
    rgb = np.dstack([g, g, g]) * 255
    if warm: rgb = rgb * (1 + np.array([warm, warm * .4, -warm]))
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))

def cover(img, W, H, cx, cy, z, rot=0.0):
    """Wycinek zdjecia wypelniajacy klatke WxH: srodek (cx, cy) w ulamkach zdjecia, zoom z >= 1, obrot w stopniach."""
    s = max(W / img.width, H / img.height) * z           # skala pokrycia * zoom
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    px, py = cx * img.width, cy * img.height
    a, b, d, e = c / s, sn / s, -sn / s, c / s
    data = (a, b, px - a * W / 2 - b * H / 2, d, e, py - d * W / 2 - e * H / 2)
    return img.convert('RGBA').transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 255))

def sticker(img, rect, outline=14, iters=6):
    """Wycinanka: GrabCut w prostokacie rect=(x0,y0,x1,y1) -> RGBA z bialym obrysem i miekkim cieniem."""
    import cv2
    a = np.asarray(img.convert('RGB'))[:, :, ::-1].copy()
    mask = np.zeros(a.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    x0, y0, x1, y1 = rect
    cv2.grabCut(a, mask, (x0, y0, x1 - x0, y1 - y0), bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))   # przecina cienkie mostki do logo w tle
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)          # tylko najwieksza czesc (postac)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); m = np.where(lab == k, 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    from scipy import ndimage
    m = (ndimage.binary_fill_holes(m > 0) * 255).astype(np.uint8)   # bez dziur w twarzy
    m = cv2.GaussianBlur(m, (5, 5), 0)
    body = Image.fromarray(m)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outline * 2 + 1, outline * 2 + 1))
    ring_a = cv2.dilate(m, ker)                                   # bialy obrys (szybko, w OpenCV)
    ring = Image.fromarray(ring_a)
    sh = Image.fromarray(cv2.GaussianBlur(ring_a, (0, 0), outline))
    out.paste((0, 0, 0, 150), (0, 0), sh.point(lambda v: int(v * .6)))
    out.paste((255, 255, 255, 255), (0, 0), ring)
    rgba = img.convert('RGBA'); rgba.putalpha(body)
    out.alpha_composite(rgba)
    bb = out.getbbox(); res = out.crop(bb); res.info['bbox'] = bb
    return res

def clock_face(size, t_spin=0.0, font_file=None):
    """Zegar z cyframi rzymskimi (bialo-czarny jak we wzorze); wskazowki krecia sie w czasie t_spin [obroty]."""
    S = size * 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    for r, w, col in ((c - 4, 26, (235, 235, 230, 255)), (c - 40, 6, (30, 30, 30, 255)), (c * .62, 4, (30, 30, 30, 255))):
        d.ellipse((c - r, c - r, c + r, c + r), outline=col, width=w)
    d.ellipse((c - c + 30, c - c + 30, c + c - 30, c + c - 30), fill=(245, 244, 238, 235))
    f = ImageFont.truetype(font_file, int(S * .085)) if font_file else ImageFont.load_default()
    for i, txt in enumerate(['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']):
        ang = math.radians(i * 30 - 90)
        x, y = c + math.cos(ang) * c * .78, c + math.sin(ang) * c * .78
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=(25, 25, 25, 255))
    for i in range(60):
        ang = math.radians(i * 6); r0 = c * (.9 if i % 5 else .86)
        d.line((c + math.cos(ang) * r0, c + math.sin(ang) * r0, c + math.cos(ang) * c * .93, c + math.sin(ang) * c * .93),
               fill=(25, 25, 25, 255), width=3 if i % 5 else 6)
    for frac, ln, w in ((t_spin / 12, .45, 16), (t_spin, .7, 10)):
        ang = math.radians(frac * 360 - 90)
        d.line((c, c, c + math.cos(ang) * c * ln, c + math.sin(ang) * c * ln), fill=(20, 20, 20, 255), width=w)
    d.ellipse((c - 18, c - 18, c + 18, c + 18), fill=(20, 20, 20, 255))
    return im.resize((size, size), Image.LANCZOS)

def card(img, width, border=18, col=(245, 244, 238, 255), rot=0.0):
    """Zdjecie jako odbitka z ramka (biala albo zlota) i cieniem; male zdjecia nie musza zajmowac calego ekranu."""
    h = int(width * img.height / img.width)
    ph = img.convert('RGBA').resize((width, h), Image.LANCZOS)
    c = Image.new('RGBA', (width + 2 * border, h + 2 * border), col)
    c.alpha_composite(ph, (border, border))
    sh = Image.new('RGBA', (c.width + 60, c.height + 60), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 170), (30, 38, 30 + c.width, 38 + c.height))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    sh.alpha_composite(c, (30, 30))
    return sh.rotate(rot, resample=Image.BICUBIC, expand=True)

def sticker_hints(img, fg, bg, outline=14, iters=8):
    """Wycinanka GrabCut z podpowiedziami (gdy sama ramka nie wystarcza, np. zdjecia czarno-biale).
    fg / bg: listy ksztaltow w ulamkach zdjecia: ('e', cx, cy, rx, ry) elipsa, ('r', x0, y0, x1, y1) prostokat
    albo ('p', [(x, y), ...]) wielokat.
    fg = na pewno postac, bg = na pewno tlo; reszta = 'raczej tlo'."""
    import cv2
    from scipy import ndimage
    a = np.asarray(img.convert('RGB'))[:, :, ::-1].copy()
    h, w = a.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    def draw(shapes, val):
        m = Image.new('L', (w, h), 0); d = ImageDraw.Draw(m)
        for s in shapes:
            if s[0] == 'e':
                _, cx, cy, rx, ry = s; d.ellipse(((cx - rx) * w, (cy - ry) * h, (cx + rx) * w, (cy + ry) * h), fill=255)
            elif s[0] == 'p':                                   # wielokat: ('p', [(x, y), ...])
                d.polygon([(x * w, y * h) for x, y in s[1]], fill=255)
            else:
                _, x0, y0, x1, y1 = s; d.rectangle((x0 * w, y0 * h, x1 * w, y1 * h), fill=255)
        mask[np.asarray(m) > 0] = val
    draw(bg, cv2.GC_BGD); draw(fg, cv2.GC_FGD)
    bgm, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(a, mask, None, bgm, fgm, iters, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); m = np.where(lab == k, 255, 0).astype(np.uint8)
    m = (ndimage.binary_fill_holes(m > 0) * 255).astype(np.uint8)
    m = cv2.GaussianBlur(m, (5, 5), 0)
    return _outline(img, m, outline)

def oval_head(img, cx, cy, rx, ry, outline=14):
    """Glowa wycieta owalem (jak "duza glowa" w memach), gdy GrabCut nie daje rady."""
    w, h = img.size
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).ellipse(((cx - rx) * w, (cy - ry) * h, (cx + rx) * w, (cy + ry) * h), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(2))
    return _outline(img, np.asarray(m), outline)

def _outline(img, m, outline):
    import cv2
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (outline * 2 + 1, outline * 2 + 1))
    ring_a = cv2.dilate(m, ker)
    out.paste((0, 0, 0, 150), (0, 0), Image.fromarray(cv2.GaussianBlur(ring_a, (0, 0), outline)).point(lambda v: int(v * .6)))
    out.paste((255, 255, 255, 255), (0, 0), Image.fromarray(ring_a))
    rgba = img.convert('RGBA'); rgba.putalpha(Image.fromarray(m))
    out.alpha_composite(rgba)
    bb = out.getbbox(); res = out.crop(bb); res.info['bbox'] = bb
    return res

def sticker_ai(img, model='u2net_human_seg', outline=14, crop=None, cut=()):
    """Wycinanka postaci modelem rembg (u2net_human_seg): wlosy, rece i tlo z balaganem wychodza dobrze.
    crop = (x0, y0, x1, y1) w ulamkach, gdy na zdjeciu jest kilka osob; cut = prostokaty (ulamki) do usuniecia
    (np. czyjas glowa w tle przyklejona do postaci). Model pobiera sie raz (~170 MB)."""
    import cv2
    from rembg import remove, new_session
    from scipy import ndimage
    if crop:
        x0, y0, x1, y1 = crop
        img = img.crop((int(img.width * x0), int(img.height * y0), int(img.width * x1), int(img.height * y1)))
    a = np.asarray(remove(img.convert('RGB'), session=new_session(model)).getchannel('A'))
    m = (a > 128).astype(np.uint8)
    for x0, y0, x1, y1 in cut:
        m[int(y0 * m.shape[0]):int(y1 * m.shape[0]), int(x0 * m.shape[1]):int(x1 * m.shape[1])] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)          # tylko najwieksza czesc (bez plam z tla)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); m = (lab == k).astype(np.uint8)
    m = ndimage.binary_fill_holes(m).astype(np.uint8)
    soft = np.where(m > 0, np.maximum(a, 200), 0).astype(np.uint8)  # miekka krawedz z modelu, srodek pelny
    return _outline(img, cv2.GaussianBlur(soft, (3, 3), 0), outline)
