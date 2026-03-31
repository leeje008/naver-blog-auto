# 2026-03-31 작업 기록: Railway 배포 + 로컬 LLM 원격 접속 구조

## 작업 목표
Streamlit 앱을 Railway에 배포하고, 로컬 MacBook의 Ollama를 Cloudflare Tunnel로 연결하여
원격에서도 AI 기능을 사용할 수 있도록 구성.

## 아키텍처
```
[브라우저] → [Streamlit on Railway] → [Cloudflare Tunnel] → [Ollama on MacBook]
```

## 변경 내역

### core/llm_client.py
- `ollama.chat()` → `ollama.Client(host=OLLAMA_HOST).chat()` 로 변경
- 환경변수 `OLLAMA_HOST_URL`로 호스트 지정 가능
- 기본 모델: `qwen3.5:27b` → `gemma3:12b`

### app/pages/1_settings.py
- 글 작성/키워드 분석 기본 모델: `gemma3:12b`로 통일

### Railway 배포 파일
- `railway.toml` — NIXPACKS 빌드 + Streamlit 시작
- `start_streamlit.sh` — Streamlit 실행 스크립트
- `requirements.txt` — Railway용 의존성

### scripts/start-local-llm.sh
- Ollama + Cloudflare Tunnel 원클릭 실행
- `--background`: 잠자기 방지 + 백그라운드
- `--stop`: 전체 종료 + 잠자기 복원
- 터널 URL 자동 코드 반영 + git push + Railway 배포

## 비용
- Railway Trial: 무료 ($5 크레딧, 500시간/월)
- Ollama + Cloudflare Tunnel: 무료
