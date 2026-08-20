"""Albert — the in-app assistant that guides users through the VBB workflow.

Reuses the existing Anthropic proxy (same key as script generation) so no new
credentials are required. Falls back to canned guidance if the key is unset,
matching the pattern used by services/prompts.py.
"""
import os
import hashlib
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/albert", tags=["albert"])

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.environ.get("VBB_ANTHROPIC_MODEL", "claude-sonnet-4-6")

ALBERT_SYSTEM_PROMPT = """You are Albert, the in-app guide for Video Brand Builder — a script-to-Flow-prompt workstation for small business video ads.

Keep replies short (2-4 sentences), plain language, no marketing jargon.

Video Brand Builder's workflow has 5 steps:
1. Add a Client (brand name, category, brand notes) — required before creating a project.
2. Create a New Project — pick the client, describe goal/audience/tone/platform/runtime, either paste your own script or let AI draft one.
3. Gate 1 — Script review: read the AI draft, ask for revisions (whole script or one line), check alternate hooks, run the claims lint, then Lock the script. Once locked, dialogue can't silently change.
4. Gate 2 — Scene review: AI drafts one scene treatment per segment (camera, action, on-screen text) using a fixed continuity profile (spokesperson, setting, lighting, brand) so every clip matches. Revise scenes without touching locked dialogue.
5. Export — Approve scenes to get a Flow-ready prompt package: one copy-pasteable prompt per 4/6/8-second clip. Paste each into your video generation tool, then stitch the clips yourself.

Key things to clarify when asked:
- "Why is my script locked?" — Gate 1 exists so the AI can't silently rewrite your dialogue after you approve it. Unlock only if you intend to revise.
- "Why do all my clips look different?" — check that continuity (spokesperson/setting/lighting/brand) is filled in on the client profile; it's stamped into every scene automatically.
- "What do I do with the exported prompts?" — paste each one individually into your video generation tool (one prompt per clip), then join the clips yourself in a video editor. VBB doesn't render video directly.
- Never invent pricing, features, or timelines not described above. If asked something outside VBB's actual scope, say so plainly and suggest contacting support instead of guessing."""


class AlbertRequest(BaseModel):
    message: str
    history: list[dict] = []


class AlbertResponse(BaseModel):
    reply: str


FALLBACK_RESPONSES = [
    "Start by adding a Client on your dashboard — you'll need one before creating a project. Then click New Project to describe your ad's goal, audience, and tone.",
    "Gate 1 locks your script so the AI can't silently change your dialogue later. Review it, ask for revisions if needed, then hit Lock Script when you're happy.",
    "After you lock your script, Gate 2 drafts one scene per segment using your client's continuity profile — same spokesperson, setting, and lighting across every clip.",
    "Once you approve scenes, you'll get one exported prompt per clip (4/6/8 seconds each). Paste each prompt into your video generation tool one at a time, then stitch the clips yourself — Video Brand Builder doesn't render video directly.",
    "If your clips look inconsistent, check the continuity fields on your client profile — spokesperson, setting, lighting, and brand notes get stamped into every scene automatically.",
    "The claims lint checks your locked script for invented prices, guarantees, or credentials before you move on — worth reviewing before you export.",
]


def _get_api_key() -> str:
    return os.environ.get("VBB_ANTHROPIC_API_KEY", "")


@router.post("", response_model=AlbertResponse)
async def albert_chat(req: AlbertRequest) -> AlbertResponse:
    api_key = _get_api_key()
    if not api_key:
        idx = int(hashlib.md5(req.message.encode()).hexdigest(), 16) % len(FALLBACK_RESPONSES)
        return AlbertResponse(reply=FALLBACK_RESPONSES[idx])

    try:
        messages = [{"role": m["role"], "content": m["content"]} for m in req.history[-10:]]
        messages.append({"role": "user", "content": req.message})

        with httpx.Client(timeout=30) as client:
            r = client.post(
                ANTHROPIC_URL,
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 300,
                    "system": ALBERT_SYSTEM_PROMPT,
                    "messages": messages,
                },
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
        reply = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return AlbertResponse(reply=reply.strip() or FALLBACK_RESPONSES[0])
    except Exception:
        idx = int(hashlib.md5(req.message.encode()).hexdigest(), 16) % len(FALLBACK_RESPONSES)
        return AlbertResponse(reply=FALLBACK_RESPONSES[idx])
