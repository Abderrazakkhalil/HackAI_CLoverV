# HackAI — MCP Server

## Why MCP here

HackAI's value is a small set of crisp capabilities: *transcribe Darija* and
*write a validated listing*. MCP exposes them as typed, structured tools so
**any** MCP client (Claude Desktop, an IDE, an agent orchestrator) can drive
the artisan workflow directly — the exact same code the web app uses, with no
bespoke REST integration. Tools/resources/prompts give an agent everything it
needs: the actions, sample data to reason over, and the copywriter prompt.

## Surface

### Tools

| Tool                      | Input                                     | Output                          |
| ------------------------- | ----------------------------------------- | ------------------------------- |
| `transcribe_audio`        | `audio_base64`, `filename`                | `{text, language, source}`      |
| `generate_product_listing`| `transcription`, `image_hint?`            | `{product, llm_provider}`       |
| `process_artisan_product` | `audio_base64`, `image_base64?`, names    | full `ProcessResponse`          |

### Resources

- `product-card://catalog` — list of seeded product ids
- `product-card://{id}` — a seeded, frontend-ready listing (e.g. `berber-rug`)

### Prompts

- `artisan_copywriter(transcription, image_hint)` — the reusable system +
  user prompt that turns Darija into listing JSON.

## How orchestration works

`process_artisan_product` → `orchestrator.run_pipeline` → `transcribe()`
(MoulSot or mock) → `generate_product()` (Groq → Gemini → seeded) →
Pydantic-validated `ProductCard`. Identical to the REST path.

## Run / register

```bash
cd apps/backend
python mcp_server.py            # stdio transport
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hackai": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "ABSOLUTE/PATH/TO/apps/backend"
    }
  }
}
```
