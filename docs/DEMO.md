# HackAI — Live Demo Playbook

## Before you walk on stage

1. `DEMO_MODE=false` for the real "wow" (Groq is fast). Keep
   `DEMO_MODE=true` as the **panic switch** if WiFi dies.
2. Start backend, then frontend (see root README).
3. Open `http://localhost:3000`. Hard-refresh once.
4. Have a product photo on the machine and rehearse a 10-second Darija
   line (or use the seeded one).

## The 60-second script

1. "Moroccan artisans make world-class goods but can't write English
    listings. Watch." → drop a photo.
2. Hold the mic, say one Darija sentence about the product, stop.
3. Click **Generate listing**.
4. Groq returns in ~1–2s → premium card appears: title, story, features,
   SEO tags, price. "That's an Etsy-ready listing from a voice note."
5. Expand the transcription to show the Darija → English leap.

## If something breaks

| Symptom                | Fix                                                    |
| ---------------------- | ------------------------------------------------------ |
| No internet / API down | `DEMO_MODE=true`, restart backend — seeded flawless run |
| Mic blocked            | Use Chrome, allow mic, or fall back to `DEMO_MODE`     |
| Backend unreachable    | Frontend shows a clear message; restart `uvicorn`      |
| Ugly LLM output        | Pipeline auto-retries, then Gemini, then seeded card   |

The system is designed so **the demo never shows an error screen.**
