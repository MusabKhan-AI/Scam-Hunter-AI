from __future__ import annotations


class ClassifierAgent:
    """Classifies an investigation request and decides which evidence sources are needed."""

    def __init__(self, router):
        self.router = router

    def run(self, user_text: str) -> dict:
        prompt = f"""
You are the classification agent for ScamHunter AI.

Analyze the user's request and return ONLY valid JSON with these keys:

{{
  "category": "one of: phishing, investment, job, romance, payment, shopping, identity_theft, giveaway, technical_support, crypto, other",
  "requires_rag": true,
  "requires_web": false,
  "risk_level": "low, medium, high, or unknown",
  "reason": "short explanation"
}}

Rules:
- Use the internal knowledge base when the request concerns scam patterns, investigation guidance, or known scam behavior.
- Set requires_web to true only when current or external information would materially help investigate the request.
- Do not decide that something is a scam solely from the user's wording.
- Do not invent facts.

USER REQUEST:
{user_text}
"""

        try:
            result = self.router.best_available(
                prompt,
                system="You are a precise scam-investigation classification agent. Return JSON only.",
                prefer_gemini=True,
            )

            return self._parse(result.text)

        except Exception:
            return {
                "category": "other",
                "requires_rag": True,
                "requires_web": False,
                "risk_level": "unknown",
                "reason": "Classification could not be completed reliably.",
            }

    @staticmethod
    def _parse(text: str) -> dict:
        import json

        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "", 1)
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "category": "other",
                "requires_rag": True,
                "requires_web": False,
                "risk_level": "unknown",
                "reason": "The classifier returned an invalid JSON response.",
            }

        return {
            "category": str(data.get("category", "other")),
            "requires_rag": bool(data.get("requires_rag", True)),
            "requires_web": bool(data.get("requires_web", False)),
            "risk_level": str(data.get("risk_level", "unknown")),
            "reason": str(data.get("reason", "")),
        }
