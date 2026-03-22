"""글 작성 페이지 — 입력 + 생성 + 블로그 스타일 미리보기 통합."""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from core.generator import generate_draft_stream, _parse_json_response
from core.image_utils import analyze_image, build_image_html, resize_image
from core.llm_client import LLMClient
from core.publisher import inject_images
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
with st.expander("🖼️ 이미지 업로드 (선택사항)"):
    uploaded_images = st.file_uploader(
        "이미지 업로드 (순서대로)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )

    image_descriptions = []
    if uploaded_images:
        # 이미지 수 변경 시 orphan 세션 키 정리
        for key in list(st.session_state.keys()):
            if key.startswith("img_desc_"):
                try:
                    idx = int(key.split("_")[-1])
                    if idx >= len(uploaded_images):
                        del st.session_state[key]
                except ValueError:
                    pass

        auto_analyze = st.toggle("🔍 Vision 모델로 이미지 자동 분석", value=False)

        if auto_analyze and st.button("📷 전체 이미지 분석", key="btn_analyze_all"):
            model = st.session_state.get("llm_model", "qwen3.5:27b")
            vision_client = LLMClient(model=model)
            kw = st.session_state.get("target_keyword", target_keyword)
            for i, img_file in enumerate(uploaded_images):
                with st.spinner(f"이미지 {i + 1} 분석 중..."):
                    raw = img_file.read()
                    img_file.seek(0)
                    desc = analyze_image(vision_client, raw, kw)
                    if desc:
                        st.session_state[f"img_desc_{i}"] = desc
                    else:
                        st.session_state[f"img_desc_{i}"] = ""
                        st.warning(f"이미지 {i + 1} 자동 분석 실패. 직접 입력해주세요.")

        st.caption("각 이미지에 대한 설명을 입력하거나 자동 분석 결과를 수정하세요.")
        for i, img_file in enumerate(uploaded_images):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(img_file, width=200)
            with col2:
                default_desc = st.session_state.get(f"img_desc_{i}", "")
                desc = st.text_input(
                    f"이미지 {i + 1} 설명",
                    key=f"img_desc_{i}",
                    value=default_desc,
                    placeholder="예: 카페 내부 인테리어 사진",
                )
                image_descriptions.append(desc)

# ── 초안 생성 ────────────────────────────────────────────────
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
        img_descs = []
        if uploaded_images:
            for img_file in uploaded_images:
                raw = img_file.read()
                resized = resize_image(raw)
                image_bytes_list.append(resized)
            img_descs = image_descriptions
        else:
            img_descs = []

        img_html_tags = (
            build_image_html(image_bytes_list, img_descs, target_keyword)
            if image_bytes_list
            else []
        )

        try:
            model = st.session_state.get("llm_model", "qwen3.5:27b")
            llm_client = LLMClient(model=model)

            with st.spinner("블로그 글 생성 중..."):
                stream = generate_draft_stream(
                    llm_client=llm_client,
                    target_keyword=target_keyword,
                    image_descriptions=img_descs,
                    reference_posts=references,
                )

                # 스트리밍 수집 (UI에 raw 표시 안 함)
                raw_chunks = []
                for token in stream:
                    raw_chunks.append(token)

                raw_text = "".join(raw_chunks)

            result = _parse_json_response(raw_text)

            # 세션 저장
            st.session_state.generated = result
            st.session_state.image_bytes_list = image_bytes_list
            st.session_state.image_html_tags = img_html_tags
            st.session_state.image_descriptions = img_descs
            st.session_state.target_keyword = target_keyword
            st.session_state.revision_history = [result.copy()]

            # 이력 저장
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_path = HISTORY_DIR / f"{ts}.json"
            history_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            st.rerun()

        except Exception as e:
            st.error(f"생성 실패: {e}")

# ── 블로그 스타일 미리보기 ──────────────────────────────────
if st.session_state.get("generated"):
    gen = st.session_state.generated
    image_html_tags = st.session_state.get("image_html_tags", [])

    st.divider()

    # 제목
    st.markdown(f"## {gen.get('title', '')}")

    # 태그
    tags = gen.get("tags", [])
    if tags:
        st.markdown(" ".join([f"`#{t}`" for t in tags]))

    st.divider()

    # 본문 — 선택/복사 가능한 블로그 스타일 렌더링
    content_html = gen.get("content", "")
    if image_html_tags:
        content_html = inject_images(content_html, image_html_tags)

    st.markdown(content_html, unsafe_allow_html=True)

    # 이미지 다운로드
    image_bytes_list = st.session_state.get("image_bytes_list", [])
    if image_bytes_list:
        st.divider()
        st.subheader("🖼️ 이미지 다운로드")
        st.caption("네이버 블로그 에디터에서 이미지를 직접 업로드하세요.")
        img_cols = st.columns(min(len(image_bytes_list), 4))
        for i, img_bytes in enumerate(image_bytes_list):
            with img_cols[i % 4]:
                st.image(img_bytes, width=150)
                st.download_button(
                    f"이미지 {i + 1}",
                    data=img_bytes,
                    file_name=f"blog_image_{i + 1}.jpg",
                    mime="image/jpeg",
                    key=f"dl_img_{i}",
                )

    st.divider()

    if st.button("🔄 재생성", width="stretch"):
        st.session_state.generated = None
        st.rerun()

    st.caption("SEO 분석 및 최적화는 '미리보기' 탭에서 확인하세요.")
