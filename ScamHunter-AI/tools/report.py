"""Build a downloadable Markdown investigation report."""
from __future__ import annotations

from datetime import datetime, timezone

LEVEL_TEXT = {
    "red": "RED - Likely scam",
    "yellow": "YELLOW - Suspicious, verify before acting",
    "green": "GREEN - No scam indicators found",
}


def _sources(evidence: list) -> list[str]:
    lines = []
    for item in evidence or []:
        if not isinstance(item, dict):
            continue
        if item.get("source_type") == "web" or item.get("url"):
            title = item.get("title") or item.get("url") or "Web source"
            lines.append(f"- Web: {title} {item.get('url') or ''}".rstrip())
        else:
            name = item.get("filename") or item.get("title") or "Knowledge-base document"
            page = item.get("page")
            lines.append(f"- Knowledge base: {name}" + (f", page {page}" if page else ""))
    return list(dict.fromkeys(lines))[:20]


def build_report(
    question: str,
    answer: str,
    verdict: dict | None = None,
    scan: dict | None = None,
    sources: list | None = None,
    mode: str = "",
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = ["# ScamHunter AI - Investigation Report", "", f"Generated: {now}"]
    if mode:
        out.append(f"Mode: {mode}")
    out += ["", "## Submitted content", "", "```", (question or "").strip()[:4000], "```", ""]

    if verdict and verdict.get("level") in LEVEL_TEXT:
        line = LEVEL_TEXT[verdict["level"]]
        if verdict.get("category"):
            line += f" ({verdict['category']})"
        out += ["## Verdict", "", f"**{line}**", ""]

    if scan and (scan.get("flags") or scan.get("urls")):
        out += ["## Instant scan (heuristic, not proof)", "", f"Signal score: {scan.get('score', 0)}/100", ""]
        for flag in scan.get("flags", []):
            out.append(f"- {flag['label']}: \"{flag['evidence']}\"")
        for url in scan.get("urls", []):
            detail = "; ".join(url["flags"]) if url["flags"] else "no automatic flags"
            out.append(f"- Link: {url['url']} ({detail})")
        out.append("")

    out += ["## Assessment", "", (answer or "").strip(), ""]

    src = _sources(sources or [])
    if src:
        out += ["## Evidence sources", ""] + src + [""]

    out += [
        "---",
        "ScamHunter AI provides investigation support only. It does not guarantee that a "
        "message, website, person or offer is safe or fraudulent. Verify through official "
        "channels before sending money or personal information.",
    ]
    return "\n".join(out)
