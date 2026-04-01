"""Generate router — SSE streaming draft / revise / SEO-optimize."""

from typing import Generator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.generator import (
    generate_draft_stream,
    revise_draft_stream,
    seo_optimize_draft_stream,
)
from core.llm_client import LLMClient
from core.reference import load_references

router = APIRouter(prefix="/api/generate", tags=["generate"])


# -- Helpers ----------------------------------------------------------------

def _sse_generator(gen: Generator[str, None, None]):
    """Wrap a synchronous token generator as SSE ``data:`` frames."""
    try:
        for chunk in gen:
            # Escape newlines inside data frames
            escaped = chunk.replace("\n", "\ndata: ")
            yield f"data: {escaped}\n\n"
    except Exception as exc:
        yield f"data: [ERROR] {exc}\n\n"
    yield "data: [DONE]\n\n"


# -- Schemas ----------------------------------------------------------------

class DraftRequest(BaseModel):
    target_keyword: str
    image_descriptions: list[str] = []
    model: str = "gemma3:12b"


class ReviseRequest(BaseModel):
    original: dict
    instruction: str
    model: str = "gemma3:12b"


class OptimizeRequest(BaseModel):
    original: dict
    seo_feedback: str
    target_keyword: str
    strategy: str = "balanced"
    model: str = "gemma3:12b"


# -- Endpoints --------------------------------------------------------------

@router.post("/draft")
async def draft(req: DraftRequest):
    """Generate a blog draft (SSE stream)."""
    llm = LLMClient(model=req.model)
    references = load_references()
    stream = generate_draft_stream(
        llm_client=llm,
        target_keyword=req.target_keyword,
        image_descriptions=req.image_descriptions,
        reference_posts=references,
    )
    return StreamingResponse(_sse_generator(stream), media_type="text/event-stream")


@router.post("/revise")
async def revise(req: ReviseRequest):
    """Revise an existing draft (SSE stream)."""
    llm = LLMClient(model=req.model)
    references = load_references()
    stream = revise_draft_stream(
        llm_client=llm,
        original=req.original,
        instruction=req.instruction,
        reference_posts=references,
    )
    return StreamingResponse(_sse_generator(stream), media_type="text/event-stream")


@router.post("/optimize")
async def optimize(req: OptimizeRequest):
    """SEO-optimize an existing draft (SSE stream)."""
    llm = LLMClient(model=req.model)
    references = load_references()
    stream = seo_optimize_draft_stream(
        llm_client=llm,
        original=req.original,
        seo_feedback=req.seo_feedback,
        target_keyword=req.target_keyword,
        reference_posts=references,
        strategy=req.strategy,
    )
    return StreamingResponse(_sse_generator(stream), media_type="text/event-stream")
