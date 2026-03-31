#!/bin/bash
# ============================================
# 네이버 블로그 자동 생성기 - 로컬 LLM 서버 실행
# Ollama + Cloudflare Tunnel + 자동 push/배포
# ============================================
# 사용법:
#   ./scripts/start-local-llm.sh              (포그라운드)
#   ./scripts/start-local-llm.sh --background (백그라운드 + 잠자기 방지)
#   ./scripts/start-local-llm.sh --stop       (종료)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

PID_FILE="/tmp/naver-blog-llm.pid"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# =====================
# --stop
# =====================
if [ "$1" = "--stop" ]; then
    echo -e "${YELLOW}서비스 종료 중...${NC}"
    pkill -f "cloudflared tunnel" 2>/dev/null || true
    pkill ollama 2>/dev/null || true
    sudo pmset -a disablesleep 0 2>/dev/null || true
    pkill caffeinate 2>/dev/null || true
    rm -f "$PID_FILE"
    echo -e "${GREEN}모든 서비스가 종료되었습니다.${NC}"
    echo -e "${GREEN}잠자기 방지가 해제되었습니다.${NC}"
    exit 0
fi

# =====================
# --background
# =====================
if [ "$1" = "--background" ]; then
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  백그라운드 모드로 실행합니다${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""

    echo -e "${YELLOW}[1/2] 잠자기 방지 활성화...${NC}"
    sudo pmset -a disablesleep 1
    caffeinate -dimsu &
    echo -e "${GREEN}  ✓ 맥북 덮개를 닫아도 서비스가 유지됩니다${NC}"

    echo -e "${YELLOW}[2/2] 서비스 시작 중...${NC}"
    nohup "$0" --foreground > /tmp/naver-blog-llm.log 2>&1 &
    BG_PID=$!
    echo "$BG_PID" > "$PID_FILE"

    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags &>/dev/null; then break; fi
        sleep 1
    done

    TUNNEL_URL=""
    for i in {1..30}; do
        TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflare-tunnel.log 2>/dev/null | head -1)
        if [ -n "$TUNNEL_URL" ]; then break; fi
        sleep 1
    done

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}  백그라운드 서비스 실행 완료!${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    if [ -n "$TUNNEL_URL" ]; then
        echo -e "  터널 URL:   ${GREEN}${TUNNEL_URL}${NC}"
    fi
    echo ""
    echo -e "  로그 확인:  ${CYAN}tail -f /tmp/naver-blog-llm.log${NC}"
    echo -e "  종료 명령:  ${CYAN}./scripts/start-local-llm.sh --stop${NC}"
    echo ""
    exit 0
fi

# =====================
# 메인 로직
# =====================
if [ "$1" != "--foreground" ]; then
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  네이버 블로그 - Local LLM 서버${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
fi

# 의존성 확인
if ! command -v ollama &>/dev/null; then
    echo -e "${RED}[ERROR] ollama 미설치. brew install ollama${NC}"; exit 1
fi
if ! command -v cloudflared &>/dev/null; then
    echo -e "${RED}[ERROR] cloudflared 미설치. brew install cloudflared${NC}"; exit 1
fi

# 기존 프로세스 정리
echo -e "${YELLOW}[1/5] 기존 프로세스 정리...${NC}"
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill ollama 2>/dev/null || true
sleep 2

# Ollama 시작
echo -e "${YELLOW}[2/5] Ollama 서버 시작...${NC}"
OLLAMA_ORIGINS="*" OLLAMA_HOST="0.0.0.0" ollama serve &>/tmp/ollama-server.log &
OLLAMA_PID=$!

for i in {1..15}; do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        MODEL_COUNT=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null)
        echo -e "${GREEN}  ✓ Ollama 실행됨 (${MODEL_COUNT}개 모델)${NC}"
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${RED}  ✗ Ollama 시작 실패${NC}"; exit 1
fi

# Cloudflare Tunnel 시작
echo -e "${YELLOW}[3/5] Cloudflare Tunnel 시작...${NC}"
cloudflared tunnel --url http://localhost:11434 &>/tmp/cloudflare-tunnel.log &
TUNNEL_PID=$!

TUNNEL_URL=""
for i in {1..20}; do
    TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare.com' /tmp/cloudflare-tunnel.log 2>/dev/null | head -1)
    if [ -n "$TUNNEL_URL" ]; then break; fi
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${RED}  ✗ 터널 생성 실패${NC}"; kill $OLLAMA_PID 2>/dev/null; exit 1
fi
echo -e "${GREEN}  ✓ 터널 생성됨: ${TUNNEL_URL}${NC}"

# 터널 URL을 코드에 반영 + push
echo -e "${YELLOW}[4/5] 터널 URL 코드 반영 및 push...${NC}"

LLM_FILE="core/llm_client.py"

# llm_client.py의 OLLAMA_HOST 기본값 업데이트
sed -i '' "s|OLLAMA_HOST = os.getenv(\"OLLAMA_HOST_URL\", \"[^\"]*\")|OLLAMA_HOST = os.getenv(\"OLLAMA_HOST_URL\", \"${TUNNEL_URL}\")|" "$LLM_FILE"

if git diff --quiet "$LLM_FILE" 2>/dev/null; then
    echo -e "${GREEN}  ✓ URL 변경 없음 (이미 최신)${NC}"
else
    git add "$LLM_FILE"
    git commit -m "터널 URL 자동 업데이트: ${TUNNEL_URL}"
    git push origin main
    echo -e "${GREEN}  ✓ main 브랜치에 push 완료${NC}"
fi

# Railway 배포
echo -e "${YELLOW}[5/5] Railway 배포...${NC}"
if command -v railway &>/dev/null; then
    railway up 2>/dev/null && echo -e "${GREEN}  ✓ Railway 배포 시작됨${NC}" || echo -e "${YELLOW}  ⚠ Railway 배포 실패 (수동 배포 필요)${NC}"
else
    echo -e "${YELLOW}  ⚠ railway CLI 없음 (git push로 자동 배포 대기)${NC}"
fi

# 결과 출력
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  모든 서비스 실행 완료!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  Ollama:     http://localhost:11434"
echo -e "  터널 URL:   ${GREEN}${TUNNEL_URL}${NC}"
echo ""

if [ "$1" = "--foreground" ]; then
    echo "백그라운드 모드로 실행 중..."
    wait
    exit 0
fi

echo -e "${YELLOW}  Ctrl+C로 종료${NC}"
echo ""

cleanup() {
    echo ""
    echo -e "${YELLOW}서비스 종료 중...${NC}"
    kill $TUNNEL_PID 2>/dev/null
    kill $OLLAMA_PID 2>/dev/null
    pkill -f "cloudflared tunnel" 2>/dev/null
    pkill ollama 2>/dev/null
    echo -e "${GREEN}모든 서비스가 종료되었습니다.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}--- Ollama 로그 (Ctrl+C로 종료) ---${NC}"
tail -f /tmp/ollama-server.log
