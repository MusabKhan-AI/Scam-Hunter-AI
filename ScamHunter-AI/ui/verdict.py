"""Risk verdict (red / yellow / green) + scam category for ScamHunter AI.

Priority of sources:
1. An explicit last line written by the Response Agent:
       VERDICT: RED | CATEGORY: Phishing
2. A verdict field in the orchestrator result (judge output), if present.
3. A keyword estimate from the final answer text (marked "estimated").
If nothing can be determined, no badge is shown (e.g. general questions).
"""

from __future__ import annotations

import html
import re


LEVELS = {
    "red": {"color": "#EF4444", "emoji": "🔴", "label": "Likely scam"},
    "yellow": {"color": "#F59E0B", "emoji": "🟡", "label": "Suspicious — verify before acting"},
    "green": {"color": "#10B981", "emoji": "🟢", "label": "Good to go"},
}

NOTES = {
    "red": "Do not pay, click links, or share personal details.",
    "yellow": "Legitimacy could not be confirmed. Verify through official channels first.",
    "green": "No scam indicators found. Still verify through official channels.",
}

_VERDICT_LINE = re.compile(
    r"^[ \t>*_`#-]*VERDICT\s*:\s*(RED|YELLOW|GREEN)\b"
    r"(?:[^\n]*?CATEGORY\s*:\s*([^\n]+?))?[ \t*_`]*$",
    re.IGNORECASE | re.MULTILINE,
)

_RED = (
    "likely a scam", "likely scam", "this is a scam", "is a scam",
    "appears to be a scam", "looks like a scam", "high risk", "high-risk",
    "strong indicators", "classic scam", "do not pay", "do not send",
)
_GREEN = (
    "not a scam", "no red flags", "no scam indicators", "low risk",
    "low-risk", "appears legitimate", "looks legitimate", "appears safe",
    "looks safe",
)
_YELLOW = (
    "suspicious", "caution", "red flag", "unverified", "could not verify",
    "cannot verify", "moderate risk", "medium risk", "unclear", "verify",
)

_CATEGORIES = [
    ("Phishing", ("phishing", "verify your account", "credential")),
    ("Job scam", ("job scam", "fake job", "employment scam", "work-from-home")),
    ("Investment scam", ("investment scam", "ponzi", "guaranteed return")),
    ("Crypto scam", ("crypto scam", "cryptocurrency scam", "crypto")),
    ("Romance scam", ("romance scam",)),
    ("Shopping scam", ("shopping scam", "fake store", "online store")),
    ("Payment scam", ("payment scam", "advance fee", "overpayment", "fake invoice")),
    ("Fake support scam", ("tech support scam", "fake support", "impersonat")),
    ("Giveaway scam", ("giveaway", "prize scam", "lottery scam")),
    ("Identity theft", ("identity theft",)),
]

_RESULT_LEVEL_KEYS = ("verdict", "risk_level", "risk", "level", "rating")
_RESULT_CATEGORY_KEYS = ("scam_type", "category", "classification", "type")

_RED_TOKENS = {"red", "high", "critical", "scam", "fraud", "malicious"}
_YELLOW_TOKENS = {"yellow", "medium", "moderate", "suspicious", "unclear", "caution"}
_GREEN_TOKENS = {"green", "low", "safe", "legitimate", "good"}


def _flatten(value, depth: int = 0) -> str:
    if depth > 3:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_flatten(v, depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_flatten(v, depth + 1) for v in value)
    return ""


def _level_from_text(text: str):
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    if not tokens or "not" in tokens:
        return None
    if tokens & _RED_TOKENS:
        return "red"
    if tokens & _YELLOW_TOKENS:
        return "yellow"
    if tokens & _GREEN_TOKENS:
        return "green"
    return None


def _level_from_answer(answer: str):
    low = answer.lower()
    r = any(p in low for p in _RED)
    g = any(p in low for p in _GREEN)
    y = any(p in low for p in _YELLOW)
    if r and g:
        return "yellow"
    if r:
        return "red"
    if g:
        return "green"
    if y:
        return "yellow"
    return None


def _category_from_answer(answer: str) -> str:
    low = answer.lower()
    best, best_pos = "", None
    for name, words in _CATEGORIES:
        for w in words:
            pos = low.find(w)
            if pos != -1 and (best_pos is None or pos < best_pos):
                best, best_pos = name, pos
    return best


def _category_from_result(result: dict) -> str:
    for key in _RESULT_CATEGORY_KEYS:
        value = result.get(key)
        if isinstance(value, dict):
            for sub in ("category", "scam_type", "label", "type"):
                if isinstance(value.get(sub), str):
                    value = value[sub]
                    break
        if isinstance(value, str) and value.strip():
            return value.replace("_", " ").strip().title()
    return ""


def extract_verdict(result: dict, answer: str) -> dict:
    """Return {"answer": cleaned_text, "verdict": dict | None}."""
    result = result or {}
    answer = answer or ""
    level, category, source = None, "", "estimated"

    match = _VERDICT_LINE.search(answer)
    if match:
        level = match.group(1).lower()
        category = (match.group(2) or "").strip(" *_`")
        source = "model"
        answer = _VERDICT_LINE.sub("", answer).rstrip()

    if level is None:
        for key in _RESULT_LEVEL_KEYS:
            found = _level_from_text(_flatten(result.get(key)))
            if found:
                level, source = found, "analysis"
                break

    if level is None:
        level = _level_from_answer(answer)
        source = "estimated"

    if level is None:
        return {"answer": answer, "verdict": None}

    if category.lower() in {"", "none", "n/a", "-", "unknown"}:
        category = _category_from_result(result) or _category_from_answer(answer)

    if level == "green":
        category = ""

    return {
        "answer": answer,
        "verdict": {"level": level, "category": category, "source": source},
    }


def badge_html(verdict: dict) -> str:
    info = LEVELS.get(verdict.get("level"))
    if not info:
        return ""
    c = info["color"]
    category = html.escape(verdict.get("category") or "")
    title = html.escape(info["label"])
    if category:
        title += f" · {category}"
    note = html.escape(NOTES[verdict["level"]])
    if verdict.get("source") == "estimated":
        note += " (Estimated from the analysis.)"
    return (
        f'<div style="display:flex;align-items:center;gap:14px;padding:12px 16px;'
        f"border:1px solid {c}55;border-left:4px solid {c};border-radius:14px;"
        f'background:{c}14;margin-bottom:12px;">'
        f'<span style="width:16px;height:16px;border-radius:50%;background:{c};'
        f'box-shadow:0 0 14px {c};display:inline-block;flex:none;"></span>'
        f'<div><div style="font-weight:700;color:var(--sh-text);">{title}</div>'
        f'<div style="font-size:13px;color:var(--sh-muted);">{note}</div></div></div>'
    )
