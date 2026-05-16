import pytest

from app.errors import ValidationError
from app.services.transcription import validate_audio
from app.services.orchestrator import validate_image


def test_audio_rejects_empty():
    with pytest.raises(ValidationError):
        validate_audio("a.wav", "audio/wav", 0)


def test_audio_rejects_oversize():
    with pytest.raises(ValidationError):
        validate_audio("a.wav", "audio/wav", 999 * 1024 * 1024)


def test_audio_rejects_bad_type():
    with pytest.raises(ValidationError):
        validate_audio("a.txt", "text/plain", 1000)


def test_audio_accepts_wav():
    validate_audio("voice.wav", "audio/wav", 2048)  # no raise


def test_audio_accepts_by_extension_when_ct_missing():
    validate_audio("voice.mp3", None, 2048)  # no raise


def test_image_rejects_bad_type():
    with pytest.raises(ValidationError):
        validate_image("doc.pdf", "application/pdf", 1000)


def test_image_accepts_png():
    validate_image("rug.png", "image/png", 4096)  # no raise
