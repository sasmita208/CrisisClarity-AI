# app/routers/verify_text.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.text_verifier import verify_text_claim

router = APIRouter()

# -------- Request --------
class TextClaimRequest(BaseModel):
    claim: str

# -------- Response --------
class EvidenceItem(BaseModel):
    source: Optional[str] = None
    url: str

class TextResponse(BaseModel):
    claim: str
    verdict: str
    confidence: float
    evidence_links: List[EvidenceItem]

# -------- Route --------
@router.post("/verify_text/", response_model=TextResponse)
def verify_text(request: TextClaimRequest):
    result = verify_text_claim(request.claim)

    # normalize evidence links into {source, url}
    evidence_items = []
    for link in result.get("evidence_links", []):
        if isinstance(link, dict):
            evidence_items.append(EvidenceItem(**link))
        else:
            evidence_items.append(EvidenceItem(url=link))

    return TextResponse(
        claim=request.claim,
        verdict=result["verdict"],
        confidence=result["confidence"],
        evidence_links=evidence_items
    )

# this code also has issues
'''
# app/routers/verify_text.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.text_verifier import verify_text_claim

router = APIRouter()

# -------- Request --------
class TextClaimRequest(BaseModel):
    claim: str

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
def verify_text(request: TextClaimRequest):
    result = verify_text_claim(request.claim)

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

    # If any evidence explicitly says "Fake", override immediately
    if any(ev.verdict and ev.verdict.lower() == "fake" for ev in evidence_items):
        final_verdict = "Fake"
        final_confidence = 1.0
    elif any(ev.verdict and ev.verdict.lower() == "true" for ev in evidence_items):
        final_verdict = "True"
        final_confidence = 1.0

    return TextResponse(
        claim=request.claim,
        verdict=final_verdict,
        confidence=final_confidence,
        evidence_links=evidence_items
    )
'''