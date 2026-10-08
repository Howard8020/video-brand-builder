import os
import httpx
import json
import re
from typing import Any, Dict, List, Optional

DEFAULT_WPM = 125
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.environ.get("VBB_ANTHROPIC_MODEL", "claude-sonnet-4-6")
_k = "VBB_ANTHROPIC_API_KEY"

def _get_api_key() -> str:
    import os
    return os.environ.get(_k, "")

def call_anthropic(prompt: str, max_tokens: int = 1000) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    with httpx.Client(timeout=120, headers={"Content-Type": "application/json"}) as client:
        r = client.post(ANTHROPIC_URL, json=payload, headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"})
        r.raise_for_status()
        data = r.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return text.replace("```json", "").replace("```", "").strip()


def call_anthropic_json(prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
    raw = call_anthropic(prompt, max_tokens=max_tokens)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fix = call_anthropic("Fix this into strictly valid JSON. Return ONLY the corrected JSON, nothing else:\n\n" + raw, max_tokens=max_tokens)
        return json.loads(fix)


def count_words(s: str) -> int:
    return len((s or "").strip().split())


def seg_cap(duration, wpm):
    return (duration / 60) * wpm


def word_budget(runtime, n_seg, wpm):
    return int(((runtime - 1.5) / 60) * wpm)


def visual_mode_rules(mode):
    if mode == "product":
        return "VISUAL MODE: product demo. Visuals are screen-forward — the app interface on a device, cursor/tap interactions, feature reveals, UI motion. Spoken copy is VOICEOVER; no on-camera presenter."
    if mode == "mixed":
        return "VISUAL MODE: mixed. Alternate a friendly on-camera presenter with screen-forward shots of the app interface in action."
    return "VISUAL MODE: spokesperson. A consistent on-camera presenter carries the ad, speaking directly to camera."


def cont_block(cont):
    if not cont:
        return ""
    lines = []
    mapping = {
        "spokesperson": "Spokesperson: {v}",
        "delivery": "Vocal delivery: {v}",
        "setting": "Setting: {v}",
        "lighting": "Lighting: {v}",
        "brand": "Brand elements: {v}",
    }
    for k, v in cont.items():
        if k == "mode":
            continue
        tpl = mapping.get(k)
        if tpl:
            lines.append("- " + tpl.format(v=v))
    return "\n".join(lines) if lines else ""


def norm_cont(p):
    c = p.get("continuity") or {}
    c.setdefault("spokesperson", "")
    c.setdefault("delivery", "warm, upbeat, and animated — never flat or monotone")
    c.setdefault("setting", "")
    c.setdefault("lighting", "")
    c.setdefault("brand", "")
    return c


def cap_table(wpm, durations):
    return ", ".join(["a {}s segment at most {} spoken words".format(d, int(seg_cap(d, wpm))) for d in durations])


def clip_text(durations):
    if len(durations) == 1:
        return str(durations[0])
    return ", ".join(str(d) for d in durations[:-1]) + ", or " + str(durations[-1])


def segment_count(runtime, durations):
    """How many clips are needed to cover `runtime` seconds.

    Veo only renders 4/6/8s clips, so a long ad MUST be split into more clips
    than a short one. The previous hardcoded "3 if <=16 else 4" capped every ad
    at 4 x 8s = 32s, which made a 40s runtime impossible to satisfy — the model
    was asked to hit a target its own constraints forbade.

    Keeps the old floor (so shorter ads are unchanged) and only raises the
    count when the allowed clip lengths physically cannot reach the runtime.
    """
    longest = max(durations) if durations else 8
    needed = -(-int(runtime) // int(longest))  # ceil division
    return max(needed, 3 if runtime <= 16 else 4)


def _schema():
    return 'Return ONLY valid JSON (no markdown, no commentary) with exactly this shape: {"brief":{"core_message":"1 sentence","emotional_appeal":"1 sentence","practical_benefit":"1 sentence","objection":"1 sentence","strategy_note":"1 sentence"},"title":"short ad title","segments":[{"name":"","purpose":"hook|benefit|example|cta","duration":4,"spoken":""}]}'


def gen_prompt(p):
    wpm = p.get("wpm") or DEFAULT_WPM
    tpl = p.get("template") or {}
    durations = p.get("settings", {}).get("clipLengths") or [4, 6, 8]
    runtime = p.get("runtime") or 24
    n_seg = segment_count(runtime, durations)
    brief = p.get("brief") or {}
    lines = []
    lines.append("You are an expert short-form video ad scriptwriter creating a {} second ad.\n\nThis is the MESSAGE stage: write dialogue only. Scene treatments are directed later, after the script is locked.\n\nBRIEF:\n- Business: {} ({})\n- Video purpose: {}\n- Campaign goal: {}\n- Target audience: {}\n- Tone: {}\n- Offer: {}\n- Required call to action (verbatim in final segment): \"{}\"\n- Platform: {} ({})".format(runtime, brief.get("clientName"), brief.get("category"), brief.get("serviceLine"), brief.get("goal"), brief.get("audience"), ", ".join(p.get("tones", [])), brief.get("offer", "none specified"), brief.get("cta"), brief.get("platform"), brief.get("aspect")))
    lines.append(visual_mode_rules(p.get("visualMode") or "spokesperson"))
    if p.get("avoid"):
        lines.append("\n- NEVER use these phrases: {}".format(p["avoid"]))
    if p.get("brandNotes"):
        lines.append("\n- Brand notes: {}".format(p["brandNotes"]))
    if p.get("styleRefs"):
        style = []
        for i, ref in enumerate(p["styleRefs"][:2]):
            style.append("{}. \"{}\": {}".format(i+1, ref.get("title"), " / ".join(['\"{}\"'.format(l) for l in ref.get("lines", [])])))
        lines.append("\nVOICE REFERENCES — this client already APPROVED these scripts. Match their voice, energy, and rhythm. Do NOT reuse their lines or hooks:\n" + "\n".join(style))
    if tpl.get("segments"):
        struct = "\nSTRUCTURE (mandatory — EXACTLY these segments in this order):\n"
        struct += "\n".join(["{}. \"{}\" — purpose {} — {}s — spoken copy {} words MAXIMUM — visual pattern: {}".format(i+1, s.get("name"), s.get("purpose"), s.get("duration"), int(seg_cap(s.get("duration", 4), wpm)), s.get("pattern", "")) for i, s in enumerate(tpl["segments"])])
    else:
        caps = [int(seg_cap(d, wpm)) for d in durations]
        struct = "\nSTRUCTURE:\n- Exactly {} segments. Durations only {} seconds, summing to within 2 seconds of {}.\n- PER-SEGMENT WORD CAPS (hard limits): {}.\n- First segment is a hook; last segment purpose is \"cta\".".format(n_seg, clip_text(durations), runtime, clip_text(caps))
    lines.append(struct)
    lines.append("\nHARD RULES:\n- Every segment's spoken copy MUST be at or under its word cap. Count the words.\n- TOTAL spoken words: {} maximum.\n- WRITE FOR THE EAR: contractions, direct \"you\", exclamation points at energy peaks. If a line would sound flat read aloud, rewrite it.\n- Do not invent prices, guarantees, credentials, testimonials, or claims.".format(word_budget(runtime, n_seg if not tpl.get("segments") else len(tpl["segments"]), wpm)))
    lines.append("\n" + _schema())
    return "\n".join(lines)


def adapt_prompt(p):
    wpm = p.get("wpm") or DEFAULT_WPM
    durations = p.get("settings", {}).get("clipLengths") or [4, 6, 8]
    runtime = p.get("runtime") or 24
    brief = p.get("brief") or {}
    n_seg = segment_count(runtime, durations)
    src = p.get("sourceScript") or ""
    lines = []
    lines.append("You are an expert short-form video script editor. The client wrote this script themselves. Your job is to ADAPT it — not rewrite it — into a {} second segmented video script ready for AI video generation.\n\nCLIENT'S ORIGINAL SCRIPT:\n\"\"\"\n{}\n\"\"\"\n\nBRIEF:\n- Business: {} ({})\n- Video purpose: {}\n- Campaign goal: {}\n- Target audience: {}\n- Tone: {}\n- Platform: {} ({})".format(runtime, src, brief.get("clientName"), brief.get("category"), brief.get("serviceLine"), brief.get("goal"), brief.get("audience"), ", ".join(p.get("tones", [])), brief.get("platform"), brief.get("aspect")))
    lines.append(visual_mode_rules(p.get("visualMode") or "spokesperson"))
    if p.get("avoid"):
        lines.append("\n- NEVER use these phrases: {}".format(p["avoid"]))
    if p.get("brandNotes"):
        lines.append("\n- Brand notes: {}".format(p["brandNotes"]))
    lines.append("\nADAPTATION RULES (priority order):\n1. PRESERVE THE WRITER'S VOICE. Keep their key phrases, ideas, and order wherever possible.\n2. STRUCTURE: exactly {} segments. Durations only {} seconds, summing to within 2 seconds of {}. First segment = hook. Last segment purpose = \"cta\".\n3. WORD CAPS at {} WPM (hard limits): {}. TOTAL ≤ {} words.\n4. CTA: keep the client's call to action if present; otherwise close with: \"{}\".\n5. Do not invent prices, guarantees, credentials, or claims.".format(n_seg, clip_text(durations), runtime, wpm, cap_table(wpm, durations), word_budget(runtime, n_seg, wpm), brief.get("cta")))
    lines.append("\n" + _schema())
    return "\n".join(lines)


def revise_prompt(p, script, instruction):
    wpm = p.get("wpm") or DEFAULT_WPM
    durations = p.get("settings", {}).get("clipLengths") or [4, 6, 8]
    runtime = p.get("runtime") or 24
    brief = p.get("brief") or {}
    source = p.get("sourceScript")
    avoid = "\n- NEVER use: {}.".format(p["avoid"]) if p.get("avoid") else ""
    src_note = "\n- This script was adapted from the client's OWN writing — preserve their voice." if source else ""
    cap_desc = ", ".join(["segment {} ({}s) <= {} words".format(i+1, s.get("duration", 4), int(seg_cap(s.get("duration", 4), wpm))) for i, s in enumerate(script.get("segments", []))])
    return 'Revise this short-form video ad script. Business: {} ({}). Required CTA: "{}".\n\nREVISION INSTRUCTION: {}\n\nCURRENT SCRIPT JSON:\n{}\n\nHARD RULES:\n- Segment durations only {} seconds, summing to within 2 seconds of {}.\n- PER-SEGMENT WORD CAPS at {} WPM: {}.\n- TOTAL spoken words: {} maximum.\n- WRITE FOR THE EAR: contractions, direct "you", exclamation points at energy peaks.{}{}'.format(brief.get("clientName"), brief.get("serviceLine"), brief.get("cta"), instruction, json.dumps({"title": script.get("title"), "segments": script.get("segments", [])}), clip_text(durations), runtime, wpm, cap_desc, word_budget(runtime, len(script.get("segments", [])), wpm), avoid, src_note)


def revise_segment_prompt(p, script, idx, instruction):
    brief = p.get("brief") or {}
    seg = script.get("segments", [])[idx]
    avoid = " Never use: {}.".format(p["avoid"]) if p.get("avoid") else ""
    cta_suffix = (' Must contain the CTA: "{}"'.format(brief.get("cta")) if seg.get("purpose") == "cta" and brief.get("cta") else "")
    src_suffix = " This script was adapted from the client's own writing — preserve their voice." if p.get("sourceScript") else ""
    others = ", ".join(['{}: "{}"'.format(script.get("segments", [])[j].get("name"), script.get("segments", [])[j].get("spoken", "")) for j in range(len(script.get("segments", []))) if j != idx])
    return 'You are revising the DIALOGUE of one segment of a {} second video ad for {} ({}). Tone: {}. {} WPM. This is the message stage — dialogue only, no visuals.\n\nFULL SCRIPT FOR CONTEXT: {}\n\nSEGMENT TO REVISE (#{} — "{}", {}s):\nCurrent dialogue: "{}"\n\nINSTRUCTION: {}\n\nRULES: spoken copy HARD MAXIMUM {} words — count them. Write for the ear — warm and upbeat: contractions, direct "you", energy. {}{}{}'.format(
        p.get("runtime", 24), brief.get("clientName"), brief.get("serviceLine"),
        ", ".join(p.get("tones", [])), p.get("wpm", DEFAULT_WPM),
        others, idx+1, seg.get("name"), seg.get("purpose"), seg.get("duration"),
        seg.get("spoken"), instruction, int(seg_cap(seg.get("duration", 4), p.get("wpm", DEFAULT_WPM))),
        avoid, src_suffix, cta_suffix)


def scenes_prompt(p):
    brief = p.get("brief") or {}
    segs = p.get("script", {}).get("segments", [])
    continuity = p.get("continuity") or {}
    runtime = p.get("runtime") or 24
    aspect = brief.get("aspect") or "9:16"
    lines = []
    lines.append('You are the director creating scene treatments for an APPROVED, LOCKED video ad script. The dialogue is final. Do not change, add, or remove any spoken words.\n\nLOCKED SCRIPT ({}s, {}, for {} — {}):'.format(runtime, aspect, brief.get("clientName"), brief.get("serviceLine")))
    for i, s in enumerate(segs):
        lines.append('{}. "{}" ({}, {}s)\n   Dialogue: "{}"'.format(i+1, s.get("name"), s.get("purpose"), s.get("duration"), s.get("spoken")))
    lines.append("\nCONTINUITY (fixed across ALL clips — do not restate in scenes):\n" + cont_block(continuity))
    lines.append(visual_mode_rules(p.get("visualMode") or "spokesperson"))
    lines.append('\nFor each segment write:\n- action: concrete filmable staging serving the dialogue. One or two sentences.\n- camera: one clear camera direction (shot size + movement).\n- on_screen_text: short supporting text, or empty string.\n\nTone: {}. Do not invent claims, prices, or offers.\n\nReturn ONLY valid JSON: {{"scenes":[{{"action":"","camera":"","on_screen_text":""}}]}}'.format(", ".join(p.get("tones", []))))
    return "\n".join(lines)


def revise_scenes_prompt(p, instruction):
    brief = p.get("brief") or {}
    segs = p.get("script", {}).get("segments", [])
    continuity = p.get("continuity") or {}
    current = p.get("scenes", {}).get("scenes", [])
    rows = []
    for i, s in enumerate(segs):
        cur = current[i] if i < len(current) else {}
        rows.append('{}. "{}" ({}s)\n   Current action: {} | camera: {} | on-screen text: {}'.format(i+1, s.get("name"), s.get("duration"), cur.get("action", "—"), cur.get("camera", "—"), cur.get("on_screen_text", "—")))
    return 'You are revising the scene treatments of a video ad. The SCRIPT IS LOCKED — dialogue cannot change. CONTINUITY IS FIXED. Only the per-clip staging changes.\n\nREVISION INSTRUCTION: {}\n\nSEGMENTS AND CURRENT SCENES:\n{}\\n\\nCONTINUITY (fixed):\\n{}{}\\n\\nReturn ONLY valid JSON: {{\\"scenes\\":[{\\"action\\":\\"\\",\\"camera\\":\\"\\",\\"on_screen_text\\":\\"\\"}]}}'.format(instruction, "\n".join(rows), cont_block(continuity), visual_mode_rules(p.get("visualMode") or "spokesperson"))


def revise_scene_prompt(p, idx, instruction):
    segs = p.get("script", {}).get("segments", [])
    continuity = p.get("continuity") or {}
    current = p.get("scenes", {}).get("scenes", [])
    s = segs[idx]
    cur = current[idx] if idx < len(current) else {}
    others = []
    for j in range(len(segs)):
        if j == idx:
            continue
        other = current[j] if j < len(current) else {}
        others.append('{}: {}'.format(segs[j].get("name"), other.get("action", "")))
    return 'You are revising ONE scene. The SCRIPT IS LOCKED. CONTINUITY IS FIXED.\n\\nOTHER SCENES:\\n{}\\n\\nSCENE TO REVISE (#{} — \\"{}\\", {}s):\\nLocked dialogue: \\"{}\\"\\nCurrent action: {} | camera: {} | on-screen text: {}\\n\\nCONTINUITY (fixed):\\n{}{}\\nINSTRUCTION: {}\\n\\nReturn ONLY valid JSON for the single revised scene: {{\\"action\\":\\"\\",\\"camera\\":\\"\\",\\"on_screen_text\\":\\"\\"}}'.format("\\n".join(others), idx+1, s.get("name"), s.get("duration"), s.get("spoken"), cur.get("action", "—"), cur.get("camera", "—"), cur.get("on_screen_text", "—"), cont_block(continuity), visual_mode_rules(p.get("visualMode") or "spokesperson"), instruction)


def _simplify_on_screen_text(text):
    """Veo 3.1 garbles long on-screen text and URLs.

    Keep it to ≤ 3 short words with no punctuation complexity.  Strip URLs,
    colons, and long phrases down to the bare minimum.  If it can't be
    simplified to something a child could read at a glance, return "" — the
    text can be burned in post with ffmpeg instead.
    """
    if not text:
        return ""
    # Strip URLs — Veo cannot render them legibly.
    import re as _re
    cleaned = _re.sub(r"https?://\S+", "", text).strip()
    # Strip "Step N:" prefixes — the colon + number confuses the model.
    cleaned = _re.sub(r"^Step\s*\d+\s*:\s*", "", cleaned, flags=_re.I).strip()
    # Strip lone trailing fragments after a middot/pipe.
    cleaned = _re.split(r"\s*[·|]\s*", cleaned)[0].strip()
    words = cleaned.split()
    if len(words) <= 3 and all(len(w) <= 12 for w in words):
        return cleaned
    # If it's a short sentence (≤ 5 words) with no digits/URLs, keep it.
    if len(words) <= 5 and not any(c.isdigit() for c in cleaned) and "." not in cleaned:
        return cleaned
    return ""  # too complex — burn in post instead


def assemble_flow_prompt(seg, i, project):
    brief = project.get("brief") or {}
    continuity = project.get("continuity") or {}
    mode = project.get("visualMode") or "spokesperson"
    delivery = continuity.get("delivery") or "warm, upbeat, and animated — never flat or monotone"
    spokesperson = continuity.get("spokesperson") or "a friendly presenter"
    action = seg.get("action") or seg.get("visual") or ""
    lines = []
    lines.append("SEGMENT {} — {}".format(i+1, seg.get("name", "")))
    lines.append("Target duration: {} seconds  ·  Aspect ratio: {}".format(seg.get("duration"), brief.get("aspect") or "9:16"))
    lines.append("")
    lines.append("Scene:")
    lines.append(action)
    lines.append("")
    lines.append("Camera: {}".format(seg.get("camera") or "—"))
    lines.append("")
    # Veo 3.1 generates audio natively when dialogue is clearly attributed
    # and quoted.  Put the speaker + the exact line up front so the model
    # "sees" the speech before the continuity clutter.
    if mode == "product":
        label = "Voiceover"
    else:
        label = "Dialogue"
    spoken = seg.get("spoken") or ""
    lines.append("{} — {} says, with {} delivery:".format(label, spokesperson.split(",")[0].strip(), delivery.split(",")[0].strip()))
    lines.append('"{}"'.format(spoken))
    lines.append("Generate clear, audible speech with synchronized lip movement matching this dialogue exactly.")
    # On-screen text is NOT sent to Veo — it reliably garbles even short text.
    # All on-screen text is burned in post with ffmpeg drawtext after assembly.
    # The on_screen_text field is preserved in the segment data for the post step.
    cont_text = cont_block(continuity) or ("Lighting: {}".format(seg.get("lighting")) if seg.get("lighting") else "")
    lines.append("")
    lines.append("Continuity — identical in every segment of this ad:")
    lines.append(cont_text)
    lines.append("")
    avoid = " Avoid: Do not change or misspell the brand name \"{}\". Do not add extra spoken words beyond the dialogue.{} Do not invent prices, offers, or claims.{}".format(brief.get("clientName"), " Do not show an on-camera spokesperson." if mode == "product" else "", (" Never include: {}".format(project.get("avoid")) if project.get("avoid") else ""))
    lines.append(avoid)
    return "\n".join(lines)


def generate_script(brief, settings, source_script=None):
    p = {
        "brief": brief,
        "settings": settings,
        "sourceScript": source_script,
        "wpm": settings.get("wpm", DEFAULT_WPM),
        "visualMode": brief.get("visualMode") or "spokesperson",
        "tones": brief.get("tones", []),
        "avoid": brief.get("avoid") or "",
        "brandNotes": brief.get("brandNotes") or "",
        "styleRefs": brief.get("styleRefs") or [],
        "template": brief.get("template") or {},
        "runtime": brief.get("runtime") or 24,
    }
    prompt = adapt_prompt(p) if source_script else gen_prompt(p)
    return call_anthropic_json(prompt, max_tokens=2000)


def revise_script(brief, script, instruction):
    p = {
        "brief": brief,
        "settings": brief.get("settings") or {},
        "sourceScript": brief.get("sourceScript"),
        "wpm": brief.get("wpm", DEFAULT_WPM),
        "visualMode": brief.get("visualMode") or "spokesperson",
        "tones": brief.get("tones", []),
        "avoid": brief.get("avoid") or "",
        "brandNotes": brief.get("brandNotes") or "",
        "runtime": brief.get("runtime") or 24,
    }
    return call_anthropic_json(revise_prompt(p, script, instruction), max_tokens=2000)


def revise_segment(brief, script, idx, instruction):
    p = {
        "brief": brief,
        "settings": brief.get("settings") or {},
        "sourceScript": brief.get("sourceScript"),
        "wpm": brief.get("wpm", DEFAULT_WPM),
        "visualMode": brief.get("visualMode") or "spokesperson",
        "tones": brief.get("tones", []),
        "avoid": brief.get("avoid") or "",
        "brandNotes": brief.get("brandNotes") or "",
        "runtime": brief.get("runtime") or 24,
    }
    return call_anthropic_json(revise_segment_prompt(p, script, idx, instruction), max_tokens=800)


def generate_scenes(brief, script, continuity):
    p = {
        "brief": brief,
        "script": script,
        "continuity": continuity,
        "tones": brief.get("tones", []),
        "visualMode": brief.get("visualMode") or "spokesperson",
    }
    return call_anthropic_json(scenes_prompt(p), max_tokens=2000)


def revise_scenes(brief, script, scenes, continuity, instruction=""):
    p = {
        "brief": brief,
        "script": script,
        "scenes": scenes,
        "continuity": continuity,
        "tones": brief.get("tones", []),
        "visualMode": brief.get("visualMode") or "spokesperson",
    }
    return call_anthropic_json(revise_scenes_prompt(p, instruction or "Improve all scenes"), max_tokens=2000)


def revise_scene(brief, script, scenes, continuity, scene_index, instruction=""):
    p = {
        "brief": brief,
        "script": script,
        "scenes": scenes,
        "continuity": continuity,
        "tones": brief.get("tones", []),
        "visualMode": brief.get("visualMode") or "spokesperson",
    }
    return call_anthropic_json(revise_scene_prompt(p, scene_index, instruction or "Improve this scene"), max_tokens=1200)


def assemble_prompts(brief, script, scenes, continuity, settings):
    out = {
        "project": {
            "clientName": brief.get("clientName"),
            "serviceLine": brief.get("serviceLine"),
            "runtime": brief.get("runtime"),
            "aspect": brief.get("aspect"),
            "platform": brief.get("platform"),
        },
        "segments": [],
        "social": {"caption": "", "hashtags": []},
    }
    segs = script.get("segments", []) if isinstance(script, dict) else []
    scenes_list = scenes.get("scenes", []) if isinstance(scenes, dict) else []
    for i, s in enumerate(segs):
        scene = scenes_list[i] if i < len(scenes_list) else {}
        merged = {**s, **scene}
        merged["duration"] = merged.get("duration") or s.get("duration") or 4
        out["segments"].append({
            "segment": i + 1,
            "name": merged.get("name", ""),
            "duration": merged.get("duration", 4),
            "prompt": assemble_flow_prompt(merged, i, {
                "brief": brief,
                "script": script,
                "continuity": continuity,
                "settings": settings,
                "visualMode": brief.get("visualMode") or "spokesperson",
                "avoid": brief.get("avoid") or "",
            }),
        })
    try:
        out["social"] = generate_caption(brief, script)
    except Exception:
        pass
    return out


def generate_caption(brief, script):
    segs = script.get("segments", []) if isinstance(script, dict) else []
    body = " ".join([s.get("spoken", "") for s in segs])
    parts = ['Write the social caption for a finished {} video ad for {} ({}). Goal: {}. Tone: {}.'.format(brief.get("platform"), brief.get("clientName"), brief.get("serviceLine"), brief.get("goal"), ", ".join(brief.get("tones", [])))]
    parts.append('FINAL SCRIPT: {}'.format(body))
    if brief.get("cta"):
        parts.append('CTA: "{}"'.format(brief["cta"]))
    if brief.get("offer"):
        parts.append('Offer: {}'.format(brief["offer"]))
    if brief.get("brandNotes"):
        parts.append('Brand notes: {}'.format(brief["brandNotes"]))
    parts.append("RULES:\n- caption: 1-3 short lines. Front-load the strongest idea, end on the CTA. Line breaks. At most 1-2 emoji.\n- hashtags: 5-8, specific to the video purpose and audience. No spaces.\n- Do not invent prices, guarantees, credentials, or claims.")
    if brief.get("avoid"):
        parts.append("\n- NEVER use: {}.".format(brief["avoid"]))
    parts.append('\nReturn ONLY valid JSON: {"caption":"","hashtags":["",""]}')
    return call_anthropic_json("\n".join(parts), max_tokens=600)

CLAIM_CHECKS = [
    (r"\$\s*\d[\d,.]*", "price"),
    (r"\d+\s*%", "percentage"),
    (r"\bguarantee[ds]?\b", "guarantee"),
    (r"\bcertified\b", "credential"),
    (r"\blicensed\b", "credential"),
    (r"\binsured\b", "credential"),
    (r"#\s?1\b|\bnumber one\b", "superiority claim"),
    (r"\baward[- ]winning\b", "credential"),
    (r"\b(?:best|top[- ]rated) (?:in|of)\b", "superiority claim"),
    (r"\b\d[\d,]*\+? (?:years|customers|clients|homes|roofs|projects|five[- ]star reviews|reviews)\b", "statistic"),
]


def lint_claims(script, offer, cta, brand_notes):
    allow = " " + (offer or "") + " " + (cta or "") + " " + (brand_notes or "") + " "
    flags = []
    segments = script.get("segments", []) if isinstance(script, dict) else []
    for i, s in enumerate(segments):
        spoken = s.get("spoken", "") or ""
        for pat, kind in CLAIM_CHECKS:
            for m in re.finditer(pat, spoken, flags=re.I):
                if m.group(0).lower() not in allow:
                    flags.append({"seg": i, "text": m.group(0), "kind": kind})
    return flags


def generate_hooks(brief, script):
    p = {
        "brief": brief,
        "wpm": brief.get("wpm", DEFAULT_WPM),
        "visualMode": brief.get("visualMode") or "spokesperson",
        "tones": brief.get("tones", []),
        "avoid": brief.get("avoid") or "",
        "brandNotes": brief.get("brandNotes") or "",
        "sourceScript": brief.get("sourceScript"),
        "runtime": brief.get("runtime") or 24,
    }
    first = script.get("segments", [{}])[0]
    cap = int(seg_cap(first.get("duration", 4), p.get("wpm", DEFAULT_WPM)))
    parts = ['You are an expert short-form video ad scriptwriter. Write 3 ALTERNATE opening hooks for a {} second ad for {} ({}). Tone: {}.'.format(p.get("runtime", 24), brief.get("clientName"), brief.get("serviceLine"), ", ".join(p.get("tones", [])))]
    parts.append('CURRENT HOOK ({}s): "{}" REST: {}'.format(first.get("duration"), first.get("spoken"), " · ".join([s.get("spoken", "") for s in script.get("segments", [])[1:]])))
    parts.append('RULES: Each hook AT MOST {} words. Different angle each time. Written for the ear.{}{}'.format(cap, " Sound like the client." if p.get("sourceScript") else "", ' Never use: {}.'.format(p["avoid"]) if p.get("avoid") else ""))
    return call_anthropic_json("\n".join(parts), max_tokens=800)

