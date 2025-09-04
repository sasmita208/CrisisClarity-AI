import requests
from bs4 import BeautifulSoup
import feedparser
import logging

logger = logging.getLogger(__name__)

PIB_URL = "https://pib.gov.in/factcheck.aspx"
ALTNEWS_FEED = "https://www.altnews.in/feed/"

def fetch_pib_factchecks(query: str):
    try:
        r = requests.get(PIB_URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        articles = soup.find_all("div", class_="content-area")
        results = []

        for art in articles:
            text = art.get_text().strip()
            if query.lower() in text.lower():
                link = art.find("a")["href"] if art.find("a") else PIB_URL
                results.append({"source": "PIB", "excerpt": text[:200], "url": link})

        return results
    except Exception as e:
        logger.error(f"PIB Scraper error: {e}")
        return []

def fetch_altnews_factchecks(query: str):
    feed = feedparser.parse(ALTNEWS_FEED)
    results = []
    for entry in feed.entries:
        if query.lower() in entry.title.lower() or query.lower() in entry.summary.lower():
            results.append({
                "source": "AltNews",
                "title": entry.title,
                "url": entry.link
            })
    return results

def check_fact_sites(query: str):
    results = []
    results.extend(fetch_pib_factchecks(query))
    results.extend(fetch_altnews_factchecks(query))
    return results
if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging()

    results = check_fact_sites("Modi")
    print(results)
