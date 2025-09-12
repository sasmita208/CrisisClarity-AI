from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.utils.factcard_generator import create_factcard

router = APIRouter()

# Define request schema
class FactCardRequest(BaseModel):
    claim: str
    verdict: str
    confidence: Optional[float] = None
    evidence_links: Optional[List[str]] = []

@router.post("/generate_factcard/")
async def generate_factcard(payload: FactCardRequest):
    factcard = create_factcard(
        claim=payload.claim,
        verdict=payload.verdict,
        confidence=payload.confidence,
        evidence_links=payload.evidence_links
    )
    return factcard
