"""
Duration estimation utility.

Provides a lightweight heuristic to estimate audio/video duration from a
file's name (extension) and size in bytes, without decoding the file.

Estimations
-----------
.mp3  — assumes 128 kbps CBR  → 16 000 bytes/s
.mp4  — assumes 256 kbps total → 32 000 bytes/s  (audio track dominates for meetings)
.wav  — assumes 16-bit / 44.1 kHz / stereo → 176 400 bytes/s
.txt  — no duration (text transcript)
Other — returns None
"""

import os

# Bytes-per-second estimates for common meeting file formats
_BYTES_PER_SECOND: dict[str, float] = {
    ".mp3": 16_000,    # 128 kbps
    ".mp4": 32_000,    # 256 kbps (audio-dominated meeting recording)
    ".wav": 176_400,   # 44.1 kHz, 16-bit, stereo (uncompressed PCM)
}


def estimate_duration_seconds(filename: str, size_bytes: int) -> float | None:
    """
    Return an estimated duration in seconds for a given filename and size.

    Returns ``None`` for text files or unsupported extensions.
    """
    ext = os.path.splitext(filename.lower())[1]
    bps = _BYTES_PER_SECOND.get(ext)
    if bps is None or size_bytes <= 0:
        return None
    return size_bytes / bps
