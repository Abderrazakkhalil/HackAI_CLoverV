import type { ArtisanProfile } from "./artisan";
import type { ProcessResponse } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function processArtisanProduct(
  audio: Blob,
  image: File | null,
  artisan: ArtisanProfile | null,
): Promise<ProcessResponse> {
  const form = new FormData();
  form.append("audio", audio, "recording.webm");
  if (image) form.append("image", image);
  if (artisan) form.append("artisan", JSON.stringify(artisan));

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

export interface FacebookPublishResult {
  status: "success";
  post_id: string;
}

/**
 * Publish the artisan's post to the linked Facebook Page.
 * `imageDataUrl` is the photo the artisan uploaded at the start (a
 * base64 data URL). When null, a text-only Page post is published.
 * The backend uses the Page token/ID configured server-side (.env).
 */
export async function publishFacebookPost(
  caption: string,
  imageDataUrl: string | null,
): Promise<FacebookPublishResult> {
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}/api/social/facebook/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caption,
        image_data_url: imageDataUrl,
      }),
    });
  } catch {
    throw new Error(
      "Cannot reach the backend. Is it running on port 8000?",
    );
  }

  const body = await resp.json().catch(() => null);
  if (!resp.ok) {
    // FastAPI/typed-error envelope → surface the most useful message.
    const detail =
      body?.detail?.message ||
      body?.detail ||
      body?.error?.message ||
      body?.error ||
      `Request failed (${resp.status})`;
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail),
    );
  }
  return body as FacebookPublishResult;
}
