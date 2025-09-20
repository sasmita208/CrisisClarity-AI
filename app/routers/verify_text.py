from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.text_verifier import verify_text_claim

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
    result = verify_text_claim(request.text)

    # normalize evidence links into {source, url, verdict}
    evidence_items: List[EvidenceItem] = []
    for link in result.get("evidence_links", []):
        if isinstance(link, dict):
            evidence_items.append(
                EvidenceItem(
                    source=link.get("source"),
                    url=link.get("url"),
                    verdict=link.get("verdict")
                )
            )
        else:  # legacy string-only links
            evidence_items.append(EvidenceItem(url=link))

    # -------- Verdict Override Logic --------
    final_verdict = result["verdict"]
    final_confidence = result["confidence"]

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
