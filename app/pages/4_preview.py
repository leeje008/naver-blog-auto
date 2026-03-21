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
from core.publisher import NaverPublisher
from core.reference import load_references
from core.seo_validator import validate_seo

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

seo_report = validate_seo(gen, target_keyword, image_count)
score = seo_report["score"]
grade = seo_report["grade"]

# 등급별 색상
grade_colors = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
grade_icon = grade_colors.get(grade, "⚪")

# 종합 점수 표시
score_col, grade_col, action_col = st.columns([1, 1, 1])
with score_col:
    st.metric("SEO 점수", f"{score}/100")
with grade_col:
    st.metric("등급", f"{grade_icon} {grade}")
with action_col:
    seo_optimize = st.button("🚀 SEO 최적화", width="stretch")

# 항목별 체크리스트
checks = seo_report["checks"]
check_labels = {
    "title": "📌 제목",
    "body_length": "📏 본문 길이",
    "keyword_density": "🔑 키워드 밀도",
    "heading_structure": "📑 헤딩 구조",
    "images": "🖼️ 이미지",
    "hashtags": "#️⃣ 해시태그",
}

cols = st.columns(3)
for i, (key, label) in enumerate(check_labels.items()):
    check = checks[key]
    icon = "✅" if check["pass"] else "❌"
    with cols[i % 3]:
        with st.expander(f"{icon} {label} ({check['score']}점)"):
            st.caption(check["message"])
            if check["suggestions"]:
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

                st.caption("SEO 최적화 중...")

                stream = seo_optimize_draft_stream(
                    llm_client=llm_client,
                    original=gen,
                    seo_feedback=seo_feedback,
                    target_keyword=target_keyword,
                    reference_posts=references,
                )

                raw_text = st.write_stream(stream)
                optimized = _parse_json_response(raw_text)

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

                st.success("SEO 최적화 완료!")
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
    content_html = NaverPublisher.inject_images(content_html, image_html_tags)

st.html(content_html)

st.divider()

# ── 액션 버튼 ────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    if st.button("📋 HTML 복사", type="primary", width="stretch"):
        st.code(content_html, language="html")
        st.info("위 HTML을 복사하여 네이버 블로그 에디터에 붙여넣으세요.")

with col2:
    if st.button("🔄 재생성", width="stretch"):
        st.session_state.generated = None
        st.rerun()

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

            rev_stream_col, rev_stop_col = st.columns([4, 1])
            with rev_stream_col:
                st.caption("수정 중...")
            with rev_stop_col:
                rev_stop_btn = st.button("⏹ 중지", key="stop_revise")

            stream_area = st.empty()
            raw_chunks = []
            was_stopped = False

            stream = revise_draft_stream(
                llm_client=llm_client,
                original=gen,
                instruction=revision_text,
                reference_posts=references,
            )

            for token in stream:
                if rev_stop_btn:
                    was_stopped = True
                    break
                raw_chunks.append(token)
                stream_area.code("".join(raw_chunks), language=None)

            raw_text = "".join(raw_chunks)
            stream_area.empty()

            if was_stopped and not raw_text.strip():
                st.warning("수정이 중단되었습니다.")
            else:
                revised = _parse_json_response(raw_text)
                if was_stopped:
                    st.warning("중단되어 불완전한 결과일 수 있습니다.")

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
