"""publisher 모듈 유닛 테스트."""

import pytest

from core.publisher import NaverPublisher


class TestNaverPublisherInit:
    def test_empty_blog_id_raises(self):
        with pytest.raises(ValueError, match="블로그 ID"):
            NaverPublisher("", "secret")

    def test_empty_password_raises(self):
        with pytest.raises(ValueError, match="API 연동 암호"):
            NaverPublisher("my_id", "")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            NaverPublisher("  ", "secret")

    def test_valid_init(self):
        pub = NaverPublisher("my_id", "my_secret")
        assert pub.blog_id == "my_id"

    def test_strips_whitespace(self):
        pub = NaverPublisher("  my_id  ", "  secret  ")
        assert pub.blog_id == "my_id"


class TestInjectImages:
    def test_inject_numbered_placeholders(self):
        html = "<p>시작</p>[IMAGE_1]<p>중간</p>[IMAGE_2]<p>끝</p>"
        tags = ['<img src="a.jpg" />', '<img src="b.jpg" />']
        result = NaverPublisher.inject_images(html, tags)
        assert "[IMAGE_1]" not in result
        assert "[IMAGE_2]" not in result
        assert 'src="a.jpg"' in result
        assert 'src="b.jpg"' in result

    def test_removes_unmatched_placeholders(self):
        html = "<p>시작</p>[IMAGE_1][IMAGE_5]<p>끝</p>"
        tags = ['<img src="a.jpg" />']
        result = NaverPublisher.inject_images(html, tags)
        assert "[IMAGE_5]" not in result

    def test_curly_brace_placeholders(self):
        html = "<p>시작</p>{{IMAGE_1}}<p>끝</p>"
        tags = ['<img src="a.jpg" />']
        result = NaverPublisher.inject_images(html, tags)
        assert "{{IMAGE_1}}" not in result
        assert 'src="a.jpg"' in result

    def test_get_post_url(self):
        pub = NaverPublisher("test_user", "secret")
        url = pub.get_post_url("12345")
        assert url == "https://blog.naver.com/test_user/12345"
