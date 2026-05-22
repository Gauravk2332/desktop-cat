#!/usr/bin/env python3
"""scripts/generate_sounds.py — Generate WAV sound effects for desktop-cat.

Output: assets/sounds/*.wav (16-bit mono, 22050 Hz)

Sounds generated:
  - purr.wav: 55Hz sine, 1s loopable, 200ms fade
  - meow_short.wav: Rising "mrr?" ~0.4s
  - meow_long.wav: Descending "meow" ~0.8s with vibrato
  - footstep.wav: 80Hz thud, 50ms decay
  - footstep2.wav: Alternate footstep ~0.3s
  - sleep_breathing.wav: Gentle filtered noise swell, 1.5s loop
  - eat_crunch.wav: Short noise burst ~0.15s
  - toy_bat.wav: Bright ping ~0.2s
  - alert.wav: Quick double chirp ~0.3s
  - yawn.wav: Descending yawn ~0.6s
"""

import os
import struct
import math
import random

SAMPLE_RATE = 22050
CHANNELS = 1  # mono
BITS = 16
MAX_AMP = 0.95  # near full scale, tiny headroom to avoid clicks

SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)


def write_wav(path: str, samples):
    """Write float samples (range -1.0 to 1.0) to a 16-bit WAV file."""
    n = len(samples)
    with open(path, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + n * 2))
        f.write(b"WAVE")

        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))  # chunk size
        f.write(struct.pack("<H", 1))   # PCM
        f.write(struct.pack("<H", CHANNELS))
        f.write(struct.pack("<I", SAMPLE_RATE))
        f.write(struct.pack("<I", SAMPLE_RATE * CHANNELS * BITS // 8))
        f.write(struct.pack("<H", CHANNELS * BITS // 8))
        f.write(struct.pack("<H", BITS))

        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", n * 2))
        for s in samples:
            s = max(-1.0, min(1.0, s))
            f.write(struct.pack("<h", int(s * 32767)))


# ── Utility ───────────────────────────────────────────────────────────

def sine(freq_hz: float, duration_sec: float, amp: float = MAX_AMP) -> list:
    n = int(SAMPLE_RATE * duration_sec)
    t = [i / SAMPLE_RATE for i in range(n)]
    return [amp * math.sin(2 * math.pi * freq_hz * ti) for ti in t]


def apply_fade(samples, fade_in: float = 0, fade_out: float = 0):
    n = len(samples)
    if fade_in:
        fi_n = int(SAMPLE_RATE * fade_in)
        for i in range(min(fi_n, n)):
            samples[i] *= i / fi_n
    if fade_out:
        fo_n = int(SAMPLE_RATE * fade_out)
        for i in range(min(fo_n, n)):
            samples[n - 1 - i] *= i / fo_n
    return samples


# ── Sound Generators ──────────────────────────────────────────────────

def gen_purr() -> list:
    """55Hz purr, 1s, loopable with 200ms fade in/out."""
    samples = sine(55, 1.0, MAX_AMP * 0.80)
    # Add a soft harmonic for richness
    harm = sine(110, 1.0, MAX_AMP * 0.25)
    samples = [a + b for a, b in zip(samples, harm)]
    samples = apply_fade(samples, fade_in=0.2, fade_out=0.05)
    return samples


def gen_meow_short() -> list:
    """Rising 'mrr?' ~0.4s with crescendo."""
    n = int(SAMPLE_RATE * 0.4)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 + 200 * (i / n)  # 300→500Hz
        amp = MAX_AMP * (0.60 + 0.35 * (i / n))  # crescendo: 60%→95%
        samples.append(amp * math.sin(2 * math.pi * freq * t))
    samples = apply_fade(samples, fade_in=0.01, fade_out=0.05)
    return samples


def gen_meow_long() -> list:
    """Descending 'meow' ~0.8s with vibrato."""
    n = int(SAMPLE_RATE * 0.8)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        vibrato = 1.0 + 0.03 * math.sin(2 * math.pi * 5 * t)
        freq = 600 * vibrato - 250 * (i / n)  # 600→350Hz
        amp = MAX_AMP * (0.85 - 0.25 * (i / n))  # 85%→60%
        samples.append(amp * math.sin(2 * math.pi * freq * t))
    samples = apply_fade(samples, fade_in=0.02, fade_out=0.1)
    return samples


def gen_footstep() -> list:
    """80Hz thud ~0.12s, fast decay."""
    n = int(SAMPLE_RATE * 0.12)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-20 * t)
        samples.append(MAX_AMP * 0.85 * decay * math.sin(2 * math.pi * 80 * t))
    samples = apply_fade(samples, fade_out=0.02)
    return samples


def gen_footstep2() -> list:
    """Lighter alternate footstep ~0.08s."""
    n = int(SAMPLE_RATE * 0.08)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-25 * t)
        samples.append(MAX_AMP * 0.65 * decay * math.sin(2 * math.pi * 120 * t))
    return list(samples)  # non-faded, naturally decays


def gen_sleep_breathing() -> list:
    """Gentle filtered noise swell, 1.5s loop."""
    n = int(SAMPLE_RATE * 1.5)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        swell = 0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t)  # 0.5Hz = 2s breath cycle
        noise = random.uniform(-1.0, 1.0)
        # Simple 200Hz low-pass: avg filter
        lp = 0.5 + 0.5 * math.sin(2 * math.pi * 200 * t) if i > 0 else 0.5
        samples.append(MAX_AMP * 0.20 * swell * noise * 0.5)
    samples = apply_fade(samples, fade_in=0.1, fade_out=0.1)
    return samples


def gen_eat_crunch() -> list:
    """Short noise burst ~0.15s."""
    n = int(SAMPLE_RATE * 0.15)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-20 * t)
        noise = random.uniform(-1.0, 1.0)
        samples.append(MAX_AMP * 0.70 * decay * noise)
    return samples


def gen_toy_bat() -> list:
    """Bright ping ~0.2s."""
    n = int(SAMPLE_RATE * 0.2)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        decay = math.exp(-15 * t)
        tone = 0.6 * math.sin(2 * math.pi * 800 * t) + 0.4 * math.sin(2 * math.pi * 1200 * t)
        samples.append(MAX_AMP * 0.75 * decay * tone)
    samples = apply_fade(samples, fade_out=0.02)
    return samples


def gen_alert() -> list:
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


def gen_yawn() -> list:
    """Descending yawn ~0.6s."""
    n = int(SAMPLE_RATE * 0.6)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 400 - 250 * (i / n)
        amp = MAX_AMP * 0.70 * (0.5 + 0.5 * math.sin(math.pi * i / n))
        samples.append(amp * math.sin(2 * math.pi * freq * t))
    samples = apply_fade(samples, fade_in=0.05, fade_out=0.1)
    return samples


# ── Main ──────────────────────────────────────────────────────────────

GENERATORS = [
    ("purr.wav", gen_purr),
    ("meow_short.wav", gen_meow_short),
    ("meow_long.wav", gen_meow_long),
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
        print(f"  {name:20s} {duration:.2f}s  peak={peak*100:.0f}%")
    print("Done.")


if __name__ == "__main__":
    main()
