"""image_utils 모듈 유닛 테스트."""

import io

from PIL import Image

from core.image_utils import (
    ImageProcessingError,
    _build_alt_text,
    resize_image,
    validate_image,
)


def _create_test_image(width: int = 1200, height: int = 800, fmt: str = "JPEG") -> bytes:
    """테스트용 이미지 바이트 생성."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


class TestResizeImage:
    def test_resize_large_image(self):
        img_bytes = _create_test_image(1200, 800)
        result = resize_image(img_bytes, max_width=860)
        img = Image.open(io.BytesIO(result))
        assert img.width == 860

    def test_keep_small_image(self):
        img_bytes = _create_test_image(400, 300)
        result = resize_image(img_bytes, max_width=860)
        img = Image.open(io.BytesIO(result))
        assert img.width == 400

    def test_invalid_bytes_returns_original(self):
        bad_bytes = b"not an image"
        result = resize_image(bad_bytes)
        assert result == bad_bytes


class TestValidateImage:
    def test_valid_jpeg(self):
        img_bytes = _create_test_image(100, 100, "JPEG")
        img = validate_image(img_bytes)
        assert img.size == (100, 100)

    def test_valid_png(self):
        img_bytes = _create_test_image(100, 100, "PNG")
        img = validate_image(img_bytes)
        assert img.size == (100, 100)

    def test_invalid_bytes_raises(self):
        try:
            validate_image(b"not an image")
            assert False, "Expected ImageProcessingError"
        except ImageProcessingError:
            pass


class TestBuildAltText:
    def test_with_keyword_and_description(self):
        alt = _build_alt_text(0, ["카페 내부 사진"], "강남 카페")
        assert "강남 카페" in alt
        assert "카페 내부 사진" in alt

    def test_keyword_already_in_description(self):
        alt = _build_alt_text(0, ["강남 카페 추천 장소"], "강남 카페")
        assert alt == "강남 카페 추천 장소"

    def test_no_description(self):
        alt = _build_alt_text(0, [], "강남 카페")
        assert "강남 카페" in alt

    def test_long_alt_truncated(self):
        long_desc = "아" * 60
        alt = _build_alt_text(0, [long_desc], "키워드")
        assert len(alt) <= 50

    def test_no_keyword_no_description(self):
        alt = _build_alt_text(2, [], "")
        assert "image_3" in alt
