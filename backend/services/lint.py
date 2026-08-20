
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


def lint_claims(script, offer="", cta="", brand_notes=""):
    """Return list of {seg, text, kind} flags for unallowed claim-like strings."""
    import re
    allow = " " + (offer or "") + " " + (cta or "") + " " + (brand_notes or "") + " "
    flags = []
    segments = script.get("segments", []) if isinstance(script, dict) else []
    for i, s in enumerate(segments):
        spoken = (s.get("spoken") or "") + " " + (s.get("on_screen_text") or "")
        for pat, kind in CLAIM_CHECKS:
            for m in re.finditer(pat, spoken, flags=re.I):
                if m.group(0).lower() not in allow:
                    flags.append({"seg": i, "text": m.group(0), "kind": kind})
    return flags
