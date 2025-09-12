import logging
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# ------------------ Sources ------------------
PIB_URL = "https://pib.gov.in/factcheck.aspx"
FEEDS = {
    "AltNews": "https://www.altnews.in/feed/",
    "BOOM": "https://www.boomlive.in/rss",
    "Factly": "https://factly.in/feed/",
}

# ------------------ Helpers ------------------
def _variants(q: str) -> list[str]:
    """
    Generate simple query variants to improve matching.
    Example: "NASA Moon Mission" -> ["nasa moon mission", "nasa", "moon mission"]
    """
    base = (q or "").strip()
    low = base.lower()
    words = low.split()

    variants = {low}

    # drop common stopwords to allow partial matches
    stops = {"the", "a", "an", "in", "on", "of", "for"}
    filtered = [w for w in words if w not in stops]
    if filtered:
        variants.add(" ".join(filtered))

    # add single keywords for broader match
    variants.update(filtered)

    return variants

# ------------------ Main Function ------------------
def fetch_factchecks(query: str, limit: int = 5):
    """
    Search PIB + AltNews/BOOM/Factly feeds for fact-checks related to query.
    Returns a list of dicts: {title, url, source}.
    """
    results = []
    variants = _variants(query)

    # --- PIB Fact Check page (HTML scraping) ---
    try:
        resp = requests.get(PIB_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for a in soup.select("a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if not href or not title:
                continue

            for v in variants:
                if v in title.lower():
                    results.append({
                        "title": title,
                        "url": urljoin(PIB_URL, href),
                        "source": "PIB"
                    })
                    break
        logger.info(f"PIB hits: {len(results)}")
    except Exception as e:
        logger.warning(f"PIB scrape error: {e}")

    # --- RSS feeds (AltNews, BOOM, Factly) ---
    for name, feed_url in FEEDS.items():
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:limit]:
                title = entry.title
                link = entry.link
                desc = getattr(entry, "summary", "")

                for v in variants:
                    if v in title.lower() or v in desc.lower():
                        results.append({
                            "title": title,
                            "url": link,
                            "source": name
                        })
                        break
        except Exception as e:
            logger.warning(f"{name} RSS error: {e}")

    return results[:limit]
