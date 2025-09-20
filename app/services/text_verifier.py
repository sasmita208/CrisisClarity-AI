from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from app.utils.news_api import search_news
from app.utils.scraper import fetch_factchecks

MODEL_NAME = "Pulk17/Fake-News-Detection"

# Load model once
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

labels = ["Fake", "Real"]

def verify_text_claim(text: str):
    # ---- Step 1: ML prediction ----
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

    verdict_index = torch.argmax(predictions).item()
    verdict = labels[verdict_index]
    confidence = float(predictions[0][verdict_index])

    evidence_links = []

    # ---- Step 2: News API evidence ----
    try:
        articles = search_news(text) or []
        urls = [a["url"] for a in articles if isinstance(a, dict) and "url" in a]
        evidence_links.extend(urls)
    except Exception as e:
        print(f"[WARN] NewsAPI failed: {e}")

    # ---- Step 3: Fact-check scraper (trusted override) ----
    try:
        factcheck_hits = fetch_factchecks(text) or []
        if factcheck_hits:
            verdict = factcheck_hits[0]["verdict"]  # trusted override
            confidence = 0.99
            evidence_links.extend([hit["url"] for hit in factcheck_hits])
    except Exception as e:
        print(f"[WARN] Scraper failed: {e}")

    # ---- Deduplicate links ----
    evidence_links = list(dict.fromkeys(evidence_links))

    return {
        "verdict": verdict,
        "confidence": confidence,
        "evidence_links": evidence_links
    }
