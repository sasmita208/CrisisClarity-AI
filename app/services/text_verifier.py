import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 🔹 Import news + fact-check helpers
from app.utils.news_api import search_news
from app.utils.scraper import fetch_factchecks

MODEL_NAME = "Pulk17/Fake-News-Detection"

# Load model + tokenizer once at startup
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

labels = ["Fake", "Real"]

def verify_text_claim(text: str):
    """
    Runs fake news detection on input text.
    Returns verdict (Fake/Real), confidence score, and evidence links.
    """
    # ---- Model prediction ----
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

    verdict_index = torch.argmax(predictions).item()
    verdict = labels[verdict_index]
    confidence = float(predictions[0][verdict_index])

    # ---- Evidence gathering ----
    evidence_links = []

    # News API articles
    try:
        articles = search_news(text) or []
        # Extract only URLs if dicts
        urls = [a["url"] for a in articles if isinstance(a, dict) and "url" in a]
        evidence_links.extend(urls)
    except Exception as e:
        print(f"[WARN] NewsAPI failed: {e}")

    # Fact-check scrapers (PIB / AltNews)
    try:
        factcheck_urls = fetch_factchecks(text) or []
        evidence_links.extend(factcheck_urls)
    except Exception as e:
        print(f"[WARN] Scraper failed: {e}")

    return {
        "verdict": verdict,
        "confidence": confidence,
        "evidence_links": evidence_links
    }
