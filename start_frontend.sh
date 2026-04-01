#!/bin/sh
set -e
echo "=== Next.js Frontend 시작 ==="
PORT="${PORT:-3000}"
cd /app/frontend
echo "Next.js 시작 (port: $PORT)"
exec npx next start -p "$PORT"
