"""ChromaDB wrapper for vector storage and retrieval."""

import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from backend.app.config import settings

logger = logging.getLogger("parakh.vector")

# ---------------------------------------------------------------------------
# Embedding model (local, singleton)
# ---------------------------------------------------------------------------

_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the BGE-M3 embedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: BAAI/bge-m3")
        _embedding_model = SentenceTransformer("BAAI/bge-m3")
    return _embedding_model


# ---------------------------------------------------------------------------
# ChromaDB client and collection
# ---------------------------------------------------------------------------

_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        logger.info(f"Initializing ChromaDB at {settings.CHROMA_PERSIST_DIR}")
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_or_create_collection(name: str = "pramaan_chunks"):
    # Keep the existing collection name so the bundled vector index remains available.
    """Get or create the ChromaDB collection for text chunks."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        try:
            _collection = client.get_collection(name)
            logger.info(f"Loaded existing collection '{name}' with {_collection.count()} items")
        except Exception:
            logger.info(f"Creating new collection '{name}'")
            _collection = client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
    return _collection


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_chunks(
    chunks: List[Dict[str, Any]],
    batch_size: int = 100,
) -> None:
    """
    Add text chunks to the vector store.

    Each chunk dict must have:
        - text: str
        - id: str (unique)
        - metadata: dict (will be stored as-is in ChromaDB)
    """
    if not chunks:
        return

    collection = get_or_create_collection()
    model = get_embedding_model()

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk["text"] for chunk in batch]
        ids = [chunk["id"] for chunk in batch]
        metadatas = [chunk["metadata"] for chunk in batch]

        # Compute embeddings
        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

        # Upsert into ChromaDB
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        logger.info(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} chunks)")


def query_chunks(
    query_text: str,
    n_results: int = 10,
    where: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Query the vector store for similar chunks.

    Returns a list of dicts with keys: id, text, metadata, distance.
    """
    collection = get_or_create_collection()
    model = get_embedding_model()

    # Embed the query
    query_embedding = model.encode([query_text], normalize_embeddings=True).tolist()[0]

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Format results
    formatted: List[Dict[str, Any]] = []
    for i in range(len(results["ids"][0])):
        formatted.append(
            {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return formatted
