#!/usr/bin/env python3
"""scripts/generate_sounds.py — Generate WAV sound effects for desktop-cat.

Output: assets/sounds/*.wav (16-bit mono, 22050 Hz)

Real cat sound reference: domestic cat meows at ~609 Hz (2.5x wild cat),
purring at 25-150 Hz. See blog.catcognition.com and petmd.com.

Sounds:
  - purr.wav: 55Hz + 110Hz harmonic, 1s loop
  - trill.wav: Rising chirrupy greeting ~0.3s
  - meow_short.wav: 300→500Hz rising "mrr?" ~0.4s
  - meow_long.wav: 600→350Hz descending "meow" ~0.8s
  - meow_greeting.wav: 200→500Hz rising chirpy "hmrr" ~0.4s (welcoming)
  - meow_plaintive.wav: 500→250Hz descending "meoow" ~0.7s (sad/longing)
  - chirp.wav: Bird-like high-pitched ~0.15s (prey excitement)
  - chatter.wav: Teeth-clicking rapid bursts ~0.3s (hunting frustration)
  - footstep.wav: 80Hz thud ~0.12s
  - footstep2.wav: Alternate footstep ~0.08s
  - sleep_breathing.wav: Gentle filtered noise, 1.5s loop
  - eat_crunch.wav: Short noise burst ~0.15s
  - toy_bat.wav: Bright ping ~0.2s
  - alert.wav: Quick double chirp ~0.3s
  - yawn.wav: Descending yawn ~0.6s
  - hiss.wav: Forced air hiss ~0.5s (fear/threat)
  - growl.wav: Low rumbling growl ~1.0s (escalating threat)
  - yowl.wav: Long distress howl ~1.2s (pain/loneliness)
"""

import os
import struct
import math
import random

SAMPLE_RATE = 22050
CHANNELS = 1  # mono
BITS = 16
MAX_AMP = 0.95  # near full scale

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)


def write_wav(path: str, samples):
    """Write float samples (range -1.0 to 1.0) to a 16-bit WAV file."""
    n = len(samples)
    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + n * 2))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))  # PCM
        f.write(struct.pack("<H", CHANNELS))
        f.write(struct.pack("<I", SAMPLE_RATE))
        f.write(struct.pack("<I", SAMPLE_RATE * CHANNELS * BITS // 8))
        f.write(struct.pack("<H", CHANNELS * BITS // 8))
        f.write(struct.pack("<H", BITS))
        f.write(b"data")
        f.write(struct.pack("<I", n * 2))
        for s in samples:
            s = max(-1.0, min(1.0, s))
            f.write(struct.pack("<h", int(s * 32767)))


def apply_fade(samples, fade_in=0, fade_out=0):
    n = len(samples)
    if fade_in:
        fi_n = int(SAMPLE_RATE * fade_in)
        for i in range(min(fi_n, n)):
            samples[i] *= (i / fi_n) ** 2  # smooth quadratic fade-in
    if fade_out:
        fo_n = int(SAMPLE_RATE * fade_out)
        for i in range(min(fo_n, n)):
            t = i / fo_n
            samples[n - 1 - i] *= 1 - t * t  # smooth quadratic fade-out
    return samples


def gen_purr():
    """55Hz + 110Hz harmonic purr, 1s, loopable."""
    n = int(SAMPLE_RATE * 1.0)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.70 * math.sin(2 * math.pi * 55 * t)
        s += 0.20 * math.sin(2 * math.pi * 110 * t)
        s += 0.10 * math.sin(2 * math.pi * 165 * t)
        samples.append(MAX_AMP * s)
    return apply_fade(samples, fade_in=0.2, fade_out=0.05)


def gen_trill():
    """Rising chirrupy trill greeting ~0.3s, like 'brrrp'."""
    n = int(SAMPLE_RATE * 0.3)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Trill = rapid frequency modulation (30Hz) + rising pitch 400->700Hz
        freq = 400 + 300 * (i / n)
        trill_mod = 1.0 + 0.15 * math.sin(2 * math.pi * 30 * t)
        s = math.sin(2 * math.pi * freq * trill_mod * t)
        # Add a lower purr-like harmonic for richness
        s += 0.4 * math.sin(2 * math.pi * 200 * t)
        # Amplitude envelope: quick attack, slower decay
        env = 0.3 + 0.7 * math.sin(math.pi * i / n)
        samples.append(MAX_AMP * 0.65 * env * s)
    return apply_fade(samples, fade_out=0.02)


def gen_meow_greeting():
    """Rising "hmrr?" greeting ~0.4s, welcoming sound."""
    n = int(SAMPLE_RATE * 0.4)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 200 + 300 * (i / n)
        env = 0.4 + 0.6 * (1.0 - math.exp(-t * 40))
        s = math.sin(2 * math.pi * freq * t) * 0.5
        s += math.sin(2 * math.pi * freq * 1.5 * t) * 0.3
        samples.append(MAX_AMP * 0.65 * env * s)
    return apply_fade(samples, fade_out=0.05)


def gen_meow_plaintive():
    """Descending sad meow ~0.7s, plaintive/longing."""
    n = int(SAMPLE_RATE * 0.7)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 1.0 + 0.02 * math.sin(2 * math.pi * 4 * t)
        freq = 500 * vib - 250 * (i / n)
        env = 0.4 + 0.6 * math.sin(math.pi * i / n)
        s = math.sin(2 * math.pi * freq * t) * 0.5
        s += math.sin(2 * math.pi * freq * 1.3 * t) * 0.25
        s += math.sin(2 * math.pi * freq * 0.5 * t) * 0.15
        samples.append(MAX_AMP * 0.65 * env * s)
    return apply_fade(samples, fade_out=0.08)


def gen_chirp():
    """Bird-like high-pitched chirp ~0.15s, prey excitement."""
    n = int(SAMPLE_RATE * 0.15)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 1000 + 500 * (i / n)  # 1000->1500Hz quick rise
        env = math.sin(math.pi * i / n)
        samples.append(MAX_AMP * 0.55 * env * math.sin(2 * math.pi * freq * t))
    return samples


def gen_chatter():
    """Teeth-clicking rapid burst ~0.3s, hunting frustration."""
    n = int(SAMPLE_RATE * 0.3)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Rapid clicks at ~20 Hz = 50ms intervals
        click = int(t * 20) % 2 == 0
        if click:
            s = math.sin(2 * math.pi * 2000 * (t * 20 - int(t * 20)))
            s *= max(0, 1.0 - (t * 20 - int(t * 20)) * 8)
        else:
            s = 0
        env = 1.0 - 0.5 * (i / n)
        samples.append(MAX_AMP * 0.60 * env * s)
    return samples


def gen_hiss():
    """Forced air hiss ~0.5s, fear/threat reaction."""
    n = int(SAMPLE_RATE * 0.5)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = random.uniform(-1.0, 1.0)
        # Bandpass around 3000-6000Hz (hissy frequencies)
        # Simple approximation: modulated noise
        env = math.sin(math.pi * i / n)
        hp = noise * (0.5 + 0.5 * math.sin(2 * math.pi * 4000 * t))
        samples.append(MAX_AMP * 0.35 * env * hp)
    return apply_fade(samples, fade_in=0.01, fade_out=0.05)


def gen_growl():
    """Low rumbling growl ~1.0s, escalating threat warning."""
    n = int(SAMPLE_RATE * 1.0)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Low frequency growl 80-150Hz with rumble
        freq = 80 + 70 * (i / n)
        s = 0.7 * math.sin(2 * math.pi * freq * t)
        s += 0.3 * random.uniform(-1.0, 1.0) * (i / n) * 0.5  # increasing noise
        env = 0.3 + 0.7 * (i / n)  # crescendo
        samples.append(MAX_AMP * 0.70 * env * s)
    return apply_fade(samples, fade_in=0.05, fade_out=0.15)


def gen_yowl():
    """Long distress howl ~1.2s, pain/loneliness."""
    n = int(SAMPLE_RATE * 1.2)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Descending howl 800->400Hz with vibrato
        vibrato = 1.0 + 0.05 * math.sin(2 * math.pi * 6 * t)
        freq = 800 * vibrato - 400 * (i / n)
        s = math.sin(2 * math.pi * freq * t)
        # Add roughness (distress quality)
        s += 0.2 * math.sin(2 * math.pi * freq * 1.5 * t)
        env = 0.4 + 0.6 * math.sin(math.pi * i / n)
        samples.append(MAX_AMP * 0.75 * env * s)
    return apply_fade(samples, fade_in=0.05, fade_out=0.1)


def gen_meow_short():
    """Rising 'mrr?' ~0.4s with crescendo."""
    n = int(SAMPLE_RATE * 0.4)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 + 200 * (i / n)
        amp = MAX_AMP * (0.60 + 0.35 * (i / n))
        s = math.sin(2 * math.pi * freq * t)
        s += 0.15 * math.sin(2 * math.pi * freq * 2 * t)  # harmonic
        samples.append(amp * s)
    return apply_fade(samples, fade_in=0.01, fade_out=0.05)


def gen_meow_long():
    """Descending 'meow' ~0.8s with vibrato."""
    n = int(SAMPLE_RATE * 0.8)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        vibrato = 1.0 + 0.03 * math.sin(2 * math.pi * 5 * t)
        freq = 600 * vibrato - 250 * (i / n)
        amp = MAX_AMP * (0.85 - 0.25 * (i / n))
        s = math.sin(2 * math.pi * freq * t)
        s += 0.15 * math.sin(2 * math.pi * freq * 1.5 * t)
        samples.append(amp * s)
    return apply_fade(samples, fade_in=0.02, fade_out=0.1)


def gen_footstep():
    """80Hz thud ~0.12s, fast decay."""
    n = int(SAMPLE_RATE * 0.12)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-20 * t)
        samples.append(MAX_AMP * 0.85 * decay * math.sin(2 * math.pi * 80 * t))
    return apply_fade(samples, fade_out=0.02)


def gen_footstep2():
    """Lighter alternate footstep ~0.08s."""
    n = int(SAMPLE_RATE * 0.08)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-25 * t)
        samples.append(MAX_AMP * 0.65 * decay * math.sin(2 * math.pi * 120 * t))
    return list(samples)


def gen_sleep_breathing():
    """Gentle filtered noise swell, 1.5s loop."""
    n = int(SAMPLE_RATE * 1.5)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        swell = 0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t)
        noise = random.uniform(-1.0, 1.0)
        samples.append(MAX_AMP * 0.20 * swell * noise * 0.5)
    return apply_fade(samples, fade_in=0.1, fade_out=0.1)


def gen_eat_crunch():
    """Short noise burst ~0.15s."""
    n = int(SAMPLE_RATE * 0.15)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-20 * t)
        noise = random.uniform(-1.0, 1.0)
        samples.append(MAX_AMP * 0.70 * decay * noise)
    return samples


def gen_toy_bat():
    """Bright ping ~0.2s."""
    n = int(SAMPLE_RATE * 0.2)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-15 * t)
        tone = 0.6 * math.sin(2 * math.pi * 800 * t) + 0.4 * math.sin(2 * math.pi * 1200 * t)
        samples.append(MAX_AMP * 0.75 * decay * tone)
    return apply_fade(samples, fade_out=0.02)


def gen_alert():
    """Quick double chirp ~0.3s."""
    n = int(SAMPLE_RATE * 0.3)
    samples = []
    chirp_n = n // 2
    for chirp in range(2):
        offset = chirp * chirp_n
        for i in range(chirp_n):
            t = (offset + i) / SAMPLE_RATE
            amp = MAX_AMP * 0.55 * math.sin(math.pi * i / chirp_n)
            freq = 700 + 500 * (i / chirp_n)
            samples.append(amp * math.sin(2 * math.pi * freq * t))
    return samples


def gen_purr_deep():
    """3s loop, deep low frequency hum (50-100Hz sine + noise)."""
    n = int(SAMPLE_RATE * 3.0)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Sweep from 50Hz to 100Hz slowly
        freq = 50 + 50 * (i / n)
        s = 0.60 * math.sin(2 * math.pi * freq * t)
        s += 0.25 * math.sin(2 * math.pi * freq * 2 * t)  # harmonic
        s += 0.15 * random.uniform(-1.0, 1.0)  # subtle noise
        samples.append(MAX_AMP * s)
    return apply_fade(samples, fade_in=0.3, fade_out=0.1)


def gen_chirp_excited():
    """0.2s high-pitched chirp (2kHz -> 4kHz sweep)."""
    n = int(SAMPLE_RATE * 0.2)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 2000 + 2000 * (i / n)
        env = math.sin(math.pi * i / n)
        samples.append(MAX_AMP * 0.50 * env * math.sin(2 * math.pi * freq * t))
    return apply_fade(samples, fade_out=0.02)


def gen_meow_demand():
    """0.6s insistent meow (rising pitch), demanding tone."""
    n = int(SAMPLE_RATE * 0.6)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 400 + 400 * (i / n)  # 400->800Hz rising
        env = 0.5 + 0.5 * math.sin(math.pi * i / n)
        s = 0.60 * math.sin(2 * math.pi * freq * t)
        s += 0.25 * math.sin(2 * math.pi * freq * 1.5 * t)  # harmonic
        samples.append(MAX_AMP * 0.70 * env * s)
    return apply_fade(samples, fade_in=0.02, fade_out=0.06)


def gen_yawn():
    """Descending yawn ~0.6s."""
    n = int(SAMPLE_RATE * 0.6)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 400 - 250 * (i / n)
        amp = MAX_AMP * 0.70 * (0.5 + 0.5 * math.sin(math.pi * i / n))
        samples.append(amp * math.sin(2 * math.pi * freq * t))
    return apply_fade(samples, fade_in=0.05, fade_out=0.1)


GENERATORS = [
    ("purr.wav", gen_purr),
    ("purr_deep.wav", gen_purr_deep),
    ("trill.wav", gen_trill),
    ("chirp.wav", gen_chirp),
    ("chirp_excited.wav", gen_chirp_excited),
    ("chatter.wav", gen_chatter),
    ("hiss.wav", gen_hiss),
    ("growl.wav", gen_growl),
    ("yowl.wav", gen_yowl),
    ("meow_greeting.wav", gen_meow_greeting),
    ("meow_plaintive.wav", gen_meow_plaintive),
    ("meow_short.wav", gen_meow_short),
    ("meow_long.wav", gen_meow_long),
    ("meow_demand.wav", gen_meow_demand),
    ("footstep.wav", gen_footstep),
    ("footstep2.wav", gen_footstep2),
    ("sleep_breathing.wav", gen_sleep_breathing),
    ("eat_crunch.wav", gen_eat_crunch),
    ("toy_bat.wav", gen_toy_bat),
    ("alert.wav", gen_alert),
    ("yawn.wav", gen_yawn),
]


def main():
    print(f"Generating {len(GENERATORS)} sounds to {SOUNDS_DIR}")
    for name, generator in GENERATORS:
        path = os.path.join(SOUNDS_DIR, name)
        samples = generator()
        write_wav(path, samples)
        duration = len(samples) / SAMPLE_RATE
        peak = max(abs(s) for s in samples)
        db = 20 * math.log10(peak) if peak > 0 else -99
        print(f"  {name:20s} {duration:.2f}s  peak={peak*100:.0f}%  {db:.0f}dB")
    print("Done.")


if __name__ == "__main__":
    main()
