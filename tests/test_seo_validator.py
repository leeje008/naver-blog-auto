"""seo_validator 모듈 유닛 테스트 — 기존 + 신규 4개 검증 항목 + 프로파일 시스템."""

from core.seo_validator import (
    SEO_PROFILES,
    _check_ai_safety,
    _check_experience_signals,
    _check_information_depth,
    _check_readability,
    validate_seo,
)


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


# ── 기존 validate_seo 테스트 ──────────────────────────────────


class TestValidateSeo:
    def test_returns_score_and_grade(self):
        draft = _make_draft()
        result = validate_seo(draft, "테스트 키워드", 3)
        assert "score" in result
        assert "grade" in result
        assert "checks" in result
        assert 0 <= result["score"] <= 100
        assert result["grade"] in ("A", "B", "C", "D")

    def test_checks_has_all_10_items(self):
        draft = _make_draft()
        result = validate_seo(draft, "테스트 키워드", 3)
        expected_keys = {
            "title", "body_length", "keyword_density", "heading_structure",
            "images", "hashtags", "readability", "experience_signals",
            "information_depth", "ai_safety",
        }
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


# ── 테스트용 샘플 콘텐츠 ─────────────────────────────────────

_NATURAL_HTML = """
<h2>직접 가본 강남 카페 추천</h2>
<p>저는 지난 주말에 강남역 근처 카페를 직접 방문해봤어요.
평소 커피를 좋아하는 저로서는 정말 기대가 컸거든요.
실제로 가보니 인테리어가 너무 예쁘더라고요.</p>
<p>특히 아메리카노가 맛있었는데, 가격은 약 5,000원 정도였어요.
방문 시간은 약 30분 정도면 충분해요. 좌석은 약 50석 정도 되는 것 같았어요.</p>
<ul><li>위치: 강남역 3번 출구</li><li>가격: 아메리카노 5,000원</li><li>분위기: 아늑하고 조용함</li></ul>
<h2>메뉴 비교</h2>
<p>다른 카페와 비교하면 가격 대비 맛이 좋은 편이에요.
반면 좌석 간격은 좀 좁은 편이라 아쉬웠어요.
장점은 커피 맛이 좋다는 것이고, 단점은 주차가 어렵다는 점이에요.</p>
<h2>총평</h2>
<p>개인적으로 다시 방문할 의향이 있어요. 여러분도 한번 가보세요!</p>
"""

_AI_LIKE_HTML = """
<h2>강남 카페 소개</h2>
<p>먼저 강남 카페에 대해 알아보겠습니다. 강남에는 다양한 카페가 있습니다. 이 글을 통해 강남 카페를 소개해 드리겠습니다.</p>
<p>다음으로 메뉴에 대해 살펴보겠습니다. 강남 카페의 메뉴는 다양합니다. 아메리카노부터 라떼까지 있습니다.</p>
<p>마지막으로 분위기에 대해 알아보겠습니다. 강남 카페의 분위기는 좋습니다. 인테리어가 깔끔합니다.</p>
<p>결론적으로 강남 카페는 추천할 만합니다. 참고하시기 바랍니다. 도움이 되셨으면 좋겠습니다.</p>
"""

_MINIMAL_HTML = "<p>짧은 글입니다.</p>"


# ── 가독성 분석 테스트 ────────────────────────────────────────


class TestCheckReadability:
    def test_optimal_sentence_length(self):
        """30~50자 문장이 많으면 적정 점수."""
        result = _check_readability(_NATURAL_HTML)
        assert result["score"] >= 50
        assert "avg_sentence_length" in result["details"]

    def test_too_long_sentences(self):
        """60자 이상 문장 → 감점."""
        long_html = "<p>" + "이것은 매우 긴 문장입니다 " * 10 + ".</p>" * 5
        result = _check_readability(long_html)
        assert result["score"] < 80

    def test_uniform_length_penalty(self):
        """균일한 문장 길이 → 리듬 부족."""
        uniform = "<p>" + ". ".join(["이것은 스무 글자의 문장입니다" for _ in range(20)]) + ".</p>"
        result = _check_readability(uniform)
        assert result["details"]["sentence_count"] >= 10

    def test_colloquial_ratio_detected(self):
        """구어체 비율 탐지."""
        result = _check_readability(_NATURAL_HTML)
        assert result["details"]["colloquial_ratio"] > 0

    def test_short_text_fails(self):
        """짧은 본문 → 분석 불가."""
        result = _check_readability(_MINIMAL_HTML)
        assert result["score"] == 0


# ── 경험 정보 감지 테스트 ────────────────────────────────────


class TestCheckExperienceSignals:
    def test_rich_experience_content(self):
        """경험 마커가 풍부하면 적정 점수."""
        result = _check_experience_signals(_NATURAL_HTML)
        assert result["score"] >= 60
        assert result["details"]["marker_count"] >= 3

    def test_no_personal_pronouns(self):
        """1인칭 대명사 없는 글."""
        impersonal = "<p>강남 카페가 좋다. 분위기도 좋다. 메뉴가 다양하다. 가격도 적당하다.</p>" * 5
        result = _check_experience_signals(impersonal)
        assert result["details"]["pronoun_count"] == 0

    def test_emotion_expressions(self):
        """감정 표현 포함."""
        result = _check_experience_signals(_NATURAL_HTML)
        assert result["details"]["emotion_count"] >= 1

    def test_short_text(self):
        result = _check_experience_signals(_MINIMAL_HTML)
        assert result["score"] == 0


# ── 정보 충실성 테스트 ───────────────────────────────────────


class TestCheckInformationDepth:
    def test_with_lists_and_data(self):
        """리스트 + 수치 데이터."""
        result = _check_information_depth(_NATURAL_HTML)
        assert result["score"] >= 50
        assert result["details"]["list_count"] >= 1
        assert result["details"]["data_count"] >= 1

    def test_no_structured_content(self):
        """구조화 없는 텍스트."""
        plain = "<p>카페에 갔다. 좋았다. 또 가고 싶다.</p>" * 10
        result = _check_information_depth(plain)
        assert result["details"]["list_count"] == 0

    def test_comparison_expressions(self):
        """비교 표현 포함."""
        result = _check_information_depth(_NATURAL_HTML)
        assert result["details"]["comparison_count"] >= 1

    def test_short_text(self):
        result = _check_information_depth(_MINIMAL_HTML)
        assert result["score"] == 0


# ── AI 콘텐츠 탐지 위험도 테스트 ─────────────────────────────


class TestCheckAiSafety:
    def test_natural_content(self):
        """자연스러운 글 → 낮은 위험."""
        result = _check_ai_safety(_NATURAL_HTML)
        assert result["score"] >= 60
        assert result["details"]["risk_level"] in ("안전", "낮음")

    def test_repetitive_starters(self):
        """반복 시작 패턴 탐지."""
        result = _check_ai_safety(_AI_LIKE_HTML)
        assert result["details"]["ai_start_ratio"] > 10

    def test_template_phrases(self):
        """템플릿 문구 탐지."""
        result = _check_ai_safety(_AI_LIKE_HTML)
        assert result["details"]["template_count"] >= 2

    def test_uniform_paragraphs(self):
        """균일한 문단 길이 → AI 의심."""
        uniform = "".join(f"<p>{'가' * 100}</p>" for _ in range(10))
        result = _check_ai_safety(uniform)
        assert result["score"] < 90


# ── SEO 프로파일 시스템 테스트 ────────────────────────────────


class TestSeoProfiles:
    def test_balanced_profile_weights_sum(self):
        total = sum(SEO_PROFILES["balanced"].values())
        assert abs(total - 1.0) < 0.01

    def test_keyword_focused_profile_weights_sum(self):
        total = sum(SEO_PROFILES["keyword_focused"].values())
        assert abs(total - 1.0) < 0.01

    def test_authenticity_profile_weights_sum(self):
        total = sum(SEO_PROFILES["authenticity"].values())
        assert abs(total - 1.0) < 0.01

    def test_all_profiles_have_same_keys(self):
        keys = set(SEO_PROFILES["balanced"].keys())
        for name, profile in SEO_PROFILES.items():
            assert set(profile.keys()) == keys, f"{name} 프로파일 키 불일치"

    def test_profile_comparison_same_content(self):
        """동일 콘텐츠, 다른 프로파일 → 다른 점수."""
        draft = {
            "title": "강남 카페 추천 직접 가본 후기",
            "content": _NATURAL_HTML,
            "tags": ["카페", "강남", "추천", "후기", "맛집"],
        }
        score_balanced = validate_seo(draft, "강남 카페", 3, profile="balanced")["score"]
        score_keyword = validate_seo(draft, "강남 카페", 3, profile="keyword_focused")["score"]
        score_auth = validate_seo(draft, "강남 카페", 3, profile="authenticity")["score"]
        scores = {score_balanced, score_keyword, score_auth}
        assert len(scores) >= 2, "프로파일에 따라 점수가 달라야 합니다"

    def test_validate_seo_returns_profile(self):
        draft = {"title": "테스트", "content": "<p>테스트 본문</p>", "tags": []}
        result = validate_seo(draft, "테스트", profile="authenticity")
        assert result["profile"] == "authenticity"

    def test_custom_weights(self):
        """사용자 정의 가중치가 프로파일보다 우선."""
        draft = {"title": "테스트 제목", "content": _NATURAL_HTML, "tags": ["테스트"]}
        custom = {k: 0.0 for k in SEO_PROFILES["balanced"]}
        custom["title"] = 1.0
        result = validate_seo(draft, "테스트", custom_weights=custom)
        assert result["score"] == result["checks"]["title"]["score"]
