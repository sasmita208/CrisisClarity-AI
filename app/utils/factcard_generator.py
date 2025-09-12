def create_factcard(claim: str, verdict: str, confidence: float, evidence_links: list[str]):
    conf = f"{round(confidence*100,1)}%" if confidence else "N/A"
    sources = evidence_links[:3] if evidence_links else ["No evidence found"]

    factcard = {
        "title": "FACT CHECK SUMMARY",
        "claim": claim,
        "verdict": verdict,
        "confidence": conf,
        "sources": sources,
        "summary_text": f"Claim: {claim}\nVerdict: {verdict}\nConfidence: {conf}\nSources: {', '.join(sources)}"
    }
    return factcard
