"""Reference router — crawl / save / load blog reference posts."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.reference import crawl_reference, load_references, save_references

router = APIRouter(prefix="/api/reference", tags=["reference"])


# -- Schemas ----------------------------------------------------------------

class CrawlRequest(BaseModel):
    url: str


# -- Endpoints --------------------------------------------------------------

@router.get("/")
async def get_references():
    """Load saved reference posts."""
    return {"references": load_references()}


@router.post("/crawl")
async def crawl(req: CrawlRequest):
    """Crawl a Naver blog post URL and return structured data."""
    try:
        result = crawl_reference(req.url)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/")
async def save(references: list[dict]):
    """Save a list of reference posts."""
    save_references(references)
    return {"ok": True}
