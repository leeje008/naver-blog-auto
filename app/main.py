"""네이버 블로그 자동 생성기 — Streamlit 엔트리포인트."""

import streamlit as st

st.set_page_config(
    page_title="네이버 블로그 자동 생성기",
    page_icon="✍️",
    layout="wide",
)

st.title("✍️ 네이버 블로그 자동 생성기")

st.markdown(
    """
### 사용 순서

1. **설정** — API 인증 + 레퍼런스 글 등록
2. **키워드** — 블루오션 키워드 탐색
3. **글 작성** — 이미지 업로드 + 초안 생성
4. **미리보기** — 수정 + 업로드
5. **작성 이력** — 과거 생성 기록 확인

사이드바에서 페이지를 선택하세요.
"""
)
