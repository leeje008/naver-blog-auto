"""네이버 블로그 XML-RPC 업로드 모듈."""

import re
import xmlrpc.client


class NaverPublisher:
    """네이버 블로그 MetaWeblog API 기반 업로드."""

    ENDPOINT = "https://api.blog.naver.com/xmlrpc"

    def __init__(self, blog_id: str, password: str):
        if not blog_id or not blog_id.strip():
            raise ValueError("네이버 블로그 ID가 설정되지 않았습니다. 설정 페이지에서 입력해 주세요.")
        if not password or not password.strip():
            raise ValueError("네이버 API 연동 암호가 설정되지 않았습니다. 설정 페이지에서 입력해 주세요.")
        self.client = xmlrpc.client.ServerProxy(self.ENDPOINT)
        self.blog_id = blog_id.strip()
        self.password = password.strip()

    def publish(self, title: str, html: str, tags: list[str] | None = None) -> str:
        """블로그 글 게시 후 post_id 반환."""
        post = {
            "title": title,
            "description": html,
        }
        if tags:
            post["mt_keywords"] = ",".join(tags)

        try:
            post_id = self.client.metaWeblog.newPost(
                self.blog_id,
                self.blog_id,
                self.password,
                post,
                True,
            )
            return str(post_id)
        except xmlrpc.client.Fault as e:
            raise RuntimeError(f"네이버 블로그 업로드 실패: {e.faultString}") from e
        except Exception as e:
            raise RuntimeError(f"네이버 블로그 업로드 중 오류: {e}") from e

    def get_post_url(self, post_id: str) -> str:
        """업로드된 포스트 URL 반환."""
        return f"https://blog.naver.com/{self.blog_id}/{post_id}"

    @staticmethod
    def inject_images(content_html: str, image_html_tags: list[str]) -> str:
        """이미지 플레이스홀더를 실제 HTML로 교체."""
        result = content_html
        for i, img_tag in enumerate(image_html_tags, 1):
            wrap = f'<div style="text-align:center;margin:20px 0;">{img_tag}</div>'
            result = result.replace(f"[IMAGE_{i}]", wrap)
            result = result.replace(f"{{{{IMAGE_{i}}}}}", wrap)

        result = re.sub(r"\[IMAGE_\d+\]", "", result)
        result = re.sub(r"\{\{IMAGE_\d+\}\}", "", result)
        return result
