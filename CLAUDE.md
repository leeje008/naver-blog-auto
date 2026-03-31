# 네이버 블로그 자동 작성 도구

## 프로젝트 개요
네이버 블로그 글 작성 자동화를 위한 도구.
블루오션 키워드 발굴 → 이미지 기반 초안 생성 → SEO 최적화 → 네이버 블로그 자동 업로드.

## 기술 스택
- Python 3.12+ (uv 패키지 관리)
- Streamlit (멀티페이지 UI)
- Ollama (로컬 LLM, 기본 모델: gemma3:12b)
- BeautifulSoup + lxml (크롤링)
- XML-RPC MetaWeblog API (네이버 블로그 업로드)
- Railway (배포, Trial 무료 플랜)
- Cloudflare Tunnel (로컬 Ollama 원격 접속)

## 아키텍처 (원격 접속)
```
[사용자 브라우저] → [Streamlit on Railway] → [Cloudflare Tunnel] → [Ollama on MacBook]
```
- Railway: Streamlit UI만 실행 (경량)
- LLM 추론: 로컬 MacBook에서 수행 (Ollama)
- Cloudflare Tunnel: 로컬 Ollama를 외부에 노출

## 디렉토리 구조
- `app/` — Streamlit UI (main.py + pages/)
- `core/` — 비즈니스 로직 모듈
  - `llm_client.py` — Ollama LLM 클라이언트 (원격 호스트 지원)
  - `keyword.py` — 블루오션 키워드 엔진
  - `generator.py` — 블로그 초안 생성 + SEO 최적화
  - `publisher.py` — 네이버 블로그 업로드
  - `reference.py` — 레퍼런스 글 크롤링/관리
  - `image_utils.py` — 이미지 리사이즈/SEO ALT 최적화
  - `seo_validator.py` — SEO 검증 엔진 (10개 항목)
- `prompts/` — YAML 프롬프트 템플릿
- `scripts/` — 자동화 스크립트
  - `start-local-llm.sh` — Ollama + Tunnel + 자동배포
- `data/` — 로컬 데이터 (references, history)
- `docs/` — 문서

## 실행 방법

### 로컬 개발
```bash
uv sync
ollama serve
streamlit run app/main.py
```

### 원격 접속 (팀원 테스트)
```bash
# 서버 운영자: 원클릭 실행
./scripts/start-local-llm.sh

# 백그라운드 (덮개 닫아도 유지)
./scripts/start-local-llm.sh --background

# 종료
./scripts/start-local-llm.sh --stop
```

## 환경변수
| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OLLAMA_HOST_URL` | Ollama 서버 URL (로컬 또는 터널) | `http://localhost:11434` |
| `NAVER_BLOG_ID` | 네이버 블로그 ID | |
| `NAVER_API_SECRET` | XML-RPC API 비밀번호 | |
| `NAVER_CLIENT_ID` | 네이버 검색 API Client ID | |
| `NAVER_CLIENT_SECRET` | 네이버 검색 API Client Secret | |

## 코딩 컨벤션
- 한국어 docstring 사용
- 타입 힌트 필수 (Python 3.12 내장 타입: `list[str]`, `dict | None`)
- 클래스 기반 모듈 설계 (KeywordEngine, NaverPublisher, LLMClient)
- 프롬프트는 반드시 `prompts/*.yaml`에 외부화
- 환경변수는 `.env` + python-dotenv
- LLM 호출은 `core/llm_client.py`의 `LLMClient` 사용

## SEO 최적화 시스템
- 10개 항목 검증: 제목, 본문 길이, 키워드 밀도, 헤딩 구조, 이미지, 해시태그, 가독성, 경험 신호, 정보 깊이, AI 안전성
- 3개 프로필: balanced, keyword_focused, authenticity
- 가중 평균 점수 (0~100) + 등급 (A/B/C/D)

## 설계 문서
- `DESIGN_v5.md` — 전체 기획 설계 명세
- `SEO_RESEARCH.md` — 네이버 SEO 최적화 리서치
- `docs/2026-03-31-railway-deploy.md` — Railway 배포 작업 기록
