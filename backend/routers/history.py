"""History router — list / delete / export keyword analysis history."""

import csv
import io
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.keyword_history import HISTORY_DIR, KeywordHistoryManager

router = APIRouter(prefix="/api/history", tags=["history"])


# -- Endpoints --------------------------------------------------------------

@router.get("/")
async def list_history():
    """List all keyword-analysis history files with metadata."""
    mgr = KeywordHistoryManager()
    items = mgr.load_all()
    summaries = []
    for item in items:
        summaries.append({
            "filename": item.get("_filename", ""),
            "timestamp": item.get("timestamp", ""),
            "seed": item.get("seed", ""),
            "selected_keyword": item.get("selected_keyword"),
            "used_for_post": item.get("used_for_post", False),
            "result_count": len(item.get("results", [])),
        })
    return {"history": summaries}


@router.delete("/{filename}")
async def delete_history(filename: str):
    """Delete a specific history file."""
    # Sanitize: only allow .json files within the history directory
    if not filename.endswith(".json") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = HISTORY_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="History file not found")

    filepath.unlink()
    return {"ok": True, "deleted": filename}


@router.get("/csv")
async def export_csv():
    """Export all keyword history as a CSV download."""
    mgr = KeywordHistoryManager()
    items = mgr.load_all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "timestamp", "seed", "selected_keyword", "used_for_post",
        "keyword", "source", "blog_count", "competition", "blue_ocean_score",
    ])

    for item in items:
        base = [
            item.get("timestamp", ""),
            item.get("seed", ""),
            item.get("selected_keyword", ""),
            item.get("used_for_post", False),
        ]
        for result in item.get("results", []):
            writer.writerow(base + [
                result.get("keyword", ""),
                result.get("source", ""),
                result.get("blog_count", ""),
                result.get("competition", ""),
                result.get("blue_ocean_score", ""),
            ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=keyword_history.csv"},
    )
