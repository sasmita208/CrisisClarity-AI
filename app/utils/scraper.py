import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin

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

    # drop common location tokens (often absent in fact-check titles)
    for loc in ("delhi", "mumbai", "bengaluru", "india", "indian"):
        if loc in words:
            variants.add(" ".join([w for w in words if w != loc]).strip())

    # crisis-related expansions
    if "flood" in low:
        variants |= {"flood warning", "flood alert fake", "old flood photo", "old image shared as recent flood"}
    if any(tok in low for tok in ("order", "advisory", "circular", "govt", "government")):
        variants |= {"fake government order", "fake advisory", "fake circular"}

    return [v for v in sorted(variants) if v]

def _any_variant_in(text: str, query: str) -> bool:
    t = (text or "").lower()
    return any(v in t for v in _variants(query))

# -------- PIB --------
def fetch_pib_factchecks(query: str):
    """Scrape PIB fact-check page and match by query variants."""
    results = []
    try:
        r = requests.get(PIB_URL, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        candidate_blocks = []
        candidate_blocks += soup.select("div.content-area")
        candidate_blocks += soup.select("div#content")

        seen_urls = set()
        for block in candidate_blocks:
            text = block.get_text(separator=" ", strip=True)
            if not text:
                continue
            if _any_variant_in(text, query):
                a = block.find("a")
                link = urljoin(PIB_URL, a["href"]) if a and a.has_attr("href") else PIB_URL
                if link not in seen_urls:
                    seen_urls.add(link)
                    results.append({
                        "source": "PIB",
                        "title": (a.get_text(strip=True) if a else "PIB Fact Check"),
                        "excerpt": text[:220],
                        "url": link
                    })
        return results
    except Exception as e:
        logger.error(f"PIB Scraper error: {e}")
        return []

# -------- RSS (AltNews / BOOM / Factly) --------
def fetch_rss_factchecks(query: str):
    """Check Indian fact-checker RSS feeds for matches."""
    results = []
    try:
        for name, feed_url in FEEDS.items():
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:50]:
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", "") or ""
                if _any_variant_in(title, query) or _any_variant_in(summary, query):
                    results.append({
                        "source": name,
                        "title": title,
                        "url": entry.link
                    })
        return results
    except Exception as e:
        logger.error(f"RSS Scraper error: {e}")
        return []

# -------- RSS Fallback (latest posts) --------
def _latest_from_feeds(limit: int = 10):
    """If no query match, return the latest items from all feeds."""
    items = []
    try:
        for name, feed_url in FEEDS.items():
            feed = feedparser.parse(feed_url)
            for e in feed.entries[:limit]:
                items.append({
                    "source": name,
                    "title": getattr(e, "title", ""),
                    "url": e.link
                })
        return items[:limit]
    except Exception as e:
        logger.error(f"Latest RSS fetch error: {e}")
        return []

# -------- Public API --------
def check_fact_sites(query: str):
    """Unified function combining PIB + Indian RSS feeds, with fallback."""
    results = []
    try:
        results.extend(fetch_pib_factchecks(query))
        results.extend(fetch_rss_factchecks(query))

        # fallback if no results at all
        if not results:
            logger.info(f"No direct matches for '{query}', falling back to latest RSS fact-checks.")
            results = _latest_from_feeds(limit=10)

        # deduplicate by URL
        unique, seen = [], set()
        for item in results:
            u = item.get("url")
            if u and u not in seen:
                seen.add(u)
                unique.append(item)
        return unique
    except Exception as e:
        logger.error(f"check_fact_sites error: {e}")
        return []

if __name__ == "__main__":
    from app.utils.logging_config import setup_logging
    setup_logging()
    q = "flood warning delhi"
    print(check_fact_sites(q))

