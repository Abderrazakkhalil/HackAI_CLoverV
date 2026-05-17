# 📘 Hirfati — Facebook Publishing

This branch documents the **Facebook posting solution**: how a generated
artisan listing is published to a Facebook Page, end to end.

> Scope: Facebook only. Instagram support was removed — `Platform`,
> models, services, endpoints, MCP tools and the scheduler branch are
> Facebook-exclusive.

---

## ✨ What it does

After a product listing is generated, the artisan publishes it to their
Facebook Page in one step from the app — using **the photo they
uploaded at the start**, or as a **text-only post** when no photo was
provided.

```
Generated listing ─► "Publish to Facebook" modal
                        │
   caption (editable, prefilled from description + SEO tags)
   + uploaded photo (data URL)  ─┐
                                 ├─► POST /api/social/facebook/publish
   no photo  ─────────────────────┘
                        │
        ┌───────────────┴────────────────┐
   has image                          no image
   multipart upload                   text post
   /{page}/photos  (file bytes)       /{page}/feed (message)
                        │
                Meta Graph API ─► live Page post
```

## 🧩 How it works

### Image rule (the core requirement)

The post **always uses the artisan's uploaded photo**:

- **Photo uploaded** → the image bytes are sent to Facebook as a real
  file (`multipart/form-data` `source` on `/{page-id}/photos`). The
  browser only has a base64 *data URL*, which Facebook cannot fetch by
  link — so we decode it server-side and upload the bytes.
- **No photo** → a **text-only** Page post via `/{page-id}/feed` with
  `message`.
- **Public image URL** (used by the scheduler, which only stores a URL)
  → photo by URL on `/{page-id}/photos`.

### Components

| Layer | File | Responsibility |
| ----- | ---- | -------------- |
| REST endpoint | `apps/backend/app/api/social.py` | `POST /api/social/facebook/publish` |
| Service | `apps/backend/app/services/social/facebook_service.py` | Chooses upload / URL / text-only and calls Graph |
| Graph client | `apps/backend/app/services/social/meta_client.py` | Retry policy, credential checks, multipart `files` support |
| Contract | `apps/backend/app/services/social/social_models.py` | `FacebookPublishInput` / `FacebookPublishResult` |
| Frontend modal | `apps/frontend/components/social/FacebookPublishModal.tsx` | Onboarding, editable caption, photo thumbnail / text-only notice, status |
| API client | `apps/frontend/lib/api.ts` | `publishFacebookPost(caption, imageDataUrl)` |

### Request / response

`POST /api/social/facebook/publish`

```json
{
  "caption": "Tapis berbère fait main…  #artisanat #maroc",
  "image_data_url": "data:image/jpeg;base64,/9j/4AAQ…"   // optional
}
```

`FacebookPublishInput`: `caption` is required; `image_data_url`
(uploaded photo) and `image_url` (scheduler / public URL) are both
optional. Success:

```json
{ "status": "success", "post_id": "1100397516495684_122093663781335895" }
```

The post is viewable at `https://www.facebook.com/{post_id}`.

### Reliability

- 3 attempts, exponential backoff (1s/2s/4s); **never** retries
  401/403 — auth/permission failures surface immediately.
- Malformed data URLs raise `FacebookPublishError` (no silent skip).
- Missing credentials raise a typed `SocialConfigError`.

---

## 🔐 Configuration

```bash
cp .env.example .env
```

| Variable | Required | Notes |
| -------- | -------- | ----- |
| `META_ACCESS_TOKEN` | yes | **Page** access token (not a user token) |
| `FACEBOOK_PAGE_ID` | yes | Target Page id |
| `META_APP_ID` / `META_APP_SECRET` | for OAuth | Needed only for the in-app account-linking flow |
| `META_REDIRECT_URI` | for OAuth | Must match a "Valid OAuth Redirect URI" in the Meta app; defaults to `FRONTEND_ORIGIN` |
| `META_GRAPH_VERSION` | no | Defaults to `v21.0` |

**Getting a Page token (fastest):** Graph API Explorer → select the
app → *Get Page Access Token* → pick the Page → grant
`pages_show_list`, `pages_read_engagement`, `pages_manage_posts` →
copy the token + Page id into `.env`.

**OAuth flow (optional, in-app linking):**
`GET /api/social/auth/meta/oauth` returns the consent URL; the
`/auth/meta/callback` exchanges the code, upgrades to a **long-lived**
Page token, discovers Pages (including those owned by a Business
Portfolio), stores them, and returns a copy-paste `env` block.

> The Graph API Explorer token is short-lived (~1h). For a stable demo
> use the OAuth flow (long-lived Page token) or refresh the token.

---

## 🚀 Run it

```bash
# Backend
cd apps/backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (point it at the backend if not on :8000)
cd apps/frontend && npm install && npm run dev
```

Open <http://localhost:3000> → generate a listing → **Publish to
Facebook** → review caption + photo thumbnail → **Publish now** →
*View the post*.

---

## 🧪 Tests

```bash
cd apps/backend
pytest tests/test_facebook.py -v
```

`test_facebook.py` covers: photo-by-URL, uploaded-photo (real file
bytes), text-only post, malformed data URL, missing credentials,
response parsing (`post_id` / `id`, integer ids), long captions, and
input validation. All service calls are mocked — **no API keys
required** to run the suite.

---

## 🛟 Troubleshooting

| Problem | Fix |
| ------- | --- |
| `401/403` on publish | Page token expired/invalid → regenerate `META_ACCESS_TOKEN` |
| `SocialConfigError` | `META_ACCESS_TOKEN` / `FACEBOOK_PAGE_ID` missing in `.env` |
| "no Page" during OAuth | Account isn't a Page admin / Page lives in a Business Portfolio not selected at consent |
| Photo not attached | Ensure the artisan uploaded an image; otherwise it's a text-only post by design |
| Backend unreachable from UI | Point the frontend at the backend (`NEXT_PUBLIC_API_URL`) and check CORS origin |
