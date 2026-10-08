# Video Brand Builder — Product Guide

## What it is

Video Brand Builder (VBB) is a tool that turns a business brief into a finished,
social-ready video ad. You describe the business, the goal, and the message.
VBB writes the script, directs the scenes, generates the video clips with
synchronized audio, joins them into one file, and burns in your branding —
delivered as a single MP4 ready to post on TikTok, YouTube Shorts, or
Facebook Reels.

### What makes it different

Most AI video tools optimize for speed — generate something fast, post it,
hope it's coherent. VBB optimizes for **coherence**: one consistent
spokesperson across every clip, one message that doesn't drift, and an
approval workflow so nothing publishes by accident.

- **Lock the script first.** Approve every word before any video is generated.
  Once locked, the dialogue doesn't change.
- **One look, every clip.** A continuity profile — spokesperson, setting,
  lighting, brand — is stamped into every segment automatically so the ad
  looks like one shoot, not five random clips.
- **Claims check built in.** Catches invented prices, guarantees, and
  credentials before they reach your ad.
- **On-screen text, done right.** Text is burned in post-production — always
  correctly spelled, always readable, never garbled.
- **Character consistency.** A reference image anchors the spokesperson's
  appearance across all independently generated clips.

---

## The two ways to use VBB

### Path 1: The Web App (human-guided)

Use the web app at `videobrandbuilders.ai` when you want hands-on control over
every step — review the script, revise scenes, approve before rendering. This
is the path for a human operator who wants to craft an ad carefully.

### Path 2: The Render API (programmatic)

Use the `/api/render-direct` endpoint when you want to submit a brief and get a
video back without manual steps — for automation, bots, or batch production.
The API handles the full pipeline server-side and returns a downloadable
video URL. This is the path for a bot or script that constructs ads from
structured data.

---

## Path 1: The Web App Workflow

### Step 1 — Create a Client

Every ad starts with a client profile. Add:
- **Business name** (e.g. "Apple Blossom")
- **Category** (e.g. "Apparel", "Contractor", "Fitness")
- **Brand notes** — tone, colors, style cues the AI should stay consistent with
- **Continuity profile** — spokesperson description, delivery style, setting,
  lighting, and brand elements that get stamped into every scene

The continuity profile is what makes the final ad look like one coherent
shoot. Fill it in once per client and it carries to every ad.

> **Tip:** The dashboard includes pre-built templates (Spring Roofing
> Inspection, Summer AC Tune-Up, Before & After Showcase, Emergency Service,
> Spring Clean-Up) that pre-fill a real-world example. Use one as a starting
> point.

### Step 2 — Start a New Project

Pick your client and describe the ad:
- **Goal** — what should the ad accomplish? (awareness, leads, appointments)
- **Target audience** — who is it for?
- **Tone** — 2-3 words (e.g. "warm, cheerful, cozy holiday")
- **Platform** — TikTok, YouTube Shorts, or Facebook Reels
- **Aspect ratio** — 9:16 (portrait, for vertical ads) or 16:9 (landscape)
- **Runtime** — total ad length in seconds
- **Call to action** — the exact phrase the ad should end on
- **Visual mode** — spokesperson (one presenter throughout), mixed
  (presenter + screen shots), or product (screen demo, voiceover only)

You can paste your own script or let AI draft one from the brief. Each project
goes through a structured pipeline — you can't skip steps or accidentally
publish unfinished work.

### Step 3 — Review & Lock the Script (Gate 1)

The AI generates a segmented script — one dialogue line per clip, with
durations (4, 6, or 8 seconds each). Read it, then:

- **Revise the whole script** with a plain-English instruction ("Make this
  more urgent", "Shorten the first segment").
- **Revise a single segment** — target one line without touching the rest.
- **Generate alternate hooks** — try different opening lines.
- **Run the Claims Lint** — catches invented prices, guarantees, credentials,
  or statistics before they reach a real ad.

When the script is right, click **Approve Script**. This locks the dialogue —
nothing changes after this point.

> **Why lock?** Once the script is locked, the AI generates scene treatments
> (camera, action, on-screen text) for each segment. If you could change the
> dialogue after scenes are designed, the scenes would no longer match the
> words. The lock prevents that drift.

### Step 4 — Review Scenes (Gate 2)

After script lock, the AI drafts one scene treatment per segment:
- **Camera** — shot size and movement (e.g. "Medium close-up, static")
- **Action** — what happens on screen (concrete and filmable)
- **On-screen text** — short label for the scene (burned in post, not in the
  AI-generated video)

Each scene is stamped with your client's continuity profile — same
spokesperson, same setting, same lighting. You can revise individual scenes
without touching the locked dialogue.

When everything looks right, click **Approve Scenes**. This unlocks the
export and render tabs.

### Step 5 — Export or Render

Two options:

**Option A — Export prompts (free):**
Get one copyable prompt per segment in Flow-ready format — duration, aspect
ratio, camera direction, exact dialogue, continuity block, and a social
caption. Paste each prompt into a video generation tool (Google Flow, Veo,
etc.) one at a time, then stitch the clips together yourself. Each prompt is
self-contained; the continuity ensures they'll match.

**Option B — Render with Veo AI (paid):**
Generate actual video clips directly from your approved prompts — no manual
pasting. Choose:
- **Standard** ($9.99/ad) — 720p, Veo 3.1 Fast, good for social media
- **Pro** ($29.99/ad) — 1080p, Veo 3.1, for client-facing deliverables

Click "Render All Segments" and watch the status update as each clip is
generated (1-5 minutes per clip). Buy credits in packs of $20, $50, or $150;
credits never expire.

### Step 6 — Assemble & Download

After all segments render, click **Assemble** to join them into one
platform-ready MP4:
- Video streams are copied losslessly (no re-encode, no quality loss)
- Audio is loudness-normalized to -14 LUFS (so volume doesn't jump at cuts)
- Faststart is applied (so platforms can process it immediately)
- On-screen text and branding are burned in post with ffmpeg (correctly
  spelled, always readable)

Download the finished file and post it.

---

## Path 2: The Render API Workflow

For programmatic use — a bot, script, or automation that submits a brief and
gets a video back without the multi-step UI workflow.

### Step 1 — Authenticate

```
POST https://tender-nurturing-production.up.railway.app/api/auth/login
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>
```

Returns a JWT bearer token.

### Step 2 — Submit the render

```
POST https://tender-nurturing-production.up.railway.app/api/render-direct
Authorization: Bearer <token>
Content-Type: application/json

{
  "brief": { ... },
  "continuity": { ... },
  "scenes": [ ... ],
  "tier": "pro"
}
```

The API accepts the request and returns a job ID immediately. The full
pipeline runs server-side in a background thread.

### Step 3 — Poll for the result

```
GET https://tender-nurturing-production.up.railway.app/api/render-direct/<job_id>
Authorization: Bearer <token>
```

Poll every 10 seconds. When `status` = `"done"`, `video_url` is the finished
video. When `status` = `"failed"`, `error` explains what went wrong.

### What the API handles automatically

You don't write these — the system handles them:
- **Prompt assembly** — combines brief + continuity + scene into a per-clip
  Veo prompt with dialogue attribution and audio instructions
- **Audio generation** — passes `generate_audio=True` to Veo so every clip
  has audible speech with synchronized lip movement
- **Character consistency** — uses a reference image of the spokesperson so
  the same person appears in every clip
- **On-screen text** — burns your text labels in post with ffmpeg (correctly
  spelled, always readable — never garbled)
- **Lower-third branding** — burns a persistent brand bar (name + tagline)
  at the bottom for the entire ad
- **Segment assembly** — joins clips with lossless stream-copy,
  loudness-normalized audio, and faststart
- **Transient retry** — if a clip fails with a transient GCP error, the
  system retries it automatically (up to 2 retries)

### The JSON structure

See `docs/grok-bot-render-guide.md` for the full field-by-field reference
with rules, word limits, and examples. Summary:

**`brief`** — the ad's business context:
- `clientName` (required), `category`, `serviceLine`, `goal`, `audience`,
  `tones`, `cta`, `platform`, `aspect`, `runtime`, `visualMode`,
  `brandNotes`, `avoid`

**`continuity`** — the presenter + setting (fixed across all clips):
- `mode`, `spokesperson` (just a name — the reference image handles
  appearance), `delivery`, `setting`, `lighting`, `brand` (leave empty)

**`scenes`** — the storyboard, one entry per clip:
- `name` (required), `purpose`, `duration` (must be 4, 6, or 8),
  `spoken` (keep to word limits), `action`, `camera`, `on_screen_text`
  (1-3 words, burned in post)

**`tier`** — `"standard"` (720p, $0.10/s) or `"pro"` (1080p, $0.40/s)

---

## How the video is actually made (under the hood)

Understanding this helps you write better prompts and diagnose issues.

### 1. Prompt assembly

Each scene becomes a text prompt for Veo 3.1. The prompt includes:
- **Scene description** — the action and camera direction
- **Dialogue** — the exact spoken words, attributed to the spokesperson
  ("Amy says, with warm delivery: '...'") with an explicit instruction to
  generate clear, audible speech
- **Continuity** — the spokesperson, setting, and lighting, repeated in
  every clip so Veo maintains visual consistency
- **Avoid rules** — things the model should not do (misspell the brand name,
  add extra words, invent prices, show distorted hands)

### 2. Video generation (Veo 3.1)

Each clip is submitted independently to Google Vertex AI's Veo 3.1:
- **Model**: `veo-3.1-fast-generate-001` (Standard, 720p) or
  `veo-3.1-generate-001` (Pro, 1080p)
- **Duration**: 4, 6, or 8 seconds per clip (hard Veo constraint)
- **Audio**: `generate_audio=True` — Veo generates speech, sound effects,
  and ambience natively from the dialogue
- **Person generation**: `"allow_all"` — permits children and families
  (Veo's default `"allow_adult"` rejects scenes with minors)
- **Negative prompt**: suppresses garbled text, illegible words, and
  distorted text
- **Reference images**: a portrait of the spokesperson (e.g. Amy) is
  passed as a `"asset"` reference so the model anchors her appearance
  across all clips

Generation is asynchronous: submit → poll → download. Typical time is
1-5 minutes per clip. Transient failures (GCP `UNAVAILABLE`, empty
responses) are retried automatically. Safety filter rejections are not
retried — they indicate the content was rejected and the prompt needs
revision.

### 3. Assembly

After all clips are generated, they are joined into one MP4:
- **Video stream**: copied losslessly (`-c:v copy`) — no re-encode, no
  quality loss, near-instant
- **Audio**: re-encoded with loudness normalization (`loudnorm` to -14
  LUFS) — so volume doesn't jump at every cut (each clip gets its own
  audio pass from Veo)
- **Container**: MP4 with `+faststart` — moov atom before mdat, so
  platforms can begin processing immediately
- **Fallback**: if stream-copy fails (mismatched parameters), re-encodes
  with libx264/CRF 18 so the user still gets a finished file

### 4. Post-burn (on-screen text + branding)

On-screen text and branding are burned in post-production with ffmpeg's
`drawtext` filter:
- **Lower-third bar**: brand name (bold) + tagline (smaller), semi-
  transparent dark background, persistent for the entire ad
- **Per-segment labels**: short ALL-CAPS text (e.g. "MATCHING SHIRTS",
  "START FREE") at the top of the frame during each segment's time range,
  with a semi-transparent background bar
- Video is re-encoded (libx264, CRF 18); audio is copied losslessly

This is why on-screen text is always correctly spelled — it's a font
overlay, not AI-generated. Veo cannot reliably render text; even short
ALL-CAPS words come back garbled. Burning in post is the only reliable
method.

---

## Pricing

### Render tiers

| Tier | Model | Resolution | Cost per second | Typical ad cost |
|------|-------|------------|----------------|----------------|
| Standard | Veo 3.1 Fast | 720p | $0.10/s | $2.40 (24s) |
| Pro | Veo 3.1 | 1080p | $0.40/s | $9.60 (24s) |

### Flat pricing (what the customer pays)

| Ad length | Standard (720p) | Pro (1080p) |
|-----------|-----------------|-------------|
| 24s | $9.99 | $29.99 |
| 40s | $9.99 | $29.99 |

Credit packs: $20 (2,000 credits), $50 (5,500 credits), $150 (18,000 credits).
Credits never expire. One Standard render = 999 credits; one Pro render =
2,999 credits.

### Raw cost vs. price (margin)

A 24s Pro ad costs $9.60 in raw GCP compute and sells for $29.99 — a
~3x margin. A 24s Standard ad costs $2.40 and sells for $9.99 — a ~4x
margin. Retried segments (transient failures) cost real GCP money but
are not charged to the customer.

---

## Technical constraints

### Veo 3.1 limits

| Constraint | Value | Why |
|------------|-------|-----|
| Clip duration | 4, 6, or 8 seconds only | Hard Veo API constraint |
| Resolution | 720p (Fast) or 1080p (Pro) | Model-tier dependent |
| Aspect ratio | 9:16 or 16:9 | Veo supports both |
| Max reference images | 3 per clip | "Ingredients to video" |
| Audio | Native, synchronized | `generate_audio=True` |
| Character consistency | Via reference images | Text alone is not enough |

### Word limits (at 125 WPM)

| Clip duration | Max spoken words | Example |
|---------------|-----------------|---------|
| 4s | ~8 | "Matching shirts nobody else has?" |
| 6s | ~12 | "Just tell me what you picture. One sentence." |
| 8s | ~16 | "I'll ask a couple of quick questions. Then you check the outline." |

Lines that exceed the word limit will rush, truncate, or drift.

### On-screen text

- Always burned in post (never in the Veo prompt)
- Keep to 1-3 words, ALL CAPS
- URLs and long phrases are not supported in the text bar
- The lower-third bar (brand name + tagline) is added to every ad
  automatically

### Rate limits

| Limit | Default | Tunable via |
|-------|---------|-------------|
| Renders per hour | 2 | `VBB_RENDER_LIMIT_PER_HOUR` |
| Ads per day | 1 | `VBB_RENDER_LIMIT_PER_DAY` |
| Concurrent segment jobs | 12 | `VBB_RENDER_MAX_CONCURRENT` |

### Platform specs (output is natively compliant)

| Spec | TikTok | Facebook Reels | YouTube Shorts |
|------|--------|----------------|-----------------|
| Resolution | 1080×1920 | 1080×1920 | 1080×1920 |
| Aspect | 9:16 | 9:16 | 9:16 |
| Codec | H.264 + AAC | H.264 + AAC | H.264 + AAC |
| Duration | ≤3 min | 3-90s | ≤60s |

Veo's output is already compliant — MP4, H.264, AAC stereo 48kHz, 9:16. No
codec conversion is needed after assembly.

---

## Known limitations

1. **No clip stitching within a segment.** Each Veo clip is a single 4/6/8s
   shot. You cannot control internal pacing (e.g. "cut every 1-2s") within a
   clip — that requires a single-prompt generator like Google Flow.

2. **On-screen text is post-burn only.** Veo cannot render text. All text
   (lower-third, scene labels, URLs) is burned in post with ffmpeg. Complex
   text layouts (multiple text zones, animated text, dynamic sizing) are not
   supported by the current post-burn system.

3. **Character consistency is high but not perfect.** The reference image
   anchors appearance, but minor variations occur (hair shade, clothing
   details, facial proportions). The same person is recognizably the same
   across clips, but not pixel-identical.

4. **Safety filters are not retryable.** If Veo rejects a clip for content
   reasons (safety filter), retrying will not help. The prompt must be
   revised. Common triggers: children in suggestive contexts, violence,
   medical content, specific real-person likenesses.

5. **No background music control.** Veo generates audio from the dialogue
   prompt — it produces speech, ambience, and sound effects, but you cannot
   specify a music track or genre. Music would need to be added in a
   post-production step.

6. **Transient GCP failures.** Veo occasionally returns `UNAVAILABLE` (code
   14) or empty responses. These are transient and succeed on retry. The
   system retries automatically (up to 2 times). Segment 3 in the Apple
   Blossom ad hit this consistently across both Oct 8 renders and always
   recovered on retry.

---

## Architecture

```
videobrandbuilders.ai (Vercel, Next.js)
         │
         ▼
tender-nurturing-production.up.railway.app (Railway, FastAPI)
         │
         ├── /api/auth          — JWT login/register
         ├── /api/projects      — create, generate script, approve, scenes
         ├── /api/render        — submit Veo jobs (UI path)
         ├── /api/render-direct — one-shot brief → video (API path)
         ├── /api/assemble       — join segments, download
         ├── /api/payments       — Stripe credits, checkout, webhook
         └── /generated, /assembled — static file mounts
                 │
                 ▼
          Vertex AI Veo 3.1 (GCP, us-central1)
```

### Stack
- **Frontend**: Next.js (Vercel) at `videobrandbuilders.ai`
- **Backend**: FastAPI (Railway) at `tender-nurturing-production.up.railway.app`
- **Database**: PostgreSQL (Railway)
- **Video generation**: Google Vertex AI Veo 3.1 (`video-brand-builder-vertex` GCP project)
- **Payments**: Stripe (credit prepay model)
- **Assembly**: ffmpeg (installed in the Railway container via nixpacks)
- **Reference images**: FAL.ai Flux (for generating the spokesperson portrait)

### Key files

| File | Purpose |
|------|---------|
| `backend/services/prompts.py` | Script generation, scene direction, prompt assembly |
| `backend/services/vertex_veo.py` | Veo 3.1 submission, polling, reference images |
| `backend/services/assembly.py` | Segment joining (stream-copy + loudnorm + faststart) |
| `backend/services/post_burn.py` | On-screen text + branding (ffmpeg drawtext) |
| `backend/services/billing.py` | Credit balance check, deduction, refund |
| `backend/services/ratelimit.py` | Rate limiting (per hour, per day, concurrent) |
| `backend/routes/render_direct.py` | One-shot API endpoint for programmatic use |
| `backend/routes/render.py` | UI render endpoint (per-project) |
| `backend/routes/assemble.py` | Assembly + download endpoint |
| `backend/routes/payments.py` | Stripe checkout + webhook + pricing |
| `backend/nixpacks.toml` | Railway build config (ffmpeg + python3) |

---

## Appendix: A complete example brief

This is the Apple Blossom Christmas ad that was rendered, verified, and
delivered on October 8, 2026 — the reference implementation for the pipeline.

**Brief:**
- Client: Apple Blossom (Apparel)
- Goal: drive free design starts for matching Christmas family shirts
- Audience: families shopping for matching holiday shirts
- Tones: warm, cheerful, cozy holiday
- CTA: "Make yours at design.appleblossomapparel.com"
- Platform: TikTok, 9:16, 40 seconds, mixed mode

**Continuity:**
- Spokesperson: Amy (reference image generated via FAL.ai — auburn hair,
  messy top-knot, freckles, white crew-neck tee with pink apple-blossom
  branch print)
- Delivery: warm, cheerful, cozy holiday energy
- Setting: bright white-brick loft, golden-hour light, apple blossoms
- Lighting: soft golden-hour, bright and airy

**Scenes (5 × 8s = 40s):**

| # | Name | Duration | Dialogue | On-screen text |
|---|------|----------|----------|----------------|
| 1 | Hook | 8s | "Matching Christmas shirts that nobody else on the block has?" | MATCHING SHIRTS |
| 2 | Intro | 8s | "Hi! I'm Amy, your AI Design Assistant. Let's make yours." | — |
| 3 | Describe | 8s | "Just tell me what you picture. One sentence is plenty. I'll ask a couple of quick questions too." | DESCRIBE IT |
| 4 | Mockup | 8s | "Then you see it on a shirt. Pick a color. Add your family name. Share one link in the family chat." | SEE IT ON A SHIRT |
| 5 | CTA | 8s | "Designing is free, so start early. Make yours at design.appleblossomapparel.com." | START FREE |

**Render:** Pro tier (1080p), Veo 3.1, ~$16 GCP cost. All 5 segments succeeded
on first attempt (no transient failures). Audio verified at -18 to -22 dB
across all segments. Post-burn applied: lower-third "Apple Blossom / AI-
designed matching shirts for families" + 4 scene labels. Final file: 53 MB,
40.08s, 1080×1920, H.264 + AAC stereo 48kHz.
