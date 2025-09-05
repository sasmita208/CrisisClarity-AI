import logging
from typing import Dict, List
from app.utils.scraper import check_fact_sites
from app.utils.news_api import search_news
from app.utils.google_factcheck import search_factchecks

logger = logging.getLogger(__name__)

def gather_evidence(query: str) -> Dict[str, List[dict]]:
    """
    Gather evidence from multiple sources:
    - PIB/AltNews scraper
    - NewsAPI / GNews
    - Google Fact Check (multi-publisher + fallback)
    """
    logger.info(f"Gathering evidence for: {query}")
    return {
        "fact_checks": check_fact_sites(query),        # PIB + AltNews scraper
        "news": search_news(query),                    # NewsAPI / GNews
        "google_factcheck": search_factchecks(query),  # Google Fact Check (multi-pub + fallback)
    }

if __name__ == "__main__":
    from app.utils.logging_config import setup_logging
    setup_logging()
    result = gather_evidence("old image shared as recent")
    print(result)

