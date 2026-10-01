def format_rag_citation(item: dict) -> str:
    page = item.get("page")
    section = item.get("section") or "General"
    return f"{item.get('filename','Unknown')} — page {page}, section {section}, chunk {item.get('chunk_id','unknown')}"

def evidence_bundle(items: list[dict]) -> list[dict]:
    return [{
        "type": "knowledge_base",
        "title": x.get("filename"),
        "page": x.get("page"),
        "section": x.get("section"),
        "chunk_id": x.get("chunk_id"),
        "excerpt": x.get("text","")[:700],
    } for x in items]
