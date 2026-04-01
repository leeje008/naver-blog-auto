"""Keyword router — keyword analysis, top-post analysis, history."""

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.keyword import KeywordEngine
from core.keyword_history import KeywordHistoryManager
from core.llm_client import LLMClient

router = APIRouter(prefix="/api/keyword", tags=["keyword"])


# -- Schemas ----------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    seed: str
    naver_client_id: str = ""
    naver_client_secret: str = ""
    model: str = "gemma3:12b"


class TopPostsRequest(BaseModel):
    keyword: str
    naver_client_id: str = ""
    naver_client_secret: str = ""


# -- Endpoints --------------------------------------------------------------

@router.post("/analyze")
async def analyze_keywords(req: AnalyzeRequest):
    """Full keyword analysis (slow — 30-60 s). Runs in a thread pool."""
    try:
        llm = LLMClient(model=req.model)
        engine = KeywordEngine(llm, req.naver_client_id, req.naver_client_secret)
        results = await asyncio.to_thread(engine.analyze, req.seed)
        return {"seed": req.seed, "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/top-posts")
async def top_posts(req: TopPostsRequest):
    """Analyze top blog posts for a given keyword."""
    try:
        llm = LLMClient()
        engine = KeywordEngine(llm, req.naver_client_id, req.naver_client_secret)
        result = engine.analyze_top_posts(req.keyword)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history")
async def keyword_history():
    """Load all keyword analysis history."""
    mgr = KeywordHistoryManager()
    return {"history": mgr.load_all()}
