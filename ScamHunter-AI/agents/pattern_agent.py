from __future__ import annotations


class ScamPatternAgent:
    """Identifies scam patterns from user content and analyzed evidence."""

    def __init__(self, router):
        self.router = router

    def run(self, user_text: str, evidence_analysis: str) -> str:
        prompt = f"""
You are the scam-pattern analysis agent for ScamHunter AI.

Analyze the user's content and the evidence analysis below.

Identify:
1. Observable scam indicators.
2. Common scam patterns that may be relevant.
3. Which indicators are directly supported by evidence.
4. Which indicators remain uncertain.
5. Important missing information.

Do not invent facts.
Do not claim that the person, company, website, message, or offer is fraudulent unless the evidence actually establishes that fact.
Use cautious language such as "may indicate", "is consistent with", or "requires verification" when appropriate.

USER CONTENT:
{user_text}

EVIDENCE ANALYSIS:
{evidence_analysis}
"""

        try:
            result = self.router.best_available(
                prompt,
                system=(
                    "You are a careful scam-pattern analyst. "
                    "Base conclusions on observable indicators and evidence."
                ),
                prefer_gemini=True,
            )
            return result.text.strip()

        except Exception as exc:
            return (
                "Scam-pattern analysis could not be completed reliably. "
                f"Reason: {exc}"
            )
