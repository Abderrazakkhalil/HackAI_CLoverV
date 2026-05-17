"""Speech-to-Text via Gradio Spaces.

Two backends are supported:
- ``darija``  -> atlasia/MoulSot.v0.3  (Darija / Arabic)
- ``amazigh`` -> Tamazight-NLP/ASR     (Tamazight / Berber)

Audio is normalised to 16 kHz mono WAV (bundled ffmpeg, no system
install needed) and sent through ``gradio_client``.

No silent fallbacks: any real failure raises a clear error so it is
visible instead of masked by a fabricated listing.
"""

from __future__ import annotations

import signal
import subprocess
import tempfile
import time
from pathlib import Path
from contextlib import contextmanager

from ..config import get_settings
from ..errors import EmptyTranscriptionError, TranscriptionError, ValidationError
from ..logging_conf import get_logger
from ..schemas import SpeechLang, TranscriptionResult

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


def _call_space(wav_path: Path, speech_lang: SpeechLang) -> str:
    from gradio_client import Client, handle_file

    settings = get_settings()
    # verbose=False: gradio_client otherwise prints a "✔" that crashes
    # the Windows cp1252 console with UnicodeEncodeError.
    timeout_s = settings.amazigh_asr_timeout_s if speech_lang == "amazigh" else settings.asr_timeout_s

    try:
        hf_token = settings.hf_token or None

        if speech_lang == "amazigh":
            log.info("Initializing Tamazight-NLP/ASR client (timeout=%ds)...", timeout_s)
            client = Client(
                settings.amazigh_asr_space,
                token=hf_token,
                verbose=False,
            )
            log.info("Calling Tamazight-NLP/ASR with api_name=%s", settings.amazigh_asr_api_name)
            result = client.predict(
                handle_file(str(wav_path)),
                api_name=settings.amazigh_asr_api_name,
            )
        else:
            log.info("Initializing MoulSot client (timeout=%ds)...", timeout_s)
            client = Client(
                settings.asr_space,
                token=hf_token,
                verbose=False,
            )
            log.info("Calling MoulSot with api_name=/transcribe, lang=%s", settings.asr_lang)
            result = client.predict(
                handle_file(str(wav_path)),
                settings.asr_lang,
                api_name="/transcribe",
            )
        log.info("Space returned: %s (type=%s, len=%s)", result, type(result).__name__, len(str(result)) if result else 0)
        return str(result).strip() if result else ""
    except TimeoutError as e:
        msg = f"ASR Space request timed out after {timeout_s}s. The Space may be slow or unavailable."
        log.error(msg)
        raise TranscriptionError("ASR service timed out.", detail=msg) from e
    except Exception as e:
        log.error("Space call failed: %s %s", type(e).__name__, str(e)[:500])
        raise


_SOURCE_BY_LANG: dict[SpeechLang, str] = {
    "darija": "moulsot",
    "amazigh": "tamazight-nlp",
}

_PROVIDER_BY_LANG: dict[SpeechLang, str] = {
    "darija": "MoulSot",
    "amazigh": "Tamazight-NLP",
}


def transcribe(
    audio_bytes: bytes,
    filename: str,
    content_type: str | None,
    speech_lang: SpeechLang = "darija",
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
            detail="HF_TOKEN is missing — set it in .env to call the ASR Space.",
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
            text = _call_space(wav_path, speech_lang)
            inference_ms = int((time.time() - start) * 1000)
        except Exception as exc:
            provider = _PROVIDER_BY_LANG[speech_lang]
            log.error("%s Space call failed: %s", provider, exc)
            raise TranscriptionError(
                f"The transcription service ({provider}) is unavailable.",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc
    finally:
        for p in (src, wav_path):
            if p:
                p.unlink(missing_ok=True)
        tmp_dir.rmdir()

    if not text:
        raise EmptyTranscriptionError()

    log.info(
        "Transcription ok lang=%s (%d chars, %d ms)",
        speech_lang, len(text), inference_ms,
    )
    return (
        TranscriptionResult(text=text, source=_SOURCE_BY_LANG[speech_lang]),
        inference_ms,
    )
