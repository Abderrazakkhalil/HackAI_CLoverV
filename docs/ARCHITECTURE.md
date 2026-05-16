# HackAI — Architecture

## Flow

```
[ Photo ] ─┐
           ├─► FastAPI /api/process ─► Orchestrator ─► MoulSot STT ─► Groq LLM ─► ProductCard ─► UI
[ Darija ]─┘                                │              │ (fallback)   │ (fallback)
 voice note                                 │            mock          Gemini → seeded
```

## Components

| Layer            | Tech                          | Responsibility                                  |
| ---------------- | ----------------------------- | ----------------------------------------------- |
| Frontend         | Next.js 14 / React / Tailwind | Upload, push-to-talk, premium card render       |
| REST API         | FastAPI                       | HTTP surface for the web app                    |
| MCP server       | `mcp` SDK (stdio)             | Same capabilities for any MCP agent             |
| Service layer    | Python                        | `transcription`, `llm`, `orchestrator` (shared) |
| Validation       | Pydantic                      | `ProductCard` contract enforced on every output |

## Key design decisions

- **One service layer, two front doors.** REST and MCP both call
  `services/orchestrator.run_pipeline` — zero logic duplication.
- **Graceful degradation everywhere.** Missing key / downtime / timeout /
  malformed JSON never crashes a demo: STT → mock, LLM → Gemini → seeded card.
- **Output is never trusted.** LLM text is JSON-extracted, schema-validated,
  and retried-on-failure before it can reach a user.
- **`DEMO_MODE`** bypasses all networks and returns seeded data — a hard
  guarantee that the live demo works on hostile conference WiFi.
- **MoulSot is configurable** (`MOULSOT_API_URL` / key) since it has no
  public spec; absence is handled, not assumed.

## Trade-offs

- No DB / auth / storage — out of MVP scope, would add demo risk.
- Image is passed through as a data URL (no vision model) — keeps latency
  low; the LLM gets a filename hint only.
- Seeded last-resort card favors a flawless demo over surfacing hard errors.
