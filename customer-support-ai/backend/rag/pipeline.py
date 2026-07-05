"""
RAG Pipeline
============
Load PDFs → chunk → embed → store in FAISS → retrieve on query
"""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Tuple

# Lazy imports (installed at runtime)
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    from pypdf import PdfReader
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False

KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
VECTORSTORE_PATH   = os.getenv("VECTORSTORE_PATH",   "backend/vectorstore")
EMBEDDING_MODEL    = os.getenv("EMBEDDING_MODEL",    "all-MiniLM-L6-v2")

CHUNK_SIZE    = 500   # characters
CHUNK_OVERLAP = 100
TOP_K         = 5     # number of chunks to retrieve


# ── Text helpers ────────────────────────────────────────────────────────────────

def load_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_text_from_txt(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, source: str) -> List[dict]:
    """Split text into overlapping chunks and tag with source."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "source": source})
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def load_all_documents() -> List[dict]:
    """Load all PDFs and text files from the knowledge base directory."""
    all_chunks = []
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        print(f"⚠️  Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return all_chunks

    for file in kb_path.iterdir():
        try:
            if file.suffix.lower() == ".pdf":
                text = load_text_from_pdf(str(file))
            elif file.suffix.lower() in (".txt", ".md"):
                text = load_text_from_txt(str(file))
            else:
                continue
            chunks = chunk_text(text, file.name)
            all_chunks.extend(chunks)
            print(f"  Loaded {len(chunks)} chunks from {file.name}")
        except Exception as e:
            print(f"  ⚠️  Could not load {file.name}: {e}")

    print(f"✅ Total chunks loaded: {len(all_chunks)}")
    return all_chunks


# ── VectorStore ─────────────────────────────────────────────────────────────────

class VectorStore:
    def __init__(self):
        self.model  = None
        self.index  = None
        self.chunks: List[dict] = []

    def _get_model(self):
        if self.model is None:
            print(f"Loading embedding model: {EMBEDDING_MODEL} …")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        return self.model

    def build(self, chunks: List[dict]):
        """Embed all chunks and build the FAISS index."""
        if not chunks:
            print("No chunks to embed.")
            return
        model = self._get_model()
        texts = [c["text"] for c in chunks]
        print(f"Embedding {len(texts)} chunks …")
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
        dim = embeddings.shape[1]
        self.index  = faiss.IndexFlatL2(dim)
        self.index.add(embeddings.astype(np.float32))
        self.chunks = chunks
        print(f"✅ FAISS index built with {self.index.ntotal} vectors (dim={dim})")

    def save(self):
        os.makedirs(VECTORSTORE_PATH, exist_ok=True)
        faiss.write_index(self.index, f"{VECTORSTORE_PATH}/index.faiss")
        with open(f"{VECTORSTORE_PATH}/chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        print(f"✅ Vector store saved to {VECTORSTORE_PATH}/")

    def load(self) -> bool:
        idx_path    = f"{VECTORSTORE_PATH}/index.faiss"
        chunks_path = f"{VECTORSTORE_PATH}/chunks.pkl"
        if not (os.path.exists(idx_path) and os.path.exists(chunks_path)):
            return False
        self.index = faiss.read_index(idx_path)
        with open(chunks_path, "rb") as f:
            self.chunks = pickle.load(f)
        _ = self._get_model()   # warm up
        print(f"✅ Vector store loaded ({self.index.ntotal} vectors).")
        return True

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Tuple[str, str, float]]:
        """Return list of (chunk_text, source, distance)."""
        if self.index is None or self.index.ntotal == 0:
            return []
        model = self._get_model()
        q_emb = model.encode([query]).astype(np.float32)
        distances, indices = self.index.search(q_emb, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                c = self.chunks[idx]
                results.append((c["text"], c["source"], float(dist)))
        return results

    def format_context(self, query: str, top_k: int = TOP_K) -> str:
        """Build a context string from top-K retrieved chunks."""
        hits = self.retrieve(query, top_k)
        if not hits:
            return ""
        parts = []
        for i, (text, source, _) in enumerate(hits, 1):
            parts.append(f"[Source: {source}]\n{text}")
        return "\n\n---\n\n".join(parts)


# ── Singleton ──────────────────────────────────────────────────────────────────

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


async def initialize_rag():
    """Called once at server startup."""
    if not DEPS_AVAILABLE:
        print("⚠️  RAG dependencies not installed; semantic retrieval disabled.")
        return

    store = get_vector_store()
    if store.load():
        return   # already have a persisted index

    # Build from scratch
    chunks = load_all_documents()
    if chunks:
        store.build(chunks)
        store.save()
    else:
        print("⚠️  No documents found – RAG context will be empty.")
