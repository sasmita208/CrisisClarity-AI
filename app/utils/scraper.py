# app/utils/scraper.py
import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Sources
PIB_URL = "https://pib.gov.in/factcheck.aspx"
FEEDS = {
    "AltNews": "https://www.altnews.in/feed/",
    "BOOM": "https://www.boomlive.in/rss",
    "Factly": "https://factly.in/feed/",
}

# -------- Helpers --------
def _variants(q: str) -> list[str]:
    """Generate simple query variants to improve matching."""
    base = (q or "").strip()
    low = base.lower()
    words = low.split()

    variants = {low}
    if len(words) > 2:
        variants.add(" ".join(words[:2]))
        variants.add(" ".join(words[-2:]))
    return list(variants)

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _filter_factcheck_links(href: str) -> bool:
    """Return True only if link is likely a fact-check article/PDF."""
    if not href:
        return False
    href = href.lower()
    if "factcheck" in href or href.endswith(".pdf"):
        return True
    return False

# -------- Main scraper --------
def fetch_factchecks(query: str) -> list[str]:
    """Fetch fact-check articles from PIB, AltNews, BOOM, Factly."""
    results = []
    variants = _variants(query)

    # ---- RSS feeds (AltNews / BOOM / Factly) ----
    for name, feed_url in FEEDS.items():
        try:
            d = feedparser.parse(feed_url)
            for entry in d.entries[:20]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                if not link:
                    continue
                for v in variants:
                    ratio = _similarity(v, title)
                    if ratio > 0.3:
                        logger.info(f"{name} matched {v} with {title} ({ratio:.2f})")
                        results.append(link)
        except Exception as e:
            logger.warning(f"Feed {name} failed: {e}")

    # ---- PIB factcheck page ----
    try:
        r = requests.get(PIB_URL, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("a[href]"):
                title = a.get_text(strip=True)
                href = urljoin(PIB_URL, a["href"])

                if not _filter_factcheck_links(href):
                    continue

                for v in variants:
                    ratio = _similarity(v, title)
                    if ratio > 0.3:
                        logger.info(f"PIB matched {v} with {title} ({ratio:.2f})")
                        results.append(href)
    except Exception as e:
        logger.warning(f"PIB fetch failed: {e}")

    # Deduplicate
    return [{"url": href, "verdict": "Fake"} for href in results]
