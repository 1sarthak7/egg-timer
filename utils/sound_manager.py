"""
Kitty Egg Timer — Sound Manager
================================
Generates tiny synthetic WAV files on first launch and plays them via QSoundEffect.
"""

import os
import math
import struct
import wave
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect


SOUNDS_DIR = Path(__file__).resolve().parent.parent / "sounds"


def _ensure_dir():
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)


def _generate_tone_wav(filepath: Path, freq: float = 880.0,
                       duration_ms: int = 300, volume: float = 0.5,
                       sample_rate: int = 44100, fade_ms: int = 40):
    """Write a simple sine-wave WAV file (mono, 16-bit)."""
    n_samples = int(sample_rate * duration_ms / 1000)
    fade_samples = int(sample_rate * fade_ms / 1000)

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = volume * math.sin(2 * math.pi * freq * t)

        # Fade in/out to avoid clicks
        if i < fade_samples:
            val *= i / fade_samples
        elif i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples

        samples.append(int(val * 32767))

    with wave.open(str(filepath), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _generate_bell_wav(filepath: Path):
    """Generate a pleasant bell/chime sound with harmonics."""
    sample_rate = 44100
    duration_ms = 800
    n_samples = int(sample_rate * duration_ms / 1000)
    fade_samples = int(sample_rate * 60 / 1000)

    harmonics = [
        (880.0, 0.35),
        (1760.0, 0.2),
        (2640.0, 0.1),
        (1320.0, 0.15),
    ]

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        val = 0.0
        for freq, amp in harmonics:
            val += amp * math.sin(2 * math.pi * freq * t)

        # Exponential decay (bell-like)
        decay = math.exp(-4.0 * t)
        val *= decay

        # Fade out to avoid click at end
        if i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples

        samples.append(int(max(-1, min(1, val)) * 32767))

    with wave.open(str(filepath), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _generate_tick_wav(filepath: Path):
    """Generate a subtle tick/click sound."""
    _generate_tone_wav(filepath, freq=1200.0, duration_ms=50, volume=0.25,
                       fade_ms=10)


def _generate_meow_wav(filepath: Path):
    """Generate a cute synthetic 'meow'-ish chirp with frequency sweep."""
    sample_rate = 44100
    duration_ms = 400
    n_samples = int(sample_rate * duration_ms / 1000)
    fade_samples = int(sample_rate * 30 / 1000)

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        progress = i / n_samples
        # Sweep from 600 Hz → 900 Hz → 500 Hz
        if progress < 0.4:
            freq = 600 + (900 - 600) * (progress / 0.4)
        else:
            freq = 900 - (900 - 500) * ((progress - 0.4) / 0.6)

        val = 0.35 * math.sin(2 * math.pi * freq * t)
        val += 0.1 * math.sin(2 * math.pi * freq * 2 * t)

        # Envelope
        if progress < 0.1:
            val *= progress / 0.1
        elif progress > 0.6:
            val *= (1 - progress) / 0.4

        if i > n_samples - fade_samples:
            val *= (n_samples - i) / fade_samples

        samples.append(int(max(-1, min(1, val)) * 32767))

    with wave.open(str(filepath), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


class SoundManager:
    """Singleton-ish sound manager. Call init() after QApplication exists."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def init(self):
        if self._initialised:
            return
        _ensure_dir()

        bell_path = SOUNDS_DIR / "bell.wav"
        tick_path = SOUNDS_DIR / "tick.wav"
        meow_path = SOUNDS_DIR / "meow.wav"

        if not bell_path.exists():
            _generate_bell_wav(bell_path)
        if not tick_path.exists():
            _generate_tick_wav(tick_path)
        if not meow_path.exists():
            _generate_meow_wav(meow_path)

        self._bell = QSoundEffect()
        self._bell.setSource(QUrl.fromLocalFile(str(bell_path)))
        self._bell.setVolume(0.7)

        self._tick = QSoundEffect()
        self._tick.setSource(QUrl.fromLocalFile(str(tick_path)))
        self._tick.setVolume(0.4)

        self._meow = QSoundEffect()
        self._meow.setSource(QUrl.fromLocalFile(str(meow_path)))
        self._meow.setVolume(0.6)

        self._initialised = True

    def play_bell(self):
        if self._initialised:
            self._bell.play()

    def play_tick(self):
        if self._initialised:
            self._tick.play()

    def play_meow(self):
        if self._initialised:
            self._meow.play()
