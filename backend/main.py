"""Naver Blog Auto — FastAPI backend.

Wraps the existing ``core/`` Python modules as REST API endpoints.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so ``import core`` works regardless
# of how / where the server is launched.
# ---------------------------------------------------------------------------
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.routers import (  # noqa: E402
    generate,
    history,
    image,
    keyword,
    reference,
    seo,
    settings,
)

load_dotenv()

app = FastAPI(
    title="Naver Blog Auto API",
    version="1.0.0",
    description="REST API backend for the naver-blog-auto project.",
)

# -- CORS (allow everything for local development) -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers ---------------------------------------------------------------
app.include_router(settings.router)
app.include_router(reference.router)
app.include_router(keyword.router)
app.include_router(generate.router)
app.include_router(image.router)
app.include_router(seo.router)
app.include_router(history.router)


# -- Health check -----------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
