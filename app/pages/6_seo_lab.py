"""SEO 실험실 — 프로파일 비교, 파라미터 튜닝, 콘텐츠 테스트."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.seo_validator import (
    PROFILE_LABELS,
    SEO_PROFILES,
    validate_seo,
)

HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "history"

st.header("🔬 SEO 실험실")
st.caption("SEO 알고리즘을 테스트하고 프로파일을 비교할 수 있습니다.")

# ── 탭 구성 ──────────────────────────────────────────────────
tab_compare, tab_tune, tab_test, tab_batch = st.tabs([
    "📊 프로파일 비교", "🎛️ 가중치 튜닝", "📝 콘텐츠 테스트", "📁 일괄 분석"
])


# ── 공용: 분석 대상 콘텐츠 선택 ──────────────────────────────

def _get_analysis_target() -> tuple[dict, str] | None:
    """현재 세션의 생성된 글 반환."""
    gen = st.session_state.get("generated")
    keyword = st.session_state.get("target_keyword", "")
    if gen:
        return gen, keyword
    return None


def _load_history_drafts() -> list[tuple[str, dict]]:
    """이력 파일에서 글 목록 로드."""
    if not HISTORY_DIR.exists():
        return []
    items = []
    for hf in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(hf.read_text(encoding="utf-8"))
            if data.get("title") or data.get("content"):
                items.append((hf.stem, data))
        except Exception:
            continue
    return items


# ══════════════════════════════════════════════════════════════
# 탭 1: 프로파일 비교
# ══════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("프로파일별 점수 비교")

    # 콘텐츠 소스 선택
    source = st.radio(
        "분석 대상",
        ["현재 생성된 글", "이력에서 선택"],
        horizontal=True,
        key="compare_source",
    )

    target_draft = None
    target_keyword = ""
    target_images = 0

    if source == "현재 생성된 글":
        result = _get_analysis_target()
        if result:
            target_draft, target_keyword = result
            target_images = len(st.session_state.get("image_bytes_list", []))
        else:
            st.info("생성된 글이 없습니다. '글 작성' 페이지에서 먼저 글을 생성하세요.")
    else:
        history = _load_history_drafts()
        if history:
            selected_name = st.selectbox(
                "이력 선택",
                [name for name, _ in history],
                key="compare_history_select",
            )
            target_draft = next(d for n, d in history if n == selected_name)
            target_keyword = st.text_input("키워드 (이력용)", key="compare_keyword")
        else:
            st.info("이력이 없습니다.")

    if target_draft:
        st.divider()
        st.markdown(f"**제목**: {target_draft.get('title', '(없음)')[:50]}")

        # 3개 프로파일 동시 분석
        profile_cols = st.columns(3)
        profile_results = {}

        for i, (profile_key, profile_label) in enumerate(PROFILE_LABELS.items()):
            report = validate_seo(target_draft, target_keyword, target_images, profile=profile_key)
            profile_results[profile_key] = report

            grade_colors = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
            with profile_cols[i]:
                st.markdown(f"### {profile_label}")
                grade_icon = grade_colors.get(report["grade"], "⚪")
                st.metric("점수", f"{report['score']}/100")
                st.metric("등급", f"{grade_icon} {report['grade']}")

        # 항목별 비교 테이블
        st.divider()
        st.subheader("항목별 점수 비교")

        check_labels = {
            "title": "제목", "body_length": "본문 길이", "keyword_density": "키워드 밀도",
            "heading_structure": "헤딩 구조", "images": "이미지", "hashtags": "해시태그",
            "readability": "가독성", "experience_signals": "경험 정보",
            "information_depth": "정보 충실성", "ai_safety": "AI 안전",
        }

        comparison_data = []
        for check_key, check_label in check_labels.items():
            row = {"항목": check_label}
            for profile_key, profile_label in PROFILE_LABELS.items():
                report = profile_results[profile_key]
                check = report["checks"].get(check_key, {})
                row[profile_label] = check.get("score", 0)
            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)
        st.dataframe(df, hide_index=True, use_container_width=True)

        # 바 차트
        chart_df = df.set_index("항목")
        st.bar_chart(chart_df)


# ══════════════════════════════════════════════════════════════
# 탭 2: 가중치 튜닝
# ══════════════════════════════════════════════════════════════
with tab_tune:
    st.subheader("가중치 실시간 조절")
    st.caption("슬라이더로 가중치를 조절하면 점수가 자동 재계산됩니다. 합계 100%로 자동 정규화됩니다.")

    # 프리셋 선택
    preset = st.selectbox(
        "프리셋 불러오기",
        ["직접 조절"] + list(PROFILE_LABELS.values()),
        key="tune_preset",
    )

    preset_weights = None
    if preset != "직접 조절":
        preset_key = next(k for k, v in PROFILE_LABELS.items() if v == preset)
        preset_weights = SEO_PROFILES[preset_key]

    check_names = {
        "title": "📌 제목",
        "body_length": "📏 본문 길이",
        "keyword_density": "🔑 키워드 밀도",
        "heading_structure": "📑 헤딩 구조",
        "images": "🖼️ 이미지",
        "hashtags": "#️⃣ 해시태그",
        "readability": "📖 가독성",
        "experience_signals": "💡 경험 정보",
        "information_depth": "📚 정보 충실성",
        "ai_safety": "🤖 AI 안전",
    }

    raw_weights = {}
    slider_cols = st.columns(2)
    for i, (key, label) in enumerate(check_names.items()):
        default_val = int((preset_weights or SEO_PROFILES["balanced"])[key] * 100)
        with slider_cols[i % 2]:
            raw_weights[key] = st.slider(
                label, 0, 50, default_val, key=f"tune_{key}"
            )

    # 정규화
    total_raw = sum(raw_weights.values())
    if total_raw > 0:
        normalized = {k: v / total_raw for k, v in raw_weights.items()}
    else:
        normalized = {k: 1.0 / len(raw_weights) for k in raw_weights}

    st.caption(f"합계: {total_raw}% → 정규화 적용")

    # 분석 대상
    result = _get_analysis_target()
    if result:
        draft, keyword = result
        images = len(st.session_state.get("image_bytes_list", []))
        report = validate_seo(draft, keyword, images, custom_weights=normalized)

        st.divider()
        grade_colors = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric("커스텀 점수", f"{report['score']}/100")
        with metric_cols[1]:
            st.metric("등급", f"{grade_colors.get(report['grade'], '⚪')} {report['grade']}")
        with metric_cols[2]:
            # 기본 balanced와 비교
            baseline = validate_seo(draft, keyword, images, profile="balanced")
            delta = report["score"] - baseline["score"]
            st.metric("Balanced 대비", f"{delta:+}점")

        # 항목별 점수
        tune_data = []
        for key, label in check_names.items():
            check = report["checks"].get(key, {})
            weight_pct = f"{normalized[key]*100:.1f}%"
            tune_data.append({
                "항목": label,
                "점수": check.get("score", 0),
                "가중치": weight_pct,
                "기여": round(check.get("score", 0) * normalized[key], 1),
            })
        st.dataframe(pd.DataFrame(tune_data), hide_index=True, use_container_width=True)

        # 커스텀 프로파일 저장
        if st.button("💾 커스텀 프로파일 저장", key="save_custom_profile"):
            from core.config import load_config, save_config
            config = load_config()
            config["custom_seo_weights"] = normalized
            save_config(config)
            st.success("커스텀 가중치가 저장되었습니다.")
    else:
        st.info("생성된 글이 없습니다. '글 작성' 페이지에서 먼저 글을 생성하세요.")


# ══════════════════════════════════════════════════════════════
# 탭 3: 콘텐츠 직접 입력 테스트
# ══════════════════════════════════════════════════════════════
with tab_test:
    st.subheader("콘텐츠 직접 입력 SEO 분석")
    st.caption("HTML 또는 평문을 붙여넣으면 즉시 SEO 분석을 수행합니다.")

    test_keyword = st.text_input("타겟 키워드", key="test_keyword", placeholder="예: 강남 카페")

    test_title = st.text_input("제목", key="test_title", placeholder="블로그 제목 입력")

    test_content = st.text_area(
        "본문 (HTML 또는 평문)",
        height=300,
        key="test_content",
        placeholder="<h2>소제목</h2>\n<p>본문 내용...</p>",
    )

    test_tags_input = st.text_input(
        "태그 (쉼표 구분)",
        key="test_tags",
        placeholder="카페, 강남, 추천",
    )
    test_tags = [t.strip() for t in test_tags_input.split(",") if t.strip()]

    test_image_count = st.number_input("이미지 수", 0, 30, 0, key="test_images")

    test_profile = st.selectbox(
        "프로파일",
        list(PROFILE_LABELS.keys()),
        format_func=lambda x: PROFILE_LABELS.get(x, x),
        key="test_profile",
    )

    if st.button("🔍 분석 실행", type="primary", key="run_test_analysis"):
        if not test_content:
            st.error("본문을 입력하세요.")
        else:
            # HTML 태그가 없으면 <p> 래핑
            if "<" not in test_content:
                test_content = "<p>" + test_content.replace("\n\n", "</p><p>") + "</p>"

            test_draft = {
                "title": test_title,
                "content": test_content,
                "tags": test_tags,
                "summary": "",
            }

            report = validate_seo(test_draft, test_keyword, test_image_count, profile=test_profile)

            st.divider()

            # 종합 점수
            grade_colors = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
            m_cols = st.columns(3)
            with m_cols[0]:
                st.metric("SEO 점수", f"{report['score']}/100")
            with m_cols[1]:
                st.metric("등급", f"{grade_colors.get(report['grade'], '⚪')} {report['grade']}")
            with m_cols[2]:
                st.metric("프로파일", PROFILE_LABELS.get(test_profile, test_profile))

            # AI 안전 경고
            ai_check = report["checks"].get("ai_safety", {})
            if ai_check.get("score", 100) < 40:
                st.error("⚠️ AI 생성 콘텐츠 탐지 위험이 높습니다!")

            # 항목별 상세
            check_labels = {
                "title": "📌 제목", "body_length": "📏 본문 길이",
                "keyword_density": "🔑 키워드 밀도", "heading_structure": "📑 헤딩 구조",
                "images": "🖼️ 이미지", "hashtags": "#️⃣ 해시태그",
                "readability": "📖 가독성", "experience_signals": "💡 경험 정보",
                "information_depth": "📚 정보 충실성", "ai_safety": "🤖 AI 안전",
            }

            detail_cols = st.columns(4)
            for i, (key, label) in enumerate(check_labels.items()):
                check = report["checks"].get(key)
                if not check:
                    continue
                icon = "✅" if check["pass"] else "❌"
                with detail_cols[i % 4]:
                    with st.expander(f"{icon} {label} ({check['score']}점)"):
                        st.caption(check["message"])
                        if check.get("suggestions"):
                            for s in check["suggestions"]:
                                st.markdown(f"- {s}")
                        # 상세 데이터 표시 (새 항목)
                        if check.get("details"):
                            with st.container():
                                st.json(check["details"])


# ══════════════════════════════════════════════════════════════
# 탭 4: 이력 일괄 분석
# ══════════════════════════════════════════════════════════════
with tab_batch:
    st.subheader("이력 일괄 SEO 분석")
    st.caption("모든 이력 파일을 선택한 프로파일로 재분석합니다.")

    batch_profile = st.selectbox(
        "분석 프로파일",
        list(PROFILE_LABELS.keys()),
        format_func=lambda x: PROFILE_LABELS.get(x, x),
        key="batch_profile",
    )

    batch_keyword = st.text_input("공통 키워드 (선택)", key="batch_keyword", placeholder="비워두면 키워드 검증 제외")

    if st.button("📊 일괄 분석 실행", key="run_batch"):
        history = _load_history_drafts()
        if not history:
            st.warning("이력 파일이 없습니다.")
        else:
            results = []
            progress = st.progress(0, text="분석 중...")
            for i, (name, draft) in enumerate(history):
                report = validate_seo(draft, batch_keyword, 0, profile=batch_profile)
                results.append({
                    "파일": name,
                    "제목": draft.get("title", "")[:30],
                    "점수": report["score"],
                    "등급": report["grade"],
                    "가독성": report["checks"]["readability"]["score"],
                    "경험": report["checks"]["experience_signals"]["score"],
                    "정보": report["checks"]["information_depth"]["score"],
                    "AI안전": report["checks"]["ai_safety"]["score"],
                })
                progress.progress((i + 1) / len(history), text=f"{i+1}/{len(history)} 분석 완료")
            progress.empty()

            df = pd.DataFrame(results)
            st.dataframe(df, hide_index=True, use_container_width=True)

            # 요약 메트릭
            st.divider()
            summary_cols = st.columns(4)
            with summary_cols[0]:
                st.metric("평균 점수", f"{df['점수'].mean():.1f}")
            with summary_cols[1]:
                st.metric("최고 점수", f"{df['점수'].max()}")
            with summary_cols[2]:
                st.metric("최저 점수", f"{df['점수'].min()}")
            with summary_cols[3]:
                a_count = (df["등급"] == "A").sum()
                st.metric("A등급 비율", f"{a_count}/{len(df)}")

            # 가장 약한 항목 분석
            weak_cols = ["가독성", "경험", "정보", "AI안전"]
            avg_scores = {col: df[col].mean() for col in weak_cols}
            weakest = min(avg_scores, key=avg_scores.get)
            st.info(f"전체적으로 가장 부족한 항목: **{weakest}** (평균 {avg_scores[weakest]:.1f}점)")

            # 점수 분포 차트
            st.bar_chart(df.set_index("제목")["점수"])

            # CSV 다운로드
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 CSV 다운로드",
                data=csv,
                file_name="seo_batch_analysis.csv",
                mime="text/csv",
            )
