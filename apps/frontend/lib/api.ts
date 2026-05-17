import type { ArtisanProfile } from "./artisan";
import type { SpeechLang } from "./speechLang";
import type { ProcessResponse } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function processArtisanProduct(
  audio: Blob,
  image: File | null,
  artisan: ArtisanProfile | null,
  speechLang: SpeechLang = "darija",
): Promise<ProcessResponse> {
  console.log(
    `[API] Processing: audio=${audio.size} bytes, image=${image?.size ?? "none"}, speech_lang=${speechLang}`,
  );

  const form = new FormData();
  form.append("audio", audio, "recording.webm");
  if (image) form.append("image", image);
  if (artisan) form.append("artisan", JSON.stringify(artisan));
  form.append("speech_lang", speechLang);

  let resp: Response;
  try {
    console.log(`[API] POST ${API_URL}/api/process`);
    resp = await fetch(`${API_URL}/api/process`, {
      method: "POST",
      body: form,
    });
    console.log(`[API] Response status: ${resp.status}`);
  } catch (e) {
    console.error("[API] Fetch failed:", e);
    throw new Error(
      "Cannot reach the backend. Is it running on port 8000?",
    );
  }

  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    const msg = body?.error || `Request failed (${resp.status})`;
    console.error("[API] Error response:", body);
    throw new Error(body?.detail ? `${msg} — ${body.detail}` : msg);
  }
  const data = await resp.json();
  console.log("[API] Success:", {
    asr_model: data.meta.asr_model,
    text_len: data.transcription.text.length,
  });
  return data;
}
