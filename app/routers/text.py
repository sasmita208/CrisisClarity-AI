from fastapi import APIRouter
from pydantic import BaseModel
from app.services.text_verifier import verify_text_claim

router = APIRouter()

class TextRequest(BaseModel):
    claim: str

@router.post("/verify_text")
async def verify_text(request: TextRequest):
    result = verify_text_claim(request.claim)
    return result
