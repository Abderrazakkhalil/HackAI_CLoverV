# 🧶 Hirfati — Artisan Listing Studio

Turn a **product photo** + a **Darija voice note** into a **rich multilingual
e-commerce listing** (EN/FR/AR title & description, price in MAD + USD,
materials, dimensions, origin, SEO tags) — instantly.

> Built for Moroccan artisans who make world-class goods but don't speak
> English or know e-commerce. Speak → Generate → sell globally.

---

## ✨ What it does

```
Photo  ┐
       ├─► MoulSot Space (Darija STT) ─► Groq Llama-4-Scout ─► validated Product ─► premium UI
Voice  ┘            ↓ mock                ↓ llama-3.3-70b fallback
                                          ↓ seeded card (last resort)
```

- **Speech-to-Text:** MoulSot via Gradio Space `atlasia/MoulSot.v0.3`
  (`gradio_client`; bundled ffmpeg normalises audio; mock fallback)
- **LLM:** Groq `meta-llama/llama-4-scout-17b-16e-instruct` (primary),
  `llama-3.3-70b-versatile` (fallback), strict JSON + retry
- **MCP server:** same capabilities exposed to any MCP agent
- **Demo-safe mode:** seeded data, zero network — the demo never fails

## 🗂 Structure

```
apps/
  backend/    FastAPI + shared services + MCP server
  frontend/   Next.js 14 + TS + Tailwind (dark Vercel/Stripe UI)
packages/
  shared-types/  TS + JSON schema (single contract source)
docs/         ARCHITECTURE.md · MCP.md · DEMO.md
scripts/      test_env.py · seed_demo.py
```

---

## 🚀 Setup

### 0. Prereqs

Python 3.10+, Node 18+, a microphone, a Groq API key and a Hugging Face
token (both free tiers work).

### 1. Configure secrets

```bash
cp .env.example .env      # then fill GROQ_API_KEY + HF_TOKEN
```

| Variable       | Required | Notes                                       |
| -------------- | -------- | ------------------------------------------- |
| `GROQ_API_KEY` | yes\*    | LLM extraction (\*not needed if DEMO_MODE)  |
| `HF_TOKEN`     | yes\*    | MoulSot Space auth; mock used if absent     |
| `DEMO_MODE`    | no       | `true` = no network, seeded data            |

ffmpeg is **not** required system-wide — a binary is bundled via
`imageio-ffmpeg`.

### 2. Backend

```bash
cd apps/backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Check: <http://localhost:8000/api/health> · Docs: <http://localhost:8000/docs>

### 3. Frontend

```bash
cd apps/frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>.

### 4. MCP server (optional)

```bash
cd apps/backend
python mcp_server.py        # stdio — see docs/MCP.md to register
```

---

## 🧪 API examples

```bash
# Health
curl http://localhost:8000/api/health

# Text-only generation (no audio needed)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"transcription":"zarbya soof tabi3i hamra kbira khdmtha b yeddi"}'

# Full pipeline
curl -X POST http://localhost:8000/api/process \
  -F "audio=@voice.wav" -F "image=@rug.jpg"
```

Validated response shape:

```json
{
  "product_title": "Handwoven Atlas Berber Wool Rug — Crimson & Honey",
  "marketing_description": "Knotted by hand in the Atlas foothills…",
  "features": ["100% natural sheep wool", "Hand-knotted", "..."],
  "suggested_price_usd": "$420 - $560",
  "seo_tags": ["berber rug", "moroccan rug", "..."]
}
```

## 🔌 MCP

A real MCP server (tools / resources / prompts) reusing the same pipeline.
See [docs/MCP.md](docs/MCP.md). Tools: `transcribe_audio`,
`generate_product_listing`, `process_artisan_product`.

## 🧷 Tests

```bash
cd apps/backend
pytest -q
```

Covers file validation, JSON sanitization, schema enforcement, and the
demo-mode pipeline.

## 🛟 Troubleshooting

| Problem                       | Fix                                                  |
| ----------------------------- | ---------------------------------------------------- |
| Backend unreachable from UI   | Backend must run on `:8000`; check CORS origin       |
| `GROQ_API_KEY` missing        | Set it, or `DEMO_MODE=true` for an offline demo      |
| Mic not working               | Use Chrome, allow mic permission                     |
| MoulSot down / no key         | Auto-falls back to mock transcription                |
| Garbled LLM JSON              | Auto sanitize + retry → Gemini → seeded card         |
| `pip install` fails on Win    | Upgrade pip; ensure Python 3.10+                     |

## 🧭 Demo

Step-by-step stage script + panic switch: [docs/DEMO.md](docs/DEMO.md).

## 🔭 Future improvements

- Vision model to read the photo (not just a filename hint)
- Supabase storage + listing history
- One-click export to Etsy/Shopify
- Streaming generation for sub-second perceived latency
- Multi-product batch mode, Docker compose

---

Architecture rationale & trade-offs: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
