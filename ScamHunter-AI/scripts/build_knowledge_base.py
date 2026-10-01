import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from rag.ingestion import KnowledgeBase


def main():
    settings = Settings.from_runtime()
    kb = KnowledgeBase(settings)

    print("Building ScamHunter AI Knowledge Base...")
    print("-" * 50)

    result = kb.build()

    print("\nKnowledge Base Ready")
    print("-" * 50)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\nGenerated files:")
    print("✓ knowledge_base/metadata.json")
    print("✓ knowledge_base/all_chunks.json")
    print("✓ knowledge_base/manifest.json")
    print("✓ knowledge_base/faiss/index.faiss")
    print("✓ knowledge_base/faiss/metadata.json")


if __name__ == "__main__":
    main()
