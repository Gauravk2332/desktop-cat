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
MAX_AMP = 0.6  # avoid clipping

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
        f.write(struct.pack("<IHHIIHH", 16, 1, CHANNELS, SAMPLE_RATE,
                            SAMPLE_RATE * CHANNELS * BITS // 8,
                            CHANNELS * BITS // 8, BITS))
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", n * 2))
        # Clamp to [-1, 1] and write
        for s in samples:
            s = max(-1.0, min(1.0, s))
            f.write(struct.pack("<h", int(s * 32767)))
    return path


def sine(freq_hz: float, duration_sec: float, amp: float = MAX_AMP) -> list:
    """Generate a sine wave."""
    n = int(SAMPLE_RATE * duration_sec)
    return [amp * math.sin(2 * math.pi * freq_hz * t / SAMPLE_RATE) for t in range(n)]


def apply_fade(samples, fade_in: float = 0, fade_out: float = 0):
    """Apply linear fade-in/out in seconds."""
    n = len(samples)
    if fade_in > 0:
        fi_n = int(SAMPLE_RATE * fade_in)
        for i in range(min(fi_n, n)):
            samples[i] *= i / fi_n
    if fade_out > 0:
        fo_n = int(SAMPLE_RATE * fade_out)
        for i in range(min(fo_n, n)):
            samples[n - 1 - i] *= i / fo_n
    return samples


def envelope_adsr(samples, attack: float = 0.01, decay: float = 0.05,
                  sustain_level: float = 0.7, release: float = 0.1):
    """Apply ADSR envelope."""
    n = len(samples)
    a_n = int(SAMPLE_RATE * attack)
    d_n = int(SAMPLE_RATE * decay)
    r_n = int(SAMPLE_RATE * release)
    for i in range(n):
        if i < a_n:
            samples[i] *= i / a_n
        elif i < a_n + d_n:
            t = (i - a_n) / d_n
            samples[i] *= 1.0 - (1.0 - sustain_level) * t
        elif i < n - r_n:
            samples[i] *= sustain_level
        else:
            t = (i - (n - r_n)) / r_n
            samples[i] *= sustain_level * (1.0 - t)
    return samples


def generate_purr():
    """55Hz sine with 200ms fade-in, loopable ~1s."""
    samples = sine(55, 1.0, MAX_AMP * 0.5)
    # Add subtle 2nd harmonic for warmth
    harm = sine(110, 1.0, MAX_AMP * 0.15)
    samples = [s + h for s, h in zip(samples, harm)]
    samples = apply_fade(samples, fade_in=0.2, fade_out=0.05)
    write_wav(os.path.join(SOUNDS_DIR, "purr.wav"), samples)
    print(f"  ✓ purr.wav ({len(samples)} samples)")


def generate_meow_short():
    """Rising 'mrr?' — frequency sweep 300→600Hz, 0.4s."""
    n = int(SAMPLE_RATE * 0.4)
    samples = []
    for t in range(n):
        freq = 300 + (600 - 300) * (t / n)
        amp = MAX_AMP * (0.3 + 0.7 * (t / n))  # crescendo
        samples.append(amp * math.sin(2 * math.pi * freq * t / SAMPLE_RATE))
    samples = apply_fade(samples, fade_in=0.01, fade_out=0.05)
    write_wav(os.path.join(SOUNDS_DIR, "meow_short.wav"), samples)
    print(f"  ✓ meow_short.wav ({len(samples)} samples)")


def generate_meow_long():
    """Descending 'meow' — 600→200Hz, 0.8s, 5Hz vibrato."""
    n = int(SAMPLE_RATE * 0.8)
    samples = []
    for t in range(n):
        freq = 600 - (600 - 200) * (t / n)
        vibrato = 1.0 + 0.03 * math.sin(2 * math.pi * 5 * t / SAMPLE_RATE)
        amp = MAX_AMP * (0.9 - 0.3 * (t / n))
        samples.append(amp * math.sin(2 * math.pi * freq * vibrato * t / SAMPLE_RATE))
    samples = apply_fade(samples, fade_in=0.02, fade_out=0.1)
    write_wav(os.path.join(SOUNDS_DIR, "meow_long.wav"), samples)
    print(f"  ✓ meow_long.wav ({len(samples)} samples)")


def generate_footstep():
    """80Hz thud, fast decay ~0.1s."""
    n = int(SAMPLE_RATE * 0.12)
    samples = []
    for t in range(n):
        decay = math.exp(-t * 30 / SAMPLE_RATE)
        samples.append(MAX_AMP * 0.4 * decay * math.sin(2 * math.pi * 80 * t / SAMPLE_RATE))
    samples = apply_fade(samples, fade_out=0.02)
    write_wav(os.path.join(SOUNDS_DIR, "footstep.wav"), samples)
    print(f"  ✓ footstep.wav ({len(samples)} samples)")


def generate_footstep2():
    """Lighter alternate footstep ~0.08s."""
    n = int(SAMPLE_RATE * 0.08)
    samples = []
    for t in range(n):
        decay = math.exp(-t * 50 / SAMPLE_RATE)
        samples.append(MAX_AMP * 0.3 * decay * math.sin(2 * math.pi * 120 * t / SAMPLE_RATE))
    write_wav(os.path.join(SOUNDS_DIR, "footstep2.wav"), samples)
    print(f"  ✓ footstep2.wav ({len(samples)} samples)")


def generate_sleep_breathing():
    """Gentle filtered noise swell, 1.5s loopable."""
    n = int(SAMPLE_RATE * 1.5)
    samples = []
    for t in range(n):
        # Pink-ish noise shaped by sine swell
        noise = random.uniform(-1, 1)
        swell = 0.5 + 0.5 * math.sin(2 * math.pi * t / n)  # 0→1→0
        lp = 0.2  # crude low-pass
        samples.append(MAX_AMP * 0.2 * swell * noise * lp)
    samples = apply_fade(samples, fade_in=0.1, fade_out=0.1)
    write_wav(os.path.join(SOUNDS_DIR, "sleep_breathing.wav"), samples)
    print(f"  ✓ sleep_breathing.wav ({len(samples)} samples)")


def generate_eat_crunch():
    """Short noise burst ~0.15s."""
    n = int(SAMPLE_RATE * 0.15)
    samples = []
    for t in range(n):
        noise = random.uniform(-1, 1)
        decay = math.exp(-t * 20 / SAMPLE_RATE)
        samples.append(MAX_AMP * 0.3 * decay * noise)
    write_wav(os.path.join(SOUNDS_DIR, "eat_crunch.wav"), samples)
    print(f"  ✓ eat_crunch.wav ({len(samples)} samples)")


def generate_toy_bat():
    """Bright ping ~0.2s."""
    n = int(SAMPLE_RATE * 0.2)
    samples = []
    for t in range(n):
        decay = math.exp(-t * 15 / SAMPLE_RATE)
        samples.append(MAX_AMP * 0.35 * decay * (
            math.sin(2 * math.pi * 880 * t / SAMPLE_RATE) * 0.6 +
            math.sin(2 * math.pi * 1320 * t / SAMPLE_RATE) * 0.3 +
            math.sin(2 * math.pi * 1760 * t / SAMPLE_RATE) * 0.1
        ))
    write_wav(os.path.join(SOUNDS_DIR, "toy_bat.wav"), samples)
    print(f"  ✓ toy_bat.wav ({len(samples)} samples)")


def generate_alert():
    """Quick double chirp ~0.3s."""
    n = int(SAMPLE_RATE * 0.3)
    chirp_n = n // 2
    samples = [0.0] * n
    for t in range(chirp_n):
        freq = 800 + (1200 - 800) * (t / chirp_n)
        amp = MAX_AMP * 0.25 * math.sin(math.pi * t / chirp_n)
        samples[t] = amp * math.sin(2 * math.pi * freq * t / SAMPLE_RATE)
        t2 = t + chirp_n
        freq2 = 1000 + (1400 - 1000) * (t / chirp_n)
        samples[t2] = amp * math.sin(2 * math.pi * freq2 * t / SAMPLE_RATE)
    write_wav(os.path.join(SOUNDS_DIR, "alert.wav"), samples)
    print(f"  ✓ alert.wav ({len(samples)} samples)")


def generate_yawn():
    """Descending yawn ~0.6s."""
    n = int(SAMPLE_RATE * 0.6)
    samples = []
    for t in range(n):
        freq = 400 - (400 - 100) * (t / n)
        amp = MAX_AMP * 0.3 * (0.5 + 0.5 * math.sin(math.pi * t / n))
        samples.append(amp * math.sin(2 * math.pi * freq * t / SAMPLE_RATE))
    samples = apply_fade(samples, fade_in=0.05, fade_out=0.1)
    write_wav(os.path.join(SOUNDS_DIR, "yawn.wav"), samples)
    print(f"  ✓ yawn.wav ({len(samples)} samples)")


def main():
    print("Generating desktop-cat sound effects...")
    print(f"  Sample rate: {SAMPLE_RATE} Hz")
    print(f"  Output: {SOUNDS_DIR}/")
    print()

    generate_purr()
    generate_meow_short()
    generate_meow_long()
    generate_footstep()
    generate_footstep2()
    generate_sleep_breathing()
    generate_eat_crunch()
    generate_toy_bat()
    generate_alert()
    generate_yawn()

    print()
    print(f"Done. {len(os.listdir(SOUNDS_DIR))} files in {SOUNDS_DIR}/")
    sizes = sum(os.path.getsize(os.path.join(SOUNDS_DIR, f))
                for f in os.listdir(SOUNDS_DIR))
    print(f"Total size: {sizes / 1024:.1f} KB")


if __name__ == "__main__":
    main()
