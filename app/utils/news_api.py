import logging
import requests
from typing import List, Dict, Optional, Iterable
from app.utils.config import settings

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"
GNEWS_URL   = "https://gnews.io/api/v4/search"

# Common Indian outlets to bias relevance (works only for NewsAPI /v2/everything).
INDIA_DOMAINS_DEFAULT = [
    "thehindu.com",
    "indianexpress.com",
    "timesofindia.indiatimes.com",
    "ndtv.com",
    "hindustantimes.com",
    "theprint.in",
    "scroll.in",
    "livemint.com",
    "aajtak.in",
    "indiatoday.in",
    "moneycontrol.com",
    "business-standard.com",
]

def _normalize(items: List[dict], provider: str, limit: int = 8) -> List[Dict]:
    out: List[Dict] = []
    seen_urls = set()
    seen_titles = set()

    for a in items:
        url = a.get("url")
        title = a.get("title") or ""

        # de-dup by url/title
        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if provider == "NewsAPI":
            source_name = (a.get("source", {}) or {}).get("name")
            published = a.get("publishedAt")
            desc = a.get("description")
        else:  # GNews
            source_name = (a.get("source", {}) or {}).get("name") or a.get("source")
            published = a.get("publishedAt")
            desc = a.get("description")

        out.append({
            "source": source_name,
            "title": title,
            "description": desc,
            "url": url,
            "publishedAt": published,
            "provider": provider,
        })
        if url: seen_urls.add(url)
        if title: seen_titles.add(title)

        if len(out) >= limit:
            break

    return out

def search_news(
    query: str,
    lang: str = "en",
    country: str = "in",  # used by GNews only
    include_domains: Optional[Iterable[str]] = None,
    page_size_newsapi: int = 25,
    gnews_max: int = 15,
) -> List[Dict]:
    """
    Search evidence articles with NewsAPI (preferred) and fall back to GNews.
    - Biases toward Indian outlets via `include_domains` (NewsAPI only).
    - Returns a small, normalized list.
    """
    # ----- NewsAPI (preferred) -----
    if settings.NEWS_API_KEY:
        try:
            params = {
                "q": query,
                "language": lang,
                "sortBy": "relevancy",         # or 'publishedAt' if you prefer latest
                "pageSize": page_size_newsapi, # cap server-side a bit
                "apiKey": settings.NEWS_API_KEY,
            }

            # Domains filter (India bias)
            domains = list(include_domains) if include_domains else INDIA_DOMAINS_DEFAULT
            if domains:
                params["domains"] = ",".join(domains)

            r = requests.get(NEWSAPI_URL, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()

            # NewsAPI wraps results in {"status":"ok","articles":[...]}
            articles = data.get("articles", []) if data.get("status") == "ok" else []
            if articles:
                logger.info(f"NewsAPI: {len(articles)} raw hits for '{query}'")
                return _normalize(articles, "NewsAPI", limit=8)
            else:
                logger.info(f"NewsAPI: 0 hits for '{query}' (domains bias applied)")
        except Exception as e:
            logger.warning(f"NewsAPI error → fallback to GNews: {e}")

    # ----- GNews (fallback) -----
    #if settings.GNEWS_API_KEY:
     #   try:
      #      params = {
       #         "q": query,
        #        "lang": lang,
         #       "country": country, # 'in' biases to India
          #      "token": settings.GNEWS_API_KEY,
           #     "max": gnews_max,
                # "in": "title,description,content",  # uncomment to restrict fields GNews searches
                # "from": "2025-08-01",              # optionally restrict date window
            #}
            #r = requests.get(GNEWS_URL, params=params, timeout=12)
            #r.raise_for_status()
           # data = r.json()
            #articles = data.get("articles", [])
          #  if articles:
           #     logger.info(f"GNews: {len(articles)} raw hits for '{query}'")
     #           return _normalize(articles, "GNews", limit=8)
    #        else:
   #             logger.info(f"GNews: 0 hits for '{query}'")
  #      except Exception as e:
 #           logger.error(f"GNews error: {e}")
#
   # logger.info("No news/evidence found or no API key set.")
    #return []

