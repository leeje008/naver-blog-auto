"""키워드 추천 페이지 — 블루오션 키워드 탐색."""

import pandas as pd
import streamlit as st

from core.keyword import KeywordEngine
from core.keyword_history import KeywordHistoryManager
from core.llm_client import LLMClient

st.header("🔑 블루오션 키워드 추천")
st.caption(
    "검색 수요는 있지만 경쟁이 적은 키워드를 찾습니다. "
    "(네이버 자동완성 + LLM 확장 + 시드 대비 상대 경쟁도)"
)

# ── 키워드 입력 ──────────────────────────────────────────────
seed_keyword = st.text_input(
    "시드 키워드", placeholder='예: "캠핑 용품", "서울 카페"'
)

if st.button("🔍 키워드 분석", type="primary", width="stretch"):
    seed_keyword = seed_keyword.strip()
    if not seed_keyword or len(seed_keyword) < 2:
        st.error("2자 이상의 키워드를 입력하세요.")
    else:
        model = st.session_state.get("keyword_model", "llama3.1:8b")
        llm_client = LLMClient(model=model)
        engine = KeywordEngine(
            llm_client,
            naver_client_id=st.session_state.get("naver_client_id", ""),
            naver_client_secret=st.session_state.get("naver_client_secret", ""),
        )

        progress = st.progress(0, text="키워드 확장 중...")

        # 키워드 확장
        keyword_items = engine.expand_keywords(seed_keyword)
        progress.progress(20, text=f"{len(keyword_items)}개 키워드 발견. 시드 블로그 수 조회 중...")

        # 시드 블로그 수 조회 (기준선)
        seed_blog_count = engine.get_blog_count(seed_keyword)
        progress.progress(25, text=f"시드 '{seed_keyword}' 블로그 수: {seed_blog_count:,}건. 경쟁도 조회 중..." if seed_blog_count else "경쟁도 조회 중...")

        # 각 키워드 경쟁도 조회
        results = []
        failed_count = 0
        for i, item in enumerate(keyword_items):
            kw = item["keyword"]
            source = item["source"]
            blog_count = engine.get_blog_count(kw)
            if blog_count is None:
                failed_count += 1

            blue_ocean_score = engine._calc_blue_ocean_score(
                keyword=kw,
                source=source,
                blog_count=blog_count,
                seed=seed_keyword,
                seed_blog_count=seed_blog_count,
            )

            ratio = None
            if blog_count is not None and seed_blog_count and seed_blog_count > 0:
                ratio = blog_count / seed_blog_count

            results.append({
                "keyword": kw,
                "source": source,
                "blog_count": blog_count if blog_count is not None else 0,
                "competition": engine._relative_competition(ratio),
                "seed_ratio": ratio,
                "blue_ocean_score": blue_ocean_score,
            })
            pct = 25 + int(75 * (i + 1) / len(keyword_items))
            progress.progress(pct, text=f"경쟁도 조회: {kw} ({i + 1}/{len(keyword_items)})")

        results.sort(key=lambda x: x["blue_ocean_score"], reverse=True)
        progress.empty()

        st.session_state.keyword_results = results
        st.session_state.seed_blog_count = seed_blog_count
        st.session_state._keyword_seed = seed_keyword

        # 키워드 이력 저장
        KeywordHistoryManager().save_analysis(seed_keyword, results)
        st.success(f"분석 완료! {len(results)}개 키워드")
        if seed_blog_count:
            st.info(f"기준: '{seed_keyword}' 블로그 수 **{seed_blog_count:,}건**")
        if failed_count > 0:
            st.warning(
                f"⚠️ {failed_count}개 키워드의 블로그 수 조회에 실패했습니다. "
                "설정 페이지에서 네이버 검색 API 키를 확인하세요."
            )

# ── 결과 표시 ────────────────────────────────────────────────
if "keyword_results" in st.session_state and st.session_state.keyword_results:
    results = st.session_state.keyword_results

    source_labels = {"autocomplete": "🔍 자동완성", "llm": "🤖 LLM"}
    df = pd.DataFrame([
        {
            "점수": r["blue_ocean_score"],
            "키워드": r["keyword"],
            "출처": source_labels.get(r["source"], r["source"]),
            "블로그 수": f"{r['blog_count']:,}",
            "시드 대비": f"{r['seed_ratio']:.1%}" if r["seed_ratio"] is not None else "-",
            "경쟁도": r["competition"],
        }
        for r in results
    ])

    st.dataframe(df, width="stretch", hide_index=True)

    with st.expander("📊 블루오션 점수 기준"):
        st.markdown(
            "- **출처 (30점)**: 네이버 자동완성 출처 = 실제 검색 수요 증거\n"
            "- **상대 경쟁도 (40점)**: 시드 키워드 대비 블로그 수 비율 (로그 스케일)\n"
            "  - 시드 대비 1% 미만 = 40점, 60%+ = 3점\n"
            "- **구체성 (30점)**: 롱테일 키워드(단어 많음)일수록 틈새 가능성"
        )

    # 키워드 선택
    keyword_options = [r["keyword"] for r in results]
    selected = st.selectbox("타겟 키워드 선택", keyword_options)

    # 상위 포스트 분석
    if st.button("🔎 상위 포스트 경쟁 분석", key="btn_top_posts"):
        model = st.session_state.get("keyword_model", "llama3.1:8b")
        llm_client = LLMClient(model=model)
        engine = KeywordEngine(
            llm_client,
            naver_client_id=st.session_state.get("naver_client_id", ""),
            naver_client_secret=st.session_state.get("naver_client_secret", ""),
        )
        with st.spinner(f"'{selected}' 상위 포스트 분석 중..."):
            top_analysis = engine.analyze_top_posts(selected)

        quality_colors = {"높음": "🔴", "중간": "🟡", "낮음": "🟢", "알수없음": "⚪"}
        quality_icon = quality_colors.get(top_analysis["quality_level"], "⚪")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("상위 포스트 수", f"{top_analysis['top_post_count']}개")
        with col_b:
            st.metric("평균 설명 길이", f"{top_analysis['avg_desc_length']}자")
        with col_c:
            st.metric("경쟁 품질", f"{quality_icon} {top_analysis['quality_level']}")

        if top_analysis["quality_level"] == "낮음":
            st.success("상위 포스트 품질이 낮아 진입하기 좋은 키워드입니다!")
        elif top_analysis["quality_level"] == "높음":
            st.warning("상위 포스트 품질이 높아 더 많은 노력이 필요합니다.")

    st.divider()

    if st.button("✅ 이 키워드로 글 작성하기", type="primary", width="stretch"):
        st.session_state.target_keyword = selected
        # 키워드 이력에 '사용됨' 표시
        seed = st.session_state.get("_keyword_seed", "")
        if seed:
            KeywordHistoryManager().mark_used(seed, selected)
        st.success(f"타겟 키워드 설정: **{selected}**")
        st.info("사이드바에서 '글 작성' 페이지로 이동하세요.")

    # 키워드 분석 이력
    st.divider()
    kw_history = KeywordHistoryManager().load_all()
    if kw_history:
        with st.expander(f"📜 키워드 분석 이력 ({len(kw_history)}건)"):
            for item in kw_history[:10]:
                used = "✅" if item.get("used_for_post") else ""
                selected_kw = item.get("selected_keyword", "")
                label = f"{used} {item.get('seed', '')} → {selected_kw or '미선택'} ({item.get('timestamp', '')[:10]})"
                st.caption(label)
