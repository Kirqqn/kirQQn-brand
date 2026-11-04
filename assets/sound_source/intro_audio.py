# Synthesized sound design for the kirQQn intro, locked to timing.json.
# python3 audio.py full out.wav | python3 audio.py short out.wav
import json, sys, math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

T = json.load(open('timing.json'))
MODE, OUT = sys.argv[1], sys.argv[2]
SHORT = MODE == 'short'
SR = 48000
DUR = T['duration']
N = int(DUR * SR) + SR  # tail room
L = np.zeros(N); R = np.zeros(N); WL = np.zeros(N); WR = np.zeros(N)
rs = np.random.default_rng(3)

def ok(t):  # skip events that belong to the cut-away part of the short version
    return not (SHORT and t < T['shortStart'] + 0.04)

def add(sig, t0, gain=1.0, pan=0.0, wet=0.0, dry=1.0):
    if not ok(t0) and not getattr(add, 'force', False):
        return
    i0 = int(round(t0 * SR));
    if i0 < 0: sig = sig[-i0:]; i0 = 0
    n = min(len(sig), N - i0)
    if n <= 0: return
    s = sig[:n] * gain
    gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    L[i0:i0 + n] += s * gl * dry; R[i0:i0 + n] += s * gr * dry
    if wet: WL[i0:i0 + n] += s * gl * wet; WR[i0:i0 + n] += s * gr * wet

def tt(d): return np.arange(int(d * SR)) / SR
def sine_f(f):  # f: array of instantaneous freq
    return np.sin(2 * np.pi * np.cumsum(f) / SR)
def env_ad(d, a, tau):
    t = tt(d); e = np.exp(-t / tau)
    if a > 0: e *= np.clip(t / a, 0, 1)
    return e
def noise(d): return rs.standard_normal(int(d * SR))
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def svf_sweep(x, f0, f1, q=4.0, curve=2.0):
    # time-varying state variable bandpass
    n = len(x); y = np.zeros(n); low = band = 0.0
    p = (np.arange(n) / max(1, n - 1)) ** curve
    f = f0 * (f1 / f0) ** p
    F = 2 * np.sin(np.pi * np.minimum(f, SR / 6) / SR); Q = 1 / q
    for i in range(n):
        low += F[i] * band; high = x[i] - low - Q * band; band += F[i] * high; y[i] = band
    return y
def square(f, d, duty=0.5):
    ph = np.cumsum(np.full(int(d * SR), f) if np.isscalar(f) else f) / SR
    return np.where((ph % 1) < duty, 1.0, -1.0)
def saw(f, d):
    ph = np.cumsum(np.full(int(d * SR), f) if np.isscalar(f) else f) / SR
    return 2 * (ph % 1) - 1

# ---------- building blocks ----------
def blip(f, d=0.018, g=0.12, pan=0.0, t0=0.0, wet=0.15):
    s = square(f, d, 0.3) * env_ad(d, 0.001, d / 3); add(lp(s, 6000), t0, g, pan, wet)
def kick(t0, g=1.0, f0=150, f1=42, d=0.9, tau=0.28):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    s = np.tanh(2.2 * sine_f(f) * np.exp(-t / tau)); add(s, t0, g)
    add(hp(noise(0.012), 2000) * env_ad(0.012, 0, 0.003), t0, 0.35 * g)
def clap(t0, g=0.5, wet=0.4):
    s = np.zeros(int(0.35 * SR))
    for k, o in enumerate([0, 0.009, 0.018, 0.028]):
        n = bp(noise(0.3), 900, 5000) * env_ad(0.3, 0, 0.012 if k < 3 else 0.09); i = int(o * SR); s[i:i + len(n)] += n[:len(s) - i]
    add(s, t0, g, 0, wet)
def glass(t0, n=70, spread=0.7, g=0.5):
    for _ in range(n):
        o = rs.random() ** 1.8 * spread; f = rs.uniform(2400, 9500); d = rs.uniform(0.03, 0.16)
        s = np.sin(2 * np.pi * f * tt(d)) * env_ad(d, 0.0005, d / 4) + 0.3 * np.sin(2 * np.pi * f * 2.71 * tt(d)) * env_ad(d, 0, d / 8)
        add(s, t0 + o, g * (1 - o / spread * 0.7) * rs.uniform(0.3, 1), rs.uniform(-0.9, 0.9), 0.35)
    nz = hp(noise(0.6), 3500) * env_ad(0.6, 0.002, 0.12); add(nz, t0, 0.35 * g, 0, 0.3)
def whoosh(t0, d, lo, hi, g=0.4, pan0=0.0, pan1=0.0, q=3.0, rev=False):
    x = svf_sweep(noise(d), lo, hi, q, 1.5) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** (0.7)
    if rev: x = x * np.linspace(0.2, 1, len(x)) ** 2
    seg = 8
    for k in range(seg):
        a, b = k * len(x) // seg, (k + 1) * len(x) // seg
        add(x[a:b], t0 + a / SR, g, pan0 + (pan1 - pan0) * (k + 0.5) / seg, 0.25)
def stab(t0, notes, d=0.5, g=0.25, cutoff=(4000, 500), wet=0.5, detune=0.006):
    t = tt(d); s = np.zeros(len(t))
    for n in notes:
        f = 440 * 2 ** ((n - 69) / 12)
        for dt in (-detune, 0, detune): s += saw(f * (1 + dt), d)
    cf = np.geomspace(cutoff[0], cutoff[1], len(t))
    # cheap filter sweep: crossfade between two lowpasses
    a, b = lp(s, cutoff[0]), lp(s, cutoff[1]); m = np.linspace(0, 1, len(t)) ** 0.5
    s = (a * (1 - m) + b * m) * env_ad(d, 0.003, d / 3) / (len(notes) * 3)
    add(s, t0, g, 0, wet)
def glitch_burst(t0, d, g=0.25, seed=0):
    r = np.random.default_rng(seed); i = 0.0
    while i < d:
        sl = r.uniform(0.012, 0.035)
        kind = r.integers(0, 3)
        if kind == 0: s = square(r.uniform(80, 900), sl, r.uniform(0.1, 0.5))
        elif kind == 1: s = np.round(noise(sl) * 2) / 2
        else: s = np.sin(2 * np.pi * r.uniform(1000, 4000) * tt(sl))
        s = s * env_ad(sl, 0.001, sl)
        if r.random() < 0.8: add(lp(s, 7000), t0 + i, g * r.uniform(0.5, 1), r.uniform(-0.6, 0.6), 0.1)
        i += sl
def plip(t0, f0=900, f1=2300, g=0.35, pan=0):
    d = 0.09; t = tt(d); f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.012))
    add(sine_f(f) * env_ad(d, 0.001, 0.025), t0, g, pan, 0.45)
    add(bp(noise(0.08), 2000, 8000) * env_ad(0.08, 0.002, 0.02), t0 + 0.004, g * 0.35, pan, 0.3)

# ---------- timeline ----------
if not SHORT:
    # CRT on
    t0 = T['crtOn']
    add(hp(noise(0.02), 800) * env_ad(0.02, 0, 0.004), t0, 0.5)
    add(sine_f(np.full(int(0.9 * SR), 7800.0)) * env_ad(0.9, 0.05, 0.4), t0, 0.025)
    add(np.tanh(3 * np.sin(2 * np.pi * 60 * tt(0.95))) * env_ad(0.95, 0.05, 0.5), t0, 0.06)
    kick(t0, 0.35, 90, 50, 0.3, 0.06)
    # typing
    for k in range(12): blip(rs.uniform(1100, 1800), t0=T['type1'] + k / 48, g=0.07, pan=-0.2)
    for k in range(23): blip(rs.uniform(1300, 2100), t0=T['type1'] + 0.16 + k / 60, g=0.06, pan=0.2)
    # progress tone that follows the bar
    def barP(x):
        p = np.clip((x - T['barStart']) / (T['barFull'] - T['barStart']), 0, 1)
        return np.select([p < .35, p < .5, p < .6, p < .75], [(1 - (1 - p / .35) ** 3) * .62, .62, .62 + (1 - (1 - (p - .5) / .1) ** 3) * .25, .87], .87 + (1 - (1 - (p - .75) / .25) ** 3) * .13)
    d = T['barFull'] - T['barStart'] + 0.04; tx = T['barStart'] + tt(d)
    f = 220 + 880 * barP(tx)
    add(lp(square(f, d, 0.25), 3000) * env_ad(d, 0.01, 10) * 0.6, T['barStart'], 0.06, 0, 0.1)
    # overflow alarm
    for k in range(4): blip(1320 if k % 2 == 0 else 990, d=0.06, g=0.11, t0=T['error'] + k * 0.065, wet=0.2)
    # riser into the break
    rd = T['hit2'] - 0.03 - 0.35
    whoosh(0.35, rd, 300, 7000, 0.55, q=5, rev=True)
    tr = tt(rd); add(np.tanh(1.5 * saw(90 + 600 * (tr / rd) ** 2.5, rd)) * (tr / rd) ** 2 * 0.5, 0.35, 0.10, 0, 0.1)
    glitch_burst(T['glitchStart'], T['hit1'] - T['glitchStart'] - 0.01, 0.16, 1)
    glitch_burst(T['hit1'] + 0.03, 0.05, 0.2, 2)
    # first hit: crack
    kick(T['hit1'], 0.55, 120, 55, 0.4, 0.08)
    add(hp(noise(0.05), 3000) * env_ad(0.05, 0, 0.01), T['hit1'], 0.6, 0, 0.3)
    glass(T['hit1'], 8, 0.08, 0.25)
    # BREAK
    h = T['hit2']
    kick(h, 1.0, 170, 34, 1.6, 0.5)
    add(np.tanh(2 * noise(0.4)) * env_ad(0.4, 0, 0.07), h, 0.35, 0, 0.3)
    clap(h, 0.45)
    glass(h, 90, 0.75, 0.55)
    stab(h, [45, 52, 57, 60, 64], 1.2, 0.30, (5000, 300))
    # ІГРИ wipe + letter drops
    c = T['cutIgry']
    whoosh(c - 0.16, 0.2, 400, 6000, 0.45, 0.8, -0.6)
    kick(c, 0.8, 160, 45, 0.6, 0.18); clap(c, 0.35)
    for i in range(5):
        tl = c + 0.02 + i * 0.03 + 0.075
        kick(tl, 0.22, 260 - i * 25, 90, 0.15, 0.04)
    stab(c, [57, 60, 64, 69], 0.35, 0.18, (6000, 600))
    # ІНОДІ — hard cut, suspense
    c = T['cutInodi']
    add(hp(noise(0.01), 1000) * env_ad(0.01, 0, 0.002), c, 0.4)
    kick(c, 0.4, 80, 38, 0.8, 0.3)
    for k in range(5): blip(rs.uniform(700, 900), d=0.025, g=0.12, t0=c + 0.05 + k / 17, wet=0.4)
    sd = T['navpaky'] - c; ts = tt(sd)
    add(np.sin(2 * np.pi * (1760 * ts + 220 * ts ** 2)) * (ts / sd) ** 1.5, c, 0.045, 0, 0.5)
    whoosh(c + 0.05, sd - 0.05, 200, 3000, 0.35, q=6, rev=True)
    # НАВПАКИ hit + flip + tape stop
    c = T['navpaky']
    kick(c, 0.9, 160, 40, 0.8, 0.22); clap(c, 0.4)
    stab(c, [52, 55, 59, 64], 0.3, 0.22, (5000, 800))
    fd = T['flipEnd'] - T['flip'] + 0.08; tf = tt(fd)
    f = 330 * (1 - 0.8 * (tf / fd) ** 1.6)
    tape = (saw(f, fd) + saw(f * 1.5, fd) * 0.5) * (1 - tf / fd) ** 0.5
    add(lp(tape, 2500), T['flip'], 0.12, 0, 0.4)
    whoosh(T['flip'], fd, 300, 4000, 0.5, -0.9, 0.9, q=2.5)
    kick(T['flipEnd'], 0.45, 130, 50, 0.4, 0.1)
    glitch_burst(T['flipEnd'], 0.1, 0.16, 3)

# collapse / line
c = T['collapse']
if SHORT:
    add.force = True
    s0 = T['shortStart'] + 0.02
    whoosh(s0 - 0.01, 0.16, 800, 9000, 0.3, -0.5, 0.5, q=4)
    add(np.sin(2 * np.pi * (300 * tt(0.15) + 9000 * tt(0.15) ** 2)) * env_ad(0.15, 0.005, 0.1), s0, 0.07, 0, 0.4)
    add.force = False
else:
    d = 0.12; tz = tt(d)
    add(np.sin(2 * np.pi * (300 * tz + 11000 * tz ** 2)) * env_ad(d, 0.005, 0.08), c, 0.09, 0, 0.4)
    add(hp(noise(0.1), 2000) * env_ad(0.1, 0.03, 0.03), c, 0.12)
# split into two dots
for k, p in enumerate((-0.4, 0.4)):
    blip(1046 if k == 0 else 1318, d=0.05, g=0.07, pan=p, t0=c + 0.2 + k * 0.03, wet=0.5)
# rings charge
d = T['ringsEnd'] - T['rings']; tc = tt(d)
for k, (fa, p) in enumerate(((523, -0.45), (659, 0.45))):
    f = fa * (1 + (tc / d) ** 1.5)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.4 + 0.6 * (tc / d)) * (1 + 0.3 * np.sin(2 * np.pi * 18 * tc))
    add(s, T['rings'], 0.05, p, 0.5)
whoosh(T['rings'], d + 0.1, 500, 8000, 0.3, q=5, rev=True)
for k in range(6): blip(523 * 2 ** ([0, 4, 7, 12, 16, 19][k] / 12), d=0.04, g=0.05, pan=(-0.5 + k / 5), t0=T['rings'] + k * d / 6, wet=0.6)
# LOGO LOCK
c = T['lock']
kick(c, 1.0, 170, 36, 1.4, 0.45)
clap(c, 0.45, 0.6)
add(hp(noise(1.4), 5000) * env_ad(1.4, 0.002, 0.35), c, 0.14, 0, 0.4)
stab(c, [45, 57, 61, 64, 69, 73], 1.6, 0.30, (6000, 900), 0.7)
# pad bed held under the logo
pd = T['crtOff'] - c + 0.1; tp = tt(pd)
pad = np.zeros(len(tp))
for n in (45, 52, 57, 61, 64):
    fr = 440 * 2 ** ((n - 69) / 12)
    for dt in (-0.004, 0.004): pad += saw(fr * (1 + dt), pd)
pad = lp(pad, 1400) * np.clip(tp / 0.4, 0, 1) * np.clip((pd - tp) / 0.05, 0, 1) / 10
add(pad, c + 0.05, 0.10, 0, 0.5)
# sheen glint
whoosh(c + 0.12, 0.55, 3000, 12000, 0.18, -0.6, 0.6, q=8)
add(np.sin(2 * np.pi * 6272 * tt(0.4)) * env_ad(0.4, 0.15, 0.08), c + 0.3, 0.035, 0.3, 0.7)
# HUD + decode ticks
for k in range(3): blip(1760, d=0.03, g=0.05, pan=[-0.7, 0.7, 0][k], t0=T['hudIn'] + 0.05 + k * 0.07, wet=0.3)
for k in range(26):
    if k in (5, 11, 17): continue
    blip(rs.uniform(2000, 3200), d=0.012, g=0.035, pan=-0.6 + 1.2 * k / 25, t0=T['tag'] + 0.12 + (k / 26) * 0.6, wet=0.2)
# tears
tipY, r, tagTop = 538, 15, 685
for k, t0 in enumerate((T['tear1'], T['tear2'])):
    pan = -0.15 if k == 0 else 0.25
    d = T['tearGrow']; tg = tt(d)
    add(np.sin(2 * np.pi * np.cumsum(300 + 500 * (tg / d)) / SR) * env_ad(d, 0.05, 0.12), t0, 0.08, pan, 0.4)
    y0 = tipY + r * 0.9; D = tagTop - r * 0.6 - y0
    hit = t0 + T['tearGrow'] + math.sqrt(2 * D / 2600)
    plip(hit, g=0.4, pan=pan)
    # sad "qq" two-note counter blip
    blip(659 if k == 0 else 622, d=0.08, g=0.06, pan=pan, t0=hit + 0.05, wet=0.5)
    blip(523 if k == 0 else 494, d=0.12, g=0.06, pan=pan, t0=hit + 0.14, wet=0.5)
    kick(hit, 0.15, 120, 60, 0.15, 0.04)
# idle glitches
glitch_burst(T['idle1'], 0.07, 0.10, 4)
glitch_burst(T['idle2'], 0.05, 0.08, 5)
# OUTRO
glitch_burst(T['outGlitch'], T['crtOff'] - T['outGlitch'], 0.2, 6)
d = T['crtOffEnd'] - T['crtOff'] + 0.05; to = tt(d)
f = 40 + 1800 * np.exp(-to / 0.06)
add(np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env_ad(d, 0.002, 0.12), T['crtOff'], 0.22, 0, 0.3)
add(hp(noise(0.015), 1500) * env_ad(0.015, 0, 0.004), T['crtOffEnd'], 0.35)

# ---------- reverb + master ----------
ir_d = 1.3; ti = tt(ir_d)
irL = rs.standard_normal(len(ti)) * np.exp(-ti / 0.32); irR = rs.standard_normal(len(ti)) * np.exp(-ti / 0.32)
irL = lp(irL, 7000); irR = lp(irR, 7000); irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
pre = int(0.018 * SR)
rvL = np.concatenate([np.zeros(pre), fftconvolve(WL, irL)])[:N]; rvR = np.concatenate([np.zeros(pre), fftconvolve(WR, irR)])[:N]
outL = L + 0.55 * rvL; outR = R + 0.55 * rvR
mix = np.stack([outL, outR], 1)
mix = hp(mix.T, 25).T
start = int(T['shortStart'] * SR) if SHORT else 0
end = int(DUR * SR)
mix = mix[start:end]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
fade = int(0.004 * SR); mix[:fade] *= np.linspace(0, 1, fade)[:, None]
mix *= 10 ** (-1 / 20) / np.abs(mix).max()
rms = 20 * np.log10(np.sqrt((mix ** 2).mean()))
print(f'{MODE}: {len(mix)/SR:.2f}s  rms {rms:.1f} dBFS')
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16))
