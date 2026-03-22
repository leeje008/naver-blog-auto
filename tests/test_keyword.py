"""keyword 모듈 유닛 테스트."""

from unittest.mock import MagicMock

from core.keyword import KeywordEngine


class TestRelativeCompetition:
    """_relative_competition 메서드 테스트."""

    def setup_method(self):
        self.engine = KeywordEngine(llm_client=MagicMock())

    def test_very_low(self):
        assert self.engine._relative_competition(0.005) == "매우 낮음"

    def test_low(self):
        assert self.engine._relative_competition(0.05) == "낮음"

    def test_medium(self):
        assert self.engine._relative_competition(0.15) == "중간"

    def test_high(self):
        assert self.engine._relative_competition(0.4) == "높음"

    def test_very_high(self):
        assert self.engine._relative_competition(0.7) == "매우 높음"

    def test_none_returns_unknown(self):
        assert self.engine._relative_competition(None) == "알수없음"
