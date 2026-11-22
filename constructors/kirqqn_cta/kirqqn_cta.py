"""kirQQn — генератор CTA для коротких відео (погоджено автором 2026-11-22).

Робить прозорі оверлеї ProRes 4444 1080×1920 60 к/с і PNG кінцевого стану
для двох макетів кадру (reaction, guide) і двох мов (en, ua).
Правила: guidelines/ГАЙДЛАЙН_CTA_КОРОТКИХ.md. Тексти й розміри не змінювати без рішення автора.

Запуск з кореня репозиторію:
    python constructors/kirqqn_cta/kirqqn_cta.py [--ffmpeg PATH] [--out resolve_pack/cta_shorts] [--seconds 6]
Потрібні Pillow (з підтримкою variable fonts) і ffmpeg з prores_ks.
"""
import argparse, os, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(ROOT, "assets", "fonts")

VOID = (7, 7, 11)
INK = (244, 244, 246)
W, H = 1080, 1920
FPS = 60
SAFE_L, SAFE_R = 96, 900          # безпечна зона тексту
TOP = 160                          # верх бейджа в усіх макетах
HEAD_SIZE = 56                     # Unbounded Black, px

# Слова погодженого CTA; рядки ламаються за змістом
TEXTS = {
    "en": ("FOLLOW", ["TO SEE WHO", "BREAKS FIRST:", "ME OR THE GAME."]),
    "ua": ("ПІДПИСУЙСЯ:", ["ПОДИВИМОСЬ,", "ХТО КОГО ЗЛАМАЄ."]),
}
# нижня межа панелі = верхній край геймплею в макеті
LAYOUTS = {
    "reaction": 612,   # шаблон віральних: гачок зверху, гра смугою
    "guide": 452,      # конструктор kirqqn_guide: гайди й Tips & Tricks
}


def font(name, size, wght):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_axes([wght])
    return f


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def frame(lang, zone_bottom, t):
    """RGBA-кадр оверлею; t — секунди від початку появи."""
    badge_txt, lines = TEXTS[lang]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = t * FPS
    # 1) панель Void: кадри 0–10, нижні 24 px — м'який край
    pa = ease_out(f / 10)
    d.rectangle((0, 0, W, zone_bottom - 24), fill=VOID + (int(255 * pa),))
    for i in range(24):
        d.line((0, zone_bottom - 24 + i, W, zone_bottom - 24 + i), fill=VOID + (int(255 * pa * (1 - i / 24)),))
    # 2) бейдж Ink, JetBrains Mono 700 34 px: кадри 4–14, виїзд зліва 24 px
    fb = font("JetBrainsMono/JetBrainsMono[wght].ttf", 34, 700)
    ba = ease_out((f - 4) / 10)
    if ba > 0:
        bx = SAFE_L - int(24 * (1 - ba))
        bw = int(fb.getlength(badge_txt)) + 36
        d.rectangle((bx, TOP, bx + bw, TOP + 52), fill=INK + (int(255 * ba),))
        d.text((bx + 18, TOP + 26), badge_txt, font=fb, fill=VOID + (int(255 * ba),), anchor="lm")
    # 3) заголовок Unbounded Black 900 56 px Ink: рядки з 8-го кадру, крок 3 кадри, підйом 18 px
    fh = font("Unbounded/Unbounded[wght].ttf", HEAD_SIZE, 900)
    assert max(fh.getlength(l) for l in lines) <= SAFE_R - SAFE_L, "рядок ширший за безпечну зону"
    lead = int(HEAD_SIZE * 1.08)
    y0 = TOP + 52 + 26
    for i, line in enumerate(lines):
        la = ease_out((f - 8 - 3 * i) / 12)
        if la > 0:
            d.text((SAFE_L, y0 + i * lead + int(18 * (1 - la))), line, font=fh, fill=INK + (int(255 * la),))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--out", default=os.path.join(ROOT, "resolve_pack", "cta_shorts"))
    ap.add_argument("--seconds", type=float, default=6)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    total = int(a.seconds * FPS)
    for layout, zone in LAYOUTS.items():
        for lang in TEXTS:
            name = f"kirqqn_cta_{layout}_{lang}"
            tmp = tempfile.mkdtemp()
            last = None
            for k in range(total):
                if k <= 30:                      # після 30-го кадру все нерухоме
                    last = frame(lang, zone, k / FPS)
                last.save(os.path.join(tmp, f"{k:04d}.png"))
            last.save(os.path.join(a.out, name + ".png"))
            subprocess.run([a.ffmpeg, "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%04d.png"),
                            "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                            "-alpha_bits", "16", "-vendor", "apl0", os.path.join(a.out, name + ".mov")], check=True)
            shutil.rmtree(tmp)
            print(name)


if __name__ == "__main__":
    main()
