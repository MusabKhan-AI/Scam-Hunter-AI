from __future__ import annotations


class RAGAgent:
    """Retrieves relevant internal knowledge-base evidence."""

    def __init__(self, retriever, settings):
        self.retriever = retriever
        self.settings = settings

    def run(self, user_text: str) -> dict:
        try:
            items = self.retriever.search(
                user_text,
                k=self.settings.rag_top_k,
            )

            evidence = []

            for item in items:
                if isinstance(item, dict):
                    evidence.append(item)
                else:
                    evidence.append({
                        "content": str(item),
                    })

            return {
                "items": items,
                "evidence": evidence,
            }

        except Exception as exc:
            return {
                "items": [],
                "evidence": [],
                "error": str(exc),
            }
