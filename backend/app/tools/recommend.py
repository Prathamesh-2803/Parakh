"""Product compliance recommendation engine using local embeddings + LLM verification."""

import logging
from typing import List, Dict, Any, Tuple
import re
import numpy as np

from sqlalchemy import select
from backend.app.db.database import async_session
from backend.app.db.models import ProductCategory, Scheme
from backend.app.tools.labs import find_labs_by_location
from backend.app.db.vector import get_embedding_model

logger = logging.getLogger("parakh.recommend")

# Confidence thresholds
HIGH_CONFIDENCE = 0.75
AMBIGUITY_MARGIN = 0.08  # If top-2 scores within this margin, it's ambiguous

# Global cache for product embeddings to ensure sub-10ms response times
_PRODUCT_CACHE_KEYS: List[int] = []
_PRODUCT_EMBEDDINGS: np.ndarray | None = None


def _extract_keywords(text: str) -> List[str]:
    """Extract normalized keywords from product description."""
    text = text.lower()
    stopwords = {
        "i", "we", "make", "manufacture", "produce", "sell", "supply", "for", "to",
        "the", "a", "an", "of", "in", "and", "or", "from", "with", "my", "our",
        "setting", "up", "factory", "unit", "producing", "making", "manufacturing",
    }
    tokens = re.findall(r"\b\w+\b", text)
    return [t for t in tokens if t not in stopwords and len(t) > 2]


async def _get_or_compute_product_embeddings(
    all_products: List[ProductCategory],
    embedding_model: Any,
) -> Tuple[List[int], np.ndarray | None]:
    """Get cached product embeddings or compute them in a single batch."""
    global _PRODUCT_CACHE_KEYS, _PRODUCT_EMBEDDINGS

    current_ids = [p.id for p in all_products]
    if _PRODUCT_EMBEDDINGS is not None and _PRODUCT_CACHE_KEYS == current_ids:
        return _PRODUCT_CACHE_KEYS, _PRODUCT_EMBEDDINGS

    if embedding_model is None:
        return current_ids, None

    try:
        texts = [f"{p.product_name} {p.category or ''}" for p in all_products]
        logger.info(f"Computing embeddings for {len(texts)} products in batch...")
        embeddings = embedding_model.encode(texts, batch_size=32, show_progress_bar=False)
        _PRODUCT_CACHE_KEYS = current_ids
        _PRODUCT_EMBEDDINGS = np.array(embeddings)
        return _PRODUCT_CACHE_KEYS, _PRODUCT_EMBEDDINGS
    except Exception as e:
        logger.warning(f"Failed to batch compute product embeddings: {e}")
        return current_ids, None


async def recommend_compliance(
    product_description: str,
    top_k: int = 3,
) -> Tuple[List[Dict[str, Any]], bool, str | None]:
    """
    Recommend compliance requirements for a product description.

    Returns:
        (candidates, is_ambiguous, clarifying_question)
    """
    logger.info(f"Recommending compliance for: '{product_description[:60]}'")

    # 1. Extract keywords
    keywords = set(_extract_keywords(product_description))
    logger.debug(f"Extracted keywords: {keywords}")

    # 2. Fetch all products from DB
    async with async_session() as session:
        result = await session.execute(select(ProductCategory))
        all_products = result.scalars().all()

        # Also fetch scheme details
        scheme_result = await session.execute(select(Scheme))
        schemes = {s.scheme_code: s for s in scheme_result.scalars().all()}

    if not all_products:
        logger.warning("No products in database for recommendation")
        return [], False, None

    # 3. Load embedding model and compute query embedding
    try:
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.encode([product_description])[0]
        query_norm = np.linalg.norm(query_embedding)
        _, prod_embeddings = await _get_or_compute_product_embeddings(all_products, embedding_model)
    except Exception as e:
        logger.warning(f"Embedding model unavailable: {e}. Using keyword-only matching.")
        query_embedding = None
        prod_embeddings = None
        query_norm = 1.0

    # 4. Score products using keyword overlap + embedding similarity
    scores: List[Tuple[ProductCategory, float]] = []

    for idx, product in enumerate(all_products):
        # A. Keyword overlap score
        prod_tokens = set(_extract_keywords(product.product_name + " " + (product.category or "")))
        common_tokens = keywords & prod_tokens
        keyword_overlap = len(common_tokens) / max(len(keywords), 1)

        # Bonus if full product name keywords matched
        exact_keyword_bonus = 0.0
        for kw in keywords:
            if kw in product.product_name.lower():
                exact_keyword_bonus += 0.2

        # B. Semantic similarity
        semantic_score = 0.0
        if prod_embeddings is not None and query_embedding is not None:
            p_emb = prod_embeddings[idx]
            p_norm = np.linalg.norm(p_emb)
            if query_norm > 0 and p_norm > 0:
                semantic_score = float(np.dot(query_embedding, p_emb) / (query_norm * p_norm))

        # Combined score: 40% keyword, 60% semantic + exact bonus
        raw_score = 0.35 * keyword_overlap + 0.55 * max(semantic_score, 0) + min(exact_keyword_bonus, 0.25)
        combined_score = min(raw_score, 1.0)
        scores.append((product, combined_score))

    # 5. Sort and take top-k
    scores.sort(key=lambda x: x[1], reverse=True)
    top_candidates = scores[:top_k]

    # 6. Check for ambiguity (top 2 scores within margin)
    is_ambiguous = False
    clarifying_question = None
    if len(top_candidates) >= 2 and top_candidates[0][1] > 0.3:
        score_diff = top_candidates[0][1] - top_candidates[1][1]
        if score_diff < AMBIGUITY_MARGIN:
            is_ambiguous = True
            names = [c[0].product_name for c in top_candidates[:2]]
            clarifying_question = (
                f"Your product could match multiple categories: '{names[0]}' or '{names[1]}'. "
                f"Please specify your exact product type."
            )

    # 7. Build candidate responses
    candidates = []
    for product, score in top_candidates:
        if score < 0.15:  # Skip very low matches
            continue

        scheme = schemes.get(product.scheme_code)

        # Generate key requirements and next steps
        key_requirements = _generate_requirements(product, scheme)
        next_steps = _generate_next_steps(product, scheme)

        # Find labs
        labs = await find_labs_by_location(scope_keyword=product.category or product.product_name)
        lab_names = [f"{lab['lab_name']} ({lab['city']})" for lab in labs[:2]]

        candidates.append({
            "product_name": product.product_name,
            "applicable_standard": product.applicable_standard,
            "scheme_code": product.scheme_code,
            "mandatory": product.mandatory,
            "qco_order": product.qco_order,
            "confidence": round(score, 2),
            "key_requirements": key_requirements,
            "next_steps": next_steps,
            "nearest_labs": lab_names,
            "source_url": product.source_url,
        })

    logger.info(f"Recommendation complete: {len(candidates)} candidates, ambiguous={is_ambiguous}")
    return candidates, is_ambiguous, clarifying_question


def _generate_requirements(product: ProductCategory, scheme: Scheme | None) -> List[str]:
    """Generate key technical/process requirements for a product."""
    reqs = []

    if product.mandatory:
        reqs.append(f"Mandatory BIS certification under {product.qco_order or 'applicable QCO'}")

    if product.applicable_standard:
        reqs.append(f"Conform to {product.applicable_standard} specifications")

    if scheme:
        if scheme.scheme_code == "ISI":
            reqs.append("Factory audit by BIS officials")
            reqs.append("Sample testing at BIS-recognized laboratory")
            reqs.append("Maintain quality control records")
        elif scheme.scheme_code == "CRS":
            reqs.append("Self-declaration of conformity")
            reqs.append("Testing at BIS-recognized lab before registration")
            reqs.append("Submit test reports with application")
        elif scheme.scheme_code == "FMCS":
            reqs.append("Overseas factory inspection by BIS")
            reqs.append("Sample testing at accredited labs")
        elif scheme.scheme_code == "HALLMARK":
            reqs.append("Register with BIS hallmarking scheme")
            reqs.append("Obtain 6-digit HUID for each article")
            reqs.append("Hallmarking at BIS-recognized Assaying & Hallmarking Centre (AHC)")

    return reqs


def _generate_next_steps(product: ProductCategory, scheme: Scheme | None) -> List[str]:
    """Generate actionable next steps to obtain certification."""
    steps = []

    if scheme:
        if scheme.scheme_code == "ISI":
            steps.append("1. Apply online at BIS portal (www.services.bis.gov.in)")
            steps.append("2. Submit manufacturing details, factory layout, and process flowchart")
            steps.append("3. Schedule factory audit")
            steps.append("4. Obtain samples and send to BIS lab for testing")
            steps.append("5. Pay license fees upon approval")
        elif scheme.scheme_code == "CRS":
            steps.append("1. Register on CRS portal (www.crsbis.in)")
            steps.append("2. Get product tested at BIS-recognized lab")
            steps.append("3. Upload test reports and manufacturing declaration")
            steps.append("4. Pay registration fee (INR 10,000)")
            steps.append("5. Receive CRS registration number")
        elif scheme.scheme_code == "HALLMARK":
            steps.append("1. Register as manufacturer/jeweller on BIS hallmarking portal")
            steps.append("2. Find nearest Assaying & Hallmarking Centre (AHC)")
            steps.append("3. Submit articles for purity testing and hallmarking")
            steps.append("4. Obtain HUID for each article")

    if not steps:
        steps.append("Visit BIS portal for detailed application guidelines")

    return steps
