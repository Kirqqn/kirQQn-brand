import math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
SHORT=False
T={'shortStart':0}
DUR=12.0
SR = 48000
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

