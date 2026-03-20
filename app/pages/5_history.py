"""작성 이력 페이지."""

import json
from pathlib import Path

import streamlit as st

HISTORY_DIR = Path(__file__).parent.parent.parent / "data" / "history"

st.header("📜 작성 이력")

if not HISTORY_DIR.exists():
    st.info("아직 작성 이력이 없습니다.")
    st.stop()

history_files = sorted(HISTORY_DIR.glob("*.json"), reverse=True)

if not history_files:
    st.info("아직 작성 이력이 없습니다.")
    st.stop()

st.caption(f"총 {len(history_files)}개 이력")

for hf in history_files:
    try:
        data = json.loads(hf.read_text(encoding="utf-8"))
    except Exception:
        continue

    title = data.get("title", "제목 없음")
    tags = data.get("tags", [])
    summary = data.get("summary", "")
    is_revised = "_revised" in hf.stem
    label = f"{'🔄 ' if is_revised else ''}{hf.stem} | {title[:40]}"

    with st.expander(label):
        st.markdown(f"**제목**: {title}")
        if tags:
            st.markdown("**태그**: " + ", ".join([f"`#{t}`" for t in tags]))
        if summary:
            st.markdown(f"**요약**: {summary}")

        st.divider()
        content = data.get("content", "")
        if content:
            st.html(content[:2000])
            if len(content) > 2000:
                st.caption("(본문이 길어 일부만 표시)")
