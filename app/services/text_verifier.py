# app/services/text_verifier.py

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_NAME = "Pulk17/Fake-News-Detection"

# Load model + tokenizer at startup (so it doesn't reload on every request)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

labels = ["Fake", "Real"]

def verify_text_claim(text: str):
    """
    Runs fake news detection on input text.
    Returns verdict (Fake/Real), confidence score.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

    verdict_index = torch.argmax(predictions).item()
    verdict = labels[verdict_index]
    confidence = float(predictions[0][verdict_index])

    return {
        "verdict": verdict,
        "confidence": confidence,
        "evidence_links": []  # placeholder -> will fill with NewsAPI + scrapers later
    }
if __name__ == "__main__":
    claim = "The government has announced free electricity for all citizens."
    result = verify_text_claim(claim)
    print(result)
