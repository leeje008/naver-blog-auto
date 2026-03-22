"""이미지 처리 유틸리티 모듈."""

import base64
import io
import logging

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

MAX_WIDTH = 860  # 네이버 블로그 본문 최대 너비
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


class ImageProcessingError(Exception):
    """이미지 처리 실패 시 발생."""


def validate_image(image_bytes: bytes) -> Image.Image:
    """이미지 바이트를 검증하고 PIL Image 객체 반환."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        # verify() 후 재오픈 필요
        img = Image.open(io.BytesIO(image_bytes))
    except UnidentifiedImageError:
        raise ImageProcessingError("인식할 수 없는 이미지 형식입니다.")
    except Exception as e:
        raise ImageProcessingError(f"이미지 파일이 손상되었습니다: {e}")

    fmt = (img.format or "").upper()
    if fmt and fmt not in SUPPORTED_FORMATS:
        raise ImageProcessingError(
            f"지원하지 않는 이미지 형식입니다: {fmt}. "
            f"지원 형식: {', '.join(SUPPORTED_FORMATS)}"
        )
    return img


def resize_image(image_bytes: bytes, max_width: int = MAX_WIDTH) -> bytes:
    """이미지를 네이버 블로그 최적 크기로 리사이즈."""
    try:
        img = validate_image(image_bytes)
    except ImageProcessingError:
        logger.warning("이미지 검증 실패, 원본 그대로 사용합니다.")
        return image_bytes

    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # RGBA → RGB 변환 (JPEG 저장용)
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background

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
            logger.debug("이미지 %d 포맷 감지 실패, jpeg으로 기본 설정", i + 1)

        alt_text = _build_alt_text(i, image_descriptions, target_keyword)
        html_tags.append(
            f'<img src="data:image/{ext};base64,{b64}" '
            f'alt="{alt_text}" style="max-width:100%;" />'
        )
    return html_tags


def analyze_image(llm_client, image_bytes: bytes, target_keyword: str = "") -> str:
    """Vision 모델로 이미지를 분석하여 블로그용 설명을 자동 생성.

    Args:
        llm_client: LLMClient 인스턴스 (Vision 지원 모델 필요)
        image_bytes: 이미지 바이트
        target_keyword: 타겟 키워드 (설명에 자연스럽게 반영)

    Returns:
        이미지 설명 문자열 (30~80자)
    """
    system_prompt = (
        "당신은 네이버 블로그 이미지 설명 전문가입니다. "
        "이미지를 보고 블로그 글에 어울리는 간결한 설명을 한국어로 작성하세요. "
        "30~80자 이내로 작성하고, 추가 설명 없이 설명만 출력하세요."
    )
    keyword_hint = f" 타겟 키워드 '{target_keyword}'와 관련지어 설명해주세요." if target_keyword else ""
    user_prompt = f"이 이미지를 블로그 글에 사용할 설명을 작성해주세요.{keyword_hint}"

    try:
        result = llm_client.generate_with_image(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            images=[image_bytes],
        )
        desc = result.strip().strip('"').strip("'")
        if len(desc) > 80:
            desc = desc[:77] + "..."
        return desc
    except Exception as e:
        logger.warning("Vision 이미지 분석 실패: %s", e)
        return ""


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
