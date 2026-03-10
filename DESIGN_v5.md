# 네이버 블로그 자동화 도구 — 기획 설계 문서 (v5)

> **문서 버전**: v5  
> **작성일**: 2026-03-08  
> **목적**: 개인 블로그 콘텐츠 작성 자동화 (1인 사용자용)

**변경 이력**

| 버전 | 주요 변경 |
|-----|---------|
| v1 | 초안 |
| v2 | 경량화 (FastAPI 제거, reference 방식) |
| v3 | 키워드 경쟁도 분석 복원 |
| v4 | selector fallback, 키워드 수 제한, reference 글자 수 제한 |
| v5 | 누락 메서드 복원, image_positions, tags, 프롬프트 템플릿 보완 |

---

## 1. 프로젝트 개요

본 프로젝트는 네이버 블로그 글 작성 작업을 자동화하기 위한 개인용 도구이다.

### 핵심 목표

- 블로그 글 작성 시간 단축
- 블루오션 키워드 발굴 (검색량은 있으나 경쟁이 적은 키워드 탐색)
- 이미지 기반 초안 생성
- 네이버 블로그 자동 업로드

### 설계 원칙

- 단순한 구조
- 로컬 실행
- 최소 인프라
- 빠른 구현

---

## 2. 시스템 구조 (MVP)

개인용 도구이므로 단순 구조를 사용한다. FastAPI 없이 Streamlit이 직접 Core 모듈을 호출한다.

```
Streamlit UI
    ↓
Core Modules (keyword / generator / publisher)
    ↓
LLM Client (Ollama)  +  Naver APIs (자동완성, 검색, 블로그 글쓰기)
```

| 모듈 | 역할 |
|-----|------|
| Streamlit | UI 및 전체 실행 환경 |
| Keyword Engine | 롱테일 키워드 추천 + 경쟁도 조회 |
| Generator | 블로그 글 초안 생성 |
| Publisher | 네이버 블로그 업로드 |
| LLM Client | LLM 호출 추상화 (Ollama → GPT 전환 대비) |

---

## 3. 핵심 기능

### 기능 A — 블로그 스타일 참고 (Reference 방식)

스타일 프로파일 생성 대신 Reference 방식을 사용한다. 기존에 작성한 블로그 글 원문을 LLM 프롬프트에 삽입하여, 톤 & 매너와 이미지 배치를 참고하도록 한다.

#### 동작 흐름

```
블로그 글 URL 입력 (3개)
    ↓
본문 수집 (크롤링)
    ↓
reference_posts로 저장 (content 최대 1500자, image_positions 포함)
    ↓
초안 생성 시 LLM 프롬프트에 삽입
```

#### 저장 형식

```json
{
  "reference_posts": [
    {
      "url": "https://blog.naver.com/...",
      "title": "글 제목",
      "content": "본문 텍스트 — 최대 1500자 (HTML 태그 제거)",
      "image_positions": [0, 3, 7]
    }
  ]
}
```

- `content`: LLM context 안정성을 위해 최대 **1500자**까지만 저장한다. (1000자는 블로그 글의 톤 파악에 너무 짧을 수 있어 1500자로 상향)
- `image_positions`: 본문 내 이미지가 삽입된 단락 인덱스. 초안 생성 시 이미지 배치 패턴 참고에 사용한다.

---

### 기능 B — 블루오션 키워드 추천

#### 핵심 목적

검색량은 있으나 경쟁(해당 키워드로 글을 쓴 블로그)이 적은 키워드를 찾는 것이 1차 목적이다.

> **MVP 설계 근거**: 네이버 자동완성에 등장하는 키워드는 이미 일정 수준의 검색량이 있다는 의미이므로, 자동완성 키워드 중 블로그 수가 적은 것을 선택하면 "검색은 되지만 경쟁이 적은" 키워드를 확보하는 효과가 있다. 검색량 API 없이도 블루오션 전략의 핵심을 실현할 수 있다.

#### 흐름

```
시드 키워드 입력 — 예: "캠핑 용품"
    ↓
[키워드 확장]
    네이버 자동완성 API + LLM 확장
    → 롱테일 키워드 후보 생성 (최대 15개로 제한)
    ↓
[경쟁도 조회]
    각 키워드별 네이버 블로그 검색 결과 수 조회
    ↓
[추천 리스트 생성]
    경쟁도(블로그 수) 기준 오름차순 정렬
    → 사용자가 타겟 키워드 선택
```

#### 추천 결과 예시

```
키워드                  │ 블로그 수 │ 경쟁도  │ 추천
───────────────────────┼─────────┼───────┼──────
1인 경량 캠핑의자 비교    │ 280     │ 낮음   │ ★ 추천
초보 캠핑 준비물 체크리스트 │ 1,200   │ 중간   │
감성 캠핑 소품 추천       │ 4,800   │ 중간   │
캠핑 용품 추천           │ 38,000  │ 높음   │
```

경쟁도 기준: 블로그 검색 결과 수 **1,000 미만 = 낮음**, 1,000~5,000 = 중간, 5,000 이상 = 높음

#### 구현

```python
# core/keyword.py
import requests
import re
import time
from bs4 import BeautifulSoup


class KeywordEngine:

    def __init__(self, llm_client):
        self.llm_client = llm_client

    # --- 키워드 확장 ---

    def expand_keywords(self, seed: str) -> list[str]:
        """네이버 자동완성 + LLM으로 키워드 확장"""
        keywords = []

        # 1) 네이버 자동완성
        try:
            ac_url = "https://ac.search.naver.com/nx/ac"
            params = {"q": seed, "con": "1", "frm": "nv", "ans": "2"}
            resp = requests.get(ac_url, params=params, timeout=5)
            if resp.ok:
                data = resp.json()
                for item in data.get("items", [[]])[0]:
                    keywords.append(item[0])
        except Exception:
            pass  # fallback to LLM only

        # 2) LLM 확장
        try:
            llm_result = self.llm_client.generate(
                system_prompt="네이버 블로그 키워드 전문가입니다.",
                user_prompt=(
                    f"'{seed}'에 대한 롱테일 검색 키워드 15개를 생성해 주세요. "
                    "키워드만 줄바꿈으로 출력해 주세요."
                )
            )
            for line in llm_result.strip().split("\n"):
                line = line.strip().lstrip("0123456789.-) ")
                if line:
                    keywords.append(line)
        except Exception:
            pass

        # 중복 제거 후 최대 15개
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        return unique[:15]

    # --- 경쟁도 조회 ---

    def get_blog_count(self, keyword: str) -> int:
        """네이버 블로그 검색 결과 수 조회"""
        url = "https://search.naver.com/search.naver"
        params = {"where": "blog", "query": keyword}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            # selector fallback (네이버 DOM 변경 대응)
            selectors = [".title_num", ".title_desc", ".sub_text"]
            text = None
            for sel in selectors:
                elem = soup.select_one(sel)
                if elem:
                    text = elem.text
                    break

            if text:
                text = text.replace(",", "")
                match = re.search(r"(\d+)건", text)
                if match:
                    return int(match.group(1))
        except Exception:
            pass

        return 0

    # --- 분석 (확장 + 경쟁도) ---

    def analyze(self, seed: str) -> list[dict]:
        """키워드 확장 + 경쟁도 조회 → 추천 리스트"""
        keywords = self.expand_keywords(seed)

        results = []
        for kw in keywords:
            blog_count = self.get_blog_count(kw)
            results.append({
                "keyword": kw,
                "blog_count": blog_count,
                "competition": self._competition_level(blog_count),
            })
            time.sleep(0.5)  # rate limiting

        results.sort(key=lambda x: x["blog_count"])
        return results

    # --- 경쟁도 레벨 ---

    def _competition_level(self, blog_count: int) -> str:
        if blog_count < 1000:
            return "낮음"
        elif blog_count < 5000:
            return "중간"
        else:
            return "높음"
```

#### MVP vs To-Be

| 구분 | MVP | To-Be |
|-----|-----|-------|
| 키워드 확장 | 네이버 자동완성 + LLM | + 검색광고 API 연관 키워드 |
| 검색량 | 없음 (자동완성 존재 = 검색량 있음으로 간주) | 네이버 검색광고 API (월간 검색량) |
| 경쟁도 | 블로그 검색 결과 수 크롤링 | + 상위 글 품질 분석 |
| 스코어링 | 경쟁도 단일 기준 정렬 | 검색량/경쟁도 복합 스코어 |

---

### 기능 C — 이미지 기반 글 생성

사용자가 업로드한 이미지를 기반으로 블로그 글 초안를 생성한다. MVP에서는 이미지 분석 대신 사용자 설명 입력 방식을 사용한다.

#### 흐름

```
이미지 업로드 (순서대로)
    ↓
각 이미지에 대한 간단한 설명 입력
    ↓
LLM 초안 생성 (타겟 키워드 + reference + 이미지 설명 결합)
```

#### 프롬프트 템플릿

```yaml
# prompts/draft_generation.yaml
system: |
  당신은 네이버 블로그 전문 작가입니다.
  아래 레퍼런스 글의 톤 & 매너, 구조, 이미지 배치를 참고하여 블로그 글을 작성해 주세요.
  
  ## 레퍼런스 글
  {reference_posts}
  
  ## 이미지 배치 참고
  레퍼런스 글의 이미지 위치: {image_positions}
  위 패턴을 참고하여 이미지를 본문 내에 자연스럽게 배치해 주세요.
  이미지 삽입 위치는 [IMAGE_1], [IMAGE_2] 형태로 표시해 주세요.
  
  ## 작성 규칙
  - 타겟 키워드 "{target_keyword}"를 제목 앞부분에 배치
  - 본문에 키워드를 자연스럽게 2~3회 포함
  - 레퍼런스 글과 유사한 문체와 구조 사용
  - HTML 형식으로 출력

user: |
  타겟 키워드: {target_keyword}
  
  이미지 {image_count}장이 있습니다.
  {image_descriptions}
  
  이 이미지들을 포함한 블로그 글 초안을 작성해 주세요.
```

```yaml
# prompts/keyword_expansion.yaml
system: |
  네이버 블로그 키워드 전문가입니다.
  사용자가 입력한 주제에 대해 네이버에서 실제 검색될 수 있는
  롱테일 키워드를 생성해 주세요.

user: |
  주제: {seed_keyword}
  
  위 주제에 대한 롱테일 검색 키워드 15개를 생성해 주세요.
  키워드만 줄바꿈으로 출력해 주세요.
```

---

### 기능 D — 초안 수정 워크플로우

```
초안 생성 완료
    ↓
미리보기 (st.markdown)
    ↓
├── [승인 & 업로드] → 네이버 블로그 게시 → 완료
│
└── [수정하기]
        ↓
    섹션별 텍스트 수정 (st.text_area)
    이미지 순서 변경 (st.number_input)
        ↓
    [수정 완료 & 업로드] → 게시
```

| UI 영역 | 컴포넌트 |
|---------|---------|
| 미리보기 | `st.markdown(html, unsafe_allow_html=True)` |
| 텍스트 수정 | `st.text_area()` × 섹션 수 |
| 이미지 순서 변경 | `st.number_input()` |
| 업로드 | `st.button("승인 & 업로드")` |

---

### 기능 E — 네이버 블로그 업로드

MetaWeblog API (XML-RPC) 기반으로 동작한다.

```python
# core/publisher.py
import xmlrpc.client


class NaverPublisher:

    ENDPOINT = "https://blog.naver.com/xmlrpc"

    def __init__(self, blog_id: str, password: str):
        self.client = xmlrpc.client.ServerProxy(self.ENDPOINT)
        self.blog_id = blog_id
        self.password = password

    def publish(self, title: str, html: str, tags: list[str] = None) -> str:
        """블로그 글 게시 후 post_id 반환"""
        post = {
            "title": title,
            "description": html,
        }
        if tags:
            post["mt_keywords"] = ",".join(tags)

        post_id = self.client.metaWeblog.newPost(
            self.blog_id,
            self.blog_id,
            self.password,
            post,
            True,
        )
        return post_id
```

#### 보안

```
# .env
NAVER_BLOG_ID=your_naver_id
NAVER_API_SECRET=your_api_secret
```

- `.gitignore`에 `.env` 포함

---

## 4. 디렉토리 구조

```
naver-blog-writer/
├── app/
│   ├── main.py                 # Streamlit 엔트리포인트
│   └── pages/
│       ├── 1_settings.py       # 설정 (API 인증, 레퍼런스 글 등록)
│       ├── 2_keyword.py        # 블루오션 키워드 추천
│       ├── 3_write.py          # 이미지 업로드 + 초안 생성
│       ├── 4_preview.py        # 미리보기 + 수정 + 업로드
│       └── 5_history.py        # 작성 이력
│
├── core/
│   ├── keyword.py              # 키워드 확장 + 경쟁도 조회
│   ├── generator.py            # LLM 초안 생성
│   ├── publisher.py            # 네이버 블로그 업로드
│   └── llm_client.py           # LLM 호출 추상화
│
├── prompts/
│   ├── draft_generation.yaml   # 초안 생성 프롬프트
│   └── keyword_expansion.yaml  # 키워드 확장 프롬프트
│
├── data/
│   ├── references/             # 레퍼런스 글 JSON
│   └── history/                # 생성 이력
│
├── .env
├── .gitignore
├── requirements.txt
├── DESIGN.md                   # ← 본 문서
└── README.md
```

---

## 5. 사용자 플로우

### 최초 설정

```
1. 네이버 블로그 API 연결 암호 발급 (가이드 문서 참조)
2. streamlit run app/main.py
3. 설정 화면에서 네이버 아이디 + API 암호 입력
4. 레퍼런스 블로그 글 URL 3개 입력 → 본문 + 이미지 위치 수집 & 저장
```

### 글 작성

```
1. 시드 키워드 입력
2. [키워드 분석] → 롱테일 키워드 + 경쟁도 테이블 표시
3. 블루오션 키워드 선택 (경쟁도 낮은 키워드)
4. 이미지 업로드 + 설명 입력
5. [초안 생성]
6. 미리보기 확인
7. 승인 → 업로드 (태그 자동 포함)  /  수정 → 업로드
```

---

## 6. MVP vs To-Be

| 영역 | MVP | To-Be |
|-----|-----|-------|
| 스타일 참고 | reference 글 원문 삽입 (3개, 1500자) | 자동 스타일 분석 프로파일 |
| 키워드 확장 | 네이버 자동완성 + LLM (최대 15개) | + 검색광고 API 연관 키워드 |
| 키워드 경쟁도 | 블로그 검색 결과 수 크롤링 | + 검색량 데이터 + 상위 글 품질 분석 |
| 이미지 분석 | 사용자 수동 설명 입력 | Vision 모델 자동 분석 |
| 이미지 배치 | reference image_positions 참고 | 자동 최적 배치 |
| 편집 UI | Streamlit text_area | React WYSIWYG 에디터 |
| 데이터 저장 | JSON 파일 | SQLite |
| LLM | Ollama 로컬 (Qwen3-32B 등) | GPT API |

---

## 7. 리스크

| 리스크 | 대응 |
|-------|------|
| 네이버 자동완성 API 변경/차단 | LLM 키워드 확장을 fallback으로 유지 |
| 네이버 검색 DOM 변경 | selector fallback 적용 (3개 selector 순차 시도) |
| 블로그 검색 크롤링 IP 차단 | rate limiting (0.5초 간격) + 결과 캐싱 |
| LLM 품질 차이 | 프롬프트 개선 + To-Be에서 GPT API 전환 |
| 이미지 업로드 호환성 | Base64 삽입 테스트 → 실패 시 `newMediaObject` 활용 |
| reference 글 크롤링 실패 | 수동 복사-붙여넣기 입력 fallback UI 제공 |

---

## 8. 확장 가능성

- 키워드 트렌드 모니터링 (주기적 경쟁도 변화 추적)
- 게시 글 조회수/검색 순위 트래킹 → 블루오션 전략 피드백 루프
- A/B 테스트 (제목/썸네일 변형)
- 예약 발행
- 다중 플랫폼 (티스토리, 워드프레스)
