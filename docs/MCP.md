# Hirfati — MCP Server

## Why MCP here

Hirfati's value is a small set of crisp capabilities: *transcribe Darija*
and *write a validated multilingual listing*. MCP exposes them as typed,
structured tools so **any** MCP client (Claude Desktop, an IDE, an agent
orchestrator) can drive the artisan workflow directly — the exact same
code the web app uses, with no bespoke REST integration. Tools + prompt
give an agent the actions and the copywriter instruction.

## Surface

### Tools

| Tool                       | Input                                                | Output                       |
| -------------------------- | ---------------------------------------------------- | ---------------------------- |
| `transcribe_audio`         | `audio_base64`, `filename`                           | `{text, language, source, inference_ms}` |
| `generate_product_listing` | `transcription`                                      | `{product, llm_model}`       |
| `process_artisan_product`  | `audio_base64`, `image_base64?`, `artisan_*?`        | full `ProcessResponse`       |

### Prompts

- `artisan_copywriter(transcription)` — the reusable system + user prompt
  that turns a Darija transcription into the multilingual listing JSON.

## How orchestration works

`process_artisan_product` → `orchestrator.run_pipeline` → `transcribe()`
(MoulSot Gradio Space) → `generate_product()` (Groq Llama-4-Scout →
`llama-3.3-70b` fallback) → Pydantic-validated `Product` + `Meta`.
Identical to the REST path. Failures raise typed errors — no fabricated
output.

## Run / register

```bash
cd apps/backend
python mcp_server.py            # stdio transport
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hirfati": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "ABSOLUTE/PATH/TO/apps/backend"
    }
  }
}
```
