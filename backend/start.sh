#!/bin/sh
set -e

echo "=== FastAPI Backend 시작 ==="

export PYTHONPATH="/app:${PYTHONPATH:-}"

PORT="${PORT:-8000}"
echo "FastAPI 시작 (port: $PORT)"

exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1
