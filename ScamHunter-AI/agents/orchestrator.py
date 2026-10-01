from __future__ import annotations

from tools.indicators import build_search_queries, scan_text


class InvestigationOrchestrator:
    def __init__(self, router, retriever, web_search, settings):
        self.router = router
        self.retriever = retriever
        self.web = web_search
        self.settings = settings

        from agents.classifier import ClassifierAgent
        from agents.rag_agent import RAGAgent
        from agents.evidence_agent import EvidenceAgent
        from agents.pattern_agent import ScamPatternAgent
        from agents.contradiction_agent import ContradictionAgent
        from agents.critic_agent import CriticAgent
        from agents.judge_agent import JudgeAgent
        from agents.response_agent import ResponseAgent
        from agents.web_agent import WebResearchAgent

        self.classifier = ClassifierAgent(router)
        self.rag = RAGAgent(retriever, settings)
        self.web = WebResearchAgent(web_search)
        self.evidence = EvidenceAgent(router)
        self.pattern = ScamPatternAgent(router)
        self.contradiction = ContradictionAgent(router)
        self.critic = CriticAgent(router)
        self.judge = JudgeAgent(router)
        self.response = ResponseAgent(router)

    # ---------------------------------------------------------
    # FAST / QUICK CHECK
    # ---------------------------------------------------------

    def run_quick(
        self,
        user_text: str,
        style: str = "Balanced",
        language: str = "English",
        signals: str = "",
    ) -> dict:
        """
        Fast investigation path.

        Only uses:
        1. FAISS/RAG retrieval
        2. One evidence-analysis LLM call
        3. One final-response LLM call

        This intentionally skips:
        classifier, web research, pattern agent,
        contradiction agent, judge and critic.
        """

        events = []

        # 1. Local knowledge-base retrieval
        rag = self.rag.run(user_text)
        events.append("Knowledge base searched")

        evidence_items = rag.get("evidence", [])
        rag_items = rag.get("items", [])

        # 2. Single analysis call
        evidence = self.evidence.run(
            user_text,
            rag,
            {"items": [], "cached": False},
            signals=signals,
        )
        events.append("Evidence analyzed")

        analysis = evidence.get("analysis", "")
        evidence_items = evidence.get("evidence", evidence_items)

        # 3. Single final response call
        final = self.response.run(
            user_text,
            analysis,
            "",
            "",
            evidence_items,
            style=style,
            language=language,
            signals=signals,
        )
        events.append("Fast response generated")

        return {
            "answer": final,
            "events": events,
            "classification": {
                "mode": "quick",
                "requires_rag": True,
                "requires_web": False,
            },
            "rag": {
                "items": rag_items,
                "evidence": evidence_items,
            },
            "web": {
                "items": [],
                "cached": False,
            },
            "analysis": analysis,
        }

    # ---------------------------------------------------------
    # FULL / DEEP INVESTIGATION
    # ---------------------------------------------------------

    def run(
        self,
        user_text: str,
        style: str = "Balanced",
        language: str = "English",
        signals: str = "",
    ) -> dict:
        events = []

        classification = self.classifier.run(user_text)
        events.append("Input classified")

        if classification.get("requires_rag", True):
            rag = self.rag.run(user_text)
        else:
            rag = {"items": [], "evidence": []}

        events.append("Knowledge base searched")

        web = {"items": [], "cached": False}

        if classification.get("requires_web", False):
            web = self.web.run(
                build_search_queries(user_text, scan_text(user_text))
            )
            events.append("Web research completed")

        evidence = self.evidence.run(
            user_text,
            rag,
            web,
            signals=signals,
        )
        events.append("Evidence analyzed")

        pattern = self.pattern.run(
            user_text,
            evidence["analysis"],
        )
        events.append("Scam patterns analyzed")

        contradiction = self.contradiction.run(
            evidence["evidence"],
        )
        events.append("Contradictions checked")

        judge = self.judge.run(
            pattern,
            contradiction,
            evidence["evidence"],
        )
        events.append("Evidence reviewed")

        draft = self.response.run(
            user_text,
            pattern,
            contradiction,
            judge,
            evidence["evidence"],
            style=style,
            language=language,
            signals=signals,
        )
        events.append("Response synthesized")

        critique = self.critic.run(
            draft,
            evidence["evidence"],
        )
        events.append("Final quality check completed")

        final = self.response.run(
            user_text,
            pattern + "\n\nQUALITY CHECK:\n" + critique,
            contradiction,
            judge,
            evidence["evidence"],
            style=style,
            language=language,
            signals=signals,
        )

        return {
            "answer": final,
            "events": events,
            "classification": classification,
            "rag": rag,
            "web": web,
            "analysis": evidence["analysis"],
            "pattern": pattern,
            "contradiction": contradiction,
            "judge": judge,
            "critique": critique,
        }
