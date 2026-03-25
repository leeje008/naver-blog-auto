"""작성 이력 페이지 — 분석 대시보드 + 관리."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
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

# ── 데이터 로딩 & DataFrame 구성 ──────────────────────────────


def _load_all_history() -> list[dict]:
    """이력 파일 전체 로드 → dict 리스트."""
    items = []
    for hf in history_files:
        try:
            data = json.loads(hf.read_text(encoding="utf-8"))
        except Exception:
            continue

        # 파일명에서 타임스탬프 파싱
        stem = hf.stem
        ts_str = stem.split("_")[0] if "_" in stem else stem
        try:
            ts = datetime.strptime(ts_str, "%Y%m%d")
        except ValueError:
            try:
                ts = datetime.strptime(ts_str[:8], "%Y%m%d")
            except ValueError:
                ts = datetime.fromtimestamp(hf.stat().st_mtime)

        title = data.get("title", "")
        content = data.get("content", "")
        tags = data.get("tags", [])
        from bs4 import BeautifulSoup
        text = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
        char_count = len(text.replace(" ", "").replace("\n", ""))

        items.append({
            "filename": hf.name,
            "filepath": str(hf),
            "timestamp": ts,
            "month": ts.strftime("%Y-%m"),
            "title": title or "(제목 없음)",
            "tags": tags,
            "content_length": char_count,
            "seo_score": data.get("seo_score"),
            "is_revised": "_revised" in stem or "_seo" in stem,
        })
    return items


history_data = _load_all_history()
df = pd.DataFrame(history_data)

# ── 요약 메트릭 ──────────────────────────────────────────────
st.subheader("📊 요약")

now = datetime.now()
current_month = now.strftime("%Y-%m")

m_cols = st.columns(4)
with m_cols[0]:
    st.metric("총 작성 수", f"{len(df)}개")
with m_cols[1]:
    this_month = len(df[df["month"] == current_month]) if not df.empty else 0
    st.metric("이번 달", f"{this_month}개")
with m_cols[2]:
    avg_len = df["content_length"].mean() if not df.empty else 0
    st.metric("평균 글자 수", f"{avg_len:,.0f}자")
with m_cols[3]:
    scores = df["seo_score"].dropna()
    avg_seo = scores.mean() if not scores.empty else 0
    st.metric("평균 SEO 점수", f"{avg_seo:.0f}" if avg_seo else "-")

# ── 차트 ─────────────────────────────────────────────────────
if len(df) >= 2:
    st.subheader("📈 추이")
    chart_tabs = st.tabs(["월별 작성 수", "글자 수 추이", "태그 빈도"])

    with chart_tabs[0]:
        monthly = df.groupby("month").size().reset_index(name="작성 수")
        st.bar_chart(monthly.set_index("month"))

    with chart_tabs[1]:
        trend_df = df[["timestamp", "content_length"]].sort_values("timestamp")
        trend_df = trend_df.set_index("timestamp")
        trend_df.columns = ["글자 수"]
        st.line_chart(trend_df)

    with chart_tabs[2]:
        all_tags = []
        for tags_list in df["tags"]:
            if isinstance(tags_list, list):
                all_tags.extend(tags_list)
        if all_tags:
            tag_counts = Counter(all_tags).most_common(20)
            tag_df = pd.DataFrame(tag_counts, columns=["태그", "빈도"])
            st.bar_chart(tag_df.set_index("태그"))
        else:
            st.info("태그 데이터가 없습니다.")

# ── 필터/검색 ────────────────────────────────────────────────
st.divider()
st.subheader("🔍 이력 목록")

filter_cols = st.columns([2, 1])
with filter_cols[0]:
    search_text = st.text_input("제목 검색", key="history_search", placeholder="검색어 입력...")
with filter_cols[1]:
    all_tags_set = set()
    for tags in df["tags"]:
        if isinstance(tags, list):
            all_tags_set.update(tags)
    tag_filter = st.selectbox("태그 필터", ["전체"] + sorted(all_tags_set), key="history_tag_filter")

# 필터 적용
filtered = df.copy()
if search_text:
    filtered = filtered[filtered["title"].str.contains(search_text, case=False, na=False)]
if tag_filter != "전체":
    filtered = filtered[filtered["tags"].apply(lambda t: tag_filter in t if isinstance(t, list) else False)]

st.caption(f"{len(filtered)}개 이력")

# CSV 내보내기
if not filtered.empty:
    export_df = filtered[["timestamp", "title", "content_length", "seo_score", "is_revised"]].copy()
    export_df.columns = ["날짜", "제목", "글자수", "SEO점수", "수정본"]
    csv = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📊 CSV 내보내기", data=csv, file_name="blog_history.csv", mime="text/csv")

# ── 이력 목록 ────────────────────────────────────────────────
for _, row in filtered.iterrows():
    is_revised = row["is_revised"]
    seo_str = f" | SEO {row['seo_score']}점" if row["seo_score"] else ""
    label = f"{'🔄 ' if is_revised else ''}{row['title'][:40]} | {row['content_length']}자{seo_str}"

    with st.expander(label):
        st.markdown(f"**제목**: {row['title']}")
        st.markdown(f"**날짜**: {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        st.markdown(f"**글자 수**: {row['content_length']:,}자")
        if row["seo_score"]:
            st.markdown(f"**SEO 점수**: {row['seo_score']}점")
        if isinstance(row["tags"], list) and row["tags"]:
            st.markdown("**태그**: " + ", ".join([f"`#{t}`" for t in row["tags"]]))

        # 삭제 버튼
        if st.button("🗑️ 삭제", key=f"del_{row['filename']}"):
            Path(row["filepath"]).unlink(missing_ok=True)
            st.success("삭제되었습니다.")
            st.rerun()
