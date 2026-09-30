"""Polite scrapers for public BIS sources."""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from backend.app.config import settings

logger = logging.getLogger("parakh.scrapers")

# Base URLs
BIS_BASE_URL = "https://www.bis.gov.in"
CRS_BASE_URL = "https://www.crsbis.in"
MANAK_BASE_URL = "https://www.services.bis.gov.in"

# Rate limiting
DEFAULT_DELAY = 2.0  # seconds between requests
RAW_DATA_DIR = Path("./data/raw")


class BISScraper:
    """Base scraper with politeness, rate limiting, and raw file saving."""

    def __init__(self, delay: float = DEFAULT_DELAY):
        self.delay = delay
        self.last_request_time = 0.0
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Parakh-Research/0.1.0",
                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            },
            timeout=30.0,
            follow_redirects=True,
        )

    async def _rate_limit(self) -> None:
        """Enforce delay between requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    async def fetch(self, url: str) -> Optional[httpx.Response]:
        """Fetch a URL with rate limiting and error handling."""
        await self._rate_limit()
        try:
            logger.info(f"Fetching: {url}")
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def save_raw(
        self,
        content: bytes | str,
        filename: str,
        url: str,
        content_type: str = "html",
    ) -> Path:
        """Save raw downloaded content along with a metadata sidecar file."""
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Save main file
        filepath = RAW_DATA_DIR / filename
        if isinstance(content, str):
            filepath.write_text(content, encoding="utf-8")
        else:
            filepath.write_bytes(content)

        # Save metadata sidecar
        meta_filepath = filepath.with_suffix(filepath.suffix + ".meta.json")
        meta = {
            "source_url": url,
            "fetched_at": datetime.utcnow().isoformat(),
            "content_type": content_type,
            "filename": filename,
        }
        meta_filepath.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        logger.info(f"Saved raw file: {filepath} ({len(content)} bytes)")
        return filepath

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Specific scrapers
# ---------------------------------------------------------------------------

class FAQScraper(BISScraper):
    """Scrapes BIS public FAQ pages."""

    FAQ_URLS = [
        ("https://www.bis.gov.in/product-certification/faqs/", "faqs_product_cert.html"),
        ("https://www.bis.gov.in/hallmarking-overview/faqs-hallmarking/", "faqs_hallmarking.html"),
        ("https://www.crsbis.in/BIS/faq.do", "faqs_crs.html"),
    ]

    async def scrape_all(self) -> List[Path]:
        saved = []
        for url, filename in self.FAQ_URLS:
            resp = await self.fetch(url)
            if resp:
                p = self.save_raw(resp.text, filename, url, "html")
                saved.append(p)
        return saved


class SchemeManualScraper(BISScraper):
    """Scrapes / downloads official BIS scheme manuals and guidelines."""

    SCHEME_URLS = [
        ("https://www.bis.gov.in/product-certification/scheme-i-mark-scheme/", "scheme_i_isi.html"),
        ("https://www.crsbis.in/BIS/about-crs.do", "scheme_ii_crs.html"),
        ("https://www.bis.gov.in/fmcs/fmcs-overview/", "scheme_fmcs.html"),
        ("https://www.bis.gov.in/hallmarking-overview/", "scheme_hallmarking.html"),
    ]

    async def scrape_all(self) -> List[Path]:
        saved = []
        for url, filename in self.SCHEME_URLS:
            resp = await self.fetch(url)
            if resp:
                p = self.save_raw(resp.text, filename, url, "html")
                saved.append(p)
        return saved


class QCOScraper(BISScraper):
    """Scrapes Quality Control Orders (QCO) listings for mandatory standards."""

    QCO_LIST_URL = "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/quality-control-orders/"

    async def scrape_all(self) -> List[Path]:
        resp = await self.fetch(self.QCO_LIST_URL)
        if resp:
            return [self.save_raw(resp.text, "qco_list.html", self.QCO_LIST_URL, "html")]
        return []
