#!/bin/sh
set -e

echo "=== Streamlit 서버 시작 ==="

# core 모듈 import를 위한 PYTHONPATH 설정
export PYTHONPATH="/app:${PYTHONPATH:-}"

PORT="${PORT:-8501}"
echo "Streamlit 시작 (port: $PORT, PYTHONPATH=$PYTHONPATH)"

exec streamlit run app/main.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true
