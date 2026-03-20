"""keyword 모듈 유닛 테스트."""

from unittest.mock import MagicMock

from core.keyword import KeywordEngine


class TestCompetitionLevel:
    """_competition_level 메서드 테스트."""

    def setup_method(self):
        self.engine = KeywordEngine(llm_client=MagicMock())

    def test_low_competition(self):
        assert self.engine._competition_level(500) == "낮음"
        assert self.engine._competition_level(0) == "낮음"
        assert self.engine._competition_level(999) == "낮음"

    def test_medium_competition(self):
        assert self.engine._competition_level(1000) == "중간"
        assert self.engine._competition_level(3000) == "중간"
        assert self.engine._competition_level(4999) == "중간"

    def test_high_competition(self):
        assert self.engine._competition_level(5000) == "높음"
        assert self.engine._competition_level(100000) == "높음"

    def test_none_returns_unknown(self):
        assert self.engine._competition_level(None) == "알수없음"
