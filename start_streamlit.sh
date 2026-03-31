#!/bin/sh
set -e

echo "=== Streamlit 서버 시작 ==="

PORT="${PORT:-8501}"
echo "Streamlit 시작 (port: $PORT)"

exec streamlit run app/main.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true
