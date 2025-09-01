from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.domain_utils import extract_domain

router = APIRouter(prefix="/verify_link", tags=["Link Verification"])

class LinkRequest(BaseModel):
    url: str

@router.post("/")
async def verify_link(payload: LinkRequest):
    domain = extract_domain(payload.url)
    return {
        "url": payload.url,
        "domain": domain,
        "status": "parsed successfully"
    }
