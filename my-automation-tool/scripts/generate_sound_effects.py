"""用标准库生成自有的短提示音，不下载或复制案例资源。"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16_000


def _write_tone(path: Path, notes: tuple[tuple[float, float], ...]) -> None:
    frames = bytearray()
    for frequency, duration in notes:
        total = int(SAMPLE_RATE * duration)
        for index in range(total):
            envelope = min(1.0, index / 120) * min(1.0, (total - index) / 180)
            value = int(8_000 * envelope * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
            frames.extend(struct.pack("<h", value))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(frames)


def main() -> None:
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(exist_ok=True)
    _write_tone(assets / "sound-on.wav", ((660.0, 0.07), (880.0, 0.09)))
    _write_tone(assets / "sound-off.wav", ((660.0, 0.07), (440.0, 0.09)))


if __name__ == "__main__":
    main()
