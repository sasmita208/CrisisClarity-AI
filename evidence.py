# app/utils/evidence.py
import logging
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# local imports (these should exist in your repo)
from app.utils.scraper import fetch_factchecks
from app.utils.news_api import search_news
from app.utils.google_factcheck import search_factchecks

logger = logging.getLogger(__name__)


# ---------------- helpers ----------------
def _similarity(a: str, b: str) -> float:
    """Fuzzy similarity between two strings (0..1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_fact_entry(entry: dict, default_source: Optional[str] = None) -> dict:
    """
    Ensure each evidence item has consistent keys:
      source, url, title, snippet, verdict
    Accepts entries from fetch_factchecks (PIB/AltNews), which may have
    different keys.
    """
    e = {
        "source": entry.get("source") or default_source or entry.get("publisher") or entry.get("site"),
        "url": entry.get("url") or entry.get("link") or "",
        "title": entry.get("title") or entry.get("headline") or "",
        "snippet": entry.get("excerpt") or entry.get("text") or entry.get("description") or "",
        "verdict": entry.get("verdict") or entry.get("rating") or entry.get("result") or None,
    }
    # normalize verdict strings (if present)
    if e["verdict"]:
        v = (e["verdict"] or "").strip()
        vlow = v.lower()
        if "false" in vlow or "fake" in vlow or "debunk" in vlow or "not true" in vlow:
            e["verdict"] = "Fake"
        elif "true" in vlow or "genuine" in vlow or "confirmed" in vlow:
            e["verdict"] = "True"
        elif "misleading" in vlow:
            e["verdict"] = "Misleading"
        else:
            # Keep text if unknown, but mark as Unverified to make code consistent
            e["verdict"] = v if v else None
    return e


# ---------------- gather evidence ----------------
def gather_evidence(query: str) -> Dict[str, List[dict]]:
    """
    Gather evidence from:
      - fetch_factchecks (PIB, AltNews, BOOM, Factly)
      - search_news (NewsAPI/GNews)
      - search_factchecks (Google Fact Check)
    Returns normalized lists under keys:
      - fact_checks: list of {source, url, title, snippet, verdict}
      - news: list of {source, url, title, snippet, verdict=None}
      - google_factcheck: list of {source, url, title, snippet, verdict}
    """
    logger.info("Gathering evidence for: %s", query)

    fact_checks = []
    news = []
    google_fc = []

    # 1) fact-check scrapers (PIB/AltNews/BOOM/Factly)
    try:
        raw_fc = fetch_factchecks(query) or []
        for r in raw_fc:
            try:
                normalized = _normalize_fact_entry(r)
                # if there's no verdict in scraper result, set Unverified for clarity
                if not normalized.get("verdict"):
                    normalized["verdict"] = "Unverified"
                fact_checks.append(normalized)
            except Exception:
                logger.exception("Failed to normalize factcheck entry: %s", r)
    except Exception as e:
        logger.exception("fetch_factchecks failed: %s", e)

    # 2) news articles (search_news) - keep snippet/title so we can match
    try:
        raw_news = search_news(query) or []
        for r in raw_news:
            try:
                n = {
                    "source": (r.get("source") and r.get("source").get("name")) or r.get("source") or r.get("publisher") or "news",
                    "url": r.get("url") or r.get("link") or "",
                    "title": r.get("title") or r.get("headline") or "",
                    "snippet": r.get("description") or r.get("content") or "",
                    "verdict": None,
                }
                news.append(n)
            except Exception:
                logger.exception("Failed to normalize news entry: %s", r)
    except Exception as e:
        logger.exception("search_news failed: %s", e)

    # 3) Google Fact Check (structured)
    try:
        raw_gfc = search_factchecks(query) or []
        for r in raw_gfc:
            try:
                g = {
                    "source": (r.get("publisher") or r.get("site") or "GoogleFactCheck"),
                    "url": r.get("url") or "",
                    "title": r.get("title") or "",
                    "snippet": r.get("text") or r.get("claimant") or "",
                    "verdict": None,
                }
                # rating field might be 'rating' or 'claimReview' etc.
                rating = (r.get("rating") or r.get("claimReview") or "")
                if rating:
                    # rating could be "False" or "True" etc. normalize
                    rlow = str(rating).lower()
                    if "false" in rlow:
                        g["verdict"] = "Fake"
                    elif "true" in rlow or "correct" in rlow:
                        g["verdict"] = "True"
                    else:
                        g["verdict"] = r.get("rating")
                else:
                    # some providers put 'reviewRating' or other fields
                    g["verdict"] = r.get("rating") or r.get("reviewRating") or None
                if not g["verdict"]:
                    g["verdict"] = "Unverified"
                google_fc.append(g)
            except Exception:
                logger.exception("Failed to normalize google factcheck entry: %s", r)
    except Exception as e:
        logger.exception("search_factchecks failed: %s", e)

    return {"fact_checks": fact_checks, "news": news, "google_factcheck": google_fc}


# ---------------- matching ----------------
def match_claim_against_evidence(claim: str, evidence: dict) -> dict:
    """
    Tries to match the claim against collected evidence.
    Priority:
      1) Google Fact Check (explicit ratings)
      2) Fact-check scrapers (PIB/AltNews/BOOM/Factly)
      3) News (lower weight)
    Returns:
       {
         "verdict": "verified_fake" | "verified_true" | "unverified" | "unknown",
         "verified_by": <publisher/source> or None,
         "url": <evidence URL> or None,
         "evidence_score": 0.0..1.0,
         "matched_evidence": [ ... evidence items that influenced decision ... ]
       }
    """
    claim_text = (claim or "").strip()
    claim_lower = claim_text.lower()

    # helper to produce result
    def _result(verdict: str, source: Optional[str], url: Optional[str], score: float, matched: List[dict]):
        return {
            "verdict": verdict,
            "verified_by": source,
            "url": url,
            "evidence_score": float(score),
            "matched_evidence": matched,
        }

    matched_items: List[dict] = []

    # 1) Google Fact Check (highest cred)
    for g in evidence.get("google_factcheck", []):
        text = (" ".join([g.get("title", ""), g.get("snippet", "")]) or "").lower()
        sim = max(_similarity(claim_lower, g.get("title", "")), _similarity(claim_lower, g.get("snippet", "")))

        # match by substring or reasonably high similarity
        if claim_lower in text or sim > 0.5:
            matched_items.append({**g, "similarity": sim, "source_weight": 1.0})
            v = (g.get("verdict") or "").lower()
            if "fake" in v or "false" in v or "debunk" in v:
                return _result("verified_fake", g.get("source"), g.get("url"), 0.95 + 0.04 * sim, matched_items)
            if "true" in v or "correct" in v or "confirmed" in v:
                return _result("verified_true", g.get("source"), g.get("url"), 0.95 + 0.04 * sim, matched_items)
            # if google says 'Unverified' include it but continue to next sources

    # 2) fact-check scrapers
    for fc in evidence.get("fact_checks", []):
        combined = (" ".join([fc.get("title", ""), fc.get("snippet", ""), fc.get("url", "")]) or "").lower()
        sim = max(_similarity(claim_lower, fc.get("title", "")), _similarity(claim_lower, fc.get("snippet", "")))
        # String-level match (loose) OR fuzzy similarity
        if (claim_lower in combined) or sim > 0.45:
            matched_items.append({**fc, "similarity": sim, "source_weight": 0.9})
            v = (fc.get("verdict") or "").lower()
            if "fake" in v or "false" in v or "debunk" in v:
                score = 0.85 + 0.1 * sim
                return _result("verified_fake", fc.get("source"), fc.get("url"), min(0.99, score), matched_items)
            if "true" in v or "confirmed" in v or "genuine" in v:
                score = 0.85 + 0.1 * sim
                return _result("verified_true", fc.get("source"), fc.get("url"), min(0.99, score), matched_items)

    # 3) news (lower trust; we only mark if multiple corroborating news items or very high similarity)
    news_matches = []
    for n in evidence.get("news", []):
        sim = max(_similarity(claim_lower, n.get("title", "")), _similarity(claim_lower, n.get("snippet", "")))
        if sim > 0.6 or claim_lower in (n.get("title", "") + " " + n.get("snippet", "")).lower():
            news_matches.append({**n, "similarity": sim, "source_weight": 0.5})

    if news_matches:
        # if multiple independent news sources match, we can mark likely true, but keep evidence_score modest
        unique_sources = {m["source"].lower() for m in news_matches if m.get("source")}
        avg_sim = sum(m["similarity"] for m in news_matches) / max(1, len(news_matches))
        matched_items.extend(news_matches)
        if len(unique_sources) >= 2 and avg_sim > 0.6:
            score = 0.6 + 0.2 * avg_sim
            return _result("verified_true", ", ".join(unique_sources), news_matches[0].get("url"), min(0.95, score), matched_items)
        # otherwise mark unverified but provide evidence
        return _result("unverified", None, news_matches[0].get("url"), 0.4 + 0.3 * avg_sim, matched_items)

    # nothing matched: return unknown
    return _result("unknown", None, None, 0.0, matched_items)


# ---------------- quick CLI test ----------------
if __name__ == "__main__":
    from app.utils.logging_config import setup_logging
    import sys
    setup_logging()
    q = "old image shared as recent"
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    ev = gather_evidence(q)
    print("EVIDENCE:", {k: len(v) for k, v in ev.items()})
    m = match_claim_against_evidence(q, ev)
    print("MATCH:", m)



