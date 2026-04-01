"""Image router — upload / resize / vision analysis."""

import base64

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from core.image_utils import analyze_image, image_to_base64, resize_image
from core.llm_client import LLMClient

router = APIRouter(prefix="/api/image", tags=["image"])


# -- Schemas ----------------------------------------------------------------

class AnalyzeImageRequest(BaseModel):
    image_base64: str
    target_keyword: str = ""
    model: str = "gemma3:12b"


# -- Endpoints --------------------------------------------------------------

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image, resize it to blog-optimal width, and return base64."""
    raw_bytes = await file.read()
    try:
        resized = resize_image(raw_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "filename": file.filename,
        "original_size": len(raw_bytes),
        "resized_size": len(resized),
        "base64": image_to_base64(resized),
    }


@router.post("/analyze")
async def analyze(req: AnalyzeImageRequest):
    """Run vision analysis on an image to generate a blog-friendly description."""
    try:
        image_bytes = base64.b64decode(req.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    llm = LLMClient(model=req.model)
    description = analyze_image(llm, image_bytes, req.target_keyword)
    return {"description": description}
