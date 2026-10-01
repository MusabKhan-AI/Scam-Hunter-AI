from __future__ import annotations

from pathlib import Path
import hashlib
import json

from rag.extraction import extract_document, clean_text
from rag.chunking import chunk_text
from rag.embeddings import get_embedder
from rag.vector_store import VectorStore


SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


class KnowledgeBase:
    def __init__(self, settings):
        self.settings = settings

        self.doc_dir = settings.data_dir / "documents"
        self.chunk_dir = settings.data_dir / "chunks"
        self.faiss_dir = settings.data_dir / "faiss"

        self.manifest_path = settings.data_dir / "manifest.json"
        self.chunks_path = settings.data_dir / "all_chunks.json"
        self.metadata_path = settings.data_dir / "metadata.json"

        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_dir.mkdir(parents=True, exist_ok=True)

        self.manifest = self._load_manifest()
        self.all_chunks = self._load_chunks()

        self.embedder = None
        self.store = VectorStore(self.faiss_dir)

    def _load_manifest(self):
        if self.manifest_path.exists():
            try:
                return json.loads(
                    self.manifest_path.read_text(encoding="utf-8")
                )
            except Exception:
                return {}
        return {}

    def _load_chunks(self):
        if self.chunks_path.exists():
            try:
                return json.loads(
                    self.chunks_path.read_text(encoding="utf-8")
                )
            except Exception:
                return []
        return []

    @staticmethod
    def sha256(path: Path) -> str:
        h = hashlib.sha256()

        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)

        return h.hexdigest()

    def _all_source_files(self):
        return [
            p
            for p in self.doc_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED
        ]

    def _chunks_for_file(self, path: Path, digest: str) -> list[dict]:
        doc_id = digest[:16]
        chunks = []

        for page in extract_document(path):
            cleaned = clean_text(page["text"])

            page_chunks = chunk_text(
                cleaned,
                self.settings.chunk_size,
                self.settings.chunk_overlap,
            )

            for n, chunk in enumerate(page_chunks):
                chunks.append(
                    {
                        "document_id": doc_id,
                        "filename": path.name,
                        "file_type": path.suffix.lower(),
                        "source_type": "knowledge_base",
                        "page": page.get("page", 1),
                        "section": page.get("section", ""),
                        "chunk_id": f"{doc_id}-{n:04d}",
                        "text": chunk,
                    }
                )

        return chunks

    def _write_metadata(self, embedding_dimension: int | None = None):
        metadata = []

        for index, chunk in enumerate(self.all_chunks):
            metadata.append(
                {
                    "faiss_index": index,
                    "document_id": chunk.get("document_id"),
                    "filename": chunk.get("filename"),
                    "file_type": chunk.get("file_type"),
                    "source_type": chunk.get("source_type"),
                    "page": chunk.get("page"),
                    "section": chunk.get("section"),
                    "chunk_id": chunk.get("chunk_id"),
                    "embedding_model": self.settings.embedding_model,
                    "embedding_dimension": embedding_dimension,
                }
            )

        payload = {
            "version": 1,
            "embedding_model": self.settings.embedding_model,
            "embedding_dimension": embedding_dimension,
            "total_documents": len(self.manifest),
            "total_chunks": len(self.all_chunks),
            "vector_index": "FAISS IndexFlatIP",
            "chunks": metadata,
        }

        self.metadata_path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def build(self) -> dict:
        files = self._all_source_files()

        current = {}
        changed = []
        removed_ids = set()

        for path in files:
            rel = str(path.relative_to(self.doc_dir))
            digest = self.sha256(path)
            doc_id = digest[:16]

            current[rel] = {
                "sha256": digest,
                "document_id": doc_id,
                "filename": path.name,
            }

            old = self.manifest.get(rel)

            if not old or old.get("sha256") != digest:
                changed.append(
                    (rel, path, digest, doc_id)
                )

        for rel, old in self.manifest.items():
            if rel not in current:
                removed_ids.add(old.get("document_id"))

        old_changed_ids = {
            self.manifest[rel]["document_id"]
            for rel, _, _, _ in changed
            if rel in self.manifest
        }

        drop_ids = removed_ids | old_changed_ids

        if drop_ids:
            self.all_chunks = [
                chunk
                for chunk in self.all_chunks
                if chunk.get("document_id") not in drop_ids
            ]

        added_chunks = []

        for _, path, digest, _ in changed:
            added_chunks.extend(
                self._chunks_for_file(path, digest)
            )

        self.all_chunks.extend(added_chunks)

        embedding_dimension = None

        if changed or removed_ids or not self.store.count:
            texts = [
                chunk["text"]
                for chunk in self.all_chunks
            ]

            if texts:
                if self.embedder is None:
                    self.embedder = get_embedder(
                        self.settings.embedding_model
                    )

                vectors = self.embedder.encode(texts)

                embedding_dimension = int(vectors.shape[1])

                self.store.replace(
                    vectors,
                    self.all_chunks,
                )

            else:
                self.store.index = None
                self.store.metadata = []

                if self.store.index_path.exists():
                    self.store.index_path.unlink()

                self.store.meta_path.write_text(
                    "[]",
                    encoding="utf-8",
                )

        else:
            if self.all_chunks:
                embedding_dimension = len(
                    self.all_chunks[0].get(
                        "embedding_dimension",
                        []
                    )
                ) or None

        self.manifest = current

        self.manifest_path.write_text(
            json.dumps(
                current,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.chunks_path.write_text(
            json.dumps(
                self.all_chunks,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self._write_metadata(
            embedding_dimension=embedding_dimension
        )

        return {
            "documents": len(files),
            "chunks": len(self.all_chunks),
            "vectors": len(self.all_chunks),
            "changed_documents": len(changed),
            "removed_documents": len(removed_ids),
            "reembedded": bool(
                changed
                or removed_ids
                or not self.store.count
            ),
            "metadata_file": str(self.metadata_path),
        }

    def add_upload(self, source_path: str | Path) -> Path:
        source_path = Path(source_path)

        target = self.doc_dir / source_path.name

        target.write_bytes(
            source_path.read_bytes()
        )

        return target
