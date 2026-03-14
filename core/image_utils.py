"""이미지 처리 유틸리티 모듈."""

import base64
import io

from PIL import Image


MAX_WIDTH = 860  # 네이버 블로그 본문 최대 너비


def resize_image(image_bytes: bytes, max_width: int = MAX_WIDTH) -> bytes:
    """이미지를 네이버 블로그 최적 크기로 리사이즈."""
    img = Image.open(io.BytesIO(image_bytes))

    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    fmt = "JPEG" if img.mode == "RGB" else "PNG"
    img.save(buf, format=fmt, quality=85)
    return buf.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    """이미지 바이트를 base64 문자열로 변환."""
    return base64.b64encode(image_bytes).decode("utf-8")


def build_image_html(
    image_bytes_list: list[bytes],
    image_descriptions: list[str] | None = None,
    target_keyword: str = "",
) -> list[str]:
    """이미지들을 SEO 최적화된 HTML img 태그로 변환.

    Args:
        image_bytes_list: 이미지 바이트 리스트
        image_descriptions: 각 이미지에 대한 설명 (ALT 텍스트용)
        target_keyword: 타겟 키워드 (ALT에 자연스럽게 포함)
    """
    html_tags = []
    for i, img_bytes in enumerate(image_bytes_list):
        b64 = image_to_base64(img_bytes)
        ext = "jpeg"
        try:
            img = Image.open(io.BytesIO(img_bytes))
            if img.format:
                ext = img.format.lower()
        except Exception:
            pass

        alt_text = _build_alt_text(i, image_descriptions, target_keyword)
        html_tags.append(
            f'<img src="data:image/{ext};base64,{b64}" '
            f'alt="{alt_text}" style="max-width:100%;" />'
        )
    return html_tags


def _build_alt_text(
    index: int,
    descriptions: list[str] | None,
    keyword: str,
) -> str:
    """SEO 최적화된 ALT 텍스트 생성 (20~50자, 키워드 포함).

    예: description="카페 내부 인테리어", keyword="강남 카페"
        → "강남 카페 - 분위기 좋은 내부 인테리어"
    """
    desc = ""
    if descriptions and index < len(descriptions):
        desc = descriptions[index].strip()

    if not desc:
        if keyword:
            return f"{keyword} 관련 이미지 {index + 1}"
        return f"image_{index + 1}"

    # 키워드가 설명에 이미 포함되어 있으면 그대로 사용
    if keyword and keyword in desc:
        alt = desc
    elif keyword:
        alt = f"{keyword} - {desc}"
    else:
        alt = desc

    # 50자 제한
    if len(alt) > 50:
        alt = alt[:47] + "..."

    return alt
