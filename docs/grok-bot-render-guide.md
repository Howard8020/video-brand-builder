# VBB Render API Guide for the Grok Bot

> **Purpose:** You are a marketing specialist. You write ad briefs and storyboards.
> This guide tells you how to format them as JSON and send them to VBB's
> `/api/render-direct` endpoint to produce finished social-ready video ads.
>
> **You do not need to know how Veo works.** You just need to fill in the JSON
> fields below with good marketing copy, and VBB handles the rest: prompt
> assembly, video generation, audio, segment joining, on-screen text overlay,
> and delivery.

---

## Quick reference

```
POST https://tender-nurturing-production.up.railway.app/api/render-direct
Authorization: Bearer <JWT>
Content-Type: application/json
```

Get the JWT first:
```
POST https://tender-nurturing-production.up.railway.app/api/auth/login
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>
```

Then submit the render, then poll:
```
GET https://tender-nurturing-production.up.railway.app/api/render-direct/<job_id>
Authorization: Bearer <JWT>
```

When `status` = `"done"`, `video_url` is the finished video path (relative to the
API base — prepend `https://tender-nurturing-production.up.railway.app`).

---

## The JSON structure

Send this object to `POST /api/render-direct`:

```json
{
  "brief": { ... },         // the ad's business context
  "continuity": { ... },    // the presenter + setting (fixed across all clips)
  "scenes": [ ... ],        // the storyboard — one entry per clip
  "tier": "pro",            // "standard" (720p, $0.10/s) or "pro" (1080p, $0.40/s)
  "settings": {}             // optional: leave empty for defaults
}
```

---

## 1. `brief` — the ad's business context

```json
{
  "clientName": "Apple Blossom",
  "category": "Apparel",
  "serviceLine": "AI-designed matching custom shirts for families",
  "goal": "drive free design starts for matching Christmas family shirts",
  "audience": "families shopping for matching holiday shirts",
  "tones": ["warm", "cheerful", "cozy holiday"],
  "cta": "Make yours at design.appleblossomapparel.com",
  "platform": "TikTok",
  "aspect": "9:16",
  "runtime": 24,
  "visualMode": "mixed",
  "brandNotes": "Brand palette: rose #D63384, cream #FFFAF7, sage #8FA396.",
  "avoid": ""
}
```

### Field rules

| Field | Required | Type | Rules |
|-------|----------|------|-------|
| `clientName` | **yes** | string | The brand name. Used in the "don't misspell" guard. |
| `category` | no | string | Business category (e.g. "Apparel", "Contractor", "Fitness"). |
| `serviceLine` | no | string | One-line description of what the business does. |
| `goal` | no | string | What this ad should accomplish (e.g. "drive free design starts"). |
| `audience` | no | string | Who the ad is for. |
| `tones` | no | string[] | 2-3 tone words. E.g. `["warm", "cheerful", "cozy holiday"]`. |
| `cta` | no | string | The exact call-to-action. Verbatim in the final segment's dialogue. |
| `platform` | no | string | `"TikTok"`, `"YouTube Shorts"`, or `"Facebook Reels"`. Default: `"TikTok"`. |
| `aspect` | no | string | `"9:16"` (portrait) or `"16:9"` (landscape). Default: `"9:16"`. |
| `runtime` | no | int | Total ad length in seconds. Default: 24. Must match the sum of scene durations (within 2s). |
| `visualMode` | no | string | `"spokesperson"` (one presenter throughout), `"mixed"` (presenter + screen shots), `"product"` (screen demo, voiceover only). Default: `"spokesperson"`. |
| `brandNotes` | no | string | Brand palette, style notes, visual guidelines. |
| `avoid` | no | string | Phrases or elements to never use. **See the AVOID section below.** |

---

## 2. `continuity` — the presenter + setting

These fields are repeated in every clip's prompt to keep the character and
environment consistent across independent Veo generations.

```json
{
  "mode": "mixed",
  "spokesperson": "Amy",
  "delivery": "warm, cheerful, cozy holiday energy — upbeat and conversational, never flat",
  "setting": "a bright white-brick loft with a black-framed window, golden-hour light, and glass vases of white and pink apple blossoms",
  "lighting": "soft golden-hour light, bright and airy",
  "brand": ""
}
```

### Field rules

| Field | Required | Type | Rules |
|-------|----------|------|-------|
| `mode` | no | string | Must match `brief.visualMode`. Default: `"spokesperson"`. |
| `spokesperson` | no | string | **Just a name** (e.g. `"Amy"`). The system has a reference image for Amy — do not describe her appearance. If using a different character, provide a short visual description here. |
| `delivery` | no | string | Vocal delivery style. One phrase: e.g. `"warm, upbeat, conversational"`. |
| `setting` | no | string | The physical environment. Be concrete: "white-brick loft, golden-hour light, apple blossoms in glass vases". |
| `lighting` | no | string | Lighting description. E.g. `"soft golden-hour light, bright and airy"`. |
| `brand` | no | string | **Leave empty.** On-screen branding is burned in post-production, not sent to the video generator. |

### Amy (the Apple Blossom spokesperson)

If the ad is for Apple Blossom, use `spokesperson: "Amy"` — the system will
automatically use the Amy reference image for character consistency. Do not
describe Amy's appearance in the prompt; the reference image handles that.

---

## 3. `scenes` — the storyboard (most important)

This is an array of segment objects, one per clip. Each clip is independently
generated by Veo and then joined together. **This is where you do the real
creative work.**

```json
[
  {
    "name": "Hook",
    "purpose": "hook",
    "duration": 8,
    "spoken": "Matching Christmas shirts that nobody else on the block has?",
    "action": "A family in matching custom Christmas shirts gathered by a decorated tree, laughing together. Warm, cozy holiday energy.",
    "camera": "Medium shot, gentle push in.",
    "on_screen_text": "MATCHING SHIRTS"
  },
  {
    "name": "CTA",
    "purpose": "cta",
    "duration": 8,
    "spoken": "Designing is free, so start early. Make yours today.",
    "action": "Amy smiles to camera as apple-blossom petals drift down. An end card appears with the brand logo.",
    "camera": "Medium close-up, static.",
    "on_screen_text": "START FREE"
  }
]
```

### Field rules

| Field | Required | Type | Rules |
|-------|----------|------|-------|
| `name` | **yes** | string | Short scene name (e.g. "Hook", "Intro", "CTA"). |
| `purpose` | no | string | `"hook"`, `"benefit"`, `"example"`, or `"cta"`. First scene = hook; last = cta. |
| `duration` | **yes** | int | **Must be exactly 4, 6, or 8.** This is a hard Veo constraint — no other values work. |
| `spoken` | no | string | The exact dialogue for this clip. See word limits below. |
| `action` | no | string | What happens on screen. Concrete and visual — describe what the camera sees, not abstract concepts. |
| `camera` | no | string | One clear camera direction: shot size + movement (e.g. "Medium close-up, static"). |
| `on_screen_text` | no | string | Short label burned in post (see rules below). Empty string `""` = no text. |

### Duration rules (critical)

- Each `duration` must be **4, 6, or 8** — no other values are accepted.
- The sum of all durations should be within 2 seconds of `brief.runtime`.
- Common ad lengths:
  - 16s = 2 × 8s
  - 24s = 3 × 8s or 4 × 6s
  - 32s = 4 × 8s
  - 40s = 5 × 8s

### Spoken dialogue word limits

Veo generates audio that matches the dialogue. If the line is too long for the
clip duration, it will rush, truncate, or drift. If the line is too **short**
for the clip duration, Veo fills the dead air with **invented speech
(gibberish)** — the model can't leave silence, so it makes up words. At 150
words per minute:

| Duration | Max words | Min words | Example |
|----------|-----------|-----------|---------|
| 4s | ~10 | 4-5 | "Matching shirts nobody else has?" |
| 6s | ~15 | 8-10 | "Just tell me what you picture. One sentence." |
| 8s | ~20 | 12-15 | "I'll ask a couple of quick questions. Then you check the design outline and change anything." |

**Match the clip length to the line.** If a line has only 5 words, use a 4s
clip — not an 8s clip. Short lines in long clips cause invented speech.

**Keep it short.** If you're not sure, cut words. Shorter lines produce clearer
audio. One speaker per clip — don't put two people's dialogue in one scene.

**The system already instructs Veo not to add extra speech** beyond the
scripted dialogue, but the most reliable fix is matching clip duration to
line length — don't rely on the instruction alone.

### On-screen text rules

On-screen text is **not generated by Veo** — it is burned in post-production with
ffmpeg after the video is assembled. This means:

- The text will always be **correctly spelled** (it's a font overlay, not AI-generated).
- Keep it **short**: 1-3 words, ALL CAPS works best.
- Good: `"MATCHING SHIRTS"`, `"START FREE"`, `"DESCRIBE IT"`, `"SEE IT"`
- Bad: `"Step 1: Describe your dream design at design.appleblossomapparel.com"` (too long for the text bar)
- Empty string `""` = no on-screen text for that clip.
- The text appears as a top-center label during the clip's time range.
- A persistent lower-third bar (brand name + tagline) is added to the entire video automatically.

### Action/camera rules

- `action` should be **concrete and filmable**: "A family in matching shirts by a tree, laughing" — not "show the value proposition."
- `camera` should be **one direction**: "Medium close-up, static" or "Slow push-in" — not "dynamic camera showing various angles."
- Avoid asking for complex hand interactions ("fingers typing on a phone screen") — Veo struggles with hands. Keep action simple: full-body or upper-body shots, people standing/sitting, simple props.

---

## 4. `tier` — quality and cost

| Tier | Resolution | Cost per second | Use when |
|------|------------|-----------------|----------|
| `"standard"` | 720p | $0.10/s | Drafts, tests, fast previews |
| `"pro"` | 1080p | $0.40/s | Final deliverable, client-facing |

For a 24s ad: standard = $2.40, pro = $9.60.
For a 40s ad: standard = $4.00, pro = $16.00.

**Use `"pro"` for finished ads. Use `"standard"` only for quick tests.**

---

## 5. AVOID — things that break Veo

The `avoid` field in the brief and the AVOID section of the prompt exist because
Veo has specific failure modes. Include these in `avoid` when relevant:

**Always avoid (put in every brief's `avoid` field):**
```
years or dates with years, misspelled text, garbled text, distorted hands, extra spoken words beyond the dialogue, real brand logos, trademarked characters, song lyrics, cartoonish or plastic-looking people
```

**Situational avoids:**
- `"ending on Amy instead of the finished product"` — for product ads
- `"long talking-head shots of Amy after 4 seconds"` — keep Amy's clips moving
- `"showing the phone screen as the final shot"` — end on the product, not the UI

---

## 6. A complete example

```json
{
  "brief": {
    "clientName": "Apple Blossom",
    "category": "Apparel",
    "serviceLine": "AI-designed matching custom shirts for families",
    "goal": "drive free design starts for matching Christmas family shirts",
    "audience": "families shopping for matching holiday shirts",
    "tones": ["warm", "cheerful", "cozy holiday"],
    "cta": "Make yours at design.appleblossomapparel.com",
    "platform": "TikTok",
    "aspect": "9:16",
    "runtime": 40,
    "visualMode": "mixed",
    "brandNotes": "Brand palette: rose #D63384, cream #FFFAF7, sage #8FA396.",
    "avoid": "years or dates with years, distorted hands, garbled text, cartoonish people, real brand logos, trademarked characters, song lyrics, ending on Amy instead of the finished shirt"
  },
  "continuity": {
    "mode": "mixed",
    "spokesperson": "Amy",
    "delivery": "warm, cheerful, cozy holiday energy — upbeat and conversational, never flat",
    "setting": "a bright white-brick loft with a black-framed window, golden-hour light, and glass vases of white and pink apple blossoms",
    "lighting": "soft golden-hour light, bright and airy",
    "brand": ""
  },
  "scenes": [
    {
      "name": "Hook",
      "purpose": "hook",
      "duration": 8,
      "spoken": "Matching Christmas shirts that nobody else on the block has?",
      "action": "A family in matching custom Christmas shirts gathered by a decorated tree, laughing together. Warm, cozy holiday energy.",
      "camera": "Medium shot, gentle push in.",
      "on_screen_text": "MATCHING SHIRTS"
    },
    {
      "name": "Intro",
      "purpose": "benefit",
      "duration": 8,
      "spoken": "Hi! I'm Amy, your AI Design Assistant. Let's make yours.",
      "action": "Amy waves warmly to camera in the loft, relaxed and welcoming.",
      "camera": "Medium close-up, static.",
      "on_screen_text": ""
    },
    {
      "name": "Describe",
      "purpose": "example",
      "duration": 8,
      "spoken": "Just tell me what you picture. One sentence is plenty.",
      "action": "Amy holds a phone, showing the design screen. She types a description of a cozy log cabin in the snow with dogs in Santa hats.",
      "camera": "Over-the-shoulder close-up on the phone screen, then back to Amy.",
      "on_screen_text": "DESCRIBE IT"
    },
    {
      "name": "Mockup",
      "purpose": "example",
      "duration": 8,
      "spoken": "Then you see it on a shirt. Pick a color. Add your family name.",
      "action": "The design appears on a shirt mockup. The shirt color switches from red to green. A family group chat shows a shared link.",
      "camera": "Slow push-in on the shirt mockup, then screen capture of the chat.",
      "on_screen_text": "SEE IT"
    },
    {
      "name": "CTA",
      "purpose": "cta",
      "duration": 8,
      "spoken": "Designing is free, so start early. Make yours at design.appleblossomapparel.com.",
      "action": "Amy smiles to camera as apple-blossom petals drift down. An end card appears with the brand logo.",
      "camera": "Medium close-up, static.",
      "on_screen_text": "START FREE"
    }
  ],
  "tier": "pro",
  "settings": {}
}
```

---

## 7. API flow

### Step 1: Login

```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=test@vbb.internal&password=VBB2026Test!
```

Response: `{"access_token": "eyJ...", "token_type": "bearer", ...}`

### Step 2: Submit render

```
POST /api/render-direct
Authorization: Bearer eyJ...
Content-Type: application/json

{ ...the JSON above... }
```

Response: `{"job_id": "rd_abc123def456", "status": "queued", "tier": "pro", "segment_count": 5}`

### Step 3: Poll (every 10 seconds)

```
GET /api/render-direct/rd_abc123def456
Authorization: Bearer eyJ...
```

Response while rendering:
```json
{"status": "rendering", "segments_done": 2, "segments_total": 5, "segments_failed": 0, "video_url": null}
```

Response when done:
```json
{"status": "done", "segments_done": 5, "segments_total": 5, "video_url": "/assembled/rd_abc123def456.mp4"}
```

### Step 4: Get the video

The `video_url` is relative to the API base. Full URL:
```
https://tender-nurturing-production.up.railway.app/assembled/rd_abc123def456.mp4
```

Download with `GET` + `Authorization: Bearer` header, or serve directly.

---

## 8. What VBB handles automatically (you don't write these)

| Step | What VBB does |
|------|---------------|
| Prompt assembly | Combines your brief + continuity + scene into a per-clip Veo prompt with dialogue attribution and audio instructions |
| Audio generation | Passes `generate_audio=True` to Veo so every clip has audible speech |
| Character consistency | Uses the Amy reference image for all Apple Blossom clips so Amy looks the same across segments |
| On-screen text | Burns your `on_screen_text` labels in post with ffmpeg (correctly spelled, always readable) |
| Lower-third branding | Burns a persistent brand bar (name + tagline) at the bottom for the entire ad |
| Segment assembly | Joins clips with lossless stream-copy, loudness-normalized audio, and faststart |
| Transient retry | If a clip fails with a transient GCP error, VBB retries it automatically |

---

## 9. Common mistakes to avoid

| Mistake | What happens | Fix |
|---------|-------------|-----|
| `duration` set to 5 or 10 | API rejects with 400 | Use only 4, 6, or 8 |
| Dialogue too long for the clip | Audio rushes or truncates | Keep to the word limits in §3 |
| `spokesperson` has a visual description | Amy looks inconsistent | Use just `"Amy"` — the reference image handles appearance |
| `on_screen_text` is a full sentence | Text bar overflows | Keep to 1-3 words, ALL CAPS |
| `brand` field has text | Garbled text in the video | Leave `brand` empty — branding is burned in post |
| `avoid` is empty | Veo generates hands, years, or garbled text | Always include the standard avoids from §5 |
| `runtime` doesn't match sum of durations | Ad is longer or shorter than intended | Set `runtime` = sum of all `duration` values |
| Using `"standard"` for a client deliverable | 720p looks soft | Use `"pro"` for 1080p on finished ads |

---

## 10. Rate limits

- **2 renders per hour** per user (rate limiter)
- **1 ad per day** per user (daily cap)
- **12 concurrent segment jobs** per user
- These are configured via `VBB_RENDER_LIMIT_PER_HOUR`, `VBB_RENDER_LIMIT_PER_DAY`,
  and `VBB_RENDER_MAX_CONCURRENT` on the backend. Ask John to raise them if needed.
