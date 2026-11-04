#!/usr/bin/env python3
"""
kirQQn — конструктор YouTube-превʼю (1280×720), версія для локального запуску.

Той самий макет, що й у веб-конструкторі kirQQn: усі розміри, відступи й позиції
зашиті в цьому файлі, тому кожне превʼю виходить однаковим. Змінюються тільки
скрін, текст, номер епізоду, емоція QQ, акцент і бік тексту.

Приклад:
  python kirqqn_thumb.py --image shot.png --line1 "БАКІР" --line2 "КІНЕЦЬ ГРИ" \
      --hl "КІНЕЦЬ" --badge "#13" --emotion win --out ep13.jpg

Пакетний режим (кілька превʼю за раз):
  python kirqqn_thumb.py --batch episodes.json

Потрібно: Python 3.8+, Pillow (pip install pillow). Більше нічого.
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720
K = W / 1280  # scale factor (kept for parity with the web version)

# ---- brand tokens (do not change) ----
VOID = (7, 7, 11)
INK = (244, 244, 246)
LIME = (198, 255, 26)
PINK = (255, 45, 111)
EMOTIONS = ["none", "cry", "look", "shock", "win", "rage", "dead", "sleep"]
FONT_DISPLAY = os.path.join(HERE, "fonts", "Unbounded-Black.ttf")
FONT_MONO = os.path.join(HERE, "fonts", "JetBrainsMono-Bold.ttf")
LAYOUT = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC

# ---- layout constants, copied from the web constructor (do not change) ----
PAD = 56 * K
HEAD_MAX_SIZE = 150 * K
HEAD_MAX_W = W * 0.64
LINE_H = 1.12
HL_PAD = 16 * K          # gap around the highlighted word
HL_BOX_X = 14 * K        # box overhang left/right
HL_TILT = -0.025         # radians
BADGE_FONT = 40 * K
BADGE_H = 62 * K
BADGE_PAD_X = 16 * K
LABEL_FONT = 24 * K
LABEL_GAP = 18 * K
STICKER_W = 290 * K
STICKER_RIGHT = 20 * K
STICKER_CY = H - 215 * K
STICKER_SRC_W = 1000.0   # mark width inside assets/qq_*.png; mark centre = image centre
MAX_BYTES = int(1.95 * 1024 * 1024)


def font(path, size):
    return ImageFont.truetype(path, max(1, int(round(size))), layout_engine=LAYOUT)


def cover(img, zoom=1.0, ox=0.0, oy=0.0):
    """Fill 1280×720 like CSS object-fit: cover, with optional zoom and offset (fractions of W/H)."""
    iw, ih = img.size
    s = max(W / iw, H / ih) * zoom
    nw, nh = max(1, round(iw * s)), max(1, round(ih * s))
    scaled = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), VOID)
    x = round((W - nw) / 2 + ox * W)
    y = round((H - nh) / 2 + oy * H)
    canvas.paste(scaled, (x, y))
    return canvas


def gradient_layers(right):
    """Side legibility gradient + bottom gradient, as one RGBA layer."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = layer.load()
    # side: stops 0 → .92, .55 → .55, 1 → 0 between x0 and x1
    x0, x1 = (W, W * 0.25) if right else (0, W * 0.75)
    side = []
    for x in range(W):
        t = (x + 0.5 - x0) / (x1 - x0)
        t = min(1, max(0, t))
        a = 0.92 + (0.55 - 0.92) * (t / 0.55) if t < 0.55 else 0.55 * (1 - (t - 0.55) / 0.45)
        side.append(a)
    for y in range(H):
        ty = (y + 0.5 - H * 0.6) / (H * 0.4)
        b = 0.7 * min(1, max(0, ty))
        for x in range(W):
            a1 = side[x]
            a = a1 + b * (1 - a1)  # two stacked layers of the same colour
            px[x, y] = (VOID[0], VOID[1], VOID[2], int(round(a * 255)))
    return layer


def text_w(f, s):
    return f.getlength(s) if s else 0.0


def draw_shadowed_text(base, xy, text, f, fill, blur, alpha):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(xy, text, font=f, fill=(0, 0, 0, int(255 * alpha)), anchor="ls")
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur / 2))
    base.alpha_composite(shadow)
    ImageDraw.Draw(base).text(xy, text, font=f, fill=fill, anchor="ls")


def rotated_rect(cx, cy, w, h, x_off, y_off, ang):
    pts = [(x_off, y_off), (x_off + w, y_off), (x_off + w, y_off + h), (x_off, y_off + h)]
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + px * c - py * s, cy + px * s + py * c) for px, py in pts]


def resolve_path(p, base=None):
    """Find a file given as absolute, relative to the current folder, the batch file or this script."""
    for cand in (p, os.path.join(base or "", p), os.path.join(HERE, p)):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit(f"Не знайдено файл скріна: {p}")


def render(o):
    """o: dict with image, line1, line2, hl, badge, label, emotion, accent, side, zoom, ox, oy."""
    if o.get("image"):
        src = Image.open(resolve_path(o["image"], o.get("_base"))).convert("RGB")
    else:
        src = Image.open(os.path.join(HERE, "examples", "example_screenshot.png")).convert("RGB")
    base = cover(src, float(o.get("zoom", 1)), float(o.get("ox", 0)), float(o.get("oy", 0))).convert("RGBA")
    right = o.get("side", "left") == "right"
    base.alpha_composite(gradient_layers(right))

    acc = PINK if o.get("accent", "lime") == "pink" else LIME
    acc_ink = INK if acc == PINK else VOID
    x0 = W - PAD if right else PAD

    # ---- headline ----
    lines = [l.strip().upper() for l in (o.get("line1", ""), o.get("line2", "")) if l and l.strip()]
    hl = (o.get("hl") or "").strip().upper()
    size = HEAD_MAX_SIZE
    for l in lines:
        w = text_w(font(FONT_DISPLAY, size), l)
        if w > HEAD_MAX_W:
            size = min(size, size * HEAD_MAX_W / w)
    f = font(FONT_DISPLAY, size)
    lh = size * LINE_H
    y_top = H * 0.5 - (lh * len(lines)) / 2 + size * 0.38
    d = ImageDraw.Draw(base)
    for i, l in enumerate(lines):
        y = y_top + i * lh + size * 0.36
        use_hl = hl if hl and hl in l else ""
        if use_hl:
            pre, post = l[: l.index(use_hl)], l[l.index(use_hl) + len(use_hl):]
            w_pre, w_h = text_w(f, pre), text_w(f, use_hl)
            total = text_w(f, l) + (HL_PAD if pre else 0) + (HL_PAD if post else 0)
            x = x0 - total if right else x0
            x_h = x + w_pre + (HL_PAD if pre else 0)
            x_post = x_h + w_h + (HL_PAD if post else 0)
            box = rotated_rect(x_h + w_h / 2, y - size * 0.36, w_h + 2 * HL_BOX_X, size * 1.0,
                               -w_h / 2 - HL_BOX_X, -size * 0.52, HL_TILT)
            d.polygon(box, fill=acc)
            d.text((x, y), pre, font=f, fill=INK, anchor="ls")
            d.text((x_h, y), use_hl, font=f, fill=acc_ink, anchor="ls")
            d.text((x_post, y), post, font=f, fill=INK, anchor="ls")
        else:
            x = x0 - text_w(f, l) if right else x0
            draw_shadowed_text(base, (x, y), l, f, INK, 24 * K, 0.6)
            d = ImageDraw.Draw(base)

    # ---- episode badge + label ----
    badge = (o.get("badge") or "").strip()
    if badge:
        fb = font(FONT_MONO, BADGE_FONT)
        tw = text_w(fb, badge)
        bw = tw + 2 * BADGE_PAD_X
        bx = W - PAD - bw if right else PAD
        by = PAD
        d.rectangle([bx, by, bx + bw, by + BADGE_H], fill=acc)
        d.text((bx + BADGE_PAD_X, by + 33 * K), badge, font=fb, fill=acc_ink, anchor="lm")
        label = (o.get("label") or "").strip().upper()
        if label:
            fl = font(FONT_MONO, LABEL_FONT)
            if right:
                d.text((bx - LABEL_GAP, by + 33 * K), label, font=fl, fill=INK, anchor="rm")
            else:
                d.text((bx + bw + LABEL_GAP, by + 33 * K), label, font=fl, fill=INK, anchor="lm")

    # ---- QQ sticker ----
    emo = o.get("emotion", "none")
    if emo and emo != "none":
        st = Image.open(os.path.join(HERE, "assets", f"qq_{emo}.png")).convert("RGBA")
        s = STICKER_W / STICKER_SRC_W
        st = st.resize((round(st.width * s), round(st.height * s)), Image.LANCZOS)
        cx = PAD + STICKER_W / 2 + 10 * K if right else W - PAD - STICKER_W / 2 - STICKER_RIGHT
        cy = STICKER_CY
        px, py = round(cx - st.width / 2), round(cy - st.height / 2)
        a = st.getchannel("A").point(lambda v: int(v * 0.75))
        shadow = Image.new("RGBA", st.size, (0, 0, 0, 0)); shadow.putalpha(a)
        shadow = shadow.filter(ImageFilter.GaussianBlur(30 * K / 2))
        base.alpha_composite(shadow, (px, py + round(6 * K)))
        base.alpha_composite(st, (px, py))
    return base.convert("RGB")


def save(img, out):
    out = out or "thumb.jpg"
    if out.lower().endswith(".png"):
        img.save(out, optimize=True)
    else:
        q = 93
        while True:
            img.save(out, "JPEG", quality=q, subsampling=0, optimize=True)
            if os.path.getsize(out) <= MAX_BYTES or q <= 60:
                break
            q -= 7
    return out


def check(o):
    """Brand rules the script enforces. Returns a list of warnings (Ukrainian)."""
    warn = []
    if o.get("emotion", "none") not in EMOTIONS:
        raise SystemExit(f"Невідома емоція «{o.get('emotion')}». Доступні: {', '.join(EMOTIONS)}")
    lines = [l for l in (o.get("line1", ""), o.get("line2", "")) if l and l.strip()]
    if not lines:
        raise SystemExit("Потрібен хоча б --line1.")
    words = sum(len(l.split()) for l in lines)
    if words > 4:
        warn.append(f"У заголовку {words} слів. Правило бренду — 3–4, інакше на телефоні не прочитають.")
    hl = (o.get("hl") or "").strip().upper()
    if hl and not any(hl in l.upper() for l in lines):
        warn.append(f"Виділене слово «{hl}» не знайдено в рядках — виділення пропущено.")
    if o.get("accent", "lime") not in ("lime", "pink"):
        raise SystemExit("--accent може бути тільки lime або pink.")
    if o.get("side", "left") not in ("left", "right"):
        raise SystemExit("--side може бути тільки left або right.")
    return warn


def load_series(path):
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    default = os.path.join(HERE, "series.json")
    if os.path.exists(default):
        with open(default, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def main():
    p = argparse.ArgumentParser(description="kirQQn YouTube thumbnail, 1280×720")
    p.add_argument("--image", help="скрін з гри (PNG/JPG). Без нього — приклад фону")
    p.add_argument("--line1", default="")
    p.add_argument("--line2", default="")
    p.add_argument("--hl", default="", help="слово або фраза для салатової/рожевої плашки")
    p.add_argument("--badge", default="", help="напр. #13 або СКАРБИ")
    p.add_argument("--label", default=None, help="підпис біля бейджа; за замовчуванням з series.json")
    p.add_argument("--emotion", default="none", choices=EMOTIONS)
    p.add_argument("--accent", default=None, choices=["lime", "pink"])
    p.add_argument("--side", default=None, choices=["left", "right"])
    p.add_argument("--zoom", type=float, default=1.0)
    p.add_argument("--ox", type=float, default=0.0, help="зсув скріна вліво/вправо, частка ширини (-0.3…0.3)")
    p.add_argument("--oy", type=float, default=0.0, help="зсув скріна вгору/вниз, частка висоти (-0.3…0.3)")
    p.add_argument("--series", default=None, help="json з підписом серії (за замовчуванням series.json)")
    p.add_argument("--batch", default=None, help="json-список превʼю")
    p.add_argument("--out", default="thumb.jpg")
    a = p.parse_args()

    series = load_series(a.series)
    jobs = []
    if a.batch:
        with open(a.batch, encoding="utf-8") as fh:
            jobs = json.load(fh)
    else:
        jobs = [{k: v for k, v in vars(a).items() if k not in ("batch", "series") and v is not None}]
    for j in jobs:
        o = {"label": series.get("label", ""), "accent": series.get("accent", "lime"), "side": series.get("side", "left")}
        o.update({k: v for k, v in j.items() if v is not None})
        if a.batch:
            o["_base"] = os.path.dirname(os.path.abspath(a.batch))
        for w in check(o):
            print("УВАГА:", w)
        out = save(render(o), o.get("out", "thumb.jpg"))
        print(f"Готово: {out} · {os.path.getsize(out) // 1024} КБ · 1280×720")


if __name__ == "__main__":
    main()
