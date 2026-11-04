#!/usr/bin/env python3
"""
kirQQn — вертикальні гайди (1080×1920) для Shorts, TikTok і Reels.

Той самий макет, що й у веб-конструкторі «Гайди kirQQn». Усі розміри, відступи,
кольори й шрифти зашиті в цьому файлі. Змінюються тільки скріни й текст у JSON.
Скрипт не дає зібрати картку, яка порушує гайдлайн: він зупиняється з поясненням.

  python kirqqn_guide.py render guide.json --out out_folder
  python kirqqn_guide.py grid shot.png          # сітка 5 % поверх скріна, щоб задати лінзу
  python kirqqn_guide.py check guide.json       # тільки перевірка, без картинок

Потрібно: Python 3.8+, Pillow (pip install pillow).
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "1.0"

# ---- brand tokens (do not change) ----
VOID = (7, 7, 11, 255)
INK = (244, 244, 246, 255)
SMOKE = (139, 139, 152, 255)
LINE = (35, 35, 45, 255)
LIME = (198, 255, 26, 255)
PINK = (255, 45, 111, 255)
F_DISP = os.path.join(HERE, "fonts", "Unbounded-Black.ttf")
F_BOLD = os.path.join(HERE, "fonts", "JetBrainsMono-Bold.ttf")
F_MED = os.path.join(HERE, "fonts", "JetBrainsMono-Medium.ttf")
LAYOUT = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC

# ---- layout (copied from the web constructor, do not change) ----
W, H = 1080, 1920
M, R, TOP, BOT = 96, 900, 130, 1440          # safe zone: top 130, bottom 1440, left 96, right 900
HERO = (0, 450, 1080, 660)                    # x, y, w, h — step cards
HERO_COVER = (0, 660, 1080, 600)              # cover and "next" cards
LENS_MAX_W, LENS_MAX_H = 804, 220
QUOTE_VERBS = ["CHOOSE", "SAY", "ANSWER", "ASK"]
VERBS = ["CHOOSE", "SAY", "ANSWER", "ASK", "GO TO", "PICK UP", "USE", "LISTEN FOR", "DODGE", "AVOID", "WAIT", "CRAFT", "EQUIP", "OPEN", "READ", "FOLLOW", "TALK TO", "KILL", "SNEAK"]
TONES = ["ok", "info", "warn"]
EMOTIONS = ["look", "win", "shock", "cry", "rage", "dead", "sleep", "none"]

_fc = {}
def font(path, size):
    key = (path, int(round(size)))
    if key not in _fc:
        _fc[key] = ImageFont.truetype(path, max(1, int(round(size))), layout_engine=LAYOUT)
    return _fc[key]

def pad2(n): return str(n).zfill(2)

def width(f, s, ls=0.0):
    if not s: return 0.0
    if ls == 0: return f.getlength(s)
    return sum(f.getlength(ch) + ls for ch in s)

def text(d, x, y, s, f, fill, ls=0.0, anchor="ls"):
    """Draw text with optional letter spacing (canvas letterSpacing semantics)."""
    if ls == 0:
        d.text((x, y), s, font=f, fill=fill, anchor=anchor); return width(f, s)
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill, anchor=anchor); cx += f.getlength(ch) + ls
    return cx - x

def wrap(f, s, max_w, max_lines):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_) if cur else w_
        if width(f, t) <= max_w or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    if len(lines) > max_lines or any(width(f, l) > max_w for l in lines): return None
    return lines

def fit_wrap(path, s, frm, to, max_w, max_lines):
    for size in range(frm, to - 1, -1):
        l = wrap(font(path, size), s, max_w, max_lines)
        if l: return size, l, True
    return to, (wrap(font(path, to), s, max_w, 99) or [s]), False

def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def rot_paste(base, lay, ang_rad, cx, cy):
    """Rotate a full-canvas layer around (cx, cy) like canvas ctx.rotate(ang) (negative = counter-clockwise)."""
    base.alpha_composite(lay.rotate(-math.degrees(ang_rad), resample=Image.BICUBIC, center=(cx, cy)))

def asset(name): return Image.open(os.path.join(HERE, "assets", name)).convert("RGBA")

def cover_geom(iw, ih, r, zoom=1.0, ox=0.0, oy=0.0):
    x, y, w, h = r
    s = max(w / iw, h / ih) * zoom
    dw, dh = iw * s, ih * s
    return s, x + (w - dw) * (1 + ox) / 2, y + (h - dh) * (1 + oy) / 2

# ---------------- pieces ----------------
def hero(base, c, r, mode):
    x, y, w, h = r
    if mode == "overlay":
        base.paste((0, 0, 0, 0), (x, y, x + w, y + h))
    elif c.get("_img") is not None:
        im = c["_img"]; iw, ih = im.size
        s, dx, dy = cover_geom(iw, ih, r, c.get("zoom", 1), c.get("ox", 0), c.get("oy", 0))
        box = ((x - dx) / s, (y - dy) / s, (x - dx + w) / s, (y - dy + h) / s)
        base.paste(im.resize((w, h), Image.LANCZOS, box=box).convert("RGBA"), (x, y))
    col_a = []
    y0 = y + h * 0.62
    for yy in range(y, y + h):
        bot = 0.72 * min(1, max(0, (yy + 0.5 - y0) / (h * 0.38))) if yy + 1 > y0 else 0.0
        top = 0.55 * (1 - (yy + 0.5 - y) / 90) if yy < y + 90 else 0.0
        col_a.append(int(round((top + bot * (1 - top)) * 255)))
    m = Image.new("L", (1, h)); m.putdata(col_a); m = m.resize((w, h), Image.NEAREST)
    g = layer(); g.paste(Image.new("RGBA", (w, h), (7, 7, 11, 255)), (x, y), m)
    base.alpha_composite(g)
    d = ImageDraw.Draw(base)
    col = (244, 244, 246, 230); L = 34
    x1, y1, x2, y2 = x + 24, y + 24, x + w - 24, y + h - 24
    corners = [(x1, y1, 1, 1), (x2, y1, -1, 1), (x2, y2, -1, -1)]
    if not (c["type"] == "step" and lens_box(c)): corners.append((x1, y2, 1, -1))
    for cx_, cy_, sx, sy in corners:
        d.rectangle(sorted_box(cx_ - 1.5, cy_ - 1.5 * sy, cx_ + 1.5, cy_ + sy * L), fill=col)
        d.rectangle(sorted_box(cx_ - 1.5 * sx, cy_ - 1.5, cx_ + sx * L, cy_ + 1.5), fill=col)

def sorted_box(x1, y1, x2, y2): return (min(x1, x2), min(y1, y2), max(x1, x2) - 1, max(y1, y2) - 1)

def header(base, g, counter, cover_expr):
    base.alpha_composite(asset("hdr_look.png" if cover_expr else "hdr_none.png"))
    d = ImageDraw.Draw(base)
    fb30 = font(F_BOLD, 30)
    big, small = counter
    ws, wb = width(fb30, small, 1), width(fb30, big, 1)
    text(d, R - ws - wb, 163, big, fb30, INK, 1)
    text(d, R - ws, 163, small, fb30, SMOKE, 1)
    avail = R - ws - wb - 28 - (M + 78)
    fm, fbs = font(F_MED, 21), font(F_BOLD, 21)
    game = (g.get("game") or "").upper()
    guide = (g.get("guide") or "").upper() + part_tag(g, " · ")
    sep = "  /  "
    full = lambda: width(fm, game + sep, 2) + width(fbs, guide, 2)
    tries = 0
    while full() > avail and tries < 80:
        tries += 1
        if len(game) > 8: game = game[:-2].rstrip() + "…"
        else: guide = guide[:-2].rstrip() + "…"
    gw = text(d, M + 78, 161, game + sep, fm, SMOKE, 2)
    text(d, M + 78 + gw, 161, guide, fbs, INK, 2)

def progress(base, n, total, p=1.0):
    d = ImageDraw.Draw(base); gap, y, h = 6, 188, 8; N = max(1, total)
    w = (R - M - gap * (N - 1)) / N
    for i in range(N):
        x = M + i * (w + gap)
        d.rectangle((round(x), y, round(x + w) - 1, y + h - 1), fill=SMOKE if i < n - 1 else LINE)
        if i == n - 1 and p > 0: d.rectangle((round(x), y, round(x + w * p) - 1, y + h - 1), fill=INK)

def part_tag(g, pre=""):
    p = int(g.get("part") or 0); ps = int(g.get("parts") or 0)
    return f"{pre}PT {p}{'/' + str(ps) if ps > 1 else ''}" if p > 0 else ""

def step_range(g, part_steps):
    first = max(1, int(g.get("start") or 1)); last = first - 1 + max(0, part_steps)
    return first, last, max(last, int(g.get("grand") or 0))

def lens_box(c):
    ln = c.get("_lens"); im = c.get("_img")
    if not ln or im is None: return None
    iw, ih = im.size
    sw, sh = ln[2] * iw, ln[3] * ih; a = sw / sh
    bw = min(LENS_MAX_W, LENS_MAX_H * a); bh = bw / a
    if bh < 120: bh = 120; bw = min(LENS_MAX_W, bh * a)
    hb = HERO[1] + HERO[3]
    return dict(x=M, y=round(hb - min(bh * 0.5, 110)), w=bw, h=bh, sx=ln[0] * iw, sy=ln[1] * ih, sw=sw, sh=sh)

def lens(base, c):
    L = lens_box(c)
    if not L: return None
    im = c["_img"]; iw, ih = im.size
    s = cover_geom(iw, ih, HERO, c.get("zoom", 1), c.get("ox", 0), c.get("oy", 0))[0]
    k = (L["w"] / L["sw"]) / s
    x, y, w, h = L["x"], L["y"], L["w"], L["h"]
    sh = layer(); ImageDraw.Draw(sh).rectangle((x - 6, y - 6 + 10, x + w + 6 - 1, y + h + 6 + 10 - 1), fill=(0, 0, 0, 191))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(base)
    d.rectangle((x - 6, y - 6, x + w + 6 - 1, y + h + 6 - 1), fill=VOID)
    crop = im.resize((round(w), round(h)), Image.LANCZOS, box=(L["sx"], L["sy"], L["sx"] + L["sw"], L["sy"] + L["sh"])).convert("RGBA")
    base.paste(crop, (x, y))
    d.rectangle((x, y, x + round(w) - 1, y + round(h) - 1), outline=INK, width=2)
    tab = f"ZOOM ×{k:.1f}"; f18 = font(F_BOLD, 18)
    tw = width(f18, tab, 2) + 24
    d.rectangle((x - 6, y - 6 - 32, x - 6 + tw - 1, y - 6 - 1), fill=INK)
    text(d, x + 6, y - 6 - 15, tab, f18, VOID, 2, anchor="lm")
    mk = c.get("mark")
    if mk is not None and mk >= 0:
        yy = y + mk * h
        d.polygon([(16, yy - 15), (42, yy), (16, yy + 15)], fill=LIME)
        d.rectangle((round(x + w + 6), round(yy - 15), round(x + w + 6) + 5, round(yy + 15) - 1), fill=LIME)
    return k

def icon(base, tone, x, y, s):
    d = ImageDraw.Draw(base); lw = max(2, round(s * 0.16))
    if tone == "warn":
        d.line([(x, y - s / 2), (x + s, y + s / 2)], fill=PINK, width=lw); d.line([(x + s, y - s / 2), (x, y + s / 2)], fill=PINK, width=lw)
    elif tone == "ok":
        d.line([(x, y), (x + s * 0.38, y + s * 0.4), (x + s, y - s * 0.45)], fill=INK, width=lw, joint="curve")
    else:
        d.line([(x, y), (x + s, y)], fill=INK, width=lw)
        d.line([(x + s * 0.55, y - s * 0.45), (x + s, y), (x + s * 0.55, y + s * 0.45)], fill=INK, width=lw, joint="curve")

def numeral(base, num, ns, x, y):
    f = font(F_DISP, ns)
    outer = Image.new("L", (W, H), 0); inner = Image.new("L", (W, H), 0)
    do, di = ImageDraw.Draw(outer), ImageDraw.Draw(inner)
    cx = x
    for ch in num:
        do.text((cx, y), ch, font=f, fill=255, anchor="ls", stroke_width=1.5, stroke_fill=255)
        di.text((cx, y), ch, font=f, fill=255, anchor="ls")
        cx += f.getlength(ch) - 4
    inner = inner.filter(ImageFilter.MinFilter(3))
    from PIL import ImageChops
    ring = ImageChops.subtract(outer, inner)
    col = Image.new("RGBA", (W, H), (244, 244, 246, 0)); col.putalpha(ring.point(lambda v: int(v * 0.5)))
    base.alpha_composite(col)

# ---------------- layout checks ----------------
def action_layout(c):
    verb = (c.get("verb") or "").upper().strip()
    act = (c.get("action") or "").strip()
    if act and verb in QUOTE_VERBS and act[0] not in "“\"«": act = "“" + act + "”"
    for size in range(38, 23, -1):
        f = font(F_BOLD, size); lh = size * 1.3
        lines = wrap(f, act, LENS_MAX_W - 40, 2)
        if not lines: continue
        ph = len(lines) * lh + 30
        if 1286 + ph + 50 <= 1436: return dict(verb=verb, act=act, size=size, lines=lines, ph=ph, lh=lh, out_y=1286 + ph + 48, ok=True)
    f = font(F_BOLD, 24); lines = wrap(f, act, LENS_MAX_W - 40, 9) or [act]
    ph = len(lines) * 24 * 1.3 + 30
    return dict(verb=verb, act=act, size=24, lines=lines, ph=ph, lh=24 * 1.3, out_y=1286 + ph + 48, ok=False)

def validate(g, base_dir):
    """Returns (errors, warnings). Errors stop rendering: they break the guideline."""
    E, Wn = [], []
    cards = g.get("cards") or []
    if not cards: E.append("У guide.json немає жодної картки (cards).")
    for k in ("game", "guide"):
        if not (g.get(k) or "").strip(): E.append(f"Порожнє поле «{k}».")
    if len((g.get("game") or "")) > 24: Wn.append("Назва гри довга — у шапці її обріже. Краще коротка: DAWNWALKER.")
    p, ps = int(g.get("part") or 0), int(g.get("parts") or 0)
    if ps and p > ps: E.append(f"part {p} більший за parts {ps}.")
    steps = [c for c in cards if c.get("type") == "step"]
    if cards and cards[0].get("type") != "cover": E.append("Перша картка має бути обкладинкою (type: cover).")
    if p > 0 and ps and p < ps and cards and cards[-1].get("type") != "next": E.append(f"Частина {p} з {ps}: остання картка має бути type: next — вона веде на PT {p + 1}.")
    if p > 0 and ps and p == ps and any(c.get("type") == "next" for c in cards): E.append("Це остання частина — картка next тут зайва.")
    if len(steps) > 8: Wn.append(f"У частині {len(steps)} кроків. Понад 8 — розбий на частини (part / parts).")
    for i, c in enumerate(cards):
        tag = f"Картка {i} ({c.get('type')})"
        t = c.get("type")
        if t not in ("cover", "step", "next"): E.append(f"{tag}: type має бути cover, step або next."); continue
        if not c.get("image"): E.append(f"{tag}: немає image (скрін з гри).")
        else:
            try: resolve(c["image"], base_dir)
            except SystemExit as e: E.append(f"{tag}: {e}")
        for k in ("zoom",):
            if k in c and not (1 <= float(c[k]) <= 2.5): E.append(f"{tag}: zoom від 1 до 2.5.")
        for k in ("ox", "oy"):
            if k in c and not (-1 <= float(c[k]) <= 1): E.append(f"{tag}: {k} від -1 до 1.")
        title = (c.get("title") or "").strip()
        if t == "step":
            nw = len(title.split())
            if not title: E.append(f"{tag}: немає title (назва кроку: дієслово + об’єкт).")
            elif nw > 4: E.append(f"{tag}: title «{title}» — {nw} слів, максимум 4.")
            v = (c.get("verb") or "").upper().strip()
            if not v: E.append(f"{tag}: немає verb.")
            elif v not in VERBS: Wn.append(f"{tag}: verb «{v}» не зі списку. Перевір, чи не підходить один із: {', '.join(VERBS)}.")
            if len(v) > 16: E.append(f"{tag}: verb довший за 16 знаків.")
            if not (c.get("action") or "").strip(): E.append(f"{tag}: немає action (що саме вибрати / куди йти).")
            if c.get("tone", "info") not in TONES: E.append(f"{tag}: tone має бути ok, info або warn.")
            if v in QUOTE_VERBS and not c.get("lens"): E.append(f"{tag}: вибір у діалозі без lens. Задай лінзу на рядки діалогу (команда grid допоможе).")
            if c.get("lens") and c.get("mark") is None and v in QUOTE_VERBS: Wn.append(f"{tag}: немає mark — стрілка не покаже, який рядок вибрати.")
            mk = c.get("mark")
            if mk is not None and not (0 <= float(mk) <= 1): E.append(f"{tag}: mark від 0 (верх лінзи) до 1 (низ).")
            al = action_layout(c)
            if not al["ok"]: E.append(f"{tag}: action задовгий навіть дрібним шрифтом. Лиши перші 4–6 слів репліки й «…».")
            oc = (c.get("outcome") or "").strip().upper()
            if not oc: Wn.append(f"{tag}: немає outcome — глядач не знає, що буде після дії.")
            elif len(oc.split()) > 7 or width(font(F_BOLD, 22), oc) > R - M - 44: E.append(f"{tag}: outcome «{oc}» задовгий. Максимум 6–7 слів, щоб читалось шрифтом від 22 px.")
        else:
            if not title: E.append(f"{tag}: немає title.")
            hl = (c.get("hl") or "").upper().strip()
            if hl and hl not in title.upper(): E.append(f"{tag}: hl «{hl}» немає в title.")
            if c.get("emotion", "look") not in EMOTIONS: E.append(f"{tag}: emotion — одна з {', '.join(EMOTIONS)}.")
            if t == "cover":
                size, lines, ok = poster_fit(title.upper())
                if not ok: E.append(f"{tag}: гачок не влазить у 3 рядки. Скороти до 2–5 слів.")
                if len(title.split()) > 5: E.append(f"{tag}: гачок «{title}» — {len(title.split())} слів, максимум 5.")
                if not hl: E.append(f"{tag}: немає hl — одне слово-цінність на салатовій плашці (нагорода чи ставка).")
            if t == "next":
                size, lines, ok = fit_wrap(F_DISP, title.upper(), 64, 36, R - M, 2)
                if not ok: E.append(f"{tag}: текст про наступну частину не влазить у 2 рядки.")
        if c.get("lens") is not None:
            ln = c["lens"]
            if not (isinstance(ln, list) and len(ln) == 4): E.append(f"{tag}: lens — список [x, y, w, h].")
    return E, Wn

# ---------------- cards ----------------
def resolve(p, base=None):
    for cand in (p, os.path.join(base or "", p), os.path.join(HERE, p)):
        if cand and os.path.exists(cand): return cand
    raise SystemExit(f"не знайдено файл «{p}»")

def norm_lens(ln, im):
    if not ln: return None
    x, y, w, h = [float(v) for v in ln]
    if max(x, y, w, h) > 1.0:  # pixels of the source screenshot
        iw, ih = im.size; x, y, w, h = x / iw, y / ih, w / iw, h / ih
    return (x, y, w, h)

# ---------------- poster cover (v2, Oct 2026) ----------------
# Full-bleed frame, hook inside the band that survives the TikTok UI (y 130…1440) and the 2:3 crop of the
# YouTube channel shelf (y 150…1770). 1–1.2 s on screen; this frame is picked as the Short's thumbnail.
PM, P_TOP, P_MAXW, P_FROM, P_TO, P_LINES, P_LS = 96, 386, 876, 168, 96, 3, -2
LIFT_TARGET, LIFT_MAX = 0.36, 1.35

def wrap_ls(f, s, max_w, max_lines, ls):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_) if cur else w_
        if width(f, t, ls) <= max_w or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    if len(lines) > max_lines or any(width(f, l, ls) > max_w for l in lines): return None
    return lines

def poster_fit(title):
    for size in range(P_FROM, P_TO - 1, -2):
        l = wrap_ls(font(F_DISP, size), title, P_MAXW, P_LINES, P_LS)
        if l: return size, l, True
    return P_TO, (wrap_ls(font(F_DISP, P_TO), title, P_MAXW, 9, P_LS) or [title]), False

def lift_gain(crop):
    from PIL import ImageStat
    L = ImageStat.Stat(crop.resize((54, 96), Image.BILINEAR).convert("L")).mean[0] / 255
    return max(1.0, min(LIFT_MAX, LIFT_TARGET / max(L, 0.01)))

def text_ls_shadow(base, x, y, s, f, ls):
    sh = layer(); text(ImageDraw.Draw(sh), x, y, s, f, (0, 0, 0, 140), ls)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    text(ImageDraw.Draw(base), x, y, s, f, INK, ls)

def poster(g, c, first, last, grand, mode):
    if mode == "overlay": base = layer()
    else:
        im = c["_img"]; iw, ih = im.size
        s, dx, dy = cover_geom(iw, ih, (0, 0, W, H), c.get("zoom", 1), c.get("ox", 0), c.get("oy", 0))
        crop = im.resize((W, H), Image.LANCZOS, box=(-dx / s, -dy / s, (-dx + W) / s, (-dy + H) / s))
        k = c.get("lift") or lift_gain(crop)
        if k > 1.001: crop = ImageEnhance.Brightness(crop).enhance(k)
        base = crop.convert("RGBA")
    col = []
    for yy in range(H):
        a = 0.0
        if yy < 900:
            u = (yy + 0.5) / 900
            if u < 0.25: a = 0.95 + (0.82 - 0.95) * u / 0.25
            elif u < 0.55: a = 0.82 + (0.55 - 0.82) * (u - 0.25) / 0.30
            else: a = 0.55 * (1 - (u - 0.55) / 0.45)
        elif yy >= 1250: a = 0.8 * (yy + 0.5 - 1250) / 670
        col.append(int(round(max(0, a) * 255)))
    m = Image.new("L", (1, H)); m.putdata(col); m = m.resize((W, H), Image.NEAREST)
    gl = Image.new("RGBA", (W, H), (7, 7, 11, 0)); gl.putalpha(m); base.alpha_composite(gl)
    d = ImageDraw.Draw(base); p = int(g.get("part") or 0)
    f26, f28 = font(F_BOLD, 26), font(F_BOLD, 28)
    tag = part_tag(g).replace("PT", "PART"); pw = width(f26, tag, 3) + 30 if p > 0 else 0
    series = f"{(g.get('game') or '').upper()} · GUIDE"
    while width(f28, series, 4) > R - PM - pw - 24 and len(series) > 10: series = series[:-2].rstrip() + "…"
    text(d, PM, 318, series, f28, INK, 4); d.rectangle((PM, 336, PM + 71, 343), fill=LIME)
    if p > 0:
        x0 = R - pw; d.rectangle((round(x0), 282, round(x0 + pw) - 1, 282 + 43), fill=INK)
        text(d, x0 + 15, 282 + 23, tag, f26, VOID, 3, anchor="lm")
    title = (c.get("title") or "").upper().strip(); hl = (c.get("hl") or "").upper().strip()
    size, lines, _ = poster_fit(title); f = font(F_DISP, size); lh = size * 1.0; b0 = P_TOP + size * 0.76
    for i, line in enumerate(lines):
        y = b0 + i * lh; at = line.find(hl) if hl else -1
        pre = line if at < 0 else line[:at]; x0 = PM + width(f, pre, P_LS)
        if at >= 0:
            w_ = width(f, hl, P_LS); lay = layer(); cx, cy = x0 + w_ / 2, y - size * 0.36
            ImageDraw.Draw(lay).rectangle((cx - w_ / 2 - 20, cy - size * 0.55, cx + w_ / 2 + 20 - 1, cy - size * 0.55 + size * 1.06 - 1), fill=LIME)
            rot_paste(base, lay, -0.03, cx, cy)
        if at < 0: text_ls_shadow(base, PM - 4, y, line, f, P_LS)
        else:
            if pre: text_ls_shadow(base, PM - 4, y, pre, f, P_LS)
            post = line[at + len(hl):]
            if post: text_ls_shadow(base, x0 - 4 + width(f, hl, P_LS), y, post, f, P_LS)
            text(ImageDraw.Draw(base), x0 - 4, y, hl, f, VOID, P_LS)
    e = c.get("emotion", "look")
    if e and e != "none": base.alpha_composite(asset(f"poster_sticker_{e}.png"))
    chip = (c.get("sub") or "").strip()
    if not chip and last: chip = f"STEPS {pad2(first)}–{pad2(last)}" if (first > 1 or grand > last) else f"{last} {'STEP' if last == 1 else 'STEPS'}"
    chip = chip.upper()
    if chip:
        f30 = font(F_BOLD, 30); tw = width(f30, chip, 3) + 40; d = ImageDraw.Draw(base)
        d.rectangle((PM, 1330, round(PM + tw) - 1, 1330 + 57), fill=INK); text(d, PM + 20, 1369, chip, f30, VOID, 3)
    return base

def card(g, idx, mode):
    cards = g["cards"]; c = cards[idx]
    steps = [x for x in cards if x.get("type") == "step"]
    first, last, grand = step_range(g, len(steps))
    t = c["type"]
    if t == "cover": return poster(g, c, first, last, grand, mode)
    base = asset("bg_shock.png" if (t == "step" and c.get("tone") == "warn") else "bg_look.png").copy()
    d = ImageDraw.Draw(base)
    if t == "step":
        n = first - 1 + steps.index(c) + 1
        total = max(n, grand)
        hero(base, c, HERO, mode)
        header(base, g, [pad2(n), "/" + pad2(total)], False)
        progress(base, n, total, 1.0)
        num = pad2(n); ns = 184
        while ns > 130:
            if R - (M - 8 + width(font(F_DISP, ns), num) - 4 * len(num) + 26) >= 470: break
            ns -= 4
        nw = width(font(F_DISP, ns), num) - 4 * len(num)
        numeral(base, num, ns, M - 8, 414)
        tx = M - 8 + nw + 26
        size, lines, _ = fit_wrap(F_DISP, (c.get("title") or "").upper(), 76, 40, R - tx, 2)
        f = font(F_DISP, size); d = ImageDraw.Draw(base)
        for i, l in enumerate(lines): d.text((tx, 412 - (len(lines) - 1 - i) * size * 1.02), l, font=f, fill=INK, anchor="ls")
        al = action_layout(c)
        lens(base, c); d = ImageDraw.Draw(base)
        text(d, M, 1270, al["verb"], font(F_BOLD, 22), SMOKE, 4)
        if al["act"]:
            lay = layer(); dl = ImageDraw.Draw(lay); fa = font(F_BOLD, al["size"])
            tw = max(width(fa, l) for l in al["lines"]); top = 1286
            dl.rectangle((M, top, M + tw + 40 - 1, top + al["ph"] - 1), fill=LIME)
            for i, l in enumerate(al["lines"]): dl.text((M + 20, top + 15 + al["size"] + i * al["lh"]), l, font=fa, fill=VOID, anchor="ls")
            rot_paste(base, lay, -0.014, M, top + al["ph"] / 2)
        oc = (c.get("outcome") or "").strip().upper()
        if oc:
            s = 26
            while s > 17 and width(font(F_BOLD, s), oc) > R - M - 44: s -= 1
            y = min(al["out_y"], 1436)
            icon(base, c.get("tone", "info"), M + 2, y - s * 0.36, 24)
            text(ImageDraw.Draw(base), M + 44, y, oc, font(F_BOLD, s), PINK if c.get("tone") == "warn" else INK, 1)
        return base
    r = HERO_COVER
    hero(base, c, r, mode)
    p = int(g.get("part") or 0)
    if t == "cover":
        if last and (first > 1 or grand > last): cnt = [f"{pad2(first)}–{pad2(last)}", "/" + pad2(grand) if grand else ""]
        elif last: cnt = [str(last), " STEP" if last == 1 else " STEPS"]
        else: cnt = ["", ""]
        header(base, g, cnt, True)
        if p > 0:
            tag = part_tag(g).replace("PT", "PART"); f26 = font(F_BOLD, 26)
            w_ = width(f26, tag, 3) + 30
            d = ImageDraw.Draw(base); d.rectangle((M, 238, M + w_ - 1, 238 + 44 - 1), fill=INK)
            text(d, M + 15, 238 + 23, tag, f26, VOID, 3, anchor="lm")
        title = (c.get("title") or "").upper()
        size, lines, _ = fit_wrap(F_DISP, title, 98 if p > 0 else 112, 56, R - M - 20, 3)
        f = font(F_DISP, size); lh = size * 1.06; base_y = 610 - (len(lines) - 1) * lh
        hl = (c.get("hl") or "").upper().strip()
        for i, line in enumerate(lines):
            y = base_y + i * lh; d = ImageDraw.Draw(base)
            if hl and hl in line:
                pre = line[:line.index(hl)]; x0 = M + width(f, pre); w_ = width(f, hl)
                lay = layer(); cx, cy = x0 + w_ / 2, y - size * 0.36
                ImageDraw.Draw(lay).rectangle((cx - w_ / 2 - 14, cy - size * 0.52, cx + w_ / 2 + 14 - 1, cy - size * 0.52 + size - 1), fill=LIME)
                rot_paste(base, lay, -0.025, cx, cy); d = ImageDraw.Draw(base)
                d.text((M, y), pre, font=f, fill=INK, anchor="ls")
                d.text((x0, y), hl, font=f, fill=VOID, anchor="ls")
                d.text((x0 + w_, y), line[len(pre) + len(hl):], font=f, fill=INK, anchor="ls")
            else:
                d.text((M, y), line, font=f, fill=INK, anchor="ls")
        sub = (c.get("sub") or "").strip().upper()
    else:  # next
        header(base, g, [pad2(last), "/" + pad2(grand)] if grand else ["", ""], False)
        if grand: progress(base, last + 1, grand, 0)
        d = ImageDraw.Draw(base); text(d, M, 268, "UP NEXT", font(F_BOLD, 24), SMOKE, 4)
        tag = f"PT {(p or 1) + 1}"; f150 = font(F_DISP, 150); w_ = width(f150, tag)
        lay = layer(); cx, cy = M + w_ / 2 + 18, 380
        ImageDraw.Draw(lay).rectangle((cx - w_ / 2 - 22, cy - 98, cx + w_ / 2 + 22 - 1, cy + 70 - 1), fill=LIME)
        rot_paste(base, lay, -0.025, cx, cy)
        ImageDraw.Draw(base).text((M + 18, 438), tag, font=f150, fill=VOID, anchor="ls")
        icon(base, "info", M + w_ + 80, 380, 92)
        size, lines, _ = fit_wrap(F_DISP, (c.get("title") or "").upper(), 64, 36, R - M, 2)
        f = font(F_DISP, size); d = ImageDraw.Draw(base)
        for i, l in enumerate(lines): d.text((M, 616 - (len(lines) - 1 - i) * size * 1.06), l, font=f, fill=INK, anchor="ls")
        sub = (c.get("sub") or f"PART {(p or 1) + 1} · ON MY PROFILE").strip().upper()
    e = c.get("emotion", "look")
    if e and e != "none": base.alpha_composite(asset(f"sticker_{e}.png"))
    if sub: text(ImageDraw.Draw(base), M, r[1] + r[3] + 90, sub, font(F_BOLD, 26), SMOKE, 3)
    return base

def label(g, i):
    c = g["cards"][i]
    if c["type"] == "cover": return "cover"
    if c["type"] == "next": return "next"
    steps = [x for x in g["cards"] if x["type"] == "step"]
    return "step" + pad2(max(1, int(g.get("start") or 1)) - 1 + steps.index(c) + 1)

def load(path):
    with open(path, encoding="utf-8") as fh: g = json.load(fh)
    base_dir = os.path.dirname(os.path.abspath(path))
    return g, base_dir

def prepare(g, base_dir):
    for c in g["cards"]:
        c["_img"] = Image.open(resolve(c["image"], base_dir)).convert("RGB")
        c["_lens"] = norm_lens(c.get("lens"), c["_img"]) if c.get("type") == "step" else None

def cmd_render(a):
    g, base_dir = load(a.guide)
    E, Wn = validate(g, base_dir)
    for w_ in Wn: print("УВАГА:", w_)
    if E:
        for e in E: print("ПОМИЛКА:", e)
        print(f"\nЗупинено: {len(E)} помилок. Виправ guide.json і запусти знову."); sys.exit(2)
    prepare(g, base_dir)
    slug = "".join(ch if ch.isalnum() else "-" for ch in (g.get("guide") or "guide").lower()).strip("-")[:40] + (f"-pt{g['part']}" if int(g.get("part") or 0) else "")
    out = a.out or os.path.join(base_dir, f"kirqqn_{slug}")
    os.makedirs(os.path.join(out, "full"), exist_ok=True); os.makedirs(os.path.join(out, "resolve_overlay"), exist_ok=True)
    fulls = []
    for i in range(len(g["cards"])):
        name = f"{pad2(i)}_{label(g, i)}"
        im = card(g, i, "full"); im.convert("RGB").save(os.path.join(out, "full", name + "_full.png")); fulls.append(im)
        card(g, i, "overlay").save(os.path.join(out, "resolve_overlay", name + "_overlay.png"))
        print("готово:", name)
    # contact sheet for a quick look
    n = len(fulls); sw, sh = 270, 480
    sheet = Image.new("RGB", (n * (sw + 12) + 12, sh + 24), (20, 20, 26))
    for i, im in enumerate(fulls): sheet.paste(im.convert("RGB").resize((sw, sh), Image.LANCZOS), (12 + i * (sw + 12), 12))
    sheet.save(os.path.join(out, "preview.jpg"), quality=90)
    p, ps = int(g.get("part") or 0), int(g.get("parts") or 0)
    lines = [f"kirQQn · {g.get('game')} · {g.get('guide')}{part_tag(g, ' · ')}", "", "Порядок карток:"]
    for i, c in enumerate(g["cards"]):
        what = ("обкладинка: " + c.get("title", "")) if c["type"] == "cover" else ("далі, PT " + str((p or 1) + 1) + ": " + c.get("title", "")) if c["type"] == "next" else f"{c.get('verb')}: {c.get('action')}  →  {c.get('outcome', '')}"
        lines.append(f"{pad2(i)}_{label(g, i)}  —  {what}")
    lines += ["", "Resolve, вертикальний таймлайн 1080×1920, 60 к/с:",
              "V1 — геймплей кроку. Inspector → Transform: Zoom 1.087, Position Y +180.",
              "     Обкладинка: Zoom 3.161, Position Y 0, Position X — на обличчя чи нагороду. Темний кадр: Color → Gain +0.2.",
              "     «Далі»: Zoom 1.0, Position Y 0.",
              "Обкладинка триває 1–1,2 с — у застосунку YouTube обери обкладинкою Short кадр саме з неї.",
              "V2 — PNG з resolve_overlay на всю довжину картки.",
              "V3 — guide_step_wipe.mov серединою на склейці між картками.",
              "Тривалість кроку: 1 с + 0,4 с на кожне слово тексту на картці, не менше 2,5 с. Обкладинка 1–1,2 с, «Далі» 2 с."]
    if p: lines.append(f"Назва відео: {g.get('guide')} — PT {p}{'/' + str(ps) if ps else ''} | {g.get('game')}")
    with open(os.path.join(out, "ЯК_ЗІБРАТИ.txt"), "w", encoding="utf-8") as fh: fh.write("\n".join(lines) + "\n")
    print(f"\nГотово: {n} карток у {out}")

def cmd_check(a):
    g, base_dir = load(a.guide); E, Wn = validate(g, base_dir)
    for w_ in Wn: print("УВАГА:", w_)
    for e in E: print("ПОМИЛКА:", e)
    print("OK — можна рендерити." if not E else f"{len(E)} помилок."); sys.exit(2 if E else 0)

def cmd_grid(a):
    im = Image.open(a.image).convert("RGB"); iw, ih = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    f = font(F_BOLD, max(12, iw // 90))
    for i in range(1, 20):
        x = iw * i / 20; y = ih * i / 20; col = (198, 255, 26, 200) if i % 2 == 0 else (198, 255, 26, 90)
        d.line([(x, 0), (x, ih)], fill=col, width=1 if i % 2 else 2); d.line([(0, y), (iw, y)], fill=col, width=1 if i % 2 else 2)
        if i % 2 == 0:
            d.text((x + 4, 4), f"{i * 5}%", font=f, fill=(198, 255, 26, 255)); d.text((4, y + 2), f"{i * 5}%", font=f, fill=(198, 255, 26, 255))
    out = a.out or os.path.splitext(a.image)[0] + "_grid.jpg"
    Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save(out, quality=90)
    print(f"Сітка: {out}\nЛінза задається часткою кадру: lens = [x, y, w, h], напр. [0.05, 0.40, 0.31, 0.20]. Або в пікселях скріна ({iw}×{ih}).")

def main():
    ap = argparse.ArgumentParser(description="kirQQn — вертикальні гайди 1080×1920")
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("render"); r.add_argument("guide"); r.add_argument("--out"); r.set_defaults(fn=cmd_render)
    c = sp.add_parser("check"); c.add_argument("guide"); c.set_defaults(fn=cmd_check)
    gr = sp.add_parser("grid"); gr.add_argument("image"); gr.add_argument("--out"); gr.set_defaults(fn=cmd_grid)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
