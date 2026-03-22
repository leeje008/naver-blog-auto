"""publisher 모듈(inject_images) 유닛 테스트."""

from core.publisher import inject_images


class TestInjectImages:
    def test_inject_numbered_placeholders(self):
        html = "<p>시작</p>[IMAGE_1]<p>중간</p>[IMAGE_2]<p>끝</p>"
        tags = ['<img src="a.jpg" />', '<img src="b.jpg" />']
        result = inject_images(html, tags)
        assert "[IMAGE_1]" not in result
        assert "[IMAGE_2]" not in result
        assert 'src="a.jpg"' in result
        assert 'src="b.jpg"' in result

    def test_removes_unmatched_placeholders(self):
        html = "<p>시작</p>[IMAGE_1][IMAGE_5]<p>끝</p>"
        tags = ['<img src="a.jpg" />']
        result = inject_images(html, tags)
        assert "[IMAGE_5]" not in result

    def test_curly_brace_placeholders(self):
        html = "<p>시작</p>{{IMAGE_1}}<p>끝</p>"
        tags = ['<img src="a.jpg" />']
        result = inject_images(html, tags)
        assert "{{IMAGE_1}}" not in result
        assert 'src="a.jpg"' in result

    def test_empty_tags(self):
        html = "<p>시작</p>[IMAGE_1]<p>끝</p>"
        result = inject_images(html, [])
        assert "[IMAGE_1]" not in result
