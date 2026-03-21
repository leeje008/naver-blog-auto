"""generator 모듈 유닛 테스트."""

from core.generator import _parse_json_response, _strip_markdown_fences, _try_repair_json


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

    def test_markdown_code_block_no_language(self):
        raw = '```\n{"title": "제목", "content": "본문", "tags": [], "summary": ""}\n```'
        result = _parse_json_response(raw)
        assert result["title"] == "제목"

    def test_json_with_nested_html_braces(self):
        raw = '{"title": "제목", "content": "<p style=\\"color: red\\">본문</p>", "tags": [], "summary": ""}'
        result = _parse_json_response(raw)
        assert result["title"] == "제목"

    def test_truncated_json_repair(self):
        """응답이 잘린 불완전 JSON 복구."""
        raw = '{"title": "제목", "content": "<p>본문이 여기서 잘'
        result = _parse_json_response(raw)
        # 복구되어 title은 추출 가능
        assert result["title"] == "제목"

    def test_truncated_json_with_fence(self):
        raw = '```json\n{"title": "제목", "content": "<p>잘림'
        result = _parse_json_response(raw)
        assert result["title"] == "제목"

    def test_markdown_fence_with_extra_whitespace(self):
        raw = '  ```json  \n{"title": "공백", "content": "본문", "tags": [], "summary": ""}\n```  '
        result = _parse_json_response(raw)
        assert result["title"] == "공백"


class TestStripMarkdownFences:
    def test_json_fence(self):
        assert _strip_markdown_fences('```json\n{"a":1}\n```') == '{"a":1}'

    def test_plain_fence(self):
        assert _strip_markdown_fences('```\n{"a":1}\n```') == '{"a":1}'

    def test_no_fence(self):
        assert _strip_markdown_fences('{"a":1}') == '{"a":1}'


class TestTryRepairJson:
    def test_missing_closing_brace(self):
        result = _try_repair_json('{"title": "제목"')
        assert result is not None
        assert result["title"] == "제목"

    def test_missing_closing_bracket(self):
        result = _try_repair_json('{"tags": ["a", "b"')
        assert result is not None
        assert result["tags"] == ["a", "b"]

    def test_missing_closing_quote(self):
        result = _try_repair_json('{"title": "제목')
        assert result is not None
        assert result["title"] == "제목"

    def test_completely_broken(self):
        result = _try_repair_json("not json at all")
        assert result is None
