"""키워드 추천 페이지 — 블루오션 키워드 탐색."""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.keyword import KeywordEngine
from core.llm_client import LLMClient

st.header("🔑 블루오션 키워드 추천")
st.caption(
    "검색량은 있지만 경쟁이 적은 키워드를 찾습니다. "
    "(네이버 자동완성 + LLM 확장 + 블로그 검색 수 기반)"
)

# ── 키워드 입력 ──────────────────────────────────────────────
seed_keyword = st.text_input(
    "시드 키워드", placeholder='예: "캠핑 용품", "서울 카페"'
)

if st.button("🔍 키워드 분석", type="primary", use_container_width=True):
    if not seed_keyword:
        st.error("키워드를 입력하세요.")
    else:
        model = st.session_state.get("llm_model", "qwen3.5:27b")
        llm_client = LLMClient(model=model)
        engine = KeywordEngine(llm_client)

        progress = st.progress(0, text="키워드 확장 중...")

        # 키워드 확장
        keywords = engine.expand_keywords(seed_keyword)
        progress.progress(30, text=f"{len(keywords)}개 키워드 발견. 경쟁도 조회 중...")

        # 경쟁도 조회
        results = []
        for i, kw in enumerate(keywords):
            blog_count = engine.get_blog_count(kw)
            results.append({
                "keyword": kw,
                "blog_count": blog_count,
                "competition": engine._competition_level(blog_count),
            })
            pct = 30 + int(70 * (i + 1) / len(keywords))
            progress.progress(pct, text=f"경쟁도 조회: {kw} ({i + 1}/{len(keywords)})")

        results.sort(key=lambda x: x["blog_count"])
        progress.empty()

        st.session_state.keyword_results = results
        st.success(f"분석 완료! {len(results)}개 키워드")

# ── 결과 표시 ────────────────────────────────────────────────
if "keyword_results" in st.session_state and st.session_state.keyword_results:
    results = st.session_state.keyword_results

    df = pd.DataFrame(results)
    df.columns = ["키워드", "블로그 수", "경쟁도"]
    df["추천"] = df["경쟁도"].apply(lambda x: "⭐ 추천" if x == "낮음" else "")

    st.dataframe(df, use_container_width=True, hide_index=True)

    # 키워드 선택
    keyword_options = [r["keyword"] for r in results]
    selected = st.selectbox("타겟 키워드 선택", keyword_options)

    if st.button("✅ 이 키워드로 글 작성하기", use_container_width=True):
        st.session_state.target_keyword = selected
        st.success(f"타겟 키워드 설정: **{selected}**")
        st.info("사이드바에서 '글 작성' 페이지로 이동하세요.")
