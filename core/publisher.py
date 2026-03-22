"""콘텐츠 HTML 처리 유틸리티."""

import re


def inject_images(content_html: str, image_html_tags: list[str]) -> str:
    """이미지 플레이스홀더를 실제 HTML로 교체."""
    result = content_html
    for i, img_tag in enumerate(image_html_tags, 1):
        wrap = f'<div style="text-align:center;margin:20px 0;">{img_tag}</div>'
        result = result.replace(f"[IMAGE_{i}]", wrap)
        result = result.replace(f"{{{{IMAGE_{i}}}}}", wrap)

    result = re.sub(r"\[IMAGE_\d+\]", "", result)
    result = re.sub(r"\{\{IMAGE_\d+\}\}", "", result)
    return result
