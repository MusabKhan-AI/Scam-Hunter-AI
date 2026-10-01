from __future__ import annotations


class CriticAgent:
    """Performs a final quality and safety review of a drafted response."""

    def __init__(self, router):
        self.router = router

    def run(self, draft: str, evidence: list) -> str:
        evidence_text = self._format_evidence(evidence)

        prompt = f"""
You are the quality-control critic for ScamHunter AI.

Review the draft response against the available evidence.

Check for:

1. Unsupported factual claims.
2. Invented evidence or citations.
3. Overconfident statements.
4. Failure to distinguish evidence from allegations.
5. Missing uncertainty or verification guidance.
6. Incorrect interpretation of URLs, messages, organizations, or offers.
7. Advice that could unnecessarily expose the user to risk.
8. Whether the response clearly explains what the user should verify.

Return a concise QUALITY CHECK containing:
- Issues found
- Required corrections
- What is already supported

If there are no significant issues, say so explicitly.

DRAFT:
{draft}

EVIDENCE:
{evidence_text}
"""

        try:
            result = self.router.best_available(
                prompt,
                system=(
                    "You are a strict but factual quality reviewer. "
                    "Do not introduce new claims during the review."
                ),
                prefer_gemini=True,
            )
            return result.text.strip()

        except Exception as exc:
            return (
                "Quality check could not be completed reliably. "
                f"Reason: {exc}"
            )

    @staticmethod
    def _format_evidence(evidence: list) -> str:
        if not evidence:
            return "No evidence available."

        lines = []

        for index, item in enumerate(evidence, start=1):
            source_type = item.get("source_type", "unknown")
            source = item.get("source", {})

            if isinstance(source, dict):
                title = source.get("title", "")
                content = (
                    source.get("content")
                    or source.get("text")
                    or source.get("snippet")
                    or str(source)
                )
                url = source.get("url", "")
            else:
                title = ""
                content = str(source)
                url = ""

            lines.append(
                f"[Evidence {index} | {source_type}]\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Content: {content}"
            )

        return "\n\n".join(lines)
