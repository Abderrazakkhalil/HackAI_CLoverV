# Amazigh ASR — Teammate Setup Guide

This commit adds **Amazigh (Tamazight) speech-to-text** alongside the existing Darija ASR. Users now pick which language they will speak before recording, and the audio is routed to the matching model.

## What's new

- **New ASR model**: [`Tamazight-NLP/ASR`](https://huggingface.co/spaces/Tamazight-NLP/ASR) (NVIDIA NeMo, `ayymen/stt_zgh_fastconformer_ctc_small`)
- **Speech-language picker UI**: A segmented control above the mic in `InputScreen` lets the user choose **الدارجة (Darija)** or **ⵜⴰⵎⴰⵣⵉⵖⵜ (Amazigh)**
- **End-to-end routing**: The choice flows through `FormData` → `/api/process` (`speech_lang` field) → orchestrator → `transcribe()` → correct Gradio Space
- **Better error tracking**: Added detailed logging across the pipeline (route → orchestrator → Space call) and timeout handling

## Setup

### 1. Pull and install

```bash
git pull origin main
```

**Backend** (Python 3.13):
```powershell
cd "<repo-root>"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r apps/backend/requirements.txt
```

**Frontend** (Node 18+):
```powershell
cd apps/frontend
npm install
```

### 2. Create `.env` at the repo root

```env
# Required: Hugging Face token (for both Darija and Amazigh Spaces)
HF_TOKEN=hf_your_token_here

# Required: Groq API key (for the LLM stage)
GROQ_API_KEY=gsk_your_key_here

# Optional
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
LOG_LEVEL=INFO
```

- Get an HF token: <https://huggingface.co/settings/tokens> (read access is enough)
- Get a Groq key: <https://console.groq.com>

> ⚠️ **Important**: Settings are cached at backend startup. If you change `.env`, **restart uvicorn** — `--reload` only watches Python files.

### 3. Run

Two terminals:

```powershell
# Terminal 1 — Backend
cd apps/backend
..\..\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
# Terminal 2 — Frontend
cd apps/frontend
npm run dev
```

Open <http://localhost:3000>. You should see the new pill picker above the mic button.

### 4. Verify it works

- Hit `http://localhost:8000/api/health` — should return `"providers": {"moulsot": true, "groq": true}`.
- Record a short Darija clip → response `meta.asr_model` should be `"moulsot-v0.3"`.
- Switch to **Amazigh**, record a clip → response `meta.asr_model` should be `"tamazight-nlp-asr"`.

## How it works under the hood

| Layer | File | Change |
|---|---|---|
| Config | [apps/backend/app/config.py](../apps/backend/app/config.py) | Added `amazigh_asr_space`, `amazigh_asr_api_name`, `amazigh_asr_timeout_s` |
| Schemas | [apps/backend/app/schemas.py](../apps/backend/app/schemas.py) | Added `SpeechLang = Literal["darija", "amazigh"]` |
| Transcription | [apps/backend/app/services/transcription.py](../apps/backend/app/services/transcription.py) | `_call_space` branches on `speech_lang`; logs every step |
| Orchestrator | [apps/backend/app/services/orchestrator.py](../apps/backend/app/services/orchestrator.py) | Threads `speech_lang` through; fills `Meta.asr_model` / `asr_provider` accordingly |
| Route | [apps/backend/app/routes.py](../apps/backend/app/routes.py) | `/api/process` accepts `speech_lang` form field (defaults to `"darija"`) |
| Frontend lib | [apps/frontend/lib/speechLang.ts](../apps/frontend/lib/speechLang.ts) | New `SpeechLang` type + localStorage persistence |
| UI picker | [apps/frontend/components/recording/SpeechLangPicker.tsx](../apps/frontend/components/recording/SpeechLangPicker.tsx) | New segmented control, disabled while recording |
| Screen | [apps/frontend/components/screens/InputScreen.tsx](../apps/frontend/components/screens/InputScreen.tsx) | Renders picker, swaps hint copy per language |
| Page state | [apps/frontend/app/page.tsx](../apps/frontend/app/page.tsx) | Owns `speechLang` state + passes to API |
| API client | [apps/frontend/lib/api.ts](../apps/frontend/lib/api.ts) | Appends `speech_lang` to FormData; added `[API]` console logging |
| i18n | [apps/frontend/lib/i18n.ts](../apps/frontend/lib/i18n.ts) | Added `speechLang.*` and `rec.describe.amazigh` keys in AR/FR/EN |

The Tamazight Space exposes `get_transcripts(audio_path)` in two `gr.Interface` tabs; we call the first via `api_name="/predict"`. The audio is normalised to 16 kHz mono WAV server-side (bundled ffmpeg via `imageio-ffmpeg`) so both Spaces accept it.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `"providers": {"groq": false}` in `/api/health` | `.env` not loaded | Make sure `.env` is at the **repo root**, then restart uvicorn |
| `AuthenticationError: 401 invalid_api_key` | Stale Groq key cached | Restart uvicorn — settings are `@lru_cache`d |
| Request hangs at 100% with no error | HF Space is cold-starting | Wait ~30–60s; logs will show "Initializing client..." then the call. Now bounded by `amazigh_asr_timeout_s` / `asr_timeout_s` (120 s) |
| `The transcription service (Tamazight-NLP) is unavailable` | Wrong `api_name`, Space is down, or token lacks access | Check backend logs for the exception class; try `gradio_client.Client("Tamazight-NLP/ASR").view_api()` to confirm the endpoint name |
| Picker disabled / grayed out | You're mid-recording | Stop recording first — the picker is intentionally locked during capture |

## Where to look for logs

- **Backend terminal** — `hackai.api`, `hackai.pipeline`, `hackai.stt`, `hackai.llm` (INFO level)
- **Browser DevTools console** — `[API]` logs trace the request lifecycle
