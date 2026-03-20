"""seo_validator 모듈 유닛 테스트."""

from core.seo_validator import validate_seo


def _make_draft(title: str = "테스트 키워드 포함 블로그 제목", content: str = "", tags: list[str] | None = None) -> dict:
    if not content:
        content = (
            "<h2>첫 번째 소제목</h2>"
            "<p>" + "테스트 키워드를 포함한 본문 내용입니다. " * 50 + "</p>"
            "<h2>두 번째 소제목</h2>"
            "<p>" + "추가 본문 내용입니다. " * 50 + "</p>"
            "<h2>세 번째 소제목</h2>"
            "<p>" + "마무리 본문입니다. " * 30 + "</p>"
        )
    return {
        "title": title,
        "content": content,
        "tags": tags or ["테스트", "키워드", "블로그"],
        "summary": "테스트 요약",
    }


class TestValidateSeo:
    def test_returns_score_and_grade(self):
        draft = _make_draft()
        result = validate_seo(draft, "테스트 키워드", 3)
        assert "score" in result
        assert "grade" in result
        assert "checks" in result
        assert 0 <= result["score"] <= 100
        assert result["grade"] in ("A", "B", "C", "D")

    def test_checks_has_all_items(self):
        draft = _make_draft()
        result = validate_seo(draft, "테스트 키워드", 3)
        expected_keys = {"title", "body_length", "keyword_density", "heading_structure", "images", "hashtags"}
        assert set(result["checks"].keys()) == expected_keys

    def test_each_check_has_required_fields(self):
        draft = _make_draft()
        result = validate_seo(draft, "테스트 키워드", 3)
        for key, check in result["checks"].items():
            assert "pass" in check, f"{key} missing 'pass'"
            assert "score" in check, f"{key} missing 'score'"
            assert "message" in check, f"{key} missing 'message'"
            assert "suggestions" in check, f"{key} missing 'suggestions'"

    def test_empty_content_low_score(self):
        draft = {"title": "", "content": "", "tags": [], "summary": ""}
        result = validate_seo(draft, "키워드", 0)
        assert result["score"] < 50
        assert result["grade"] in ("C", "D")

    def test_no_keyword_in_title(self):
        draft = _make_draft(title="관련 없는 제목")
        result = validate_seo(draft, "테스트 키워드", 3)
        assert not result["checks"]["title"]["pass"]
