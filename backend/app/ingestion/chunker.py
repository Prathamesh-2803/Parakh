"""Structure-aware chunker for Indian Standards and BIS documents."""

import hashlib
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger("parakh.chunker")


class StructureChunker:
    """Chunks documents into semantic pieces based on clauses, headings, or Q&A pairs."""

    @staticmethod
    def chunk_document(
        parsed_doc: Dict[str, Any],
        max_chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Structure-aware chunking:
        1. If sections/clauses exist, split by clause/heading
        2. Fallback to paragraph-based splitting
        3. Attach comprehensive metadata to every chunk
        """
        meta = parsed_doc.get("metadata", {})
        source_name = meta.get("filename", "unknown")
        url = meta.get("source_url", "")
        chunks: List[Dict[str, Any]] = []

        sections = parsed_doc.get("sections", [])
        if sections:
            # Chunk by HTML/document sections
            for sec in sections:
                heading = sec.get("heading", "")
                content = sec.get("content", "")
                if not content:
                    continue

                # Detect standard number or scheme in heading/content
                std_no = StructureChunker._extract_standard_no(f"{heading} {content}")
                scheme = StructureChunker._extract_scheme(f"{heading} {content}")

                chunk_text = f"## {heading}\n\n{content}"
                if len(chunk_text) > max_chunk_size:
                    sub_chunks = StructureChunker._split_text(chunk_text, max_chunk_size, chunk_overlap)
                    for i, sub in enumerate(sub_chunks):
                        chunks.append(
                            StructureChunker._create_chunk_dict(
                                text=sub,
                                source_name=source_name,
                                url=url,
                                clause=heading,
                                standard_no=std_no,
                                scheme=scheme,
                                chunk_idx=len(chunks),
                            )
                        )
                else:
                    chunks.append(
                        StructureChunker._create_chunk_dict(
                            text=chunk_text,
                            source_name=source_name,
                            url=url,
                            clause=heading,
                            standard_no=std_no,
                            scheme=scheme,
                            chunk_idx=len(chunks),
                        )
                    )
        else:
            # Fallback to paragraph / clause-based text chunking
            full_text = parsed_doc.get("full_text", "")
            raw_chunks = StructureChunker._split_text(full_text, max_chunk_size, chunk_overlap)

            for i, text in enumerate(raw_chunks):
                std_no = StructureChunker._extract_standard_no(text)
                scheme = StructureChunker._extract_scheme(text)
                clause = StructureChunker._extract_clause(text)

                chunks.append(
                    StructureChunker._create_chunk_dict(
                        text=text,
                        source_name=source_name,
                        url=url,
                        clause=clause,
                        standard_no=std_no,
                        scheme=scheme,
                        chunk_idx=i,
                    )
                )

        logger.info(f"Chunked document {source_name} into {len(chunks)} chunks")
        return chunks

    @staticmethod
    def _create_chunk_dict(
        text: str,
        source_name: str,
        url: str,
        clause: Optional[str],
        standard_no: Optional[str],
        scheme: Optional[str],
        chunk_idx: int,
    ) -> Dict[str, Any]:
        """Create standard chunk dictionary with deterministic ID and rich metadata."""
        # Generate stable ID
        id_str = f"{source_name}:{chunk_idx}:{text[:50]}"
        chunk_id = hashlib.md5(id_str.encode("utf-8")).hexdigest()

        return {
            "id": chunk_id,
            "text": text,
            "metadata": {
                "source_name": source_name,
                "url": url,
                "standard_no": standard_no or "N/A",
                "clause": clause or "N/A",
                "scheme": scheme or "N/A",
                "product_category": "General",
                "mandatory_or_voluntary": "Mandatory" if "QCO" in text or "compulsory" in text.lower() else "Voluntary",
                "date": "2026-09",
            },
        }

    @staticmethod
    def _split_text(text: str, max_size: int, overlap: int) -> List[str]:
        """Split text cleanly on paragraph boundaries or sentences with overlap."""
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > max_size and current:
                chunks.append("\n\n".join(current))
                # Keep last paragraph for overlap
                current = [current[-1], p] if len(current[-1]) < overlap else [p]
                current_len = sum(len(x) for x in current)
            else:
                current.append(p)
                current_len += p_len

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    @staticmethod
    def _extract_standard_no(text: str) -> Optional[str]:
        """Regex extraction for Indian Standard numbers like 'IS 1239', 'IS/ISO 9001'."""
        match = re.search(r"\b(IS(?:/ISO)?\s*\d+(?:\s*(?:Part\s*\d+|Pt\s*\d+|\(Part\s*\d+\)))?(?::\s*\d{4})?)\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    @staticmethod
    def _extract_scheme(text: str) -> Optional[str]:
        """Detect BIS certification scheme."""
        t = text.lower()
        if "hallmarking" in t or "huid" in t:
            return "Hallmarking"
        if "crs" in t or "compulsory registration" in t:
            return "CRS (Scheme-II)"
        if "fmcs" in t or "foreign manufacturers" in t:
            return "FMCS"
        if "isi" in t or "scheme-i" in t or "scheme i" in t or "mark scheme" in t:
            return "ISI (Scheme-I)"
        return None

    @staticmethod
    def _extract_clause(text: str) -> Optional[str]:
        """Detect clause numbers like 'Clause 4.1' or '4.1 Scope'."""
        match = re.search(r"(?:Clause\s+)?(\d+\.\d+(?:\.\d+)?\s+[A-Z][a-zA-Z\s]+)", text)
        if match:
            return match.group(1).strip()
        return None
