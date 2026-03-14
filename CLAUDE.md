# 네이버 블로그 자동 작성 도구

## 프로젝트 개요
네이버 블로그 글 작성 자동화를 위한 1인 사용자용 도구.
블루오션 키워드 발굴 → 이미지 기반 초안 생성 → 네이버 블로그 자동 업로드.

## 기술 스택
- Python 3.12+ (uv 패키지 관리)
- Streamlit (멀티페이지 UI)
- Ollama (로컬 LLM)
- BeautifulSoup + lxml (크롤링)
- XML-RPC MetaWeblog API (네이버 블로그 업로드)

## 실행 방법
```bash
uv sync
streamlit run app/main.py
```

## 디렉토리 구조
- `app/` — Streamlit UI (main.py + pages/)
- `core/` — 비즈니스 로직 모듈
  - `llm_client.py` — Ollama LLM 추상화
  - `keyword.py` — 블루오션 키워드 엔진
  - `generator.py` — 블로그 초안 생성 + SEO 최적화 재작성
  - `publisher.py` — 네이버 블로그 업로드
  - `reference.py` — 레퍼런스 글 크롤링/관리
  - `image_utils.py` — 이미지 리사이즈/HTML 변환/SEO ALT 최적화
  - `seo_validator.py` — SEO 검증 엔진 (6개 항목 점수 분석)
- `prompts/` — YAML 프롬프트 템플릿
  - `draft_generation.yaml` — 초안 생성 (SEO 규칙 포함)
  - `keyword_expansion.yaml` — 키워드 확장
  - `seo_optimization.yaml` — SEO 최적화 재작성
- `data/` — 로컬 데이터 (references, history)
- `legacy/` — v1 코드 (참고용)

## 코딩 컨벤션
- 한국어 docstring 사용
- 타입 힌트 필수 (Python 3.12 내장 타입: `list[str]`, `dict | None`)
- 클래스 기반 모듈 설계 (KeywordEngine, NaverPublisher, LLMClient)
- 프롬프트는 반드시 `prompts/*.yaml`에 외부화
- 환경변수는 `.env` + python-dotenv

## SEO 최적화 시스템
- `core/seo_validator.py` — 네이버 D.I.A.+ 알고리즘 기반 SEO 검증
- 6개 항목 검증: 제목, 본문 길이, 키워드 밀도, 헤딩 구조, 이미지, 해시태그
- 가중 평균 점수 (0~100) + 등급 (A/B/C/D)
- 미리보기 페이지에서 SEO 대시보드 자동 표시
- "SEO 최적화" 버튼으로 LLM 기반 자동 개선
- 상세 리서치: `SEO_RESEARCH.md`

## 설계 문서
- `DESIGN_v5.md` — 전체 기획 설계 명세
- `SEO_RESEARCH.md` — 네이버 SEO 최적화 리서치 보고서
