"""미리보기 페이지 — 수정 + 업로드."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.generator import revise_draft
from core.llm_client import LLMClient
from core.publisher import NaverPublisher

HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "history"

st.header("👁️ 미리보기")

if not st.session_state.get("generated"):
    st.info("먼저 '글 작성' 페이지에서 초안을 생성하세요.")
    st.stop()

gen = st.session_state.generated
image_html_tags = st.session_state.get("image_html_tags", [])

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
    if st.button("✅ 승인 & 업로드", type="primary", use_container_width=True):
        blog_id = st.session_state.get("naver_blog_id", "")
        api_secret = st.session_state.get("naver_api_secret", "")

        if not blog_id or not api_secret:
            st.error("설정 페이지에서 네이버 블로그 ID와 API 암호를 입력하세요.")
        else:
            with st.spinner("네이버 블로그에 업로드 중..."):
                try:
                    publisher = NaverPublisher(blog_id, api_secret)
                    post_id = publisher.publish(
                        title=gen["title"],
                        html=content_html,
                        tags=tags,
                    )
                    url = publisher.get_post_url(post_id)
                    st.success("업로드 완료!")
                    st.markdown(f"[📄 블로그에서 확인하기]({url})")
                except Exception as e:
                    st.error(f"업로드 실패: {e}")

with col2:
    if st.button("🔄 재생성", use_container_width=True):
        st.session_state.generated = None
        st.rerun()

# ── 수정 요청 ────────────────────────────────────────────────
st.divider()
st.subheader("✏️ 수정 요청")

revision_text = st.text_area(
    "수정 사항을 입력하세요",
    placeholder="예: 서론을 더 짧게 해주세요, 결론에 CTA를 추가해주세요",
)

if st.button("📝 수정 반영", use_container_width=True):
    if not revision_text:
        st.warning("수정 사항을 입력하세요.")
    else:
        with st.spinner("수정 중..."):
            try:
                model = st.session_state.get("llm_model", "qwen3.5:27b")
                llm_client = LLMClient(model=model)

                revised = revise_draft(
                    llm_client=llm_client,
                    original=gen,
                    instruction=revision_text,
                )

                st.session_state.generated = revised
                history = st.session_state.get("revision_history", [])
                history.append(revised.copy())
                st.session_state.revision_history = history

                # 이력 저장
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
