"""네이버 블로그 자동 생성기 — Streamlit 엔트리포인트."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core.config import DEFAULT_CONFIG, load_config

load_dotenv()

# ── .streamlit/config.toml 자동 생성 (테마) ───────────────────
_streamlit_dir = Path(__file__).parent.parent / ".streamlit"
_config_toml = _streamlit_dir / "config.toml"
if not _config_toml.exists():
    _streamlit_dir.mkdir(parents=True, exist_ok=True)
    _config_toml.write_text(
        '[theme]\nprimaryColor = "#03C75A"\n'
        'backgroundColor = "#FFFFFF"\n'
        'secondaryBackgroundColor = "#F0F2F6"\n'
        'textColor = "#262730"\n'
        'font = "sans serif"\n\n'
        "[browser]\ngatherUsageStats = false\n"
    )

st.set_page_config(
    page_title="네이버 블로그 자동 생성기",
    page_icon="✍️",
    layout="wide",
)

# ── .env 기반 세션 기본값 초기화 ──────────────────────────────
_env_defaults = {
    "naver_client_id": os.getenv("NAVER_CLIENT_ID", ""),
    "naver_client_secret": os.getenv("NAVER_CLIENT_SECRET", ""),
    "naver_blog_id": os.getenv("NAVER_BLOG_ID", ""),
    "naver_api_secret": os.getenv("NAVER_API_SECRET", ""),
}
for key, default in _env_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── 사용자 설정(config.json) 로드 ─────────────────────────────
_user_config = load_config()
for key, default in DEFAULT_CONFIG.items():
    if key not in st.session_state:
        st.session_state[key] = _user_config.get(key, default)

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
