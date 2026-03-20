"""generator 모듈 유닛 테스트."""

from core.generator import _parse_json_response


class TestParseJsonResponse:
    """_parse_json_response 함수 테스트."""

    def test_valid_json(self):
        raw = '{"title": "테스트", "content": "<p>본문</p>", "tags": ["태그1"], "summary": "요약"}'
        result = _parse_json_response(raw)
        assert result["title"] == "테스트"
        assert result["content"] == "<p>본문</p>"
        assert result["tags"] == ["태그1"]

    def test_json_with_surrounding_text(self):
        raw = '여기 결과입니다:\n{"title": "제목", "content": "본문", "tags": [], "summary": ""}\n끝'
        result = _parse_json_response(raw)
        assert result["title"] == "제목"

    def test_invalid_json_fallback(self):
        raw = "이건 JSON이 아닌 평문 텍스트입니다."
        result = _parse_json_response(raw)
        assert result["title"] == ""
        assert result["content"] == raw
        assert result["tags"] == []

    def test_empty_string(self):
        result = _parse_json_response("")
        assert result["content"] == ""

    def test_markdown_code_block_json(self):
        raw = '```json\n{"title": "마크다운", "content": "본문", "tags": ["t"], "summary": "s"}\n```'
        result = _parse_json_response(raw)
        assert result["title"] == "마크다운"
