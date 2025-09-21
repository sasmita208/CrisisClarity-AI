# app/utils/scraper.py
import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
from typing import List, Dict

logger = logging.getLogger(__name__)

PIB_URL = "https://pib.gov.in/factcheck.aspx"
FEEDS = {
    "AltNews": "https://www.altnews.in/feed/",
    "BOOM": "https://www.boomlive.in/rss",
    "Factly": "https://factly.in/feed/",
}

# ---------- helpers ----------
def _variants(q: str) -> List[str]:
    base = (q or "").strip()
    low = base.lower()
    words = low.split()
    variants = {low}
    if len(words) > 2:
        variants.add(" ".join(words[:2]))
        variants.add(" ".join(words[-2:]))
    return list(variants)

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

def _filter_factcheck_links(href: str) -> bool:
    if not href:
        return False
    href = href.lower()
    return any(k in href for k in ["factcheck", "fake", "misleading"]) or href.endswith(".pdf") or "fact-check" in href

def _infer_verdict(title: str) -> str:
    t = (title or "").lower()
    if not t:
        return "Unverified"
    if any(x in t for x in ["fake", "false", "fabricated", "misleading", "not true", "debunk"]):
        return "Fake"
    if any(x in t for x in ["true", "genuine", "verified", "confirmed", "authentic"]):
        return "True"
    if any(x in t for x in ["misleading", "partly", "partly true", "half true"]):
        return "Misleading"
    return "Unverified"

def _read_title_from_url(url: str, timeout=6) -> str:
    try:
        if url.endswith(".pdf"):
            return ""
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"crisiclarity-bot/1.0"})
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "lxml")
        h = soup.find(["h1", "h2"])
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception as e:
        logger.debug("title fetch failed for %s: %s", url, e)
    return ""

# ---------- main fetch ----------
def fetch_factchecks(query: str) -> List[Dict]:
    """
    Return list of fact-check items:
    {"source": "PIB"|"AltNews"|..., "url": "...", "verdict": "Fake|True|Misleading|Unverified"}
    """
    results = []
    variants = _variants(query)

    # RSS feeds
    for name, feed_url in FEEDS.items():
        try:
            d = feedparser.parse(feed_url)
            for entry in d.entries[:25]:
                title = entry.get("title", "") or ""
                link = entry.get("link", "") or ""
                if not link:
                    continue
                for v in variants:
                    if _similarity(v, title) > 0.32:
                        verdict = _infer_verdict(title)
                        results.append({"source": name, "url": link, "verdict": verdict})
                        break
        except Exception as e:
            logger.warning("Feed %s failed: %s", name, e)

    # PIB page (fact checks index)
    try:
        r = requests.get(PIB_URL, timeout=10, headers={"User-Agent":"crisiclarity-bot/1.0"})
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select("a[href]"):
                title_text = a.get_text(strip=True) or ""
                href = urljoin(PIB_URL, a["href"])
                if not _filter_factcheck_links(href):
                    continue
                for v in variants:
                    if _similarity(v, title_text) > 0.30:
                        # try to get article title if the matched link is an index or redirect
                        actual_title = _read_title_from_url(href) or title_text
                        verdict = _infer_verdict(actual_title)
                        results.append({"source": "PIB", "url": href, "verdict": verdict})
                        break
    except Exception as e:
        logger.warning("PIB fetch failed: %s", e)

    # Deduplicate by url (keep first)
    seen = set()
    dedup = []
    for item in results:
        u = item.get("url")
        if not u:
            continue
        if u not in seen:
            dedup.append(item)
            seen.add(u)

    return dedup
