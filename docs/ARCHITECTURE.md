# Hirfati — Architecture

## Flow

```
[ Photo ]   ─┐
[ Darija ]   ─┤─► FastAPI /api/process ─► Orchestrator ─► MoulSot STT ─► Groq LLM ─► Product+Meta ─► UI
[ Artisan ]  ─┘                                              │             │ llama-3.3-70b fallback
 (profile)                                            ffmpeg 16k mono   strict JSON + validate + retry
```

Any STT/LLM failure raises a clear, typed error — nothing is fabricated.

## Components

| Layer         | Tech                          | Responsibility                                   |
| ------------- | ----------------------------- | ------------------------------------------------ |
| Frontend      | Next.js 14 / React / Tailwind | Onboarding, upload, push-to-talk, localized card |
| i18n          | React context (AR/FR/EN)      | AR default + RTL, persisted, drives post language |
| REST API      | FastAPI                       | HTTP surface for the web app                     |
| MCP server    | `mcp` SDK (stdio)             | Same pipeline as tools/prompt for any MCP agent  |
| Service layer | Python                        | `transcription`, `llm`, `orchestrator` (shared)  |
| Validation    | Pydantic                      | `Product` contract enforced on every LLM output  |

## Key design decisions

- **One service layer, two front doors.** REST and MCP both call
  `services/orchestrator.run_pipeline` — zero logic duplication.
- **No silent fallbacks.** Missing key / downtime / timeout / malformed
  JSON raise typed errors surfaced to the user (`TranscriptionError`,
  `LLMError`); the pipeline never substitutes fabricated data.
- **Output is never trusted.** LLM text is JSON-extracted, schema-validated
  against the multilingual `Product`, and retried (then a second Groq
  model) before it can reach a user.
- **Blocking SDKs off the event loop.** `gradio_client` / `groq` run in
  worker threads via `asyncio.to_thread`, keeping FastAPI async.
- **Artisan profile travels with the post.** Captured at sign-up
  (frontend `localStorage`), echoed by the backend into the response so
  it is part of the canonical listing (REST + MCP).

## Trade-offs

- No DB / auth / storage — out of MVP scope. Artisan profile is
  per-device (`localStorage`), not a server account.
- Image is passed through as a data URL (no vision model) — keeps latency
  low; the LLM works from the transcription only.
- Requires `GROQ_API_KEY` + `HF_TOKEN`; without them the relevant step
  fails loudly by design rather than degrading.
