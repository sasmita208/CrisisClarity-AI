'''# app/routers/verify_link.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.services.link_verifier import analyze_url

router = APIRouter()

# Request model
class LinkRequest(BaseModel):
    url: str  # free-form to allow http/https/internal URLs

# Response model
class LinkResponse(BaseModel):
    url: str
    domain: str
    status: str
    domain_age_days: Optional[int]
    reasons: List[str]
    trusted: bool

@router.post("/verify_link/", response_model=LinkResponse)
def verify_link(req: LinkRequest):
    return analyze_url(req.url)
'''
# app/routers/verify_link.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.link_verifier import analyze_url

router = APIRouter()

# Request model
class LinkRequest(BaseModel):
    url: str  # free-form to allow http/https/internal URLs

# Response model
class LinkResponse(BaseModel):
    url: str
    domain: str
    status: str
    domain_age_days: Optional[int]
    reasons: List[str]
    trusted: bool
    urlscan: Optional[Dict[str, Any]] = None  # integration with UrlScan.io
    dns: Optional[Dict[str, Any]] = None      # fallback DNS info

@router.post("/verify_link/", response_model=LinkResponse)
def verify_link(req: LinkRequest):
    try:
        result = analyze_url(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
