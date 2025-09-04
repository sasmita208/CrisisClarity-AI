from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/verify_text", tags=["Text Verification"])

class TextRequest(BaseModel):
    claim: str

@router.post("/")
async def verify_text(payload: TextRequest):
    """
    Stub endpoint for text claim verification.
    Currently just echoes back the claim with placeholder status.
    """
    return {
        "claim": payload.claim,
        "status": "pending_verification"
    }
