"""Hybrid retrieval: BM25 + ChromaDB vector with reciprocal rank fusion."""

import logging
from typing import List, Dict, Any, Optional, Tuple

from rank_bm25 import BM25Okapi

from backend.app.db.vector import query_chunks, get_or_create_collection
from backend.app.tools.standards import search_standards_by_product, lookup_by_standard_no

logger = logging.getLogger("parakh.retrieval")

# BM25 index (lazy-loaded)
_bm25_index: Optional[BM25Okapi] = None
_bm25_corpus: List[Dict[str, Any]] = []


def _build_bm25_index() -> None:
    """Build BM25 index from all chunks in ChromaDB."""
    global _bm25_index, _bm25_corpus

    if _bm25_index is not None:
        return  # Already built

    logger.info("Building BM25 index from ChromaDB...")
    try:
        collection = get_or_create_collection()
        all_data = collection.get(include=["documents", "metadatas"])
    except Exception as e:
        logger.warning(f"Failed to access ChromaDB for BM25: {e}")
        _bm25_corpus = []
        _bm25_index = None
        return

    if not all_data["ids"] or len(all_data["documents"]) == 0:
        logger.warning("No documents in ChromaDB to build BM25 index")
        _bm25_corpus = []
        _bm25_index = None
        return

    _bm25_corpus = [
        {
            "id": all_data["ids"][i],
            "text": all_data["documents"][i],
            "metadata": all_data["metadatas"][i],
        }
        for i in range(len(all_data["ids"]))
    ]

    # Tokenize for BM25
    tokenized = [doc["text"].lower().split() for doc in _bm25_corpus]
    # Filter out empty token lists
    tokenized = [t for t in tokenized if t]
    if not tokenized:
        _bm25_index = None
        return

    _bm25_index = BM25Okapi(tokenized)
    logger.info(f"BM25 index built with {len(_bm25_corpus)} documents")


def retrieve_bm25(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Retrieve top-k chunks using BM25."""
    _build_bm25_index()

    if _bm25_index is None or not _bm25_corpus:
        return []

    tokenized_query = query.lower().split()
    if not tokenized_query:
        return []

    scores = _bm25_index.get_scores(tokenized_query)

    # Get top-k indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:  # Only include docs with non-zero score
            results.append(
                {
                    "id": _bm25_corpus[idx]["id"],
                    "text": _bm25_corpus[idx]["text"],
                    "metadata": _bm25_corpus[idx]["metadata"],
                    "score": float(scores[idx]),
                }
            )

    return results


def retrieve_vector(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Retrieve top-k chunks using vector similarity."""
    try:
        results = query_chunks(query, n_results=top_k)
        return [
            {
                "id": r["id"],
                "text": r["text"],
                "metadata": r["metadata"],
                "score": 1.0 - r["distance"],  # Convert distance to similarity
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Vector retrieval failed or collection empty: {e}")
        return []


def reciprocal_rank_fusion(
    bm25_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Fuse BM25 and vector results using Reciprocal Rank Fusion.
    RRF score = sum(1 / (k + rank)) for each result list.
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # Process BM25 results
    for rank, doc in enumerate(bm25_results, start=1):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        doc_map[doc_id] = doc

    # Process vector results
    for rank, doc in enumerate(vector_results, start=1):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in doc_map:
            doc_map[doc_id] = doc

    # Sort by fused score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id]
        doc["fused_score"] = scores[doc_id]
        fused.append(doc)

    return fused


async def hybrid_retrieve(
    query: str,
    top_k: int = 10,
    use_reranker: bool = False,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: BM25 + vector with RRF fusion.
    Optional: reranking (not implemented in Phase 2).
    """
    logger.info(f"Hybrid retrieval for: '{query[:60]}...'")

    # 1. BM25 retrieval
    bm25_results = retrieve_bm25(query, top_k=top_k * 2)
    logger.info(f"BM25 retrieved {len(bm25_results)} results")

    # 2. Vector retrieval
    vector_results = retrieve_vector(query, top_k=top_k * 2)
    logger.info(f"Vector retrieved {len(vector_results)} results")

    # 3. Fuse with RRF
    fused = reciprocal_rank_fusion(bm25_results, vector_results)[:top_k]
    logger.info(f"RRF fused to top {len(fused)} results")

    # 4. Optional reranker (placeholder for Phase 3)
    if use_reranker:
        logger.info("Reranker not implemented in Phase 2, skipping")

    return fused


async def gather_context(intent: str, question: str, language: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Gather context for the given question using hybrid retrieval + SQL tools.
    Returns a tuple of (context_string, list_of_retrieved_chunks).
    The intent and language are currently unused but kept for API compatibility.
    """
    logger.debug(f"gather_context called with question: {question}")
    # 1. Hybrid retrieval from ChromaDB (scraped web pages)
    results = await hybrid_retrieve(query=question, top_k=5)
    logger.debug(f"hybrid_retrieve returned {len(results)} results")
    
    # 2. SQL tools for product/standard lookup (from seed data in SQLite)
    sql_results = []
    
    # Try to extract IS standard number from question
    import re
    is_match = re.search(r"IS\s*\d+(?:\s*:\s*\d+)?", question, re.IGNORECASE)
    if is_match:
        logger.debug(f"IS match found: {is_match.group(0)}")
        try:
            std_result = await lookup_by_standard_no(is_match.group(0))
            if std_result:
                sql_results.append({
                    "id": f"sql_standard_{std_result.get('applicable_standard', 'unknown')}",
                    "text": f"Product: {std_result.get('product_name', 'N/A')}\nStandard: {std_result.get('applicable_standard', 'N/A')}\nScheme: {std_result.get('scheme_code', 'N/A')}\nMandatory: {std_result.get('mandatory', False)}\nQCO Order: {std_result.get('qco_order', 'N/A')}",
                    "metadata": {"source": "sql_tool", "type": "standard_lookup"},
                    "score": 1.0,
                })
        except Exception as e:
            logger.warning(f"SQL standard lookup failed: {e}")
    
    # Search for products matching the query
    try:
        product_results = await search_standards_by_product(question)
        logger.info(f"SQL product search returned {len(product_results)} results for: {question}")
        for i, prod in enumerate(product_results[:3]):
            sql_results.append({
                "id": f"sql_product_{prod.get('product_name', 'unknown')}_{i}",
                "text": f"Product: {prod.get('product_name', 'N/A')}\nStandard: {prod.get('applicable_standard', 'N/A')}\nScheme: {prod.get('scheme_code', 'N/A')}\nMandatory: {prod.get('mandatory', False)}\nQCO Order: {prod.get('qco_order', 'N/A')}",
                "metadata": {"source": "sql_tool", "type": "product_search"},
                "score": 0.9 - i * 0.1,
            })
    except Exception as e:
        logger.warning(f"SQL product search failed: {e}")
    
    # Combine results
    all_results = results + sql_results
    
    # Build context string
    context = "\n\n---\n\n".join([doc["text"] for doc in all_results])
    logger.info(f"gather_context returning {len(all_results)} results ({len(results)} vector + {len(sql_results)} sql)")
    return context, all_results
