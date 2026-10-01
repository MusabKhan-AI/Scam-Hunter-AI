from __future__ import annotations


class JudgeAgent:
    """Reviews the available analysis and determines the evidence-supported assessment."""

    def __init__(self, router):
        self.router = router

    def run(
        self,
        pattern_analysis: str,
        contradiction_analysis: str,
        evidence: list,
    ) -> str:
        evidence_text = self._format_evidence(evidence)

        prompt = f"""
You are the evidence-review judge for ScamHunter AI.

Review the pattern analysis, contradiction analysis, and underlying evidence.

Produce a balanced assessment containing:

- Evidence-supported observations
- Important warning indicators
- Contradictions or unresolved issues
- What cannot be established from the available evidence
- A practical verification status:
  "requires verification", "evidence supports concern",
  or "insufficient evidence"

Do not present suspicion as proof.
Do not invent facts.
Do not make claims about a person or organization that are not supported by the evidence.

PATTERN ANALYSIS:
{pattern_analysis}

CONTRADICTION ANALYSIS:
{contradiction_analysis}

EVIDENCE:
{evidence_text}
"""

        try:
            result = self.router.best_available(
                prompt,
                system=(
                    "You are a neutral evidence-review agent. "
                    "Your assessment must remain proportional to the evidence."
                ),
                prefer_gemini=True,
            )
            return result.text.strip()

        except Exception as exc:
            return (
                "Evidence review could not be completed reliably. "
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
