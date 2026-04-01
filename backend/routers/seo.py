"""SEO router — validate drafts and list profiles."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.seo_validator import PROFILE_LABELS, SEO_PROFILES, validate_seo

router = APIRouter(prefix="/api/seo", tags=["seo"])


# -- Schemas ----------------------------------------------------------------

class ValidateRequest(BaseModel):
    draft: dict
    target_keyword: str
    image_count: int = 0
    profile: str = "balanced"
    custom_weights: dict[str, float] | None = None


# -- Endpoints --------------------------------------------------------------

@router.post("/validate")
async def seo_validate(req: ValidateRequest):
    """Run full SEO validation on a draft."""
    result = validate_seo(
        draft=req.draft,
        target_keyword=req.target_keyword,
        image_count=req.image_count,
        profile=req.profile,
        custom_weights=req.custom_weights,
    )
    return result


@router.get("/profiles")
async def seo_profiles():
    """Return available SEO profiles and their weight configs."""
    return {
        "profiles": SEO_PROFILES,
        "labels": PROFILE_LABELS,
    }
