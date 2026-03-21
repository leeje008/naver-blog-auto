"""글 작성 페이지 — 이미지 업로드 + 초안 생성."""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.generator import generate_draft_stream, _parse_json_response
from core.image_utils import build_image_html, resize_image
from core.llm_client import LLMClient
from core.reference import load_references

HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

st.header("📝 글 작성")

# ── 타겟 키워드 ──────────────────────────────────────────────
default_keyword = st.session_state.get("target_keyword", "")
target_keyword = st.text_input(
    "타겟 키워드",
    value=default_keyword,
    placeholder="키워드 페이지에서 선택하거나 직접 입력",
)

# ── 이미지 업로드 ────────────────────────────────────────────
st.subheader("🖼️ 이미지 업로드")
uploaded_images = st.file_uploader(
    "이미지 업로드 (순서대로)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

# 각 이미지에 대한 설명 입력
image_descriptions = []
if uploaded_images:
    st.caption("각 이미지에 대한 간단한 설명을 입력하세요.")
    for i, img_file in enumerate(uploaded_images):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(img_file, width=200)
        with col2:
            desc = st.text_input(
                f"이미지 {i + 1} 설명",
                key=f"img_desc_{i}",
                placeholder="예: 카페 내부 인테리어 사진",
            )
            image_descriptions.append(desc)

# ── 초안 생성 ────────────────────────────────────────────────
st.divider()

if st.button("🚀 초안 생성", type="primary", width="stretch"):
    if not target_keyword:
        st.error("타겟 키워드를 입력하세요.")
    else:
        references = load_references()
        if not references:
            st.warning("레퍼런스 글이 없습니다. 설정 페이지에서 등록하면 더 나은 결과를 얻을 수 있습니다.")
            references = []

        # 이미지 처리
        image_bytes_list = []
        if uploaded_images:
            for img_file in uploaded_images:
                raw = img_file.read()
                resized = resize_image(raw)
                image_bytes_list.append(resized)

        # 이미지 HTML 태그 생성 (SEO 최적화 ALT 텍스트 포함)
        img_html_tags = (
            build_image_html(image_bytes_list, image_descriptions, target_keyword)
            if image_bytes_list
            else []
        )

        try:
            model = st.session_state.get("llm_model", "qwen3.5:27b")
            llm_client = LLMClient(model=model)

            st.caption("생성 중... (페이지를 이동하면 중단됩니다)")

            stream = generate_draft_stream(
                llm_client=llm_client,
                target_keyword=target_keyword,
                image_descriptions=image_descriptions,
                reference_posts=references,
            )

            raw_text = st.write_stream(stream)

            result = _parse_json_response(raw_text)

            # 세션 저장
            st.session_state.generated = result
            st.session_state.image_bytes_list = image_bytes_list
            st.session_state.image_html_tags = img_html_tags
            st.session_state.image_descriptions = image_descriptions
            st.session_state.target_keyword = target_keyword
            st.session_state.revision_history = [result.copy()]

            # 이력 저장
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_path = HISTORY_DIR / f"{ts}.json"
            history_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            st.success("초안 생성 완료! '미리보기' 페이지에서 확인하세요.")

        except Exception as e:
            st.error(f"생성 실패: {e}")

# ── 현재 생성 상태 표시 ─────────────────────────────────────
if st.session_state.get("generated"):
    gen = st.session_state.generated
    st.divider()
    st.info(f"생성된 초안: **{gen.get('title', '제목 없음')}**")
    st.caption("'미리보기' 페이지에서 전체 내용을 확인하고 수정/업로드할 수 있습니다.")
