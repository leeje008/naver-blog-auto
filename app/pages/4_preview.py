"""미리보기 페이지 — SEO 대시보드 + 수정 + 업로드."""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.generator import (
    _parse_json_response,
    revise_draft_stream,
    seo_optimize_draft_stream,
)
from core.llm_client import LLMClient
from core.publisher import inject_images
from core.reference import load_references
from core.seo_validator import PROFILE_LABELS, SEO_PROFILES, validate_seo

HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "history"

st.header("👁️ 미리보기")

if not st.session_state.get("generated"):
    st.info("먼저 '글 작성' 페이지에서 초안을 생성하세요.")
    st.stop()

gen = st.session_state.generated
image_html_tags = st.session_state.get("image_html_tags", [])
target_keyword = st.session_state.get("target_keyword", "")
image_count = len(st.session_state.get("image_bytes_list", []))
references = load_references()  # 톤 & 매너 유지용

# ── SEO 대시보드 ──────────────────────────────────────────────
st.subheader("📊 SEO 분석")

# 프로파일 선택
profile_options = list(PROFILE_LABELS.keys())
profile_labels_display = list(PROFILE_LABELS.values())
default_profile = st.session_state.get("seo_profile", "balanced")
default_idx = profile_options.index(default_profile) if default_profile in profile_options else 0

selected_profile = st.selectbox(
    "SEO 프로파일",
    profile_options,
    index=default_idx,
    format_func=lambda x: PROFILE_LABELS.get(x, x),
    key="preview_seo_profile",
)

seo_report = validate_seo(gen, target_keyword, image_count, profile=selected_profile)
score = seo_report["score"]
grade = seo_report["grade"]

# 등급별 색상
grade_colors = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
grade_icon = grade_colors.get(grade, "⚪")

# 종합 점수 표시
score_col, grade_col, action_col = st.columns([1, 1, 1])
with score_col:
    prev_score = st.session_state.get("seo_before")
    delta = score - prev_score if prev_score is not None else None
    st.metric("SEO 점수", f"{score}/100", delta=f"{delta:+}점" if delta is not None else None)
with grade_col:
    st.metric("등급", f"{grade_icon} {grade}")
with action_col:
    seo_optimize = st.button("🚀 SEO 최적화", width="stretch")

# 최적화 전략 선택
strategy_map = {
    "균형 최적화": "balanced",
    "정보 충실도 강화": "depth",
    "경험 주입": "experience",
    "AI 안전성 강화": "human",
}
strategy_descriptions = {
    "균형 최적화": "SEO 분석 결과의 낮은 점수 항목을 전반적으로 개선",
    "정보 충실도 강화": "수치, 리스트, 비교 분석 등 구체적 데이터 추가",
    "경험 주입": "개인 경험, 감정 표현, 1인칭 시점 추가",
    "AI 안전성 강화": "반복 패턴 제거, 구어체 추가, 자연스러운 문체로 변환",
}
selected_strategy_label = st.selectbox(
    "최적화 전략",
    list(strategy_map.keys()),
    key="seo_strategy_select",
)
st.caption(strategy_descriptions[selected_strategy_label])

# AI 안전 경고
ai_check = seo_report["checks"].get("ai_safety", {})
if ai_check.get("score", 100) < 40:
    st.error("⚠️ AI 생성 콘텐츠 탐지 위험이 높습니다. 개인 경험을 추가하고 구어체를 섞어 자연스럽게 만드세요.")

# 항목별 체크리스트 (10개 항목, 4열)
checks = seo_report["checks"]
check_labels_map = {
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

cols = st.columns(4)
for i, (key, label) in enumerate(check_labels_map.items()):
    check = checks.get(key)
    if not check:
        continue
    icon = "✅" if check["pass"] else "❌"
    with cols[i % 4]:
        with st.expander(f"{icon} {label} ({check['score']}점)"):
            st.caption(check["message"])
            if check.get("suggestions"):
                for suggestion in check["suggestions"]:
                    st.markdown(f"- {suggestion}")

# SEO 최적화 버튼 처리
if seo_optimize:
    if not target_keyword:
        st.warning("타겟 키워드가 없습니다.")
    else:
        # 낮은 점수 항목의 피드백 수집
        feedback_items = []
        for key, check in checks.items():
            if not check["pass"] and check["suggestions"]:
                label = check_labels.get(key, key)
                for s in check["suggestions"]:
                    feedback_items.append(f"- {label}: {s}")

        if not feedback_items:
            st.success("이미 SEO 점수가 충분합니다!")
        else:
            seo_feedback = "\n".join(feedback_items)
            try:
                model = st.session_state.get("llm_model", "qwen3.5:27b")
                llm_client = LLMClient(model=model)
                strategy_key = strategy_map.get(selected_strategy_label, "balanced")

                with st.spinner(f"SEO 최적화 중... ({selected_strategy_label})"):
                    stream = seo_optimize_draft_stream(
                        llm_client=llm_client,
                        original=gen,
                        seo_feedback=seo_feedback,
                        target_keyword=target_keyword,
                        reference_posts=references,
                        strategy=strategy_key,
                    )
                    raw_chunks = []
                    for token in stream:
                        raw_chunks.append(token)
                    raw_text = "".join(raw_chunks)

                optimized = _parse_json_response(raw_text)

                # 최적화 전후 점수 비교
                new_seo = validate_seo(optimized, target_keyword, image_count)
                optimized["seo_score"] = new_seo["score"]

                st.session_state.generated = optimized
                history = st.session_state.get("revision_history", [])
                history.append(optimized.copy())
                st.session_state.revision_history = history

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                HISTORY_DIR.mkdir(parents=True, exist_ok=True)
                history_path = HISTORY_DIR / f"{ts}_seo.json"
                history_path.write_text(
                    json.dumps(optimized, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                delta = new_seo["score"] - score
                st.success(
                    f"SEO 최적화 완료! "
                    f"점수: {score} → {new_seo['score']} ({'+' if delta > 0 else ''}{delta}점)"
                )
                st.session_state.seo_before = score
                st.rerun()
            except Exception as e:
                st.error(f"SEO 최적화 실패: {e}")

st.divider()

# ── 미리보기 ─────────────────────────────────────────────────
st.markdown(f"### {gen.get('title', '')}")

tags = gen.get("tags", [])
if tags:
    st.markdown(" ".join([f"`#{t}`" for t in tags]))

st.divider()

# 이미지 삽입된 본문
content_html = gen.get("content", "")
if image_html_tags:
    content_html = inject_images(content_html, image_html_tags)

st.html(content_html)

st.divider()

# ── 내보내기 ─────────────────────────────────────────────────
st.subheader("📥 내보내기")
export_cols = st.columns(4)

with export_cols[0]:
    st.download_button(
        "📄 HTML",
        data=content_html,
        file_name=f"{gen.get('title', 'blog')[:20]}.html",
        mime="text/html",
        key="dl_html",
    )

with export_cols[1]:
    from bs4 import BeautifulSoup as BS4
    plain_text = BS4(content_html, "html.parser").get_text("\n", strip=True)
    st.download_button(
        "📝 텍스트",
        data=plain_text,
        file_name=f"{gen.get('title', 'blog')[:20]}.txt",
        mime="text/plain",
        key="dl_txt",
    )

with export_cols[2]:
    def _html_to_markdown(html: str) -> str:
        soup = BS4(html, "html.parser")
        md_lines = []
        for el in soup.descendants:
            if el.name == "h1":
                md_lines.append(f"\n# {el.get_text(strip=True)}\n")
            elif el.name == "h2":
                md_lines.append(f"\n## {el.get_text(strip=True)}\n")
            elif el.name == "h3":
                md_lines.append(f"\n### {el.get_text(strip=True)}\n")
            elif el.name == "p":
                md_lines.append(f"\n{el.get_text(strip=True)}\n")
            elif el.name == "li":
                md_lines.append(f"- {el.get_text(strip=True)}")
        return "\n".join(md_lines).strip()

    md_text = _html_to_markdown(content_html)
    st.download_button(
        "📋 Markdown",
        data=md_text,
        file_name=f"{gen.get('title', 'blog')[:20]}.md",
        mime="text/markdown",
        key="dl_md",
    )

with export_cols[3]:
    if st.button("🔄 재생성", width="stretch"):
        st.session_state.generated = None
        st.rerun()

with st.expander("📋 HTML 소스 보기"):
    st.code(content_html, language="html")
    st.info("위 HTML을 복사하여 네이버 블로그 에디터에 붙여넣으세요.")

# ── 수정 요청 ────────────────────────────────────────────────
st.divider()
st.subheader("✏️ 수정 요청")

revision_text = st.text_area(
    "수정 사항을 입력하세요",
    placeholder="예: 서론을 더 짧게 해주세요, 결론에 CTA를 추가해주세요",
)

if st.button("📝 수정 반영", width="stretch"):
    if not revision_text:
        st.warning("수정 사항을 입력하세요.")
    else:
        try:
            model = st.session_state.get("llm_model", "qwen3.5:27b")
            llm_client = LLMClient(model=model)

            with st.spinner("수정 중..."):
                stream = revise_draft_stream(
                    llm_client=llm_client,
                    original=gen,
                    instruction=revision_text,
                    reference_posts=references,
                )
                raw_chunks = []
                for token in stream:
                    raw_chunks.append(token)
                raw_text = "".join(raw_chunks)

            revised = _parse_json_response(raw_text)

            revised_seo = validate_seo(revised, target_keyword, image_count)
            revised["seo_score"] = revised_seo["score"]

            st.session_state.generated = revised
            history = st.session_state.get("revision_history", [])
            history.append(revised.copy())
            st.session_state.revision_history = history

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            history_path = HISTORY_DIR / f"{ts}_revised.json"
            history_path.write_text(
                json.dumps(revised, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            st.success("수정 완료!")
            st.rerun()
        except Exception as e:
            st.error(f"수정 실패: {e}")

# ── 수정 이력 ────────────────────────────────────────────────
revision_history = st.session_state.get("revision_history", [])
if len(revision_history) > 1:
    with st.expander(f"📜 수정 이력 ({len(revision_history)}개 버전)"):
        for i, ver in enumerate(revision_history):
            st.caption(f"버전 {i + 1}: {ver.get('title', '')[:40]}...")
