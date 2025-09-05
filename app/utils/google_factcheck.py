import logging
import requests
from typing import List, Dict, Iterable
from app.utils.config import settings

logger = logging.getLogger(__name__)
BASE = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

DEFAULT_PUBLISHERS = (
    "altnews.in",
    "boomlive.in",
    "factly.in",
    "indiatoday.in",           
    "aajtak.in",               
    "afp.com",                 
)

def _normalize(data: dict) -> List[Dict]:
    out = []
    for c in data.get("claims", []):
        rv = (c.get("claimReview") or [{}])[0]
        out.append({
            "text": c.get("text"),
            "claimant": c.get("claimant"),
            "publisher": rv.get("publisher", {}).get("name"),
            "site": rv.get("publisher", {}).get("site"),
            "title": rv.get("title"),
            "url": rv.get("url"),
            "rating": rv.get("textualRating"),
            "reviewDate": rv.get("reviewDate"),
            "provider": "GoogleFactCheck",
        })
    return out

def _fetch(query: str, publisher: str | None, page_size: int = 10) -> List[Dict]:
    params = {
        "query": query,
        "pageSize": page_size,
        "key": settings.GOOGLE_FACTCHECK_API_KEY,
    }
    if publisher:
        params["reviewPublisherSiteFilter"] = publisher
    r = requests.get(BASE, params=params, timeout=10)
    r.raise_for_status()
    return _normalize(r.json())

def search_factchecks(
    query: str,
    publishers: Iterable[str] = DEFAULT_PUBLISHERS,
    include_fallback: bool = True
) -> List[Dict]:
    """
    Try several Indian fact-check publishers. If nothing found, optionally try no filter.
    """
    if not settings.GOOGLE_FACTCHECK_API_KEY:
        logger.info("Google Fact Check key missing; skipping.")
        return []

    results: List[Dict] = []
    tried_any = False

    # Try each publisher
    for pub in publishers:
        try:
            tried_any = True
            items = _fetch(query, pub)
            if items:
                logger.info(f"Google Fact Check: {len(items)} items from {pub} for '{query}'")
                results.extend(items)
        except requests.RequestException as e:
            logger.warning(f"Publisher '{pub}' fetch failed: {e}")

    # Fallback: no publisher filter
    if include_fallback and not results:
        try:
            items = _fetch(query, publisher=None)
            if items:
                logger.info(f"Google Fact Check (no filter): {len(items)} items for '{query}'")
                results.extend(items)
        except requests.RequestException as e:
            logger.error(f"Google Fact Check fallback failed: {e}")

    if tried_any and not results:
        logger.info(f"No fact-checks found for '{query}' with given publishers.")
    return results[:10]  # cap results

