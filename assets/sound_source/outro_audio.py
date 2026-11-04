import sys, math, numpy as np
from scipy.io import wavfile
import sfx
from sfx import *
V, OUT = sys.argv[1], sys.argv[2]
DUR = 12.0
T = dict(on=0.05, pop=0.32, lines=0.42, sub1=0.85, slots=0.9, subRing=1.1, look=3.0, g2=5.0, b2=7.0, g3=7.1, g4=8.6, b3=10.0, out=11.3, off=11.45, offEnd=11.72)
# CRT on
add(hp(noise(0.02), 800) * env_ad(0.02, 0, 0.004), T['on'], 0.4)
glitch_burst(0.0, 0.28, 0.12, 7)
whoosh(0.0, 0.32, 400, 8000, 0.35, q=5, rev=True)
# verdict pop
kick(T['pop'], 1.0, 170, 36, 1.3, 0.45); clap(T['pop'], 0.45, 0.6)
if V == 'win':
    stab(T['pop'], [57, 61, 64, 69, 73], 1.4, 0.3, (6000, 900), 0.7)
    for k, n in enumerate([81, 85, 88, 93]): blip(440 * 2 ** ((n - 69) / 12), d=0.07, g=0.05, pan=-0.4 + k * 0.27, t0=T['pop'] + 0.1 + k * 0.06, wet=0.6)
else:
    stab(T['pop'], [45, 48, 52, 57, 60], 1.4, 0.3, (5000, 500), 0.7)
    fd = 0.6; tf = tt(fd); f = 330 * (1 - 0.7 * (tf / fd) ** 1.4)
    add(lp(saw(f, fd) + 0.5 * saw(f * 1.5, fd), 2200) * (1 - tf / fd) ** 0.6, T['pop'] + 0.15, 0.10, 0, 0.4)
glass(T['pop'], 30, 0.4, 0.3)
# letters landing
for i in range(10): kick(T['lines'] + 0.06 + i * 0.03, 0.12, 240 - i * 10, 90, 0.12, 0.03)
# UI
for k in range(3): blip(1760, d=0.03, g=0.05, pan=0.6, t0=T['slots'] + 0.05 + k * 0.12, wet=0.3)
blip(1318, d=0.06, g=0.06, pan=-0.6, t0=T['subRing'], wet=0.4)
# bed: soft pad + slow pulse, 1.0 .. off
pd = T['off'] - 0.6; tp = tt(pd)
pad = np.zeros(len(tp)); chord = [45, 52, 57, 61, 64] if V == 'win' else [45, 52, 57, 60, 64]
for n in chord:
    fr = 440 * 2 ** ((n - 69) / 12)
    for dt in (-0.004, 0.004): pad += saw(fr * (1 + dt), pd)
pad = lp(pad, 1200) * np.clip(tp / 0.8, 0, 1) * np.clip((pd - tp) / 0.3, 0, 1) / 10
add(pad, 0.6, 0.09, 0, 0.6)
for b in np.arange(1.6, T['out'], 0.8):  # heartbeat-ish pulse
    kick(b, 0.18, 90, 45, 0.3, 0.09)
# eyes: blinks + gaze moves
for t0 in (T['look'] - 0.08, T['b2'], T['b3']): blip(880, d=0.03, g=0.04, t0=t0, wet=0.5)
for t0, p in ((T['look'], 0.5), (T['g2'], 0.5), (T['g3'], -0.5), (T['g4'], 0.5)): whoosh(t0, 0.2, 2000, 6000, 0.06, -p, p, q=6)
# outro
glitch_burst(T['out'], T['off'] - T['out'], 0.18, 8)
d = T['offEnd'] - T['off'] + 0.05; to = tt(d); f = 40 + 1800 * np.exp(-to / 0.06)
add(np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env_ad(d, 0.002, 0.12), T['off'], 0.2, 0, 0.3)
add(hp(noise(0.015), 1500) * env_ad(0.015, 0, 0.004), T['offEnd'], 0.3)
# reverb + master (same chain as the intro)
ti = tt(1.3); rs2 = np.random.default_rng(9)
irL = lp(rs2.standard_normal(len(ti)) * np.exp(-ti / 0.32), 7000); irR = lp(rs2.standard_normal(len(ti)) * np.exp(-ti / 0.32), 7000)
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
L, R, WL, WR = sfx.L, sfx.R, sfx.WL, sfx.WR; N = sfx.N; pre = int(0.018 * SR)
rvL = np.concatenate([np.zeros(pre), fftconvolve(WL, irL)])[:N]; rvR = np.concatenate([np.zeros(pre), fftconvolve(WR, irR)])[:N]
mix = np.stack([L + 0.55 * rvL, R + 0.55 * rvR], 1); mix = hp(mix.T, 25).T[:int(DUR * SR)]
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix *= 10 ** (-1 / 20) / np.abs(mix).max()
wavfile.write(OUT, SR, (mix * 32767).astype(np.int16)); print('ok', OUT)
