"""Settings router — Ollama models, app config, Naver credential test."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.config import load_config, save_config
from core.keyword import validate_naver_credentials
from core.llm_client import LLMClient

router = APIRouter(prefix="/api/settings", tags=["settings"])


# -- Schemas ----------------------------------------------------------------

class NaverCredentials(BaseModel):
    client_id: str
    client_secret: str


# -- Endpoints --------------------------------------------------------------

@router.get("/models")
async def list_models():
    """Return the list of locally available Ollama models."""
    try:
        client = LLMClient()
        models = client.list_models()
        return {"models": models}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/config")
async def get_config():
    """Load the current application config."""
    return load_config()


@router.put("/config")
async def put_config(config: dict):
    """Overwrite the application config."""
    save_config(config)
    return {"ok": True}


@router.post("/test-naver")
async def test_naver(creds: NaverCredentials):
    """Validate Naver Search API credentials."""
    success, message = validate_naver_credentials(creds.client_id, creds.client_secret)
    return {"success": success, "message": message}
