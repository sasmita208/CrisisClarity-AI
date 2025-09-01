from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/verify_link", tags=["Link Verification"])

class LinkRequest(BaseModel):
    url: str

@router.post("/")
async def verify_link(payload: LinkRequest):
    return {"url": payload.url, "status": "stub - to be implemented"}
