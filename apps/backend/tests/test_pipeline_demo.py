"""Demo-mode pipeline must work fully offline (no keys, no network)."""

import importlib

import pytest


@pytest.fixture
def demo_settings(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("HF_TOKEN", "")
    import app.config as config

    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


async def test_demo_pipeline_end_to_end(demo_settings):
    from app.services import orchestrator

    importlib.reload(orchestrator)
    resp = await orchestrator.run_pipeline(
        audio_bytes=b"fake-bytes",
        audio_filename="voice.webm",
        audio_content_type="audio/webm",
    )
    assert resp.demo_mode is True
    assert resp.transcription.source == "mock"
    assert resp.meta.pipeline_version
    assert resp.meta.asr_model == "moulsot-v0.3"

    p = resp.product
    assert p.title.en and p.title.fr and p.title.ar
    assert p.description.en
    assert p.price.currency == "MAD"
    assert p.price.price_usd_estimate > 0
    assert p.tags and p.materials
    assert p.origin.country == "Morocco"
    # transcript is forced to the (mock) input transcription
    assert p.raw_transcript == resp.transcription.text
