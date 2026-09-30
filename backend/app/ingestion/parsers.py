"""Document parsers: PDF, HTML, and OCR fallback for scanned pages."""

import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger("parakh.parsers")

# OCR availability check
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class DocumentParser:
    """Multi-format parser for BIS documents (PDF, HTML, Text)."""

    @staticmethod
    def parse_file(filepath: Path) -> Dict[str, Any]:
        """Auto-detect format and parse file, returning text + structural elements."""
        suffix = filepath.suffix.lower()
        meta_file = filepath.with_suffix(filepath.suffix + ".meta.json")

        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not load metadata for {filepath}: {e}")

        if suffix == ".pdf":
            parsed = DocumentParser.parse_pdf(filepath)
        elif suffix in [".html", ".htm"]:
            parsed = DocumentParser.parse_html(filepath)
        elif suffix in [".txt", ".md"]:
            parsed = DocumentParser.parse_text(filepath)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        parsed["metadata"] = meta
        parsed["filepath"] = str(filepath)
        return parsed

    @staticmethod
    def parse_pdf(filepath: Path) -> Dict[str, Any]:
        """Extract text, tables, and sections from PDF using PyMuPDF and pdfplumber."""
        text_pages = []
        tables = []
        toc = []

        try:
            # 1. Fast text and TOC extraction with PyMuPDF
            doc = fitz.open(filepath)
            toc = doc.get_toc()

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                # If page is empty or very short, try OCR fallback
                if len(page_text.strip()) < 50 and TESSERACT_AVAILABLE:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = pytesseract.image_to_string(img)
                    if len(ocr_text.strip()) > len(page_text.strip()):
                        page_text = ocr_text

                text_pages.append(
                    {
                        "page_number": page_num + 1,
                        "text": page_text,
                    }
                )

            # 2. Table extraction with pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    extracted_tables = page.extract_tables()
                    for t in extracted_tables:
                        if t:
                            tables.append(
                                {
                                    "page_number": page_num + 1,
                                    "table": t,
                                }
                            )

        except Exception as e:
            logger.error(f"Error parsing PDF {filepath}: {e}")
            raise

        full_text = "\n\n".join([p["text"] for p in text_pages])
        return {
            "full_text": full_text,
            "pages": text_pages,
            "tables": tables,
            "toc": toc,
        }

    @staticmethod
    def parse_html(filepath: Path) -> Dict[str, Any]:
        """Extract clean text, headings, and tables from HTML."""
        content = filepath.read_text(encoding="utf-8")
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for s in soup(["script", "style", "nav", "footer", "header"]):
            s.decompose()

        # Extract headings and structure
        sections = []
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            h_text = heading.get_text(strip=True)
            # Find all content until next heading
            content_nodes = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h1", "h2", "h3", "h4"]:
                    break
                content_nodes.append(sibling.get_text(strip=True))
            sections.append(
                {
                    "heading": h_text,
                    "content": "\n".join(content_nodes),
                }
            )

        # Extract tables
        tables = []
        for t in soup.find_all("table"):
            rows = []
            for tr in t.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({"table": rows})

        full_text = soup.get_text(separator="\n\n", strip=True)

        return {
            "full_text": full_text,
            "sections": sections,
            "tables": tables,
        }

    @staticmethod
    def parse_text(filepath: Path) -> Dict[str, Any]:
        """Parse raw text or markdown."""
        content = filepath.read_text(encoding="utf-8")
        return {
            "full_text": content,
            "sections": [],
            "tables": [],
        }
