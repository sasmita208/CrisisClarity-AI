from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.text_verifier import verify_text_claim
from app.utils.evidence import gather_evidence

router = APIRouter()

# -------- Request --------
class TextInput(BaseModel):
    text: str

# -------- Response --------
class EvidenceItem(BaseModel):
    source: Optional[str] = None
    url: str
    verdict: Optional[str] = None

class TextResponse(BaseModel):
    claim: str
    verdict: str
    confidence: float
    evidence_links: List[EvidenceItem]

# -------- Route --------
@router.post("/verify_text/", response_model=TextResponse)
def verify_text_endpoint(request: TextInput):
    # get model + evidence
    model_result = verify_text_claim(request.text)
    evidence_result = gather_evidence(request.text)

    evidence_items: List[EvidenceItem] = []

    # Collect fact-checks
    for fc in evidence_result.get("fact_checks", []):
        evidence_items.append(EvidenceItem(
            source=fc.get("source"),
            url=fc.get("url"),
            verdict=fc.get("verdict")
        ))

    # Collect news
    for news in evidence_result.get("news", []):
        evidence_items.append(EvidenceItem(
            source=news.get("source"),
            url=news.get("url"),
            verdict=news.get("verdict")
        ))

    # Collect Google fact-checks
    for gfc in evidence_result.get("google_factcheck", []):
        evidence_items.append(EvidenceItem(
            source=gfc.get("source"),
            url=gfc.get("url"),
            verdict=gfc.get("verdict")
        ))

    # -------- Verdict Override Logic --------
    final_verdict = model_result["verdict"]
    final_confidence = model_result["confidence"]

    if any(ev.verdict and ev.verdict.lower() == "fake" for ev in evidence_items):
        final_verdict = "Fake"
        final_confidence = 1.0
    elif any(ev.verdict and ev.verdict.lower() == "true" for ev in evidence_items):
        final_verdict = "True"
        final_confidence = 1.0

    return TextResponse(
        claim=request.text,
        verdict=final_verdict,
        confidence=final_confidence,
        evidence_links=evidence_items
    )

