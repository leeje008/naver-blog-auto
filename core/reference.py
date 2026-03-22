"""레퍼런스 블로그 글 크롤링 및 관리 모듈."""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

import requests
from bs4 import BeautifulSoup, FeatureNotFound

logger = logging.getLogger(__name__)


REFERENCES_PATH = Path(__file__).parent.parent / "data" / "references" / "references.json"


def crawl_reference(url: str) -> dict:
    """블로그 글 URL에서 Reference 데이터 수집.

    Returns:
        {"url", "title", "content" (최대 1500자), "image_positions"}
    """
    # URL에서 blog_id, log_no 추출
    match = re.search(r"blog\.naver\.com/([^/?]+)/(\d+)", url)
    if not match:
        match = re.search(r"blogId=([^&]+).*logNo=(\d+)", url)
        if not match:
            raise ValueError(f"유효한 블로그 글 URL이 아닙니다: {url}")
    blog_id, log_no = match.group(1), match.group(2)

    fetch_url = (
        f"https://blog.naver.com/PostView.naver?"
        f"blogId={blog_id}&logNo={log_no}"
        f"&redirect=Dlog&widgetTypeCall=true&directAccess=true"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    resp = requests.get(fetch_url, headers=headers, timeout=10)
    resp.raise_for_status()

    try:
        soup = BeautifulSoup(resp.text, "lxml")
    except FeatureNotFound:
        logger.info("lxml 파서 미설치. html.parser로 대체합니다.")
        soup = BeautifulSoup(resp.text, "html.parser")

    # 제목
    title_tag = soup.select_one(".se-title-text, .pcol1, .se_title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # 본문 + 이미지 위치
    content_area = soup.select_one(
        ".se-main-container, #postViewArea, .se_component_wrap"
    )
    text_content = ""
    image_positions = []
    paragraph_idx = 0

    if not content_area:
        logger.warning("본문 영역을 찾을 수 없습니다: %s (DOM 구조 변경 가능)", url)

    if content_area:
        for child in content_area.children:
            if not hasattr(child, "select"):
                continue
            has_img = bool(child.select("img.se-image-resource, img"))
            has_text = bool(child.select(".se-text-paragraph, p, span.se_textarea"))

            if has_img:
                image_positions.append(paragraph_idx)
            if has_text:
                text_content += child.get_text(strip=True) + "\n"
                paragraph_idx += 1

    return {
        "url": url,
        "title": title,
        "content": text_content.strip()[:1500],
        "image_positions": image_positions,
    }


def save_references(references: list[dict]) -> None:
    """레퍼런스 목록을 JSON으로 저장."""
    REFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"reference_posts": references}
    REFERENCES_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Streamlit 캐시 무효화
    load_references.cache_clear()


@lru_cache(maxsize=1)
def load_references() -> list[dict]:
    """저장된 레퍼런스 목록 로드. 없으면 빈 리스트 반환."""
    if REFERENCES_PATH.exists():
        data = json.loads(REFERENCES_PATH.read_text(encoding="utf-8"))
        return data.get("reference_posts", [])
    return []
