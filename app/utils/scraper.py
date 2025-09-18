# app/utils/scraper.py
import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# ---------------- Sources ----------------
PIB_URL = "https://pib.gov.in/factcheck.aspx"
FEEDS = {
    "AltNews": "https://www.altnews.in/feed/",
    "BOOM": "https://www.boomlive.in/rss",
    "Factly": "https://factly.in/feed/",
}

# ---------------- Helpers ----------------
def _variants(q: str) -> list[str]:
    """Generate simple query variants to improve matching."""
    base = (q or "").strip()
    low = base.lower()
    words = low.split()

    variants = {low}
    if len(words) > 2:
        variants.add(" ".join(words[:2]))   # first two words
        variants.add(" ".join(words[-2:]))  # last two words
    return list(variants)

def _similarity(a: str, b: str) -> float:
    """Compute fuzzy similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _filter_factcheck_links(href: str) -> bool:
    """Return True if link looks like a fact-check article or PDF."""
    if not href:
        return False
    href = href.lower()
    if "factcheck" in href or href.endswith(".pdf") or "fake" in href:
        return True
    return False

# ---------------- Main Scraper ----------------
def fetch_factchecks(query: str) -> list[dict]:
    """
    Fetch fact-check articles from PIB, AltNews, BOOM, Factly.
    Returns: list of {url, verdict}
    """
    results = []
    variants = _variants(query)

    # ---- RSS feeds (AltNews / BOOM / Factly) ----
    for name, feed_url in FEEDS.items():
        try:
            d = feedparser.parse(feed_url)
            for entry in d.entries[:20]:  # look at latest 20 posts
                title = entry.get("title", "")
                link = entry.get("link", "")
                if not link:
                    continue

                for v in variants:
                    ratio = _similarity(v, title)
                    if ratio > 0.3:  # loose threshold
                        logger.info(f"{name} matched {v} with {title} ({ratio:.2f})")
                        results.append({"url": link, "verdict": "Fake"})
                        break
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
                        results.append({"url": href, "verdict": "Fake"})
                        break
    except Exception as e:
        logger.warning(f"PIB fetch failed: {e}")

    # ---- Deduplicate by URL ----
    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            deduped.append(r)
            seen.add(r["url"])

    return deduped

# the code gives null values as verdict and source, can be updated later
'''
# app/utils/scraper.py
import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# ---------------- Sources ----------------
PIB_URL = "https://pib.gov.in/factcheck.aspx"
FEEDS = {
    "AltNews": "https://www.altnews.in/feed/",
    "BOOM": "https://www.boomlive.in/rss",
    "Factly": "https://factly.in/feed/",
}

# ---------------- Helpers ----------------
def _variants(q: str) -> list[str]:
    """Generate simple query variants to improve matching."""
    base = (q or "").strip()
    low = base.lower()
    words = low.split()

    variants = {low}
    if len(words) > 2:
        variants.add(" ".join(words[:2]))   # first two words
        variants.add(" ".join(words[-2:]))  # last two words
    return list(variants)

def _similarity(a: str, b: str) -> float:
    """Compute fuzzy similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def _filter_factcheck_links(href: str) -> bool:
    """Return True if link looks like a fact-check article or PDF."""
    if not href:
        return False
    href = href.lower()
    return any(keyword in href for keyword in ["factcheck", "fake", "misleading"]) or href.endswith(".pdf")

def _infer_verdict(title: str) -> str:
    """Guess verdict based on title text."""
    t = (title or "").lower()
    if "fake" in t or "false" in t: 
        return "Fake"
    if "true" in t or "genuine" in t: 
        return "True"
    if "misleading" in t: 
        return "Misleading"
    return "Unverified"

# ---------------- Main Scraper ----------------
def fetch_factchecks(query: str) -> list[dict]:
    """
    Fetch fact-check articles from PIB, AltNews, BOOM, Factly.
    Returns: list of {url, source, verdict}
    """
    results = []
    variants = _variants(query)

    # ---- RSS feeds (AltNews / BOOM / Factly) ----
    for name, feed_url in FEEDS.items():
        try:
            d = feedparser.parse(feed_url)
            for entry in d.entries[:20]:  # look at latest 20 posts
                title = entry.get("title", "")
                link = entry.get("link", "")
                if not link:
                    continue

                for v in variants:
                    ratio = _similarity(v, title)
                    if ratio > 0.3:  # loose threshold
                        verdict = _infer_verdict(title)
                        logger.info(f"{name} matched {v} with {title} ({ratio:.2f})")
                        results.append({
                            "source": name,
                            "url": link,
                            "verdict": verdict
                        })
                        break
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
                        verdict = _infer_verdict(title)
                        logger.info(f"PIB matched {v} with {title} ({ratio:.2f})")
                        results.append({
                            "source": "PIB",
                            "url": href,
                            "verdict": verdict
                        })
                        break
    except Exception as e:
        logger.warning(f"PIB fetch failed: {e}")

    # ---- Deduplicate by URL ----
    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            deduped.append(r)
            seen.add(r["url"])

    return deduped
'''