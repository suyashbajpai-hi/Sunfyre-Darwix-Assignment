"""WAV helpers used by test-call synthesis and the Q4 chunked replay."""
from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


def read_wav(path: Path) -> Tuple[bytes, int, int]:
    """Return (pcm16, sample_rate, channels)."""
    with wave.open(str(path), "rb") as wf:
        assert wf.getsampwidth() == 2, "only 16-bit PCM WAV is supported"
        return wf.readframes(wf.getnframes()), wf.getframerate(), wf.getnchannels()


def write_wav(path: Path, pcm: bytes, sample_rate: int = 24000, channels: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)


def silence(seconds: float, sample_rate: int = 24000) -> bytes:
    n = max(0, int(seconds * sample_rate))
    return b"\x00\x00" * n


def concat_pcm(*parts: bytes) -> bytes:
    return b"".join(parts)


@dataclass
class WavChunk:
    index: int
    start_s: float
    end_s: float
    pcm: bytes
    sample_rate: int

    @property
    def wav_bytes(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(self.pcm)
        return buf.getvalue()


def chunk_wav(path: Path, chunk_seconds: float) -> List[WavChunk]:
    pcm, rate, channels = read_wav(path)
    if channels != 1:
        # downmix: take first channel
        frame = channels * 2
        pcm = b"".join(pcm[i : i + 2] for i in range(0, len(pcm), frame))
    bytes_per = int(chunk_seconds * rate) * 2
    chunks: List[WavChunk] = []
    i = 0
    pos = 0
    while pos < len(pcm):
        sl = pcm[pos : pos + bytes_per]
        start = pos / (rate * 2)
        end = (pos + len(sl)) / (rate * 2)
        chunks.append(WavChunk(index=i, start_s=start, end_s=end, pcm=sl, sample_rate=rate))
        i += 1
        pos += bytes_per
    return chunks


def wav_duration_s(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def pcm16_to_wav_bytes(pcm: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    byte_rate = sample_rate * channels * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, channels * 2, 16)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm
