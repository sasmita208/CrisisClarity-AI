# app/routers/verify_text.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.text_verifier import verify_text_claim

router = APIRouter()

class TextClaimRequest(BaseModel):
    claim: str

@router.post("/verify_text/")
def verify_text(request: TextClaimRequest):
    result = verify_text_claim(request.claim)
    return {
        "claim": request.claim,
        **result
    }
