# 네이버 블로그 자동 작성 도구

블루오션 키워드 발굴 → 이미지 기반 초안 생성 → SEO 최적화 → 네이버 블로그 자동 업로드까지 원스톱으로 처리하는 1인 사용자용 도구입니다.

## 주요 기능

- **블루오션 키워드 추천** — 네이버 자동완성 + LLM 롱테일 키워드 확장 + 경쟁도 분석
- **이미지 기반 초안 생성** — 업로드한 이미지 설명을 반영한 LLM 블로그 글 생성
- **SEO 최적화** — 네이버 D.I.A.+ 알고리즘 기반 6개 항목 점수 분석 + 자동 개선
- **레퍼런스 톤 & 매너 유지** — 기존 블로그 글 크롤링으로 문체 일관성 유지
- **네이버 블로그 업로드** — XML-RPC MetaWeblog API를 통한 원클릭 발행

## 설치 및 실행

### 사전 요구 사항

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- [Ollama](https://ollama.com/) (로컬 LLM 서버)

### 설치

```bash
git clone <repo-url>
cd naver-blog-auto
uv sync
```

### Ollama 모델 준비

```bash
ollama pull qwen3.5:27b  # 또는 원하는 모델
ollama serve              # Ollama 서버 실행
```

### 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 네이버 블로그 API 인증 정보를 입력합니다:

```
NAVER_BLOG_ID=your_naver_id
NAVER_API_SECRET=your_api_secret
```

> 네이버 블로그 > 관리 > 글쓰기 API 설정에서 API 연동 암호를 발급받을 수 있습니다.

### 실행

```bash
streamlit run app/main.py
```

## 사용 흐름

1. **설정** — 네이버 API 인증, LLM 모델 선택, 레퍼런스 블로그 글 등록
2. **키워드 추천** — 시드 키워드 입력 → 블루오션 키워드 탐색
3. **글 작성** — 타겟 키워드 + 이미지 업로드 → LLM 초안 생성
4. **미리보기** — SEO 점수 확인 → 최적화/수정 → 네이버 블로그 업로드

## 기술 스택

| 영역 | 기술 |
|------|------|
| UI | Streamlit (멀티페이지) |
| LLM | Ollama (로컬) |
| 크롤링 | BeautifulSoup + lxml |
| 업로드 | XML-RPC MetaWeblog API |
| 이미지 | Pillow |
| 패키지 관리 | uv |

## 테스트

```bash
uv run pytest tests/ -v
```

## 디렉토리 구조

```
app/           Streamlit UI (main.py + pages/)
core/          비즈니스 로직 모듈
prompts/       YAML 프롬프트 템플릿
data/          로컬 데이터 (references, history, logs)
tests/         유닛 테스트
```
