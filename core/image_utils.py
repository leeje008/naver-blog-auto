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


def build_image_html(image_bytes_list: list[bytes]) -> list[str]:
    """이미지들을 HTML img 태그로 변환."""
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
        html_tags.append(
            f'<img src="data:image/{ext};base64,{b64}" '
            f'alt="image_{i + 1}" style="max-width:100%;" />'
        )
    return html_tags
