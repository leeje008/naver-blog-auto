"""HTTP 클라이언트 유틸리티 — 속도 제한 포함."""

import time

import requests


class ThrottledSession(requests.Session):
    """요청 간 최소 간격을 보장하는 requests Session."""

    def __init__(self, min_interval: float = 0.5):
        super().__init__()
        self.min_interval = min_interval
        self._last_request_time = 0.0
        self.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def request(self, method, url, **kwargs):
        """요청 전 최소 간격만큼 대기."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.time()
        kwargs.setdefault("timeout", 10)
        return super().request(method, url, **kwargs)
