"""설정 페이지 — API 인증 + 레퍼런스 글 등록."""

import os

import streamlit as st
from dotenv import load_dotenv

from core.llm_client import LLMClient
from core.reference import crawl_reference, save_references, load_references

load_dotenv()

st.header("⚙️ 설정")

# ── LLM 모델 설정 ────────────────────────────────────────────
st.subheader("🤖 LLM 모델 설정")

available_models = []
try:
    client = LLMClient()
    available_models = client.list_models()
except Exception:
    st.warning("Ollama에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요.")

col_model1, col_model2 = st.columns(2)

with col_model1:
    st.caption("**글 작성 / SEO 최적화용** (고품질)")
    if available_models:
        if "llm_model" not in st.session_state:
            st.session_state.llm_model = available_models[0]
        st.session_state.llm_model = st.selectbox(
            "글 작성 모델", available_models, index=0
        )
    else:
        st.session_state.llm_model = st.text_input(
            "글 작성 모델 직접 입력", value="qwen3.5:27b", placeholder="qwen3.5:27b"
        )

with col_model2:
    st.caption("**키워드 분석용** (경량·빠름)")
    if available_models:
        # 8b/12b 모델 우선, 없으면 첫 번째 모델
        default_kw = next(
            (m for m in available_models if "8b" in m or "12b" in m),
            available_models[0],
        )
        default_idx = available_models.index(default_kw) if default_kw in available_models else 0
        if "keyword_model" not in st.session_state:
            st.session_state.keyword_model = default_kw
        st.session_state.keyword_model = st.selectbox(
            "키워드 모델", available_models, index=default_idx
        )
    else:
        st.session_state.keyword_model = st.text_input(
            "키워드 모델 직접 입력", value="llama3.1:8b", placeholder="llama3.1:8b"
        )

st.divider()

# ── 레퍼런스 블로그 글 등록 ──────────────────────────────────
st.subheader("📝 레퍼런스 블로그 글 등록")
st.caption("기존에 작성한 블로그 글 URL을 입력하면 톤 & 매너를 참고합니다. (최대 3개)")

ref_urls = []
for i in range(1, 4):
    url = st.text_input(
        f"레퍼런스 URL {i}",
        key=f"ref_url_{i}",
        placeholder="https://blog.naver.com/your_id/포스트번호",
    )
    if url:
        ref_urls.append(url)

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 크롤링으로 등록", width="stretch"):
        if not ref_urls:
            st.error("URL을 1개 이상 입력하세요.")
        else:
            references = []
            for url in ref_urls:
                with st.spinner(f"크롤링 중: {url[:50]}..."):
                    try:
                        ref = crawl_reference(url)
                        references.append(ref)
                        st.success(f"✅ {ref['title'][:30]}... ({len(ref['content'])}자)")
                    except Exception as e:
                        st.error(f"크롤링 실패 ({url[:30]}...): {e}")
            if references:
                save_references(references)
                st.success(f"레퍼런스 {len(references)}개 저장 완료!")

with col2:
    if st.button("📋 수동 입력으로 전환", width="stretch"):
        st.session_state.manual_input = True

# 수동 입력 fallback
if st.session_state.get("manual_input"):
    st.divider()
    st.caption("크롤링이 실패한 경우 직접 복사-붙여넣기로 등록할 수 있습니다.")

    manual_refs = []
    for i in range(1, 4):
        with st.expander(f"레퍼런스 {i} (수동 입력)"):
            title = st.text_input(f"제목", key=f"manual_title_{i}")
            content = st.text_area(
                f"본문 (최대 1500자)",
                key=f"manual_content_{i}",
                max_chars=1500,
                height=200,
            )
            if title and content:
                manual_refs.append({
                    "url": "",
                    "title": title,
                    "content": content[:1500],
                    "image_positions": [],
                })

    if st.button("💾 수동 입력 저장", width="stretch"):
        if manual_refs:
            save_references(manual_refs)
            st.success(f"레퍼런스 {len(manual_refs)}개 저장 완료!")
        else:
            st.warning("제목과 본문을 입력하세요.")

# 저장된 레퍼런스 표시
st.divider()
saved_refs = load_references()
if saved_refs:
    st.subheader(f"📋 저장된 레퍼런스 ({len(saved_refs)}개)")
    for i, ref in enumerate(saved_refs, 1):
        with st.expander(f"레퍼런스 {i}: {ref.get('title', '제목 없음')[:40]}"):
            st.markdown(f"**URL**: {ref.get('url', '없음')}")
            st.markdown(f"**글자 수**: {len(ref.get('content', ''))}자")
            st.markdown(f"**이미지 위치**: {ref.get('image_positions', [])}")
            st.text(ref.get("content", "")[:500] + "...")
else:
    st.info("저장된 레퍼런스가 없습니다. 위에서 등록해 주세요.")
