import type { ProcessResponse } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function processArtisanProduct(
  audio: Blob,
  image: File | null,
): Promise<ProcessResponse> {
  const form = new FormData();
  form.append("audio", audio, "recording.webm");
  if (image) form.append("image", image);

  let resp: Response;
  try {
    resp = await fetch(`${API_URL}/api/process`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new Error(
      "Cannot reach the backend. Is it running on port 8000?",
    );
  }

  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    const msg = body?.error || `Request failed (${resp.status})`;
    throw new Error(body?.detail ? `${msg} — ${body.detail}` : msg);
  }
  return resp.json();
}

export async function getHealth(): Promise<{
  status: string;
  demo_mode: boolean;
}> {
  const resp = await fetch(`${API_URL}/api/health`);
  return resp.json();
}
