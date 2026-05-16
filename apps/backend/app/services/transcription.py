"""Darija Speech-to-Text via the MoulSot Gradio Space.

Audio is normalised to 16 kHz mono WAV (bundled ffmpeg, no system
install needed) and sent to ``atlasia/MoulSot.v0.3`` through
``gradio_client``.

No silent fallbacks: any real failure raises a clear error so it is
visible instead of masked by a fabricated listing.
"""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path

from ..config import get_settings
from ..errors import EmptyTranscriptionError, TranscriptionError, ValidationError
from ..logging_conf import get_logger
from ..schemas import TranscriptionResult

log = get_logger("hackai.stt")

TARGET_SR = 16_000


def validate_audio(filename: str, content_type: str | None, size: int) -> None:
    settings = get_settings()
    if size <= 0:
        raise ValidationError("The audio file is empty.")
    if size > settings.max_audio_bytes:
        raise ValidationError(
            f"Audio is too large (max {settings.max_audio_bytes // (1024 * 1024)} MB)."
        )
    ct = (content_type or "").lower().split(";")[0].strip()
    ext_ok = filename.lower().endswith(
        (".wav", ".mp3", ".mpeg", ".webm", ".m4a", ".ogg", ".mp4")
    )
    if ct and ct not in settings.allowed_audio_types and not ext_ok:
        raise ValidationError(f"Unsupported audio format: {ct or filename}")


def _ffmpeg_exe() -> str:
    """Bundled ffmpeg binary (no system install required)."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _to_wav_16k_mono(src: Path) -> Path:
    dst = src.with_suffix(".norm.wav")
    proc = subprocess.run(
        [
            _ffmpeg_exe(), "-y", "-i", str(src),
            "-ar", str(TARGET_SR), "-ac", "1", "-f", "wav", str(dst),
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg conversion failed: {proc.stderr.decode()[:300]}"
        )
    return dst


def _call_space(wav_path: Path) -> str:
    from gradio_client import Client, handle_file

    settings = get_settings()
    # verbose=False: gradio_client otherwise prints a "✔" that crashes
    # the Windows cp1252 console with UnicodeEncodeError.
    client = Client(
        settings.asr_space, hf_token=settings.hf_token, verbose=False
    )
    result = client.predict(
        handle_file(str(wav_path)),
        settings.asr_lang,
        api_name="/transcribe",
    )
    return str(result).strip() if result else ""


def transcribe(
    audio_bytes: bytes, filename: str, content_type: str | None
) -> tuple[TranscriptionResult, int]:
    """Return ``(TranscriptionResult, inference_ms)``.

    Raises :class:`TranscriptionError` (with a human-readable detail) on
    any infrastructure failure — nothing is silently substituted.
    """
    settings = get_settings()
    validate_audio(filename, content_type, len(audio_bytes))

    if not settings.hf_token:
        raise TranscriptionError(
            "Speech-to-text is not configured.",
            detail="HF_TOKEN is missing — set it in .env to call MoulSot.",
        )

    suffix = Path(filename).suffix or ".webm"
    tmp_dir = Path(tempfile.mkdtemp(prefix="hirafi_"))
    src = tmp_dir / f"input{suffix}"
    src.write_bytes(audio_bytes)

    wav_path: Path | None = None
    try:
        try:
            wav_path = _to_wav_16k_mono(src)
        except Exception as exc:
            log.error("ffmpeg conversion failed: %s", exc)
            raise TranscriptionError(
                "Could not process the audio file.",
                detail=f"ffmpeg: {exc}",
            ) from exc

        try:
            start = time.time()
            text = _call_space(wav_path)
            inference_ms = int((time.time() - start) * 1000)
        except Exception as exc:
            log.error("MoulSot Space call failed: %s", exc)
            raise TranscriptionError(
                "The transcription service (MoulSot) is unavailable.",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc
    finally:
        for p in (src, wav_path):
            if p:
                p.unlink(missing_ok=True)
        tmp_dir.rmdir()

    if not text:
        raise EmptyTranscriptionError()

    log.info("Transcription ok (%d chars, %d ms)", len(text), inference_ms)
    return TranscriptionResult(text=text, source="moulsot"), inference_ms
