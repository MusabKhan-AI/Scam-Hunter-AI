from __future__ import annotations


class ContradictionAgent:
    """Checks evidence for conflicting, inconsistent, or unsupported claims."""

    def __init__(self, router):
        self.router = router

    def run(self, evidence: list) -> str:
        if not evidence:
            return "No evidence was available for contradiction checking."

        evidence_text = self._format_evidence(evidence)

        prompt = f"""
You are the contradiction-checking agent for ScamHunter AI.

Review the supplied evidence and identify:

1. Direct contradictions between sources.
2. Claims that are unsupported by the supplied evidence.
3. Differences in dates, names, URLs, amounts, organizations, or other important details.
4. Information that cannot currently be verified.
5. Any important uncertainty that should be disclosed.

Do not invent contradictions.
If there is no contradiction, explicitly say so.

EVIDENCE:
{evidence_text}
"""

        try:
            result = self.router.best_available(
                prompt,
                system=(
                    "You are a rigorous fact-checking agent. "
                    "Distinguish contradictions from simple differences or missing data."
                ),
                prefer_gemini=True,
            )
            return result.text.strip()

        except Exception as exc:
            return (
                "Contradiction checking could not be completed reliably. "
                f"Reason: {exc}"
            )

    @staticmethod
    def _format_evidence(evidence: list) -> str:
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
