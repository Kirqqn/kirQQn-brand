#!/usr/bin/env python3
"""
kirQQn — титри для довгих YouTube-епізодів (PNG 2560×1440 з прозорим фоном для Resolve).

Той самий макет, що й у веб-конструкторі «Титри kirQQn». Розміри, місця, шрифти й кольори
зашиті тут. Скрипт не дає зібрати картку, яка порушує гайдлайн: зупиняється з поясненням.

  python kirqqn_episode.py render episode.txt --out out_folder
  python kirqqn_episode.py check episode.txt
  python kirqqn_episode.py counters --out out_folder        # лічильники qq ×01…×30

episode.txt — один рядок на картку: таймкод, код, текст. Також читає EDL з маркерами Resolve
і JSON-список карток. Формат — у ГАЙДЛАЙН_ЕПІЗОДИ.md.

Потрібно: Python 3.8+, Pillow (pip install pillow).
"""
import argparse, json, math, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
VOID = (7, 7, 11, 255); INK = (244, 244, 246, 255); SMOKE = (139, 139, 152, 255); LIME = (198, 255, 26, 255); PINK = (255, 45, 111, 255)
F_DISP = os.path.join(HERE, "fonts", "Unbounded-Black.ttf")
F_BOLD = os.path.join(HERE, "fonts", "JetBrainsMono-Bold.ttf")
F_MED = os.path.join(HERE, "fonts", "JetBrainsMono-Medium.ttf")
LAYOUT = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC

# ---- layout (copied from the web constructor, do not change) ----
W, H = 2560, 1440
LANE = 1150
A = {"TL": (128, 190, "left", False), "TC": (1280, 196, "center", False), "BC": (1280, 1120, "center", True), "BL": (128, 1110, "left", True)}
ALLOWED = {"chapter": ["TL"], "goal": ["TL"], "verdict": ["TL"], "caption": ["TL", "TC"], "hint": ["TL", "BC"], "translate": ["BC"], "counter": ["BL"]}
ICONS = ["none", "pin", "clock", "person", "item", "enemy", "quest"]
EMOTIONS = ["cry", "dead", "win", "shock", "rage", "look", "sleep"]
TYPE_UA = {"meme": "мем-штамп", "chapter": "розділ", "goal": "мета", "caption": "підпис", "hint": "порада", "translate": "переклад", "verdict": "підсумок", "counter": "лічильник"}
LIMITS = {"chapter": 4, "goal": 1, "verdict": 1, "hint": 3, "translate": 6, "caption": 8, "counter": 6, "meme": 2}
MEMES = {"tak_i_zadumano": "ТАК І ЗАДУМАНО", "lehendarno": "ЛЕГЕНДАРНО", "ne_bah_a_ficha": "ЦЕ НЕ БАГ, ЦЕ ФІЧА", "plan_buv_idealnyi": "ПЛАН БУВ ІДЕАЛЬНИЙ", "nu_yak_tak": "НУ ЯК ТАК?!", "vidstupaiemo": "ВІДСТУПАЄМО"}
# density (minimum standard of the channel: graphics must help, not nag)
HOOK_S, MIN_GAP_S, WINDOW_S, WINDOW_MAX, TEN_MIN_MAX, MEME_GAP_S = 15, 1.0, 60, 2, 8, 300

_fc = {}
def font(path, size):
    k = (path, int(round(size)))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, max(1, int(round(size))), layout_engine=LAYOUT)
    return _fc[k]
def width(f, s, ls=0.0):
    if not s: return 0.0
    return f.getlength(s) if ls == 0 else sum(f.getlength(c) + ls for c in s)
def text(d, x, y, s, f, fill, ls=0.0, anchor="ls"):
    if ls == 0: d.text((x, y), s, font=f, fill=fill, anchor=anchor); return width(f, s)
    cx = x
    for c in s: d.text((cx, y), c, font=f, fill=fill, anchor=anchor); cx += f.getlength(c) + ls
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
def fit(path, s, frm, to, max_w):
    for size in range(frm, to - 1, -1):
        if width(font(path, size), s) <= max_w: return size, True
    return to, False
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def asset(n): return Image.open(os.path.join(HERE, "assets", n)).convert("RGBA")
def paste_center(base, im, cx, cy, ax, ay): base.alpha_composite(im, (int(round(cx - ax)), int(round(cy - ay))))

# ---------- primitives ----------
def shade(base, top, bottom, reach=1550):
    y1 = max(0, top - 160); y2 = min(H, top - 160 + bottom - top + 320)
    hx = Image.new("L", (W, 1)); px = []
    for x in range(W):
        u = (x + 0.5) / reach
        a = 0.0 if u >= 1 else (0.78 + (0.62 - 0.78) * u / 0.4 if u < 0.4 else 0.62 * (1 - (u - 0.4) / 0.6))
        px.append(int(round(a * 255)))
    hx.putdata(px); hx = hx.resize((W, H), Image.NEAREST)
    vy = Image.new("L", (1, H)); vv = []
    span = bottom - top + 320; f = 160
    for y in range(H):
        if y < y1 or y >= y2: vv.append(0); continue
        u = y + 0.5 - (top - 160)
        vv.append(int(round(255 * (min(1, u / f) if u < f else (min(1, (span - u) / f) if u > span - f else 1)))))
    vy.putdata(vv); vy = vy.resize((W, H), Image.NEAREST)
    from PIL import ImageChops
    m = ImageChops.multiply(hx, vy)
    lay = Image.new("RGBA", (W, H), (7, 7, 11, 0)); lay.putalpha(m); base.alpha_composite(lay)

def label(base, x, y, s):
    d = ImageDraw.Draw(base); d.rectangle((x, y - 24, x + 21, y - 3), fill=LIME)
    text(d, x + 40, y, s.upper(), font(F_BOLD, 30), INK, 6)

def panel(base, x, y, w, h, a=0.9):
    sh = layer(); ImageDraw.Draw(sh).rectangle((x, y + 10, x + w - 1, y + h + 10 - 1), fill=(0, 0, 0, 140))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    lay = layer(); d = ImageDraw.Draw(lay)
    d.rectangle((x, y, x + w - 1, y + h - 1), fill=(7, 7, 11, int(round(a * 255))))
    base.alpha_composite(lay)
    ImageDraw.Draw(base).rectangle((x, y, x + w - 1, y + h - 1), outline=(42, 42, 53, 255), width=2)

def ss_patch(size, fn):
    """Draw at 4× and downsample, so thin icon strokes are antialiased like canvas."""
    S = 4; im = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0)); fn(ImageDraw.Draw(im), S)
    return im.resize((size, size), Image.LANCZOS)

def arc_pts(cx, cy, r, a0, a1, n=48): return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * r) for i in range(n + 1)]

def ep_icon(base, kind, cx, cy, s, col=INK):
    P = int(s * 2)
    def fn(d, S):
        c = P * S / 2; r = s / 2 * S; lw = max(3, s * 0.1) * S
        L = lambda pts, close=False: d.line(pts + ([pts[0]] if close else []), fill=col, width=int(round(lw)), joint="curve")
        if kind == "pin":
            pts = arc_pts(c, c - r * 0.25, r * 0.55, math.pi * 0.85, math.pi * 2.15) + [(c, c + r * 0.85)]
            L(pts, True); rr = r * 0.17; d.ellipse((c - rr, c - r * 0.25 - rr, c + rr, c - r * 0.25 + rr), fill=col)
        elif kind == "clock":
            L(arc_pts(c, c, r * 0.8, 0, math.pi * 2, 64)); L([(c, c - r * 0.45), (c, c), (c + r * 0.35, c + r * 0.2)])
        elif kind == "person":
            L(arc_pts(c, c - r * 0.35, r * 0.32, 0, math.pi * 2, 48))
            q = [(c - r * 0.7, c + r * 0.45)]
            for i in range(1, 21):
                t = i / 20; x0, y0 = c - r * 0.7, c + r * 0.45; x1, y1 = c, c - r * 0.05; x2, y2 = c + r * 0.7, c + r * 0.45
                q.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2))
            L([(c - r * 0.7, c + r * 0.8)] + q + [(c + r * 0.7, c + r * 0.8)])
        elif kind in ("item", "quest"):
            L([(c, c - r * 0.8), (c + r * 0.8, c), (c, c + r * 0.8), (c - r * 0.8, c)], True)
            if kind == "quest":
                d.rectangle((c - r * 0.07, c - r * 0.4, c + r * 0.07, c + r * 0.05), fill=col); d.rectangle((c - r * 0.07, c + r * 0.18, c + r * 0.07, c + r * 0.32), fill=col)
        elif kind == "enemy":
            L([(c - r * 0.7, c - r * 0.6), (c + r * 0.7, c - r * 0.6), (c + r * 0.55, c + r * 0.35), (c + r * 0.25, c + r * 0.35), (c + r * 0.2, c + r * 0.75), (c - r * 0.2, c + r * 0.75), (c - r * 0.25, c + r * 0.35), (c - r * 0.55, c + r * 0.35)], True)
            d.rectangle((c - r * 0.42, c - r * 0.25, c - r * 0.14, c - r * 0.01), fill=col); d.rectangle((c + r * 0.14, c - r * 0.25, c + r * 0.42, c - r * 0.01), fill=col)
    base.alpha_composite(ss_patch(P, fn), (int(round(cx - P / 2)), int(round(cy - P / 2))))

def tone_icon(base, tone, x, y, s):
    P = int(s * 2)
    def fn(d, S):
        ox, oy = (P * S - s * S) / 2, P * S / 2; lw = int(round(s * 0.16 * S)); X = lambda v: ox + v * S
        if tone == "warn":
            d.line([(X(0), oy - s / 2 * S), (X(s), oy + s / 2 * S)], fill=PINK, width=lw); d.line([(X(s), oy - s / 2 * S), (X(0), oy + s / 2 * S)], fill=PINK, width=lw)
        else:
            d.line([(X(0), oy), (X(s * 0.38), oy + s * 0.4 * S), (X(s), oy - s * 0.45 * S)], fill=INK, width=lw, joint="curve")
    base.alpha_composite(ss_patch(P, fn), (int(round(x - (P - s) / 2)), int(round(y - P / 2))))

# ---------- tokens with [KEY] keycaps ----------
def tokens(s): return re.findall(r"\[[^\]]+\]|[^\s\[]+", s or "")
def glue(t): return re.match(r"^[,.;:!?…)»]", t) is not None
def tok_w(t, fs):
    if t.startswith("["): return width(font(F_BOLD, round(fs * 0.8)), t[1:-1]) + 26
    return width(font(F_MED, fs), t)
def wrap_tok(s, fs, max_w, max_lines):
    sp = width(font(F_MED, fs), " "); lines, cur, cw = [], [], 0
    for t in tokens(s):
        w_ = tok_w(t, fs); g = 0 if glue(t) else sp
        if cur and cw + g + w_ > max_w: lines.append(cur); cur = [t]; cw = w_
        else: cw += (g if cur else 0) + w_; cur.append(t)
    if cur: lines.append(cur)
    lw = lambda l: sum(tok_w(t, fs) + (sp if i and not glue(t) else 0) for i, t in enumerate(l))
    return lines if len(lines) <= max_lines and all(lw(l) <= max_w for l in lines) else None
def draw_tok_line(base, line, x, y, fs, col):
    d = ImageDraw.Draw(base); f = font(F_MED, fs); sp = width(f, " "); cx = x
    for i, t in enumerate(line):
        if i and glue(t): cx -= sp
        if t.startswith("["):
            k = t[1:-1]; w_ = tok_w(t, fs); h = fs * 1.2; top = y - fs * 0.92
            d.rectangle((round(cx + 0.5), round(top), round(cx + w_ - 0.5), round(top + h)), outline=col, width=2)
            fk = font(F_BOLD, round(fs * 0.8)); d.text((cx + w_ / 2, top + h / 2 + fs * 0.28), k, font=fk, fill=col, anchor="ms")
            cx += w_ + sp
        else:
            d.text((cx, y), t, font=f, fill=col, anchor="ls"); cx += width(f, t) + sp

# ---------- components ----------
def chapter(base, it, E):
    x, y = A["TL"][:2]
    title = (it.get("title") or "").upper()
    size, lines, ok = fit_wrap(F_DISP, title, 112, 64, LANE, 2)
    if not ok: E.append("Назва розділу не влазить у 2 рядки. До 4 слів.")
    top = y + 74; b0 = top + size * 0.76; lh = size * 1.02
    last_b = b0 + (len(lines) - 1) * lh; bar_y = last_b + 36; sub_b = bar_y + 74
    sub = (it.get("sub") or "").strip()
    shade(base, y, (sub_b if sub else bar_y + 10) + 10)
    n = str(it.get("n") or "").strip()
    label(base, x, y + 40, ("РОЗДІЛ " + n.zfill(2)) if n else "РОЗДІЛ")
    d = ImageDraw.Draw(base); f = font(F_DISP, size)
    for i, l in enumerate(lines): d.text((x - 4, b0 + i * lh), l, font=f, fill=INK, anchor="ls")
    d.rectangle((x, round(bar_y), x + 159, round(bar_y) + 9), fill=LIME)
    if sub: text(d, x, sub_b, sub.upper(), font(F_MED, 32), SMOKE, 3)

def goal(base, it, E):
    x, y = A["TL"][:2]
    items = [s.strip() for s in (it.get("items") or []) if s and s.strip()]
    if len(items) > 3: E.append("Мета: максимум 3 пункти."); items = items[:3]
    if not items: E.append("Мета без пунктів.")
    row = 82; top = y + 84; bottom = top + len(items) * row
    shade(base, y, bottom); label(base, x, y + 40, it.get("label") or "СЬОГОДНІ")
    d = ImageDraw.Draw(base)
    for i, t in enumerate(items):
        ry = top + i * row
        d.rectangle((x, ry, x + 42, ry + 42), outline=INK, width=3)
        fs, ok = fit(F_BOLD, t, 46, 32, LANE - 72)
        if not ok: E.append(f"Пункт мети «{t}» задовгий.")
        d.text((x + 72, ry + 36), t, font=font(F_BOLD, fs), fill=INK, anchor="ls")

def verdict(base, it, E):
    x, y = A["TL"][:2]
    items = [v for v in (it.get("items") or []) if (v.get("t") or "").strip()][:3]
    row = 76; top = y + 84; cost_top = top + len(items) * row + 40; num_b = cost_top + 44 + 190
    shade(base, y, num_b + 20); label(base, x, y + 40, "ПІДСУМОК")
    d = ImageDraw.Draw(base)
    for i, v in enumerate(items):
        ry = top + i * row; ok_ = v.get("ok", True) is not False; t = v["t"].strip()
        tone_icon(base, "ok" if ok_ else "warn", x + 4, ry + 20, 34)
        fs, okf = fit(F_BOLD, t, 44, 30, LANE - 70)
        if not okf: E.append(f"Пункт підсумку «{t}» задовгий.")
        ImageDraw.Draw(base).text((x + 62, ry + 34), t, font=font(F_BOLD, fs), fill=INK if ok_ else PINK, anchor="ls")
    d = ImageDraw.Draw(base); text(d, x, cost_top + 30, "ЦІНА", font(F_BOLD, 30), SMOKE, 6)
    num = str(int(it.get("cost") or 0)); f = font(F_DISP, 200)
    d.text((x - 8, num_b), num, font=f, fill=INK, anchor="ls"); nw = width(f, num)
    e = it.get("emotion") or "cry"
    paste_center(base, asset(f"verdict_{e}.png"), x + nw + 40 + 170, num_b - 78, 320, 220)

def caption(base, it, E):
    ax, ay, al, _ = A[it.get("anchor") or "TL"]
    txt = (it.get("text") or "").upper(); sub = (it.get("sub") or "").upper(); icon = (it.get("icon") or "none") != "none"; Hh = 76
    tw = width(font(F_BOLD, 34), txt, 2); sw = width(font(F_MED, 26), sub, 2) + 40 if sub else 0
    w_ = (Hh if icon else 0) + tw + 52
    if w_ > LANE: E.append("Підпис задовгий: до ~30 знаків.")
    x0 = ax - max(w_, sw) / 2 if al == "center" else ax; y0 = ay
    sh = layer(); ImageDraw.Draw(sh).rectangle((x0, y0 + 8, x0 + w_ - 1, y0 + Hh + 8 - 1), fill=(0, 0, 0, 140)); base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(15)))
    d = ImageDraw.Draw(base); d.rectangle((round(x0), y0, round(x0 + w_) - 1, y0 + Hh - 1), fill=INK)
    if icon:
        lay = layer(); ImageDraw.Draw(lay).rectangle((round(x0), y0, round(x0) + Hh - 1, y0 + Hh - 1), fill=(7, 7, 11, 235)); base.alpha_composite(lay)
        ep_icon(base, it["icon"], x0 + Hh / 2, y0 + Hh / 2, 40)
    text(ImageDraw.Draw(base), x0 + (Hh if icon else 0) + 26, y0 + 50, txt, font(F_BOLD, 34), VOID, 2)
    if sub:
        sx = ax - sw / 2 if al == "center" else x0
        lay = layer(); ImageDraw.Draw(lay).rectangle((round(sx), y0 + Hh, round(sx + sw) - 1, y0 + Hh + 51), fill=(7, 7, 11, 224)); base.alpha_composite(lay)
        text(ImageDraw.Draw(base), sx + 20, y0 + Hh + 35, sub, font(F_MED, 26), SMOKE, 2)

def hint(base, it, E):
    ax, ay, al, bottom = A[it.get("anchor") or "TL"]
    Wp, pad, fs, lh = 880, 36, 38, 54
    lines = wrap_tok(it.get("text") or "", fs, Wp - pad * 2, 3)
    if not lines: E.append("Порада задовга: максимум 3 рядки, ~14 слів."); lines = wrap_tok(it.get("text") or "", fs, Wp - pad * 2, 9) or [tokens(it.get("text"))]
    h = pad + 40 + 26 + len(lines) * lh + pad - 18
    x0 = ax - Wp / 2 if al == "center" else ax; y0 = ay - h if bottom else ay
    x0, y0 = round(x0), round(y0)
    panel(base, x0, y0, Wp, h)
    tag = (it.get("label") or "ПОРАДА").upper(); f24 = font(F_BOLD, 24); tgw = width(f24, tag, 4) + 28
    d = ImageDraw.Draw(base); d.rectangle((x0 + pad, y0 + pad, round(x0 + pad + tgw) - 1, y0 + pad + 39), fill=LIME)
    text(d, x0 + pad + 14, y0 + pad + 29, tag, f24, VOID, 4)
    for i, l in enumerate(lines): draw_tok_line(base, l, x0 + pad, y0 + pad + 40 + 26 + 38 + i * lh, fs, INK)

def translate(base, it, E):
    Wp, pad = 1150, 30
    t = it.get("text") or ""
    size, lines, ok = fit_wrap(F_BOLD, t, 40, 30, Wp - pad * 2, 2)
    if not ok: E.append("Переклад задовгий: 2 рядки максимум.")
    lh = size * 1.32; has_o = bool((it.get("original") or "").strip())
    h = pad + 30 + 22 + len(lines) * lh + (44 if has_o else 0) + pad - 12
    x0 = round(1280 - Wp / 2); y0 = round(1120 - h)
    panel(base, x0, y0, Wp, round(h), 0.88)
    d = ImageDraw.Draw(base); d.rectangle((x0 + pad, y0 + pad, x0 + pad + 53, y0 + pad + 29), fill=INK)
    d.text((x0 + pad + 12, y0 + pad + 23), "UA", font=font(F_BOLD, 22), fill=VOID, anchor="ls")
    text(d, x0 + pad + 72, y0 + pad + 24, (it.get("speaker") or "").upper(), font(F_BOLD, 24), SMOKE, 3)
    f = font(F_BOLD, size)
    for i, l in enumerate(lines): d.text((x0 + pad, y0 + pad + 30 + 22 + size * 0.82 + i * lh), l, font=f, fill=INK, anchor="ls")
    if has_o:
        o = "EN · " + it["original"].strip(); f24 = font(F_MED, 24)
        while width(f24, o) > Wp - pad * 2 and len(o) > 8: o = o[:-2].rstrip() + "…"
        d.text((x0 + pad, y0 + h - pad + 2), o, font=f24, fill=SMOKE, anchor="ls")

def counter(base, it, E):
    ax, ay = A["BL"][:2]; txt = "×" + str(int(it.get("count") or 1)).zfill(2)
    f = font(F_BOLD, 52); tw = width(f, txt); h = 96; w_ = round(24 + 120 + 16 + tw + 30); y0 = ay - h
    panel(base, ax, y0, w_, h, 0.88)
    paste_center(base, asset(f"counter_{it.get('emotion') or 'cry'}.png"), ax + 24 + 60, y0 + h / 2 + 4, 120, 90)
    ImageDraw.Draw(base).text((ax + 24 + 120 + 16, y0 + 66), txt, font=f, fill=INK, anchor="ls")

DRAW = {"chapter": chapter, "goal": goal, "verdict": verdict, "caption": caption, "hint": hint, "translate": translate, "counter": counter}

def render_item(it):
    base = layer(); E = []; DRAW[it["type"]](base, it, E); return base, E

# ---------- input ----------
def parse_line(code, rest):
    C = code.upper(); r = rest.strip()
    def cap(icon, anchor="TL"):
        t, _, s = r.partition(" / "); return {"type": "caption", "anchor": anchor, "icon": icon, "text": t.strip(), "sub": s.strip()}
    if C == "CH":
        m = re.match(r"^(\d+)\s+(.*)$", r); body = m.group(2) if m else r; t, _, s = body.partition(" / ")
        return {"type": "chapter", "n": int(m.group(1)) if m else "", "title": t.strip(), "sub": s.strip()}
    if C == "GOAL": return {"type": "goal", "items": [x.strip() for x in r.split(";") if x.strip()]}
    if C in ("CAP", "LOC"): return cap("pin")
    if C == "TIME": return cap("clock", "TC")
    if C == "WHO": return cap("person")
    if C == "ITEM": return cap("item")
    if C == "ENEMY": return cap("enemy")
    if C == "QUEST": return cap("quest")
    if C == "TIP": return {"type": "hint", "anchor": "TL", "text": r}
    if C == "MEME":
        key = r.strip().lower().replace(" ", "_")
        for k, v in MEMES.items():
            if key == k or r.strip().upper().rstrip(".") == v: return {"type": "meme", "name": k}
        return {"type": "meme", "name": key}
    if C == "TR":
        i = r.find(":"); return {"type": "translate", "speaker": r[:i].strip() if i > 0 else "", "text": (r[i + 1:] if i > 0 else r).strip(), "original": ""}
    if C == "QQ": return {"type": "counter", "count": int(re.sub(r"\D", "", r) or 1), "emotion": "cry"}
    if C == "VERDICT":
        parts = [p.strip() for p in r.split(";") if p.strip()]; cost = 0
        if parts and parts[-1].isdigit(): cost = int(parts.pop())
        items = [{"t": re.sub(r"^[+-]\s*", "", p), "ok": not p.startswith("-")} for p in parts[:3]]
        return {"type": "verdict", "items": items, "cost": cost, "emotion": "dead" if cost >= 5 else "cry"}
    return None

def parse_text(txt):
    out, last_tc, unknown = [], "", []
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"): continue
        tcs = re.findall(r"\b\d{2}:\d{2}:\d{2}[:;]\d{2}\b", line); mk = re.search(r"\|M:([^|]*)", line)
        if mk: tc, body = last_tc, mk.group(1).strip()
        elif len(tcs) >= 4: last_tc = tcs[0]; continue
        else:
            m = re.match(r"^(\d{1,2}:\d{2}(?::\d{2})?(?:[:;]\d{2})?)\s+(.*)$", line)
            tc, body = (m.group(1), m.group(2)) if m else ("", line)
        m2 = re.match(r"^([A-Za-z]+)\s*[:\-]?\s+(.*)$", body)
        if not m2: unknown.append(line); continue
        it = parse_line(m2.group(1), m2.group(2))
        if it: it["tc"] = tc; out.append(it)
        else: unknown.append(line)
    return out, unknown

def load(path):
    with open(path, encoding="utf-8", errors="replace") as fh: s = fh.read()
    if path.lower().endswith(".json"):
        data = json.loads(s); items = data["items"] if isinstance(data, dict) else data; return items, []
    return parse_text(s)

def words(s): return len([w for w in re.split(r"\s+", s or "") if w])
def duration(it):
    t = it["type"]
    if t in ("hint", "translate"): return max(3.0, 1 + 0.4 * words(it.get("text")))
    return {"chapter": 3.0, "goal": 5.5, "verdict": 6.0, "caption": 3.0, "counter": 2.0, "meme": 1.6}.get(t, 3.0)
def tc_s(tc):
    m = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})(?:[:;](\d{2}))?$", tc or "")
    if m: return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + (int(m.group(4)) / 60 if m.group(4) else 0)
    m = re.match(r"^(\d{1,3}):(\d{2})$", tc or "")
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None
def fmt(sec): sec = int(sec); return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"

def density(items):
    """Errors for graphics that would nag the viewer. Timecodes are required."""
    E = []
    secs = [tc_s(it.get("tc")) for it in items]
    if any(x is None for x in secs):
        E.append("У кожної картки має бути таймкод (00:12:30:00) — без нього не перевірити, чи графіки не забагато."); return E
    if secs and min(secs) >= 3600: secs = [x - 3600 for x in secs]  # Resolve timelines start at 01:00:00:00
    ev = sorted(zip(secs, items), key=lambda p: p[0])
    for i, (t, it) in enumerate(ev):
        if t < HOOK_S: E.append(f"{fmt(t)} {TYPE_UA[it['type']]}: перші {HOOK_S} с — гачок епізоду, без карток.")
        if i:
            pt, pit = ev[i - 1]
            if t < pt + duration(pit) + MIN_GAP_S: E.append(f"{fmt(t)} {TYPE_UA[it['type']]} накладається на {TYPE_UA[pit['type']]} з {fmt(pt)} (та триває ~{duration(pit):.0f} с). Одна картка на екрані за раз.")
        n = sum(1 for t2, _ in ev if t <= t2 < t + WINDOW_S)
        if n > WINDOW_MAX: E.append(f"{fmt(t)}: {n} карток за хвилину, максимум {WINDOW_MAX}. Прибери зайве — графіка має допомагати, а не смикати.")
        n10 = sum(1 for t2, _ in ev if t <= t2 < t + 600)
        if n10 > TEN_MIN_MAX: E.append(f"{fmt(t)}: {n10} карток за 10 хвилин, максимум {TEN_MIN_MAX}.")
    memes = [t for t, it in ev if it["type"] == "meme"]
    for a, b in zip(memes, memes[1:]):
        if b - a < MEME_GAP_S: E.append(f"{fmt(b)}: мем-штамп через {int(b - a)} с після попереднього. Між мемами щонайменше 5 хвилин.")
    types = [it["type"] for _, it in ev]
    if "goal" in types and types[0] != "goal": E.append("Мета епізоду — перша картка, одразу після гачка й інтро.")
    if "verdict" in types and types[-1] != "verdict": E.append("Підсумок — остання картка, перед аутро.")
    return list(dict.fromkeys(E))

def validate(items, unknown):
    E, Wn = [], []
    for u in unknown: Wn.append(f"Рядок без відомого коду пропущено: «{u[:60]}»")
    if not items: E.append("Жодної картки. Перевір коди: CH, GOAL, CAP, TIME, WHO, LOC, ITEM, ENEMY, QUEST, TIP, TR, QQ, VERDICT.")
    for t, n in LIMITS.items():
        c = sum(1 for i in items if i.get("type") == t)
        if c > n: E.append(f"{TYPE_UA[t].capitalize()}: {c} на епізод, максимум {n}.")
    if items and all(i.get("type") in DRAW or i.get("type") == "meme" for i in items): E += density(items)
    for k, it in enumerate(items):
        tag = f"Картка {k + 1} ({TYPE_UA.get(it.get('type'), it.get('type'))}{' ' + it['tc'] if it.get('tc') else ''})"
        t = it.get("type")
        if t == "meme":
            if it.get("name") not in MEMES: E.append(f"{tag}: невідомий мем-штамп «{it.get('name')}». Є: {', '.join(MEMES)}.")
            continue
        if t not in DRAW: E.append(f"{tag}: невідомий тип."); continue
        an = it.get("anchor") or ALLOWED[t][0]
        if an not in ALLOWED[t]: E.append(f"{tag}: місце {an} не дозволене. Можна: {', '.join(ALLOWED[t])}.")
        if t == "caption":
            if (it.get("icon") or "none") not in ICONS: E.append(f"{tag}: icon — один з {', '.join(ICONS)}.")
            if not (it.get("text") or "").strip(): E.append(f"{tag}: порожній текст.")
        if t == "chapter":
            if not (it.get("title") or "").strip(): E.append(f"{tag}: немає назви.")
            elif len(it["title"].split()) > 4: E.append(f"{tag}: назва довша за 4 слова.")
        if t in ("hint", "translate") and not (it.get("text") or "").strip(): E.append(f"{tag}: порожній текст.")
        if t == "translate" and not (it.get("speaker") or "").strip(): Wn.append(f"{tag}: не вказано, хто говорить (TR Ім'я: текст).")
        if t in ("verdict", "counter") and (it.get("emotion") or "cry") not in EMOTIONS: E.append(f"{tag}: emotion — одна з {', '.join(EMOTIONS)}.")
        _, e2 = render_item(it)
        E += [f"{tag}: {e}" for e in e2]
    return E, Wn

def slug(s): return (re.sub(r"[^0-9a-zа-яіїєґ]+", "-", (s or "").lower()).strip("-")[:32]) or "card"
def short(it):
    t = it["type"]
    if t == "meme": return MEMES.get(it.get("name"), "")
    if t == "goal": return " · ".join(x for x in (it.get("items") or []) if isinstance(x, str))
    if t == "verdict": return f"ціна {it.get('cost', 0)}"
    if t == "counter": return f"×{it.get('count', 1)}"
    return (it.get("title") if t == "chapter" else it.get("text")) or ""
def name_of(it, i): return f"{(it.get('tc') or str(i + 1).zfill(2)).replace(':', '-').replace(';', '-')}_{it['type']}_{slug(short(it))}.png"

def cmd_render(a):
    items, unknown = load(a.script)
    E, Wn = validate(items, unknown)
    for w_ in Wn: print("УВАГА:", w_)
    if E:
        for e in E: print("ПОМИЛКА:", e)
        print(f"\nЗупинено: {len(E)} помилок. Виправ файл і запусти знову."); sys.exit(2)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.script)), "kirqqn_titles"); os.makedirs(out, exist_ok=True)
    thumbs = []
    bg = Image.open(os.path.join(HERE, "examples", "example_hud.jpg")).convert("RGBA").resize((W, H))
    for i, it in enumerate(items):
        if it["type"] == "meme": continue
        im, _ = render_item(it); n = name_of(it, i); im.save(os.path.join(out, n)); print("готово:", n)
        t = bg.copy(); t.alpha_composite(im); thumbs.append(t.convert("RGB").resize((480, 270), Image.LANCZOS))
    cols = 4; rows = math.ceil(len(thumbs) / cols); sheet = Image.new("RGB", (cols * 492 + 12, rows * 282 + 12), (20, 20, 26))
    for i, t in enumerate(thumbs): sheet.paste(t, (12 + (i % cols) * 492, 12 + (i // cols) * 282))
    sheet.save(os.path.join(out, "preview.jpg"), quality=88)
    lines = ["kirQQn · титри епізоду", "", *[(f"{it.get('tc')}  —  мем-штамп: stamp_{it['name']}.mov з kirQQn_resolve_pack (V3, серединою на моменті)" if it["type"] == "meme" else f"{name_of(it, i)}  —  {TYPE_UA[it['type']]}: {short(it)}") for i, it in enumerate(items)], "",
             "Resolve: PNG на доріжку V2 над геймплеєм. Таймлайн 2560×1440 — без масштабування.",
             "Розділ, мета, підсумок: ep_card_in.mov на V3 з початку картки (PNG з’являється на 0,22 с), ep_card_out.mov у кінці.",
             "Підпис, порада, переклад, лічильник: ручки фейду на кліпі, 4 кадри на вхід і вихід.",
             "Тривалість: розділ 2,5–3 с; підпис 3 с; порада й переклад — 1 с + 0,4 с на слово; мета й підсумок 5–6 с."]
    with open(os.path.join(out, "ЯК_ЗІБРАТИ.txt"), "w", encoding="utf-8") as fh: fh.write("\n".join(lines) + "\n")
    print(f"\nГотово: {len(items)} карток у {out}")

def cmd_check(a):
    items, unknown = load(a.script); E, Wn = validate(items, unknown)
    for w_ in Wn: print("УВАГА:", w_)
    for e in E: print("ПОМИЛКА:", e)
    print("OK — можна рендерити." if not E else f"{len(E)} помилок."); sys.exit(2 if E else 0)

def cmd_counters(a):
    out = a.out or "kirqqn_qq_counter"; os.makedirs(out, exist_ok=True)
    for n in range(1, 31):
        im, _ = render_item({"type": "counter", "count": n, "emotion": "dead" if n >= 10 else "cry"}); im.save(os.path.join(out, f"qq_counter_{n:02d}.png"))
    print(f"Готово: 30 лічильників у {out}")

def main():
    ap = argparse.ArgumentParser(description="kirQQn — титри епізодів 2560×1440")
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("render"); r.add_argument("script"); r.add_argument("--out"); r.set_defaults(fn=cmd_render)
    c = sp.add_parser("check"); c.add_argument("script"); c.set_defaults(fn=cmd_check)
    q = sp.add_parser("counters"); q.add_argument("--out"); q.set_defaults(fn=cmd_counters)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
